"""Étape 2 : score des moments forts et sélection des extraits, à valider à la main."""

from __future__ import annotations

import csv
import html
from pathlib import Path

import cv2
import numpy as np

from .analyze import episodes, load_analysis
from .config import Config
from .media import grab_frame

CSV_FIELDS = ["id", "keep", "episode", "file", "start", "end", "duration", "score", "peak"]


def selection_dir(cfg: Config) -> Path:
    return cfg.work / "selection"


def _robust_z(x: np.ndarray, valid: np.ndarray) -> np.ndarray:
    ref = x[valid] if valid.any() else x
    med = np.median(ref)
    spread = np.subtract(*np.percentile(ref, [75, 25])) or (ref.std() + 1e-6)
    return np.clip((x - med) / spread, -3, 3)


def _smooth(x: np.ndarray, n: int) -> np.ndarray:
    if n <= 1:
        return x
    return np.convolve(x, np.ones(n) / n, mode="same")


def moment_scores(cfg: Config, meta: dict, feats: dict) -> tuple[np.ndarray, np.ndarray]:
    """Score "intensité" par pas de temps, et masque des instants utilisables."""
    hop = meta["hop"]
    n = len(feats["loudness"])
    valid = np.ones(n, dtype=bool)
    a = cfg["analysis"]
    valid[: int(float(a["skip_start"]) / hop)] = False
    if float(a["skip_end"]) > 0:
        valid[n - int(float(a["skip_end"]) / hop):] = False
    for s, e in meta.get("excluded", []):
        valid[int(s / hop): int(np.ceil(e / hop))] = False
    valid &= feats["loudness"] > -60  # silence ou noir

    w = cfg["selection"]["weights"]
    cut_rate = _smooth(feats["cuts"], max(1, int(3 / hop)))
    score = (
        w["loudness"] * _robust_z(feats["loudness"], valid)
        + w["onset"] * _robust_z(feats["onset"], valid)
        + w["motion"] * _robust_z(feats["motion"], valid)
        + w["cut_rate"] * _robust_z(cut_rate, valid)
    )
    return _smooth(score, max(1, int(1 / hop))), valid


def candidate_windows(meta: dict, score: np.ndarray, valid: np.ndarray, min_s: float, max_s: float,
                      peak_w: float) -> list[dict]:
    """Fenêtres qui commencent et finissent sur des changements de plan."""
    hop = meta["hop"]
    dur = meta["duration"]
    bounds = sorted({0.0, *meta["cuts"], dur})
    out = []
    for i, start in enumerate(bounds[:-1]):
        for end in bounds[i + 1:]:
            length = end - start
            if length > max_s:
                end, length = start + max_s, max_s
            if length < min_s:
                continue
            b0, b1 = int(start / hop), max(int(start / hop) + 1, int(end / hop))
            if not valid[b0:b1].all():
                break
            seg = score[b0:b1]
            top = np.sort(seg)[-max(1, len(seg) // 10):].mean()
            out.append({
                "start": round(start, 3),
                "end": round(end, 3),
                "score": float(seg.mean() + peak_w * top),
                "peak": round(float(np.argmax(seg) * hop), 2),
            })
            if length >= max_s:
                break
    return out


def run_selection(cfg: Config) -> Path:
    s = cfg["selection"]
    min_s, max_s = float(s["min_seconds"]), float(s["max_seconds"])
    candidates = []
    for ep_idx, ep in enumerate(episodes(cfg), start=1):
        meta, feats = load_analysis(cfg, ep)
        score, valid = moment_scores(cfg, meta, feats)
        for c in candidate_windows(meta, score, valid, min_s, max_s, float(s["weights"]["peak"])):
            c.update(episode=ep_idx, file=str(ep))
            candidates.append(c)

    candidates.sort(key=lambda c: c["score"], reverse=True)
    chosen: list[dict] = []
    per_ep: dict[int, int] = {}
    for c in candidates:
        if len(chosen) >= int(s["clips_total"]):
            break
        if per_ep.get(c["episode"], 0) >= int(s["max_per_episode"]):
            continue
        overlap = any(o["episode"] == c["episode"] and c["start"] < o["end"] + 2 and o["start"] < c["end"] + 2
                      for o in chosen)
        if overlap:
            continue
        chosen.append(c)
        per_ep[c["episode"]] = per_ep.get(c["episode"], 0) + 1

    out = selection_dir(cfg)
    thumbs = out / "thumbs"
    thumbs.mkdir(parents=True, exist_ok=True)
    rows = []
    for rank, c in enumerate(chosen, start=1):
        clip_id = f"c{rank:02d}_ep{c['episode']:02d}_{int(c['start']):05d}"
        img = grab_frame(Path(c["file"]), c["start"] + c["peak"], width=360)
        if img is not None:
            cv2.imwrite(str(thumbs / f"{clip_id}.jpg"), img)
        rows.append({
            "id": clip_id, "keep": 1, "episode": c["episode"], "file": c["file"],
            "start": c["start"], "end": c["end"], "duration": round(c["end"] - c["start"], 2),
            "score": round(c["score"], 3), "peak": c["peak"],
        })

    csv_path = out / "clips.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    _write_review_page(out / "review.html", rows)
    print(f"{len(rows)} extraits proposés → {csv_path}")
    print(f"Aperçu : {out / 'review.html'}  (mettez keep=0 dans le CSV pour écarter un extrait)")
    return csv_path


def load_selection(cfg: Config) -> list[dict]:
    csv_path = selection_dir(cfg) / "clips.csv"
    if not csv_path.exists():
        raise SystemExit("Pas de sélection : lancez d'abord la commande `select`.")
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    clips = []
    for r in rows:
        if str(r.get("keep", "1")).strip() in ("0", "", "non", "no", "false"):
            continue
        for k in ("start", "end", "duration", "score", "peak"):
            r[k] = float(r[k])
        r["episode"] = int(r["episode"])
        clips.append(r)
    return clips


def _fmt(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def _write_review_page(path: Path, rows: list[dict]) -> None:
    cards = "\n".join(
        f"""<figure><img src="thumbs/{html.escape(r['id'])}.jpg" alt="">
<figcaption><b>{html.escape(r['id'])}</b><br>Épisode {r['episode']} · {_fmt(r['start'])} → {_fmt(r['end'])}
({r['duration']:.0f} s)<br>score {r['score']:.2f} · moment fort à +{r['peak']:.1f} s</figcaption></figure>"""
        for r in rows
    )
    path.write_text(f"""<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Extraits proposés</title>
<style>
body{{font-family:system-ui,sans-serif;margin:16px;background:#111;color:#eee}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
figure{{margin:0;background:#1d1d1d;border-radius:8px;overflow:hidden}}
img{{width:100%;display:block;aspect-ratio:16/9;object-fit:cover;background:#000}}
figcaption{{padding:8px 10px;font-size:13px;line-height:1.5}}
</style>
<h1>Extraits proposés ({len(rows)})</h1>
<p>Pour écarter un extrait, mettez <code>keep</code> à 0 dans <code>clips.csv</code>.</p>
<main>{cards}</main></html>""", encoding="utf-8")
