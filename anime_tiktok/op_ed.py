"""Repère les passages audio identiques entre épisodes (opening, ending, récap) pour les ignorer."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .analyze import load_analysis, save_meta
from .config import Config


def _unit(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=1, keepdims=True) + 1e-6)


def match_matrix(a: np.ndarray, b: np.ndarray, similarity: float, max_rms_db: float = 6.0) -> np.ndarray:
    """Vrai quand deux instants ont le même son : même spectre ET même évolution d'un instant au suivant.

    L'évolution (delta) évite de confondre deux passages stationnaires différents (bruit de fond,
    silence, note tenue), qui ont un spectre moyen proche sans être le même enregistrement.
    """
    da, db = np.diff(a, axis=0, prepend=a[:1]), np.diff(b, axis=0, prepend=b[:1])
    na, nb = np.linalg.norm(da, axis=1), np.linalg.norm(db, axis=1)
    active_a = na > 0.25 * np.median(na[na > 0]) if (na > 0).any() else na > 0
    active_b = nb > 0.25 * np.median(nb[nb > 0]) if (nb > 0).any() else nb > 0
    sim = (_unit(da) @ _unit(db).T) >= similarity
    sim &= active_a[:, None] & active_b[None, :]
    # Écart RMS des énergies par bande (log naturel -> dB : x 4.34)
    sq = (a ** 2).sum(1)[:, None] + (b ** 2).sum(1)[None, :] - 2 * a @ b.T
    rms_db = np.sqrt(np.maximum(sq, 0) / a.shape[1]) * 4.34
    return sim & (rms_db <= max_rms_db)


def long_runs(mask: np.ndarray, min_len: int, max_gap: int) -> list[tuple[int, int]]:
    """Plages [début, fin) de True d'au moins `min_len`, en tolérant des trous de `max_gap`."""
    runs: list[tuple[int, int]] = []
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return runs
    start = prev = idx[0]
    for i in idx[1:]:
        if i - prev > max_gap + 1:
            if prev + 1 - start >= min_len:
                runs.append((int(start), int(prev + 1)))
            start = i
        prev = i
    if prev + 1 - start >= min_len:
        runs.append((int(start), int(prev + 1)))
    return runs


def repeated_ranges(a: np.ndarray, b: np.ndarray, threshold: float, min_len: int, max_gap: int = 6) -> list[tuple[int, int]]:
    """Plages de `a` (en indices) dont l'audio se retrouve à l'identique dans `b`."""
    sim = match_matrix(a, b, threshold)
    found: list[tuple[int, int]] = []
    for k in range(-(sim.shape[0] - min_len), sim.shape[1] - min_len + 1):
        diag = np.diagonal(sim, offset=k)
        if diag.sum() < min_len * 0.6:
            continue
        row0 = max(0, -k)
        for s, e in long_runs(diag, min_len, max_gap):
            found.append((row0 + s, row0 + e))
    return found


def detect_op_ed(cfg: Config, eps: list[Path]) -> None:
    a = cfg["analysis"]
    hop = float(a["hop_seconds"])
    min_len = int(float(a["op_ed_min_seconds"]) / hop)
    threshold = float(a["op_ed_similarity"])
    data = [load_analysis(cfg, ep) for ep in eps]
    print("Recherche des génériques / récaps répétés entre épisodes…")
    for i, (meta, feats) in enumerate(data):
        mask = np.zeros(len(feats["bands"]), dtype=bool)
        # Comparaison avec deux autres épisodes (voisins) : suffisant pour OP/ED, et rapide.
        others = [j for j in (i - 1, i + 1, i + 2, i - 2) if 0 <= j < len(data) and j != i][:2]
        for j in others:
            for s, e in repeated_ranges(feats["bands"], data[j][1]["bands"], threshold, min_len):
                mask[s:e] = True
        ranges = [(round(s * hop, 2), round(e * hop, 2)) for s, e in long_runs(mask, 1, 0)]
        meta["excluded"] = ranges
        save_meta(cfg, meta)
        desc = ", ".join(f"{_fmt(s)}–{_fmt(e)}" for s, e in ranges) or "aucun"
        print(f"  {meta['name']} : passages ignorés {desc}")


def _fmt(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"
