"""Petites fonctions autour de ffmpeg / ffprobe."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

VIDEO_EXTS = {".mkv", ".mp4", ".webm", ".mov", ".avi", ".m4v", ".ts"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def require_ffmpeg() -> None:
    for exe in ("ffmpeg", "ffprobe"):
        if shutil.which(exe) is None:
            raise SystemExit(f"{exe} est introuvable. Installez-le (apt install ffmpeg) avant de continuer.")


def run(cmd: list, quiet: bool = True) -> subprocess.CompletedProcess:
    cmd = [str(c) for c in cmd]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        tail = "\n".join(res.stderr.strip().splitlines()[-15:])
        raise RuntimeError(f"Commande en échec ({res.returncode}) : {' '.join(cmd[:6])} …\n{tail}")
    if not quiet and res.stderr:
        print(res.stderr)
    return res


def ffmpeg(*args, quiet: bool = True) -> subprocess.CompletedProcess:
    return run(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-loglevel", "error", *args], quiet=quiet)


@dataclass
class VideoInfo:
    path: Path
    duration: float
    width: int
    height: int
    fps: float
    has_audio: bool


def probe(path: Path) -> VideoInfo:
    res = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path])
    data = json.loads(res.stdout)
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise RuntimeError(f"Pas de piste vidéo dans {path}")
    num, den = video.get("avg_frame_rate", "0/1").split("/")
    fps = float(num) / float(den) if float(den) else 0.0
    if fps <= 0:
        num, den = video.get("r_frame_rate", "24/1").split("/")
        fps = float(num) / float(den)
    duration = float(data["format"].get("duration") or video.get("duration") or 0)
    has_audio = any(s["codec_type"] == "audio" for s in data["streams"])
    return VideoInfo(path, duration, int(video["width"]), int(video["height"]), fps, has_audio)


def list_media(folder: Path, exts: set[str]) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.suffix.lower() in exts and p.is_file())


def read_audio(path: Path, rate: int = 16000, start: float | None = None, duration: float | None = None) -> np.ndarray:
    """Audio mono float32 dans [-1, 1]. Tableau vide si pas de son."""
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", str(path)]
    if duration is not None:
        cmd += ["-t", f"{duration:.3f}"]
    cmd += ["-vn", "-ac", "1", "-ar", str(rate), "-f", "s16le", "-"]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        return np.zeros(0, dtype=np.float32)
    return np.frombuffer(res.stdout, dtype=np.int16).astype(np.float32) / 32768.0


def iter_frames(path: Path, fps: float, width: int, height: int):
    """Décode la vidéo en basse résolution (BGR) image par image, sans tout charger en mémoire."""
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-i", str(path),
        "-vf", f"fps={fps},scale={width}:{height}:flags=area", "-an",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    size = width * height * 3
    try:
        while True:
            buf = proc.stdout.read(size)
            if len(buf) < size:
                break
            yield np.frombuffer(buf, dtype=np.uint8).reshape(height, width, 3)
    finally:
        proc.stdout.close()
        proc.wait()


def grab_frame(path: Path, t: float, width: int | None = None) -> np.ndarray | None:
    import cv2

    vf = ["-vf", f"scale={width}:-2"] if width else []
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-ss", f"{max(t, 0):.3f}",
        "-i", str(path), "-frames:v", "1", *vf, "-f", "image2pipe", "-vcodec", "png", "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or not res.stdout:
        return None
    return cv2.imdecode(np.frombuffer(res.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)


@lru_cache(maxsize=None)
def encoder_works(name: str) -> bool:
    try:
        ffmpeg("-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.2", "-c:v", name, "-f", "null", "-")
        return True
    except RuntimeError:
        return False


def pick_encoder(choice: str, intermediate: bool = False) -> str:
    """Encodeur GPU (NVENC) si possible. Sans GPU : H.264 rapide pour les extraits intermédiaires
    (x265 est ~10 fois plus lent en 4K à 120 fps), HEVC pour les vidéos finales."""
    if choice != "auto":
        return choice
    cpu = ("libx264", "libx265") if intermediate else ("libx265", "libx264")
    for name in ("hevc_nvenc", "h264_nvenc", *cpu):
        if encoder_works(name):
            return name
    raise SystemExit("Aucun encodeur vidéo utilisable trouvé dans ffmpeg.")


def nvenc_error() -> str | None:
    """Pourquoi NVENC ne marche pas (pilote trop ancien pour ce ffmpeg, pas de GPU…), ou None."""
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i",
                          "color=c=black:s=256x256:d=0.2", "-c:v", "hevc_nvenc", "-f", "null", "-"],
                         capture_output=True, text=True)
    if res.returncode == 0:
        return None
    lines = res.stderr.strip().splitlines() or ["erreur inconnue"]
    # la ligne utile (pilote trop ancien, pas de GPU…) précède souvent un message générique
    useful = [l for l in lines if any(k in l.lower() for k in ("nvenc", "driver", "cuda", "cannot load", "no capable"))]
    return (useful or lines)[0].strip()


def encoder_args(name: str, quality: int, fps: float, fast: bool = False) -> list[str]:
    """Paramètres d'encodage vidéo compatibles TikTok (mp4, yuv420p, faststart).
    fast=True : réglages rapides pour les fichiers intermédiaires."""
    gop = str(int(round(fps * 2)))
    if name == "hevc_nvenc":
        args = ["-c:v", name, "-preset", "p5", "-rc", "vbr", "-cq", str(quality), "-b:v", "0", "-tag:v", "hvc1"]
    elif name == "h264_nvenc":
        args = ["-c:v", name, "-preset", "p5", "-rc", "vbr", "-cq", str(quality), "-b:v", "0"]
    elif name == "libx265":
        args = ["-c:v", name, "-preset", "fast" if fast else "medium", "-crf", str(quality), "-tag:v", "hvc1",
                "-x265-params", "log-level=error"]
    else:
        args = ["-c:v", name, "-preset", "veryfast" if fast else "medium", "-crf", str(quality)]
    return args + ["-g", gop, "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
