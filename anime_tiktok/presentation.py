"""Présentations d'animés narrées : script -> voix off -> plans choisis selon le texte -> vidéo.

Deux étapes, pour pouvoir valider les plans entre les deux (depuis l'application) :
  plan   : voix off, minutage des phrases, plans candidats pour chaque créneau, vignettes ;
  render : rendu des plans retenus (vertical, interpolation, agrandissement) et montage final
           avec la voix, la musique de fond (baissée sous la voix) et le titre de l'animé.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

import cv2

from .config import Config
from .enhance import render_clip, resolve_backends
from .matching import plan_slots, resolve_matcher
from .media import AUDIO_EXTS, encoder_args, ffmpeg, grab_frame, list_media, pick_encoder
from .montage import _segment
from .script import parse_script
from .voice import resolve_voice_backend, synthesize

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def presentations_dir(cfg: Config) -> Path:
    return cfg.work / "presentations"


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "presentation"


def load_plan(cfg: Config, name: str) -> dict:
    p = presentations_dir(cfg) / name / "plan.json"
    if not p.exists():
        raise SystemExit(f"Présentation inconnue : {name}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_plan(cfg: Config, plan: dict) -> None:
    p = presentations_dir(cfg) / plan["name"] / "plan.json"
    p.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")


def make_plan(cfg: Config, name: str, script_text: str, music: str | None = None) -> dict:
    sentences = parse_script(script_text)
    if not sentences:
        raise SystemExit("Le script est vide.")
    folder = presentations_dir(cfg) / name
    shutil.rmtree(folder / "thumbs", ignore_errors=True)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "script.txt").write_text(script_text, encoding="utf-8")

    voice_path, timings = synthesize(cfg, sentences, folder)
    matcher = resolve_matcher(cfg)
    print(f"Choix des plans : {'CLIP (texte ↔ image)' if matcher == 'clip' else 'ambiance + beauté (sans CLIP)'}")
    slots = plan_slots(cfg, sentences, timings, matcher)

    thumbs = folder / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    for k, slot in enumerate(slots):
        for c, cand in enumerate(slot["candidates"]):
            img = grab_frame(Path(cand["file"]), (cand["start"] + cand["end"]) / 2, width=320)
            if img is not None:
                cv2.imwrite(str(thumbs / f"{k:03d}_{c}.jpg"), img)

    title = next((s.title for s in sentences if s.title), "")
    plan = {
        "name": name,
        "title": title,
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "duration": timings[-1]["end"],
        "voice": resolve_voice_backend(cfg),
        "matcher": matcher,
        "music": music,
        "sentences": [{"text": s.text, "emotion": s.emotion, "visual": s.visual, "title": s.title, **t}
                      for s, t in zip(sentences, timings)],
        "slots": slots,
    }
    save_plan(cfg, plan)
    print(f"Plan prêt : {len(sentences)} phrases, {len(slots)} plans, {plan['duration']:.0f} s")
    return plan


def find_font(cfg: Config) -> str | None:
    wanted = cfg["presentation"].get("font", "auto")
    if wanted and wanted != "auto":
        return wanted if Path(wanted).exists() else None
    for f in FONT_CANDIDATES:
        if Path(f).exists():
            return f
    try:
        res = subprocess.run(["fc-match", "-f", "%{file}", "sans:bold"], capture_output=True, text=True)
        if res.returncode == 0 and Path(res.stdout.strip()).exists():
            return res.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def _title_filter(text_file: Path, font: str, t0: float, t1: float) -> str:
    fade = 0.35
    alpha = (f"if(lt(t\\,{t0:.3f})\\,0\\,if(lt(t\\,{t0 + fade:.3f})\\,(t-{t0:.3f})/{fade}\\,"
             f"if(lt(t\\,{t1 - fade:.3f})\\,1\\,max(0\\,({t1:.3f}-t)/{fade}))))")
    return (f"drawtext=fontfile='{font}':textfile='{text_file}':fontsize=h/11:fontcolor=white:"
            f"borderw=6:bordercolor=black@0.75:shadowx=0:shadowy=8:shadowcolor=black@0.5:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-h*0.06:alpha='{alpha}':enable='between(t\\,{t0:.3f}\\,{t1:.3f})'")


def render_presentation(cfg: Config, name: str) -> Path:
    plan = load_plan(cfg, name)
    p, r = cfg["presentation"], cfg["render"]
    fps, size = float(r["fps"]), (int(r["width"]), int(r["height"]))
    folder = presentations_dir(cfg) / name
    backends = resolve_backends(cfg)
    print(f"Présentation « {name} » : {len(plan['slots'])} plans, {plan['duration']:.0f} s, "
          f"rendu {size[0]}x{size[1]} @ {fps:g} fps")

    # 1. Rendu de chaque plan retenu (partie centrale du plan, juste ce qu'il faut pour le créneau)
    sources = []
    for k, slot in enumerate(plan["slots"]):
        cand = slot["candidates"][slot["choice"]]
        need = slot["duration"] + 0.25
        mid = (cand["start"] + cand["end"]) / 2
        start = max(cand["start"], min(mid - need / 2, cand["end"] - need))
        clip = {"id": f"{name}_{k:03d}", "file": cand["file"], "start": round(start, 3),
                "end": round(min(cand["end"], start + need), 3)}
        print(f"  [{k + 1}/{len(plan['slots'])}] rendu du plan {clip['id']}")
        sources.append(render_clip(cfg, clip, "crop", backends))

    # 2. Montage : plans bout à bout, titre, voix et musique
    graph, labels = [], []
    for k, slot in enumerate(plan["slots"]):
        graph.append(_segment(f"{k}:v", f"s{k}", 0, slot["duration"], fps, size,
                              drift=float(p["drift_zoom"]), grade=p.get("grade") or None))
        labels.append(f"[s{k}]")
    total = plan["duration"]
    video = f"concat=n={len(labels)}:v=1:a=0,trim=duration={total:.3f}"
    font = find_font(cfg) if p.get("title_card", True) else None
    title_sentence = next((s for s in plan["sentences"] if s.get("title")), None)
    if title_sentence and font:
        text_file = folder / "title.txt"
        text_file.write_text(title_sentence["title"].upper(), encoding="utf-8")
        t0, t1 = title_sentence["start"], min(total, title_sentence["end"] + 1.2)
        video += "," + _title_filter(text_file, font, t0, t1)
    elif title_sentence:
        print("  (pas de police trouvée : titre non affiché)")
    graph.append("".join(labels) + video + "[outv]")

    n = len(sources)
    inputs: list[str] = []
    for s in sources:
        inputs += ["-i", str(s)]
    inputs += ["-i", str(folder / "voice.wav")]
    graph.append(f"[{n}:a]aformat=sample_rates=48000:channel_layouts=stereo,apad[voice]")
    music = plan.get("music")
    tracks = list_media(cfg.path("music"), AUDIO_EXTS)
    music_path = (cfg.path("music") / music) if music else (tracks[0] if tracks and p.get("auto_music") else None)
    if music_path and Path(music_path).exists():
        inputs += ["-stream_loop", "-1", "-i", str(music_path)]
        vol = float(p["music_volume"])
        graph += [
            f"[{n + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={vol}[bgm]",
            "[voice]asplit=2[vkey][vmix]",
            "[bgm][vkey]sidechaincompress=threshold=0.03:ratio=8:attack=15:release=350[duck]",
            f"[vmix][duck]amix=inputs=2:duration=first:normalize=0,"
            f"afade=t=out:st={max(0.0, total - 1.5):.3f}:d=1.5[outa]",
        ]
    else:
        graph.append("[voice]anull[outa]")

    out_dir = cfg.path("output") / f"{dt.datetime.now():%Y-%m-%d_%H%M}_presentation"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{name}.mp4"
    codec = pick_encoder(r["encoder"])
    ffmpeg(*inputs, "-filter_complex", ";".join(graph), "-map", "[outv]", "-map", "[outa]",
           "-t", f"{total:.3f}", *encoder_args(codec, int(r["quality"]), fps),
           "-c:a", "aac", "-b:a", r["audio_bitrate"], out)
    title = plan.get("title") or cfg["delivery"].get("anime", "")
    tag = re.sub(r"[^0-9a-zA-Z]", "", unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower())
    caption = f"{title} — à regarder absolument 👀\n#anime #{tag or 'anime'} #animerecommendation #pourtoi #fyp"
    out.with_suffix(".txt").write_text(caption, encoding="utf-8")
    print(f"Terminé → {out}")
    return out
