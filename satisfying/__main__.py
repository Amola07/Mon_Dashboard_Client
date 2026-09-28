"""Génère une vidéo « oddly satisfying » : python -m satisfying [--concept auto] [--out output/satisfying]."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import tempfile
import time
from pathlib import Path

import numpy as np

from . import concepts
from .engine import PALETTES, TIMBRES, Ctx, FPS, Painter, Sound, Video, mux

HISTORY = Path(__file__).with_name("history.json")
HASHTAGS = "#oddlysatisfying #satisfying #asmr #relaxing #hypnotique #satisfaisant #fyp #pourtoi"
CAPTIONS = [
    "Regarde jusqu'à la fin 🤍", "Impossible d'arrêter de regarder", "Ton moment de calme de la journée",
    "Le son à la fin… 🎧", "Mets le son 🔊", "Tu l'as regardé combien de fois ?", "Juste… satisfaisant",
    "Respire. Regarde. 🌙",
]


def load_history():
    try:
        return json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def pick_concept(history, rnd):
    """Le concept utilisé le moins récemment (au hasard parmi les jamais utilisés)."""
    last = {h["concept"]: i for i, h in enumerate(history)}
    never = [n for n in concepts.NAMES if n not in last]
    if never:
        return rnd.choice(never)
    return min(concepts.NAMES, key=lambda n: last[n])


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m satisfying", description=__doc__)
    ap.add_argument("--concept", default="auto", help="auto ou " + ", ".join(concepts.NAMES))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--palette", default="auto", help="auto ou " + ", ".join(p.name for p in PALETTES))
    ap.add_argument("--timbre", default="auto", help="auto ou " + ", ".join(TIMBRES))
    ap.add_argument("--seconds", type=float, default=64.0, help="durée visée (au moins 61 s pour être rémunérable)")
    ap.add_argument("--out", default="output/satisfying")
    ap.add_argument("--preview", type=float, default=None, help="ne rend que les N premières secondes (test rapide)")
    ap.add_argument("--no-history", action="store_true", help="ne pas noter la vidéo dans history.json")
    a = ap.parse_args(argv)

    history = load_history()
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(1 << 31)
    rnd = random.Random(seed)
    name = pick_concept(history, rnd) if a.concept == "auto" else a.concept
    module = concepts.load(name)
    if a.palette == "auto":
        recent = {h.get("palette") for h in history[-2:]}
        pal = rnd.choice([p for p in PALETTES if p.name not in recent] or PALETTES)
    else:
        pal = next((p for p in PALETTES if p.name == a.palette), None)
        if pal is None:
            raise SystemExit(f"Palette inconnue : {a.palette}")
    rng = np.random.default_rng(seed)
    sound = Sound(np.random.default_rng(seed + 1), timbre="" if a.timbre == "auto" else a.timbre)

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{dt.date.today():%Y-%m-%d}_{name}_{seed}"
    out = out_dir / f"{stem}.mp4"
    print(f"Concept : {module.TITLE} | palette {pal.name} | son {sound.timbre} en {sound.key} | graine {seed}", flush=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        video = Video(tmp / "video.mp4", preview=a.preview is not None)
        ctx = Ctx(rng=rng, pal=pal, painter=Painter(pal), sound=sound, video=video, seconds=a.seconds,
                  max_frames=int(a.preview * FPS) if a.preview else None)
        module.render(ctx)
        video.close()
        duration = video.frames / FPS
        sound.render(duration, tmp / "audio.wav")
        mux(tmp / "video.mp4", tmp / "audio.wav", out)
    caption = f"{rnd.choice(CAPTIONS)}\n\n{HASHTAGS}"
    out.with_suffix(".txt").write_text(caption + "\n", encoding="utf-8")
    print(f"{out} : {duration:.1f} s, rendu en {time.time() - t0:.0f} s", flush=True)
    if not a.no_history and a.preview is None:
        history.append({"date": f"{dt.date.today():%Y-%m-%d}", "concept": name, "seed": seed, "palette": pal.name,
                        "timbre": sound.timbre, "key": sound.key, "seconds": round(duration, 1)})
        HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    main()
