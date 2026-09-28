"""Étape 3 : rendu des extraits retenus en vertical, interpolés (120/240 fps) et agrandis (4K).

Chaîne pour un extrait :
  épisode --(découpe + recadrage 9:16 + suppression des images dupliquées)--> images basse résolution
          --(interpolation RIFE / ffmpeg)--> flux d'images au fps cible
          --(agrandissement Real-ESRGAN / Lanczos)--> encodeur ffmpeg --> extrait .mp4

Les images interpolées et agrandies passent en flux et par petits lots : l'espace disque reste faible,
même en 4K à 240 fps.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Iterator

import cv2
import numpy as np

from .analyze import load_analysis
from .config import Config
from .media import encoder_args, ffmpeg, pick_encoder
from .reframe import reframe_filter

RIFE_CHUNK = 96


# --------------------------------------------------------------------------- détection des outils

def _tiny_frames(folder: Path, n: int = 2) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        img = np.full((64, 64, 3), 40 + 80 * i, dtype=np.uint8)
        cv2.imwrite(str(folder / f"{i + 1:08d}.png"), img)


@lru_cache(maxsize=None)
def rife_works(binary: str, model: str, scratch: str) -> bool:
    if not Path(binary).exists():
        return False
    src, dst = Path(scratch) / "rife_in", Path(scratch) / "rife_out"
    shutil.rmtree(dst, ignore_errors=True)
    _tiny_frames(src)
    dst.mkdir(parents=True)
    res = subprocess.run([binary, "-i", str(src), "-o", str(dst), "-n", "4", "-m", model],
                         capture_output=True, text=True)
    ok = res.returncode == 0 and len(list(dst.glob("*.png"))) == 4
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    return ok


@lru_cache(maxsize=None)
def ncnn_upscaler_works(binary: str, model: str, scratch: str) -> bool:
    if not Path(binary).exists():
        return False
    src, dst = Path(scratch) / "esr_in", Path(scratch) / "esr_out"
    shutil.rmtree(dst, ignore_errors=True)
    _tiny_frames(src, 1)
    dst.mkdir(parents=True)
    res = subprocess.run([binary, "-i", str(src), "-o", str(dst), "-n", model, "-s", "2", "-f", "png"],
                         capture_output=True, text=True)
    ok = res.returncode == 0 and len(list(dst.glob("*.png"))) == 1
    shutil.rmtree(src, ignore_errors=True)
    shutil.rmtree(dst, ignore_errors=True)
    return ok


@lru_cache(maxsize=None)
def torch_works(model_path: str) -> bool:
    try:
        import spandrel  # noqa: F401
        import torch
    except ImportError:
        return False
    return torch.cuda.is_available() and Path(model_path).exists()


def resolve_backends(cfg: Config) -> tuple[str, str]:
    r = cfg["render"]
    scratch = str(cfg.tmp)
    rife_bin = str(cfg.tool("rife_ncnn"))
    rife_model = str(Path(rife_bin).parent / cfg["tools"]["rife_model"])
    esr_bin = str(cfg.tool("realesrgan_ncnn"))
    esr_model = cfg["tools"]["realesrgan_model"]

    interp = r["interpolation"]
    if interp == "auto":
        interp = "rife" if rife_works(rife_bin, rife_model, scratch) else "ffmpeg"
    up = r["upscaler"]
    if up == "auto":
        if torch_works(str(cfg.tool("torch_model"))):
            up = "torch"
        elif ncnn_upscaler_works(esr_bin, esr_model, scratch):
            up = "ncnn"
        else:
            up = "lanczos"
    return interp, up


# --------------------------------------------------------------------------- interpolation

def _index_map(n_in: int, n_out: int) -> list[int]:
    return [min(n_in - 1, int(i * n_in / n_out)) for i in range(n_out)]


def interp_none(files: list[Path], n_out: int) -> Iterator[np.ndarray]:
    cache_idx, cache_img = -1, None
    for idx in _index_map(len(files), n_out):
        if idx != cache_idx:
            cache_idx, cache_img = idx, cv2.imread(str(files[idx]))
        yield cache_img


def interp_ffmpeg(files: list[Path], n_out: int, duration: float, fps: float, size: tuple[int, int]) -> Iterator[np.ndarray]:
    w, h = size
    rate = len(files) / duration
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
        "-framerate", f"{rate:.6f}", "-i", str(files[0].parent / "%08d.png"),
        "-vf", f"minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1",
        "-frames:v", str(n_out), "-f", "rawvideo", "-pix_fmt", "bgr24", "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    count, last = 0, None
    try:
        while count < n_out:
            buf = proc.stdout.read(w * h * 3)
            if len(buf) < w * h * 3:
                break
            last = np.frombuffer(buf, dtype=np.uint8).reshape(h, w, 3)
            count += 1
            yield last
    finally:
        proc.stdout.close()
        proc.wait()
    while count < n_out and last is not None:  # complète si ffmpeg rend une image de moins
        count += 1
        yield last


def interp_rife(files: list[Path], n_out: int, binary: Path, model: Path, scratch: Path) -> Iterator[np.ndarray]:
    """RIFE par lots d'images (avec une image de recouvrement) pour limiter l'espace disque."""
    n_in = len(files)
    ratio = n_out / n_in
    produced = 0
    for i0 in range(0, n_in, RIFE_CHUNK):
        i1 = min(n_in, i0 + RIFE_CHUNK)  # images [i0, i1) à couvrir
        keep = round(i1 * ratio) - produced
        if keep <= 0:
            continue
        if i1 - i0 == 1 and i1 == n_in:  # dernière image seule : rien à interpoler
            last = cv2.imread(str(files[i0]))
            for _ in range(keep):
                yield last
            produced += keep
            continue
        chunk_in, chunk_out = scratch / "rife_in", scratch / "rife_out"
        for d in (chunk_in, chunk_out):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)
        src = files[i0:min(n_in, i1 + 1)]  # + l'image suivante pour interpoler jusqu'à elle
        for k, f in enumerate(src):
            (chunk_in / f"{k + 1:08d}.png").symlink_to(f.resolve())
        n_req = max(keep, round(len(src) * ratio))  # même espacement temporel que le rendu global
        subprocess.run([str(binary), "-i", str(chunk_in), "-o", str(chunk_out), "-n", str(n_req), "-m", str(model)],
                       check=True, capture_output=True)
        outs = sorted(chunk_out.glob("*.png"))
        if not outs:
            raise RuntimeError("RIFE n'a produit aucune image")
        for idx in _index_map(len(outs), n_req)[:keep]:
            yield cv2.imread(str(outs[idx]))
        produced += keep
    shutil.rmtree(scratch / "rife_in", ignore_errors=True)
    shutil.rmtree(scratch / "rife_out", ignore_errors=True)


# --------------------------------------------------------------------------- agrandissement

class LanczosUpscaler:
    scale = 1

    def upscale(self, frames: list[np.ndarray]) -> list[np.ndarray]:
        return frames


class TorchUpscaler:
    """Real-ESRGAN (ou tout modèle compatible spandrel) sur GPU CUDA, en demi-précision."""

    def __init__(self, model_path: Path):
        import torch
        from spandrel import ModelLoader

        self.torch = torch
        self.model = ModelLoader().load_from_file(str(model_path)).cuda().eval()
        self.half = bool(self.model.supports_half)
        if self.half:
            self.model.half()
        self.scale = self.model.scale

    def upscale(self, frames: list[np.ndarray]) -> list[np.ndarray]:
        torch = self.torch
        x = torch.from_numpy(np.ascontiguousarray(np.stack(frames)[..., ::-1])).cuda()
        x = x.permute(0, 3, 1, 2)
        x = (x.half() if self.half else x.float()) / 255.0
        with torch.inference_mode():
            y = self.model(x)
        y = (y.clamp(0, 1) * 255).round().to(torch.uint8).permute(0, 2, 3, 1).cpu().numpy()
        return [np.ascontiguousarray(f[..., ::-1]) for f in y]


class NcnnUpscaler:
    """realesrgan-ncnn-vulkan (GPU via Vulkan), appelé par petits lots d'images."""

    def __init__(self, binary: Path, model: str, scale: int, scratch: Path):
        self.binary, self.model, self.scale, self.scratch = binary, model, scale, scratch

    def upscale(self, frames: list[np.ndarray]) -> list[np.ndarray]:
        src, dst = self.scratch / "esr_in", self.scratch / "esr_out"
        for d in (src, dst):
            shutil.rmtree(d, ignore_errors=True)
            d.mkdir(parents=True)
        for k, f in enumerate(frames):
            cv2.imwrite(str(src / f"{k:08d}.png"), f, [cv2.IMWRITE_PNG_COMPRESSION, 1])
        subprocess.run([str(self.binary), "-i", str(src), "-o", str(dst), "-n", self.model,
                        "-s", str(self.scale), "-f", "png"], check=True, capture_output=True)
        return [cv2.imread(str(dst / f"{k:08d}.png")) for k in range(len(frames))]


def make_upscaler(cfg: Config, backend: str, factor: float):
    if backend == "lanczos" or factor <= 1.05:
        return LanczosUpscaler()
    if backend == "torch":
        return TorchUpscaler(cfg.tool("torch_model"))
    if backend == "ncnn":
        scale = min(4, max(2, math.ceil(factor)))
        return NcnnUpscaler(cfg.tool("realesrgan_ncnn"), cfg["tools"]["realesrgan_model"], scale, cfg.tmp)
    raise SystemExit(f"Agrandisseur inconnu : {backend!r}")


# --------------------------------------------------------------------------- encodage

class FrameEncoder:
    def __init__(self, out: Path, size: tuple[int, int], fps: float, audio: Path, codec: str, quality: int, abr: str):
        w, h = size
        cmd = [
            "ffmpeg", "-hide_banner", "-nostdin", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-framerate", str(fps), "-i", "-",
            "-i", str(audio), "-map", "0:v", "-map", "1:a",
            *encoder_args(codec, quality, fps), "-c:a", "aac", "-b:a", abr, "-shortest", str(out),
        ]
        self.size = size
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    def write(self, frame: np.ndarray) -> None:
        w, h = self.size
        if frame.shape[1] != w or frame.shape[0] != h:
            interp = cv2.INTER_AREA if frame.shape[0] > h else cv2.INTER_LANCZOS4
            frame = cv2.resize(frame, (w, h), interpolation=interp)
        self.proc.stdin.write(np.ascontiguousarray(frame).tobytes())

    def close(self) -> None:
        self.proc.stdin.close()
        err = self.proc.stderr.read().decode(errors="replace")
        if self.proc.wait() != 0:
            raise RuntimeError(f"Encodage en échec :\n{err[-2000:]}")


# --------------------------------------------------------------------------- rendu d'un extrait

def rendered_path(cfg: Config, clip: dict, mode: str) -> Path:
    return cfg.work / "rendered" / mode / f"{clip['id']}.mp4"


def render_clip(cfg: Config, clip: dict, mode: str, backends: tuple[str, str]) -> Path:
    r = cfg["render"]
    size = (int(r["width"]), int(r["height"]))
    fps = float(r["fps"])
    out = rendered_path(cfg, clip, mode)
    settings = {"clip": [clip["file"], clip["start"], clip["end"]], "size": size, "fps": fps,
                "dedupe": bool(r["dedupe"]), "backends": list(backends)}
    stamp = out.with_suffix(".json")
    if out.exists() and stamp.exists() and json.loads(stamp.read_text()) == settings:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)

    interp, up = backends
    meta, _ = load_analysis(cfg, Path(clip["file"]))
    vf, canvas = reframe_filter(cfg, mode, clip, meta)
    duration = clip["end"] - clip["start"]
    tmp = cfg.tmp / f"{clip['id']}_{mode}"
    frames_dir = tmp / "frames"
    shutil.rmtree(tmp, ignore_errors=True)
    frames_dir.mkdir(parents=True)

    # 1. Découpe + recadrage (+ suppression des images répétées de l'animation)
    if r["dedupe"] and interp != "none":
        vf_full, sync = f"{vf},mpdecimate", ["-fps_mode", "vfr"]
    else:
        vf_full, sync = vf, ["-fps_mode", "passthrough"]
    ffmpeg("-ss", f"{clip['start']:.3f}", "-i", clip["file"], "-t", f"{duration:.3f}", "-an",
           "-vf", f"{vf_full},format=rgb24", *sync, "-start_number", "1", frames_dir / "%08d.png")
    audio = tmp / "audio.wav"
    if meta["has_audio"]:
        ffmpeg("-ss", f"{clip['start']:.3f}", "-i", clip["file"], "-t", f"{duration:.3f}", "-vn",
               "-ac", "2", "-ar", "48000", audio)
    else:
        ffmpeg("-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", f"{duration:.3f}", audio)
    files = sorted(frames_dir.glob("*.png"))
    if not files:
        raise RuntimeError(f"Aucune image extraite pour {clip['id']}")

    # 2. Interpolation vers le fps cible
    n_out = max(1, round(duration * fps))
    if interp == "rife" and len(files) >= 2:
        rife_bin = cfg.tool("rife_ncnn")
        stream = interp_rife(files, n_out, rife_bin, rife_bin.parent / cfg["tools"]["rife_model"], tmp)
    elif interp == "ffmpeg" and len(files) >= 2:
        stream = interp_ffmpeg(files, n_out, duration, fps, canvas)
    else:
        stream = interp_none(files, n_out)

    # 3. Agrandissement + encodage
    upscaler = make_upscaler(cfg, up, size[1] / canvas[1])
    codec = pick_encoder(r["encoder"])
    enc = FrameEncoder(out, size, fps, audio, codec, int(r["intermediate_quality"]), r["audio_bitrate"])
    batch_size = int(r["torch_batch"]) if up == "torch" else int(r["ncnn_chunk"]) if up == "ncnn" else 16
    batch: list[np.ndarray] = []
    done, next_report = 0, 0.25

    def flush():
        nonlocal done, next_report
        for f in upscaler.upscale(batch):
            enc.write(f)
        done += len(batch)
        batch.clear()
        if done / n_out >= next_report:
            print(f"      {clip['id']} : {100 * done / n_out:.0f} %")
            next_report += 0.25

    try:
        for frame in stream:
            batch.append(frame)
            if len(batch) >= batch_size:
                flush()
        if batch:
            flush()
    finally:
        enc.close()
    shutil.rmtree(tmp, ignore_errors=True)
    stamp.write_text(json.dumps(settings))
    return out
