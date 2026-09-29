"""Version 3D (Blender Cycles) : python -m satisfying.render3d [--seed N] [--out output/satisfying3d].

La simulation et la bande-son viennent du moteur 2D ; Blender calcule l'image (verre, reflets, flou
de profondeur, flou de mouvement). Pensé pour un GPU (Kaggle) : on rend en 540×960 à 30 i/s, puis on
agrandit en 1080×1920 et on double la fluidité (RIFE si disponible, sinon ffmpeg).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

from .concepts import grow
from .engine import FPS, PALETTES, H, W, Sound, lerp_rgb

ROOT = Path(__file__).resolve().parent.parent
SCENES = Path(__file__).with_name("blender")
RING = 2.0


def find_blender(explicit: str | None):
    """Commande pour lancer une scène : Blender officiel (tools/blender) ou module Python bpy."""
    for cand in [explicit, os.environ.get("BLENDER"), str(ROOT / "tools/blender/blender"), shutil.which("blender")]:
        if cand and Path(cand).exists():
            return lambda scene, params: [cand, "-b", "--factory-startup", "-P", str(scene), "--", str(params)]
    try:
        import importlib.util
        if importlib.util.find_spec("bpy"):
            return lambda scene, params: [sys.executable, str(scene), str(params)]
    except (ImportError, ValueError):
        pass
    raise SystemExit("Blender introuvable : lancez scripts/setup_tools.sh (télécharge Blender dans tools/) "
                     "ou pip install bpy")


def interpolate(src: Path, dst: Path, n_out: int) -> bool:
    """Double la fluidité avec RIFE (Vulkan). Retourne False si RIFE n'est pas disponible."""
    rife = ROOT / "tools/rife-ncnn-vulkan/rife-ncnn-vulkan"
    if not rife.exists():
        return False
    dst.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([str(rife), "-i", str(src), "-o", str(dst), "-n", str(n_out), "-m",
                        str(rife.parent / "rife-v4.6"), "-f", "%08d.png"], capture_output=True, text=True)
    return r.returncode == 0 and len(list(dst.glob("*.png"))) >= n_out - 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m satisfying.render3d", description=__doc__)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--palette", default="auto")
    ap.add_argument("--seconds", type=float, default=64.0)
    ap.add_argument("--fps", type=int, default=30, help="images/s calculées par Blender (doublées ensuite)")
    ap.add_argument("--scale", type=float, default=0.5, help="résolution de rendu (0.5 = 540×960)")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--device", default="auto", choices=["auto", "cpu"])
    ap.add_argument("--preview", type=float, default=None, help="ne rend que N secondes (à partir de --start)")
    ap.add_argument("--start", type=float, default=0.0, help="début de l'aperçu (s)")
    ap.add_argument("--still", type=float, default=None, help="rend une seule image à cet instant (s)")
    ap.add_argument("--blender", default=None, help="chemin de l'exécutable blender")
    ap.add_argument("--out", default="output/satisfying3d")
    a = ap.parse_args(argv)

    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(1 << 31)
    rnd = random.Random(seed)
    pal = rnd.choice(PALETTES) if a.palette == "auto" else next(p for p in PALETTES if p.name == a.palette)
    rng = np.random.default_rng(seed)
    sound = Sound(np.random.default_rng(seed + 1))
    plan = grow.plan(rng, sound, a.seconds)
    frames = plan["frames"]
    total_s = len(frames) / FPS
    first = 0
    if a.preview:
        first = int(a.start * a.fps)
        total_s = min(total_s, a.start + a.preview)
    step = FPS / a.fps
    idx = [min(len(frames) - 1, int(round(i * step))) for i in range(first, int(total_s * a.fps))]
    cx, cy, R, r0 = plan["cx"], plan["cy"], plan["R"], plan["r0"]
    x = np.array([(frames[i][0][0] - cx) / R * RING for i in idx])
    z = np.array([-(frames[i][0][1] - cy) / R * RING for i in idx])
    rad = np.array([frames[i][1] / R * RING for i in idx])
    cols = np.array([lerp_rgb(pal.accents, (frames[i][1] - r0) / (R - 4 - r0)) for i in idx])

    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{dt.date.today():%Y-%m-%d}_grow3d_{seed}"
    run = find_blender(a.blender)
    print(f"Balle qui grossit en 3D | palette {pal.name} | son {sound.timbre} en {sound.key} | graine {seed} | "
          f"{len(idx)} images à calculer", flush=True)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "frames").mkdir()
        np.savez(tmp / "tracks.npz", x=x, z=z, r=rad, color=cols)
        params = {
            "tracks": str(tmp / "tracks.npz"), "frames_dir": str(tmp / "frames"), "fps": a.fps,
            "width": int(W * a.scale) // 2 * 2, "height": int(H * a.scale) // 2 * 2, "samples": a.samples,
            "device": a.device, "ring_radius": RING, "bg": pal.bg, "accent": pal.accents[int(rng.integers(5))],
            "nebula": pal.accents[int(rng.integers(5))], "neon_strength": float(rng.uniform(10, 16)),
            "cam_distance": 6.9, "cam_height": float(rng.uniform(0.2, 0.9)), "cam_swing_deg": float(rng.uniform(5, 12)),
        }
        if a.still is not None:
            params["still"] = max(1, int(a.still * a.fps))
        (tmp / "params.json").write_text(json.dumps(params), encoding="utf-8")
        proc = subprocess.Popen(run(SCENES / "grow_scene.py", tmp / "params.json"), stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, bufsize=1)
        def progress():  # compte les images écrites (les journaux de Blender varient selon la version)
            while proc.poll() is None:
                time.sleep(60)
                done = len(list((tmp / "frames").glob("f_*.png")))
                if done:
                    el = time.time() - t0
                    print(f"  {done}/{len(idx)} images, {el / done:.1f} s/image, "
                          f"reste ~{el / done * (len(idx) - done) / 60:.0f} min", flush=True)

        threading.Thread(target=progress, daemon=True).start()
        for line in proc.stdout:
            if line.startswith("Rendu sur") or "images en" in line or "Traceback" in line or "Error:" in line:
                print(line.rstrip(), flush=True)
        if proc.wait():
            raise SystemExit("Blender a échoué")
        if a.still is not None:
            dest = out_dir / f"{stem}_still.png"
            shutil.copy(tmp / "frames/still.png", dest)
            print(dest)
            return dest

        src, fps_in = tmp / "frames", a.fps
        if a.fps < FPS:
            n_out = len(idx) * (FPS // a.fps)
            if interpolate(src, tmp / "interp", n_out):
                src, fps_in = tmp / "interp", FPS
                print("  fluidité doublée avec RIFE", flush=True)
        # agrandissement + halo lumineux doux (bloom) autour des zones claires
        vf = [f"scale={W}:{H}:flags=lanczos,split[a][b];[b]gblur=sigma=22,eq=brightness=-0.06:contrast=1.3[g];"
              f"[a][g]blend=all_mode=screen:all_opacity=0.45"]
        if fps_in < FPS:
            vf.append(f"minterpolate=fps={FPS}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
            print("  fluidité doublée avec ffmpeg (RIFE absent)", flush=True)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(fps_in),
                        "-pattern_type", "glob", "-i", str(src / "*.png"), "-vf", ",".join(vf),
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", str(tmp / "video.mp4")],
                       check=True)
        duration = len(idx) / a.fps
        sound.render(first / a.fps + duration, tmp / "audio.wav")
        out = out_dir / f"{stem}.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp / "video.mp4"),
                        "-ss", f"{first / a.fps:.3f}", "-i", str(tmp / "audio.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
    out.with_suffix(".txt").write_text("Regarde jusqu'à la fin 🤍\n\n#oddlysatisfying #satisfying #asmr #3d "
                                       "#relaxing #hypnotique #fyp #pourtoi\n", encoding="utf-8")
    print(f"{out} : {duration:.1f} s, rendu en {(time.time() - t0) / 60:.0f} min", flush=True)
    return out


if __name__ == "__main__":
    main()
