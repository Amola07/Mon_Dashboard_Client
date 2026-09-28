"""Étape 1 : analyse de chaque épisode (plans, son, mouvement) sans IA payante."""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .config import Config
from .media import VIDEO_EXTS, iter_frames, list_media, probe, read_audio

AUDIO_RATE = 16000
N_FFT = 1024
FFT_HOP = 256
N_BANDS = 24


def analysis_dir(cfg: Config) -> Path:
    return cfg.work / "analysis"


def episodes(cfg: Config) -> list[Path]:
    eps = list_media(cfg.path("episodes"), VIDEO_EXTS)
    if not eps:
        raise SystemExit(f"Aucun épisode trouvé dans {cfg.path('episodes')}")
    return eps


def audio_features(samples: np.ndarray, n_bins: int, hop: float) -> dict[str, np.ndarray]:
    """Volume (dB), attaques sonores (spectral flux) et énergie par bandes, un point par `hop` secondes."""
    per_bin = int(round(hop * AUDIO_RATE))
    loud = np.full(n_bins, -90.0, dtype=np.float32)
    onset = np.zeros(n_bins, dtype=np.float32)
    bands = np.zeros((n_bins, N_BANDS), dtype=np.float32)
    if samples.size < N_FFT:
        return {"loudness": loud, "onset": onset, "bands": bands}

    freqs = np.fft.rfftfreq(N_FFT, 1 / AUDIO_RATE)
    edges = np.geomspace(60, 7000, N_BANDS + 1)
    band_idx = np.clip(np.digitize(freqs, edges) - 1, -1, N_BANDS)
    window = np.hanning(N_FFT).astype(np.float32)

    # Traitement par blocs d'une minute pour garder une mémoire raisonnable.
    bins_per_chunk = max(1, int(60 / hop))
    prev_logmag = None
    for b0 in range(0, n_bins, bins_per_chunk):
        b1 = min(n_bins, b0 + bins_per_chunk)
        seg = samples[b0 * per_bin: b1 * per_bin]
        if seg.size < N_FFT:
            break
        n_frames = 1 + (seg.size - N_FFT) // FFT_HOP
        idx = np.arange(N_FFT)[None, :] + FFT_HOP * np.arange(n_frames)[:, None]
        mag = np.abs(np.fft.rfft(seg[idx] * window, axis=1)).astype(np.float32)
        logmag = np.log1p(mag * 10)
        if prev_logmag is None:
            prev_logmag = logmag[:1]
        flux = np.maximum(0, np.diff(np.vstack([prev_logmag, logmag]), axis=0)).sum(axis=1)
        prev_logmag = logmag[-1:]
        power = mag ** 2
        band_power = np.zeros((n_frames, N_BANDS), dtype=np.float32)
        for b in range(N_BANDS):
            sel = band_idx == b
            if sel.any():
                band_power[:, b] = power[:, sel].mean(axis=1)
        frame_bin = (np.arange(n_frames) * FFT_HOP + N_FFT // 2) // per_bin
        for local in range(b1 - b0):
            m = frame_bin == local
            chunk = seg[local * per_bin:(local + 1) * per_bin]
            if chunk.size:
                loud[b0 + local] = 20 * np.log10(np.sqrt(np.mean(chunk ** 2)) + 1e-5)
            if m.any():
                onset[b0 + local] = flux[m].mean()
                bands[b0 + local] = np.log(band_power[m].mean(axis=0) + 1e-8)
    return {"loudness": loud, "onset": onset, "bands": bands}


def video_features(path: Path, n_bins: int, hop: float, sample_fps: float,
                   threshold: float, min_scene: float) -> tuple[np.ndarray, list[float]]:
    """Mouvement moyen par pas de temps et instants des changements de plan."""
    motion_sum = np.zeros(n_bins, dtype=np.float32)
    motion_cnt = np.zeros(n_bins, dtype=np.float32)
    cuts: list[float] = []
    prev_hist = prev_gray = None
    for i, frame in enumerate(iter_frames(path, sample_fps, 160, 90)):
        t = i / sample_fps
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [16, 4, 4], [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist, hist)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev_hist is not None:
            change = 1 - cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
            diff = float(np.mean(np.abs(gray - prev_gray))) / 255
            if change > threshold and diff > 0.06:
                if not cuts or t - cuts[-1] >= min_scene:
                    cuts.append(round(t, 3))
            else:
                b = int(t / hop)
                if b < n_bins:
                    motion_sum[b] += diff
                    motion_cnt[b] += 1
        prev_hist, prev_gray = hist, gray
    motion = np.divide(motion_sum, motion_cnt, out=np.zeros_like(motion_sum), where=motion_cnt > 0)
    return motion, cuts


def analyze_episode(cfg: Config, path: Path, force: bool = False) -> Path:
    out_dir = analysis_dir(cfg)
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / f"{path.stem}.json"
    if meta_path.exists() and not force:
        print(f"  ✓ {path.name} (déjà analysé)")
        return meta_path

    a = cfg["analysis"]
    hop = float(a["hop_seconds"])
    info = probe(path)
    n_bins = int(np.ceil(info.duration / hop))
    print(f"  … {path.name} ({info.duration / 60:.1f} min, {info.width}x{info.height} @ {info.fps:.2f} fps)")

    samples = read_audio(path, AUDIO_RATE) if info.has_audio else np.zeros(0, dtype=np.float32)
    feats = audio_features(samples, n_bins, hop)
    motion, cuts = video_features(path, n_bins, hop, float(a["sample_fps"]),
                                  float(a["scene_threshold"]), float(a["min_scene_seconds"]))
    cut_bins = np.zeros(n_bins, dtype=np.float32)
    for c in cuts:
        if int(c / hop) < n_bins:
            cut_bins[int(c / hop)] += 1

    np.savez_compressed(out_dir / f"{path.stem}.npz", motion=motion, cuts=cut_bins, **feats)
    meta = {
        "file": str(path),
        "name": path.name,
        "duration": info.duration,
        "width": info.width,
        "height": info.height,
        "fps": info.fps,
        "has_audio": info.has_audio,
        "hop": hop,
        "cuts": cuts,
        "excluded": [],
    }
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"  ✓ {path.name} : {len(cuts) + 1} plans détectés")
    return meta_path


def load_analysis(cfg: Config, path: Path) -> tuple[dict, dict[str, np.ndarray]]:
    d = analysis_dir(cfg)
    meta = json.loads((d / f"{path.stem}.json").read_text(encoding="utf-8"))
    with np.load(d / f"{path.stem}.npz") as z:
        feats = {k: z[k] for k in z.files}
    return meta, feats


def save_meta(cfg: Config, meta: dict) -> None:
    stem = Path(meta["file"]).stem
    (analysis_dir(cfg) / f"{stem}.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


def run_analysis(cfg: Config, force: bool = False) -> None:
    from .op_ed import detect_op_ed

    eps = episodes(cfg)
    print(f"Analyse de {len(eps)} épisode(s)")
    for ep in eps:
        analyze_episode(cfg, ep, force=force)
    if cfg["analysis"].get("detect_op_ed", True) and len(eps) >= 2:
        detect_op_ed(cfg, eps)
