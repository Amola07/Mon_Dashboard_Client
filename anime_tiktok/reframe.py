"""Passage du 16:9 au vertical 9:16 : recadrage qui suit l'action, ou image entière sur fond flouté."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from .config import Config
from .media import grab_frame

BLUR_CANVAS = (1080, 1920)

_cascade = None


def _face_cascade(cfg: Config):
    global _cascade
    if _cascade is None:
        path = cfg.tool("anime_face_cascade")
        _cascade = cv2.CascadeClassifier(str(path)) if path.exists() else False
        if _cascade is not False and _cascade.empty():
            _cascade = False
    return _cascade or None


def _focus_x(cfg: Config, frames: list[np.ndarray], crop_w: int) -> float | None:
    """Abscisse (0-1) du centre d'intérêt : visages d'animé en priorité, sinon zones de détail/mouvement."""
    h, w = frames[0].shape[:2]
    cascade = _face_cascade(cfg)
    if cascade is not None:
        centers, weights = [], []
        for f in frames:
            gray = cv2.equalizeHist(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
            for (x, y, fw, fh) in cascade.detectMultiScale(gray, 1.1, 4, minSize=(h // 12, h // 12)):
                centers.append(x + fw / 2)
                weights.append(fw * fh)
        if centers:
            return float(np.average(centers, weights=weights)) / w

    energy = np.zeros(w, dtype=np.float32)
    grays = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in frames]
    for g in grays:
        energy += np.abs(cv2.Laplacian(g, cv2.CV_32F)).sum(axis=0)
    for g0, g1 in zip(grays, grays[1:]):
        energy += 3 * np.abs(g1 - g0).sum(axis=0)
    if energy.sum() <= 0:
        return None
    win = max(1, int(crop_w * w))
    sums = np.convolve(energy, np.ones(win), mode="valid")
    best = int(np.argmax(sums))
    return (best + win / 2) / w


def crop_filter(cfg: Config, clip: dict, meta: dict) -> tuple[str, tuple[int, int]]:
    """Filtre ffmpeg de recadrage 9:16, avec une position fixe par plan (pas de tremblement)."""
    src_w, src_h = meta["width"], meta["height"]
    crop_w = int(round(src_h * 9 / 16 / 2)) * 2
    if crop_w >= src_w:
        return f"scale={src_w}:{src_h}", (src_w, src_h)
    start, end = clip["start"], clip["end"]
    cuts = [c - start for c in meta["cuts"] if start < c < end]
    bounds = [0.0, *cuts, end - start]
    path = Path(clip["file"])
    positions = []
    for s, e in zip(bounds, bounds[1:]):
        frames = [grab_frame(path, start + s + (e - s) * q, width=480) for q in (0.2, 0.5, 0.8)]
        frames = [f for f in frames if f is not None]
        fx = _focus_x(cfg, frames, crop_w / src_w) if frames else None
        x = (fx if fx is not None else 0.5) * src_w - crop_w / 2
        positions.append(int(np.clip(x, 0, src_w - crop_w)))
    expr = str(positions[-1])
    for cut, x in reversed(list(zip(bounds[1:-1], positions[:-1]))):
        expr = f"if(lt(t\\,{cut:.3f})\\,{x}\\,{expr})"
    return f"crop={crop_w}:{src_h}:x={expr}:y=0", (crop_w, src_h)


def blur_filter(target: tuple[int, int]) -> tuple[str, tuple[int, int]]:
    # Composition en 1080x1920 au plus : l'agrandissement IA se charge ensuite de la 4K.
    w, h = min(BLUR_CANVAS[0], target[0]), min(BLUR_CANVAS[1], target[1])
    graph = (
        f"split=2[bgsrc][fgsrc];"
        f"[bgsrc]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=24:2,eq=brightness=-0.08[bg];"
        f"[fgsrc]scale={w}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )
    return graph, (w, h)


def reframe_filter(cfg: Config, mode: str, clip: dict, meta: dict) -> tuple[str, tuple[int, int]]:
    if mode == "crop":
        return crop_filter(cfg, clip, meta)
    if mode == "blur":
        return blur_filter((int(cfg["render"]["width"]), int(cfg["render"]["height"])))
    raise SystemExit(f"Mode de recadrage inconnu : {mode!r} (crop ou blur)")
