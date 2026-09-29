"""Rendu d'un court métrage 3D : python -m films.render_film --film goutte --scene film [--scale 0.5] [--samples 96].

Film muet : Blender calcule les images (GPU conseillé : Kaggle), puis on agrandit en 1080×1920, on ajoute un
halo doux, la musique (accords, notes sur les moments clés) et les bruitages (vent, sifflement de la chute).
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np

from satisfying.engine import SR, Sound
from satisfying.render3d import find_blender

FILMS = Path(__file__).resolve().parent


def read_wav(path):
    with wave.open(str(path)) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32767
        return data.reshape(-1, w.getnchannels())


def write_wav(path, st):
    st = st / max(1e-9, np.abs(st).max() / 0.9)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(st.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


def film_music(tl, duration, path):
    """Musique en sections (ambiance différente par acte), fondues les unes dans les autres."""
    from satisfying.engine import PROGRESSIONS
    n = int(duration * SR)
    mix = np.zeros((n, 2))
    for i, (t0, t1, key, prog, timbre, pad) in enumerate(tl.MUSIC):
        snd = Sound(np.random.default_rng(10 + i), key=key, timbre=timbre, prog=PROGRESSIONS[prog])
        snd.bar = 4.0
        for t, step, vel in tl.CUES:
            if t0 <= t < t1:
                snd.hit(t, vel, step=step)
        for a0, a1, gap in tl.ARPEGGIO:
            t = max(a0, t0)
            while t < min(a1, t1):
                snd.hit(t, 0.45)
                t += gap
        if i == 0:
            for kind, keys in tl.BEDS:
                env = [tl.interp(keys, k / 60, ease=lambda u: u) for k in range(int(duration * 60))]
                snd.bed(kind, env, level=1.0)
        snd.render(duration, path.with_name(f"part{i}.wav"), pad_level=pad)
        part = read_wav(path.with_name(f"part{i}.wav"))[:n]
        tt = np.arange(len(part)) / SR
        fade = 1.5
        env = np.clip((tt - (t0 - fade)) / fade, 0, 1) * np.clip(((t1 + fade) - tt) / fade, 0, 1)
        if i == 0:
            env = np.clip(((t1 + fade) - tt) / fade, 0, 1)
        if i == len(tl.MUSIC) - 1:
            env = np.clip((tt - (t0 - fade)) / fade, 0, 1)
        mix[:len(part)] += part * env[:, None] / max(1e-9, np.abs(part).max())
    write_wav(path, mix)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m films.render_film", description=__doc__)
    ap.add_argument("--film", default="goutte")
    ap.add_argument("--scene", default="film", choices=["film", "pilote"])
    ap.add_argument("--step", type=int, default=1, help="n'image qu'une image sur N (brouillon rapide)")
    ap.add_argument("--no-grains", action="store_true", help="sans grains de sable (brouillon rapide)")
    ap.add_argument("--frames-dir", default=None, help="dossier des images (permet de reprendre un rendu interrompu)")
    ap.add_argument("--scale", type=float, default=0.5, help="0.5 = 540×960 (agrandi ensuite), 1 = 1080×1920")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--device", default="auto", choices=["auto", "cpu"])
    ap.add_argument("--still", type=int, default=None, help="rend une seule image (n°)")
    ap.add_argument("--blender", default=None)
    ap.add_argument("--out", default="output/films")
    a = ap.parse_args(argv)

    tl = importlib.import_module(f"films.{a.film}.{'film_timeline' if a.scene == 'film' else 'timeline'}")
    scene = FILMS / a.film / f"{a.scene}.py"
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    run = find_blender(a.blender)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        frames = Path(a.frames_dir) if a.frames_dir else tmp / "frames"
        frames.mkdir(parents=True, exist_ok=True)
        params = {"out": str(frames), "scale": a.scale, "samples": a.samples, "device": a.device, "step": a.step,
                  "grains": not a.no_grains}
        if a.still:
            params["still"] = a.still
        (tmp / "p.json").write_text(json.dumps(params), encoding="utf-8")
        n_total = (tl.f(tl.DURATION) - 1 + a.step - 1) // a.step
        proc = subprocess.Popen(run(scene, tmp / "p.json"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1)

        def progress():
            while proc.poll() is None:
                time.sleep(60)
                done = len(list(frames.glob("f_*.png")))
                if done:
                    el = time.time() - t0
                    print(f"  {done}/{n_total} images, {el / done:.1f} s/image, "
                          f"reste ~{el / done * (n_total - done) / 60:.0f} min", flush=True)

        threading.Thread(target=progress, daemon=True).start()
        for line in proc.stdout:
            if line.startswith("Rendu sur") or "Traceback" in line or "Error:" in line:
                print(line.rstrip(), flush=True)
        if proc.wait():
            raise SystemExit("Blender a échoué")
        if a.still:
            dest = out_dir / f"{a.film}_{a.still}.png"
            shutil.copy(frames / "still.png", dest)   # /tmp et /kaggle/working sont sur des disques différents
            print(f"{dest} : image calculée en {time.time() - t0:.0f} s", flush=True)
            return dest

        # image : agrandissement + halo doux
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(tl.FPS / a.step),
                        "-pattern_type", "glob", "-i", str(frames / "*.png"), "-vf",
                        "scale=1080:1920:flags=lanczos,format=gbrp,split[a][b];[b]gblur=sigma=24,eq=brightness=-0.05:contrast=1.25[g];"
                        "[a][g]blend=all_mode=screen:all_opacity=0.35,format=yuv420p",
                        "-r", str(tl.FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(tmp / "v.mp4")],
                       check=True)
        duration = (tl.f(tl.DURATION) - 1) / tl.FPS
        if hasattr(tl, "MUSIC"):
            film_music(tl, duration, tmp / "a.wav")
            out = out_dir / f"{a.film}.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp / "v.mp4"),
                            "-i", str(tmp / "a.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                            "-movflags", "+faststart", str(out)], check=True)
            print(f"{out} : {duration:.1f} s, rendu en {(time.time() - t0) / 60:.0f} min", flush=True)
            return out
        # pilote : nappe d'accords, notes aux moments clés, vent du désert, sifflement de la chute
        snd = Sound(np.random.default_rng(7), key="ré", timbre="cristal")
        for t, step, vel in tl.CUES:
            snd.hit(t, vel, step=step)
        env = np.clip(np.linspace(0.3, 1.0, int(duration * 60)), 0, 1)
        snd.bed("vent", env, level=0.8)
        whoosh = np.zeros(int(duration * 60))                  # la chute siffle de plus en plus fort
        i0, i1 = int(tl.FALL_START * 60), int(tl.LAND * 60)
        whoosh[i0:i1] = np.linspace(0, 1, i1 - i0) ** 2
        snd.bed("vent", whoosh, level=1.6)
        snd.render(duration, tmp / "music.wav", pad_level=0.6)
        music = read_wav(tmp / "music.wav")
        write_wav(tmp / "a.wav", music)
        out = out_dir / f"{a.film}_pilote.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp / "v.mp4"),
                        "-i", str(tmp / "a.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
    print(f"{out} : {duration:.1f} s, rendu en {(time.time() - t0) / 60:.0f} min", flush=True)
    return out


if __name__ == "__main__":
    main()
