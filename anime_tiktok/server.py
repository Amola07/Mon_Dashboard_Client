"""Serveur de contrôle à distance (utilisé par l'application mobile).

Il tourne là où tourne le pipeline (Kaggle, Colab, PC) et expose une API HTTP protégée par un mot de passe :
lancer l'analyse / la sélection / le rendu, suivre la progression, valider les extraits, regarder et
télécharger les vidéos, envoyer des musiques. Avec --tunnel, une adresse publique https est créée via
Cloudflare, et publiée (avec --ntfy-topic) sur un sujet ntfy.sh que l'application écoute pour se connecter
toute seule.
"""

from __future__ import annotations

import csv
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import Config, load_config
from .media import AUDIO_EXTS, VIDEO_EXTS, list_media

ROOT = Path(__file__).resolve().parents[1]
API_VERSION = 1

# Réglages modifiables depuis l'application (clé de config -> type)
REMOTE_SETTINGS = {
    "delivery.anime": str,
    "render.fps": int,
    "render.width": int,
    "render.height": int,
    "selection.clips_total": int,
    "selection.max_per_episode": int,
    "selection.min_seconds": float,
    "selection.max_seconds": float,
    "analysis.skip_start": float,
    "analysis.skip_end": float,
}


# --------------------------------------------------------------------------- notifications ntfy.sh

class Notifier:
    def __init__(self, topic: str | None, server: str = "https://ntfy.sh"):
        self.url = f"{server.rstrip('/')}/{topic}" if topic else None

    def send(self, title: str, message: str, tags: str = "") -> None:
        if not self.url:
            return
        req = urllib.request.Request(self.url, data=message.encode("utf-8"), method="POST",
                                     headers={"Title": title.encode("utf-8").decode("latin-1", "ignore"),
                                              "Tags": tags})
        try:
            urllib.request.urlopen(req, timeout=10).read()
        except OSError as exc:
            print(f"[ntfy] envoi impossible : {exc}")


# --------------------------------------------------------------------------- tâches en arrière-plan

@dataclass
class Job:
    id: str
    command: str
    args: list[str]
    status: str = "running"          # running | done | failed | cancelled
    started: float = field(default_factory=time.time)
    ended: float | None = None
    progress: float | None = None    # 0..1, None = indéterminé
    step: str = ""
    lines: deque = field(default_factory=lambda: deque(maxlen=500))
    line_count: int = 0
    total: int = 0
    current: int = 0

    def to_dict(self, with_log: bool = False) -> dict:
        d = {k: getattr(self, k) for k in ("id", "command", "args", "status", "started", "ended", "progress", "step")}
        if with_log:
            d["log"] = list(self.lines)
        return d


class Runner:
    """Exécute une commande du pipeline à la fois (dans un processus séparé) et suit sa progression."""

    def __init__(self, config_path: Path, base_sets: list[str], notifier: Notifier):
        self.config_path = config_path
        self.base_sets = base_sets
        self.notifier = notifier
        self.lock = threading.Lock()
        self.job: Job | None = None
        self.proc: subprocess.Popen | None = None

    def start(self, command: str, extra: list[str], sets: list[str]) -> Job:
        with self.lock:
            if self.job and self.job.status == "running":
                raise RuntimeError("Une tâche est déjà en cours")
            cmd = [sys.executable, "-u", "-m", "anime_tiktok", command, "--config", str(self.config_path)]
            for s in [*self.base_sets, *sets]:
                cmd += ["--set", s]
            cmd += extra
            job = Job(id=secrets.token_hex(4), command=command, args=extra)
            env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            self.proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         text=True, bufsize=1, env=env)
            self.job = job
        threading.Thread(target=self._follow, args=(job, self.proc), daemon=True).start()
        return job

    def cancel(self) -> bool:
        with self.lock:
            if self.job and self.job.status == "running" and self.proc:
                self.job.status = "cancelled"
                self.proc.terminate()
                return True
        return False

    def _follow(self, job: Job, proc: subprocess.Popen) -> None:
        for raw in proc.stdout:
            line = raw.rstrip()
            if not line:
                continue
            job.lines.append(line)
            job.line_count += 1
            _parse_progress(job, line)
        code = proc.wait()
        job.ended = time.time()
        if job.status == "running":
            job.status = "done" if code == 0 else "failed"
        if job.status == "done":
            job.progress = 1.0
        labels = {"analyze": "Analyse", "select": "Sélection", "make": "Rendu et montage", "download": "Téléchargement"}
        label = labels.get(job.command, job.command)
        minutes = (job.ended - job.started) / 60
        if job.status == "done":
            self.notifier.send(f"{label} terminé", f"{job.step or 'OK'} ({minutes:.0f} min)", "white_check_mark")
        elif job.status == "failed":
            self.notifier.send(f"{label} en échec", "\n".join(list(job.lines)[-3:]), "x")


_RE_TOTAL_EP = re.compile(r"Analyse de (\d+) épisode")
_RE_TOTAL_CLIPS = re.compile(r"Style « .+ » : (\d+) extrait")
_RE_RENDER = re.compile(r"\[(\d+)/(\d+)\] rendu de")
_RE_PERCENT = re.compile(r": (\d+) %$")


def _parse_progress(job: Job, line: str) -> None:
    text = line.strip()
    if m := _RE_TOTAL_EP.search(text):
        job.total, job.current, job.progress = int(m.group(1)), 0, 0.0
    elif job.command == "analyze" and text.startswith("✓") and job.total:
        job.current += 1
        job.progress = min(0.95, job.current / job.total)
    elif m := _RE_TOTAL_CLIPS.search(text):
        job.total, job.progress = int(m.group(1)), 0.0
    elif m := _RE_RENDER.search(text):
        job.current, job.total = int(m.group(1)), int(m.group(2))
        job.progress = 0.9 * (job.current - 1) / job.total
    elif (m := _RE_PERCENT.search(text)) and job.command == "make" and job.total:
        job.progress = 0.9 * (job.current - 1 + int(m.group(1)) / 100) / job.total
    elif text.startswith("montage") and job.command == "make":
        job.progress = max(job.progress or 0, 0.9)
    job.step = text


# --------------------------------------------------------------------------- application FastAPI

def create_app(config_path: Path, base_sets: list[str], token: str, notifier: Notifier,
               web_dir: Path | None = None):
    app = FastAPI(title="Anime TikTok Studio", version=str(API_VERSION))
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    runner = Runner(config_path, base_sets, notifier)

    def cfg() -> Config:
        return load_config(config_path, [*base_sets, *_settings_sets(cfg_base())])

    def cfg_base() -> Config:
        return load_config(config_path, base_sets)

    def settings_file() -> Path:
        return cfg_base().work / "remote_settings.json"

    def load_settings(c: Config | None = None) -> dict:
        p = (c or cfg_base()).work / "remote_settings.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def _settings_sets(c: Config) -> list[str]:
        return [f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in load_settings(c).items()]

    def auth(authorization: str | None = Header(None), token_q: str | None = Query(None, alias="token")):
        given = (authorization or "").removeprefix("Bearer ").strip() or token_q or ""
        if not secrets.compare_digest(given, token):
            raise HTTPException(401, "Mot de passe incorrect")

    def selection_csv(c: Config) -> Path:
        return c.work / "selection" / "clips.csv"

    def read_clips(c: Config) -> list[dict]:
        p = selection_csv(c)
        if not p.exists():
            return []
        with open(p, encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def write_clips(c: Config, rows: list[dict]) -> None:
        with open(selection_csv(c), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    def safe_child(base: Path, *parts: str) -> Path:
        p = base.joinpath(*parts).resolve()
        if base.resolve() not in p.parents:
            raise HTTPException(404, "Introuvable")
        return p

    @app.get("/api/ping")
    def ping():
        return {"app": "anime-tiktok", "version": API_VERSION}

    @app.get("/api/status", dependencies=[Depends(auth)])
    def status():
        c = cfg()
        eps = list_media(c.path("episodes"), VIDEO_EXTS)
        analyzed = sum((c.work / "analysis" / f"{e.stem}.json").exists() for e in eps)
        clips = read_clips(c)
        job = runner.job
        return {
            "job": job.to_dict() if job else None,
            "episodes": len(eps),
            "analyzed": analyzed,
            "clips": len(clips),
            "kept": sum(r.get("keep") == "1" for r in clips),
            "styles": list(c["styles"].keys()),
            "music": len(list_media(c.path("music"), AUDIO_EXTS)),
            "render": {k: c["render"][k] for k in ("width", "height", "fps")},
            "anime": c["delivery"].get("anime", ""),
        }

    @app.get("/api/settings", dependencies=[Depends(auth)])
    def get_settings():
        c = cfg()
        out = {}
        for key in REMOTE_SETTINGS:
            node = c
            for part in key.split("."):
                node = node[part]
            out[key] = node
        return out

    @app.put("/api/settings", dependencies=[Depends(auth)])
    def put_settings(values: dict):
        saved = load_settings()
        for key, value in values.items():
            if key not in REMOTE_SETTINGS:
                raise HTTPException(400, f"Réglage non modifiable : {key}")
            try:
                saved[key] = REMOTE_SETTINGS[key](value)
            except (TypeError, ValueError):
                raise HTTPException(400, f"Valeur invalide pour {key}")
        p = settings_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
        return get_settings()

    @app.get("/api/episodes", dependencies=[Depends(auth)])
    def get_episodes():
        c = cfg()
        out = []
        for e in list_media(c.path("episodes"), VIDEO_EXTS):
            meta_p = c.work / "analysis" / f"{e.stem}.json"
            meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else None
            out.append({
                "name": e.name,
                "size": e.stat().st_size,
                "analyzed": meta is not None,
                "duration": meta["duration"] if meta else None,
                "excluded": meta["excluded"] if meta else [],
            })
        return out

    @app.post("/api/jobs", dependencies=[Depends(auth)])
    def start_job(body: dict):
        command = body.get("command")
        extra: list[str] = []
        c = cfg()
        if command == "analyze":
            if body.get("force"):
                extra.append("--force")
        elif command == "select":
            pass
        elif command == "make":
            style = body.get("style", "brut")
            if style not in c["styles"]:
                raise HTTPException(400, f"Style inconnu : {style}")
            extra += ["--style", style]
            if body.get("music"):
                extra += ["--music", str(safe_child(c.path("music"), body["music"]))]
            if body.get("only"):
                extra += ["--only", *[str(x) for x in body["only"]]]
        elif command == "download":
            url = str(body.get("url", ""))
            if not url.startswith(("http://", "https://")):
                raise HTTPException(400, "Adresse de téléchargement invalide")
            return _start_download(url, c)
        else:
            raise HTTPException(400, "Commande inconnue (analyze, select, make, download)")
        try:
            job = runner.start(command, extra, _settings_sets(cfg_base()))
        except RuntimeError as exc:
            raise HTTPException(409, str(exc))
        return job.to_dict()

    def _start_download(url: str, c: Config):
        dest = c.path("episodes")
        name = Path(url.split("?")[0]).name or "episode.mp4"
        code = ("import sys,urllib.request,shutil,pathlib;"
                "u,d=sys.argv[1],pathlib.Path(sys.argv[2]);d.parent.mkdir(parents=True,exist_ok=True);"
                "r=urllib.request.urlopen(u);t=int(r.headers.get('Content-Length') or 0);n=0;f=open(d,'wb')\n"
                "while True:\n b=r.read(1<<20)\n if not b: break\n f.write(b);n+=len(b)\n"
                " print(f'téléchargement : {100*n//t} %' if t else f'{n>>20} Mo', flush=True)\n"
                "print('✓ '+d.name)")
        with runner.lock:
            if runner.job and runner.job.status == "running":
                raise HTTPException(409, "Une tâche est déjà en cours")
            job = Job(id=secrets.token_hex(4), command="download", args=[name])
            runner.proc = subprocess.Popen([sys.executable, "-c", code, url, str(dest / name)],
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            runner.job = job
        threading.Thread(target=runner._follow, args=(job, runner.proc), daemon=True).start()
        return job.to_dict()

    @app.post("/api/jobs/cancel", dependencies=[Depends(auth)])
    def cancel_job():
        return {"cancelled": runner.cancel()}

    @app.get("/api/jobs/current", dependencies=[Depends(auth)])
    def current_job():
        if not runner.job:
            raise HTTPException(404, "Aucune tâche")
        return runner.job.to_dict(with_log=True)

    @app.get("/api/clips", dependencies=[Depends(auth)])
    def get_clips():
        rows = read_clips(cfg())
        for r in rows:
            r["keep"] = r.get("keep") == "1"
            for k in ("start", "end", "duration", "score", "peak"):
                r[k] = float(r[k])
            r["episode"] = int(r["episode"])
            r["file"] = Path(r["file"]).name
        return rows

    @app.put("/api/clips/keep", dependencies=[Depends(auth)])
    def set_keep(body: dict):
        """{"keep": {"id1": true, "id2": false}}"""
        c = cfg()
        rows = read_clips(c)
        if not rows:
            raise HTTPException(404, "Pas de sélection")
        changes = body.get("keep", {})
        for r in rows:
            if r["id"] in changes:
                r["keep"] = "1" if changes[r["id"]] else "0"
        write_clips(c, rows)
        return {"kept": sum(r["keep"] == "1" for r in rows)}

    @app.get("/api/clips/{clip_id}/thumb", dependencies=[Depends(auth)])
    def clip_thumb(clip_id: str):
        c = cfg()
        p = safe_child(c.work / "selection" / "thumbs", f"{clip_id}.jpg")
        if not p.exists():
            raise HTTPException(404, "Pas de vignette")
        return FileResponse(p, media_type="image/jpeg")

    @app.get("/api/clips/{clip_id}/preview", dependencies=[Depends(auth)])
    def clip_preview(clip_id: str):
        """Aperçu léger (360p) de l'extrait source, généré à la demande."""
        c = cfg()
        row = next((r for r in read_clips(c) if r["id"] == clip_id), None)
        if row is None:
            raise HTTPException(404, "Extrait inconnu")
        out = safe_child(c.work / "selection" / "previews", f"{clip_id}.mp4")
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            start, dur = float(row["start"]), float(row["end"]) - float(row["start"])
            res = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
                                  "-ss", f"{start:.3f}", "-i", row["file"], "-t", f"{dur:.3f}",
                                  "-vf", "scale=-2:360", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                                  "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(out)],
                                 capture_output=True, text=True)
            if res.returncode != 0:
                out.unlink(missing_ok=True)
                raise HTTPException(500, "Aperçu impossible")
        return FileResponse(out, media_type="video/mp4")

    @app.get("/api/outputs", dependencies=[Depends(auth)])
    def get_outputs():
        base = cfg().path("output")
        out = []
        if base.exists():
            for d in sorted((p for p in base.iterdir() if p.is_dir()), reverse=True):
                videos = []
                for v in sorted(d.glob("*.mp4")):
                    cap = v.with_suffix(".txt")
                    videos.append({"name": v.name, "size": v.stat().st_size,
                                   "caption": cap.read_text(encoding="utf-8") if cap.exists() else ""})
                style = d.name.split("_", 2)[-1] if d.name.count("_") >= 2 else d.name
                out.append({"folder": d.name, "style": style, "created": d.stat().st_mtime, "videos": videos})
        return out

    @app.get("/api/outputs/{folder}/{name}", dependencies=[Depends(auth)])
    def get_output_file(folder: str, name: str):
        p = safe_child(cfg().path("output"), folder, name)
        if not p.exists():
            raise HTTPException(404, "Introuvable")
        return FileResponse(p, media_type="video/mp4" if p.suffix == ".mp4" else "text/plain",
                            filename=p.name)

    @app.delete("/api/outputs/{folder}", dependencies=[Depends(auth)])
    def delete_output(folder: str):
        p = safe_child(cfg().path("output"), folder)
        if p.is_dir():
            shutil.rmtree(p)
        return {"deleted": folder}

    @app.get("/api/music", dependencies=[Depends(auth)])
    def get_music():
        return [{"name": p.name, "size": p.stat().st_size} for p in list_media(cfg().path("music"), AUDIO_EXTS)]

    @app.post("/api/upload/{kind}", dependencies=[Depends(auth)])
    def upload(kind: str, file: UploadFile = File(...)):
        c = cfg()
        if kind == "music":
            dest_dir, exts = c.path("music"), AUDIO_EXTS
        elif kind == "episodes":
            dest_dir, exts = c.path("episodes"), VIDEO_EXTS
        else:
            raise HTTPException(400, "Type d'envoi inconnu (music, episodes)")
        name = Path(file.filename or "").name
        if Path(name).suffix.lower() not in exts:
            raise HTTPException(400, f"Format non pris en charge : {name}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = safe_child(dest_dir, name)
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f, length=1 << 20)
        return {"name": name, "size": dest.stat().st_size}

    app.state.runner = runner
    if web_dir and (web_dir / "index.html").exists():
        # Web app (version Safari / iPhone) servie à la racine : utilisable sans hébergeur.
        app.mount("/", NoCacheStaticFiles(directory=web_dir, html=True), name="webapp")
    return app


class NoCacheStaticFiles(StaticFiles):
    """Fichiers de la web app, revalidés à chaque visite (sinon Safari garde une ancienne version)."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


def find_web_dir() -> Path | None:
    """Build de la web app : branche web-build clonée par le notebook, ou build local de Flutter."""
    for candidate in (ROOT / "webapp", ROOT / "mobile" / "build" / "web"):
        if (candidate / "index.html").exists():
            return candidate
    return None


# --------------------------------------------------------------------------- tunnel Cloudflare

CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"


def start_tunnel(port: int, tools: Path, timeout: float = 60) -> str:
    exe = shutil.which("cloudflared") or str(tools / "cloudflared")
    if not Path(exe).exists():
        print("Téléchargement de cloudflared…")
        tools.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(CLOUDFLARED_URL, exe)
        os.chmod(exe, 0o755)
    proc = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    found: list[str] = []

    def reader():
        for line in proc.stdout:
            m = re.search(r"https://[-a-z0-9]+\.trycloudflare\.com", line)
            if m and not found:
                found.append(m.group(0))

    threading.Thread(target=reader, daemon=True).start()
    t0 = time.time()
    while not found and time.time() - t0 < timeout:
        if proc.poll() is not None:
            break
        time.sleep(0.5)
    if not found:
        raise SystemExit("Impossible d'ouvrir le tunnel Cloudflare (Internet est-il activé ?)")
    return found[0]


def serve(config_path: str, base_sets: list[str], port: int, token: str | None, tunnel: bool,
          ntfy_topic: str | None) -> None:
    import uvicorn

    token = token or os.environ.get("ANIME_TIKTOK_TOKEN") or secrets.token_urlsafe(9)
    notifier = Notifier(ntfy_topic)
    cfg = load_config(config_path, base_sets)
    web_dir = find_web_dir()
    app = create_app(Path(config_path).resolve(), base_sets, token, notifier, web_dir)
    url = f"http://127.0.0.1:{port}"
    if tunnel:
        # Le tunnel ne répond qu'une fois le serveur démarré : on le lance juste avant uvicorn.
        threading.Thread(target=_announce, args=(port, cfg.path("tools"), notifier, token), daemon=True).start()
    print("=" * 60)
    print(f"Serveur de contrôle sur le port {port}")
    print(f"Mot de passe : {token}")
    if web_dir:
        print(f"Web app (iPhone) servie depuis {web_dir}")
    if ntfy_topic:
        print(f"Sujet ntfy  : {ntfy_topic}  (l'application trouvera l'adresse toute seule)")
    print("=" * 60, flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def _announce(port: int, tools: Path, notifier: Notifier, token: str) -> None:
    public = None
    for attempt in range(1, 4):
        try:
            public = start_tunnel(port, tools)
            break
        except SystemExit as exc:
            print(f"[tunnel] tentative {attempt}/3 : {exc}", flush=True)
            time.sleep(5 * attempt)
    if public is None:
        print("[tunnel] échec : le serveur reste accessible seulement en local.", flush=True)
        notifier.send("Tunnel impossible", "Le serveur tourne mais sans adresse publique (Internet activé ?)", "warning")
        return
    print("=" * 60)
    print(f"Adresse publique : {public}")
    print("Dans l'application : Réglages → adresse + mot de passe (ou sujet ntfy)")
    print("=" * 60, flush=True)
    notifier.send("anime-tiktok-url", json.dumps({"url": public, "time": int(time.time())}), "satellite")
