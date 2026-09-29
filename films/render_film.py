"""Rendu d'un court métrage 3D : python -m films.render_film --film goutte [--scale 0.5] [--samples 96] [--voix].

Blender calcule les images (GPU conseillé : Kaggle), puis on agrandit en 1080×1920, on ajoute un halo doux,
la musique (accords, notes sur les moments clés, vent) et, avec --voix, la voix off Kokoro.
"""
from __future__ import annotations

import argparse
import importlib
import json
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


def voice_track(lines, duration):
    """Voix off française (Kokoro, voix ff_siwis) placée aux instants donnés ; None si Kokoro est absent."""
    try:
        from kokoro import KPipeline
    except ImportError:
        print("Kokoro absent : pas de voix off", flush=True)
        return None
    pipe = KPipeline(lang_code="f", repo_id="hexgrad/Kokoro-82M")
    track = np.zeros(int((duration + 1) * SR))
    for t0, text in lines:
        chunks = [np.asarray(audio, dtype=float) for _, _, audio in pipe(text, voice="ff_siwis", speed=0.92)]
        if not chunks:
            continue
        v = np.concatenate(chunks)
        v = np.interp(np.arange(int(len(v) * SR / 24000)) * 24000 / SR, np.arange(len(v)), v)   # 24 → 48 kHz
        i = int(t0 * SR)
        n = min(len(v), len(track) - i)
        track[i:i + n] += v[:n]
    return track[: int(duration * SR)]


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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m films.render_film", description=__doc__)
    ap.add_argument("--film", default="goutte")
    ap.add_argument("--scale", type=float, default=0.5, help="0.5 = 540×960 (agrandi ensuite), 1 = 1080×1920")
    ap.add_argument("--samples", type=int, default=96)
    ap.add_argument("--device", default="auto", choices=["auto", "cpu"])
    ap.add_argument("--voix", action="store_true", help="ajoute la voix off (Kokoro)")
    ap.add_argument("--still", type=int, default=None, help="rend une seule image (n°)")
    ap.add_argument("--blender", default=None)
    ap.add_argument("--out", default="output/films")
    a = ap.parse_args(argv)

    tl = importlib.import_module(f"films.{a.film}.timeline")
    scene = FILMS / a.film / "pilote.py"
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    run = find_blender(a.blender)
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        frames = tmp / "frames"
        frames.mkdir()
        params = {"out": str(frames), "scale": a.scale, "samples": a.samples, "device": a.device}
        if a.still:
            params["still"] = a.still
        (tmp / "p.json").write_text(json.dumps(params), encoding="utf-8")
        n_total = tl.f(tl.DURATION) - 1
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
            (frames / "still.png").rename(dest)
            print(dest)
            return dest

        # image : agrandissement + halo doux
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(tl.FPS),
                        "-pattern_type", "glob", "-i", str(frames / "*.png"), "-vf",
                        "scale=1080:1920:flags=lanczos,format=gbrp,split[a][b];[b]gblur=sigma=24,eq=brightness=-0.05:contrast=1.25[g];"
                        "[a][g]blend=all_mode=screen:all_opacity=0.35,format=yuv420p",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", str(tmp / "v.mp4")],
                       check=True)
        # son : nappe d'accords, notes aux moments clés, vent du désert, voix off
        duration = n_total / tl.FPS
        snd = Sound(np.random.default_rng(7), key="ré", timbre="cristal")
        for t, step, vel in tl.CUES:
            snd.hit(t, vel, step=step)
        env = np.clip(np.linspace(0.3, 1.0, int(duration * 60)), 0, 1)
        snd.bed("vent", env, level=0.8)
        snd.render(duration, tmp / "music.wav", pad_level=0.6)
        music = read_wav(tmp / "music.wav")
        voice = voice_track(tl.VOICE, duration) if a.voix else None
        if voice is not None:
            n = min(len(voice), len(music))
            level = np.convolve(np.abs(voice[:n]), np.ones(SR // 5) / (SR // 5), mode="same")
            duck = 1 - 0.55 * np.clip(level / max(1e-9, level.max()) * 4, 0, 1)
            music = music[:n] * duck[:, None] * 0.8 + voice[:n, None] * 1.1
        write_wav(tmp / "a.wav", music)
        out = out_dir / f"{a.film}_pilote.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(tmp / "v.mp4"),
                        "-i", str(tmp / "a.wav"), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                        "-movflags", "+faststart", str(out)], check=True)
    print(f"{out} : {duration:.1f} s, rendu en {(time.time() - t0) / 60:.0f} min", flush=True)
    return out


if __name__ == "__main__":
    main()
