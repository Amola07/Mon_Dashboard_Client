"""Voix off de synthèse, gratuite et locale.

- kokoro : Kokoro-82M (licence Apache 2.0, usage commercial autorisé), voix française « ff_siwis ».
  Tourne sur le GPU de Kaggle/Colab (ou le CPU, plus lentement).
- espeak : espeak-ng, voix robotique ; repli si Kokoro n'est pas installé (et pour les tests).

Chaque phrase est synthétisée séparément, à la vitesse de son émotion, puis suivie de son silence :
on obtient ainsi une piste voix et le minutage exact de chaque phrase pour caler les plans.
"""

from __future__ import annotations

import shutil
import subprocess
import wave
from functools import lru_cache
from pathlib import Path

import numpy as np

from .config import Config
from .script import Sentence

SAMPLE_RATE = 24000


@lru_cache(maxsize=1)
def _kokoro_pipeline():
    from kokoro import KPipeline

    return KPipeline(lang_code="f", repo_id="hexgrad/Kokoro-82M")


def kokoro_available() -> bool:
    try:
        import kokoro  # noqa: F401
    except ImportError:
        return False
    return True


def _kokoro(text: str, speed: float, voice: str) -> np.ndarray:
    pipeline = _kokoro_pipeline()
    parts = []
    for result in pipeline(text, voice=voice, speed=speed, split_pattern=None):
        audio = result.audio
        if audio is not None:
            parts.append(audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio))
    if not parts:
        raise RuntimeError(f"Kokoro n'a rien produit pour : {text!r}")
    return np.concatenate(parts).astype(np.float32)


def _espeak(text: str, speed: float, tmp: Path) -> np.ndarray:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if exe is None:
        raise SystemExit("Aucune voix disponible : installez Kokoro (pip install kokoro) ou espeak-ng.")
    raw = tmp / "espeak.wav"
    subprocess.run([exe, "-v", "fr", "-s", str(int(165 * speed)), "-w", str(raw), text], check=True,
                   capture_output=True)
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-i", str(raw),
                          "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(res.stdout, dtype=np.float32)


def _trim_silence(audio: np.ndarray, threshold: float = 0.01, keep: float = 0.05) -> np.ndarray:
    """Retire les silences en début/fin (les pauses sont gérées par le script)."""
    idx = np.flatnonzero(np.abs(audio) > threshold)
    if idx.size == 0:
        return audio
    k = int(keep * SAMPLE_RATE)
    return audio[max(0, idx[0] - k): idx[-1] + k]


def write_wav(path: Path, audio: np.ndarray) -> None:
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm.tobytes())


def resolve_voice_backend(cfg: Config) -> str:
    choice = cfg["presentation"]["voice"]
    if choice == "auto":
        return "kokoro" if kokoro_available() else "espeak"
    return choice


def synthesize(cfg: Config, sentences: list[Sentence], out_dir: Path) -> tuple[Path, list[dict]]:
    """Crée la piste voix (voice.wav) et renvoie le minutage de chaque phrase :
    [{"start": s, "speech_end": s, "end": s}] où end inclut le silence qui suit la phrase."""
    backend = resolve_voice_backend(cfg)
    voice_name = cfg["presentation"]["kokoro_voice"]
    base_speed = float(cfg["presentation"]["speed"])
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Voix off : {backend}" + (f" ({voice_name})" if backend == "kokoro" else ""))
    pieces, timings, t = [], [], 0.0
    for i, s in enumerate(sentences, start=1):
        speed = s.speed * base_speed
        audio = _kokoro(s.text, speed, voice_name) if backend == "kokoro" else _espeak(s.text, speed, out_dir)
        audio = _trim_silence(audio)
        pause = np.zeros(int(s.pause * SAMPLE_RATE), dtype=np.float32)
        speech = len(audio) / SAMPLE_RATE
        timings.append({"start": round(t, 3), "speech_end": round(t + speech, 3),
                        "end": round(t + speech + s.pause, 3)})
        t += speech + s.pause
        pieces += [audio, pause]
        print(f"  [{i}/{len(sentences)}] {s.emotion:>12} · {speech:4.1f} s · {s.text[:60]}")
    track = np.concatenate(pieces) if pieces else np.zeros(SAMPLE_RATE, dtype=np.float32)
    peak = float(np.abs(track).max()) or 1.0
    path = out_dir / "voice.wav"
    write_wav(path, track * (0.9 / peak))
    return path, timings
