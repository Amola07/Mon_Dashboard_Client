"""Choix des plans d'après le script : quel plan des épisodes illustre le mieux chaque phrase ?

1. Index des plans (une fois par épisode, mis en cache) : pour chaque plan, son image centrale est
   décrite par CLIP (OpenAI ViT-B/32) et on garde ses mesures visuelles (luminosité, mouvement…).
2. Pour chaque phrase, le texte (français) est projeté dans le même espace par le modèle CLIP
   multilingue de sentence-transformers ; on combine :
   - la ressemblance texte ↔ image (et l'indication {visuel: …} si elle est donnée),
   - l'ambiance voulue par l'émotion (tendu = sombre/agité, posé = calme/lumineux),
   - la beauté du plan, et un léger bonus d'ordre chronologique (l'histoire avance avec le script).
Sans CLIP (non installé), seuls les trois derniers critères sont utilisés.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from .analyze import episodes, load_analysis
from .config import Config
from .media import grab_frame
from .script import Sentence
from .select import _robust_z, moment_scores

IMAGE_MODEL = "openai/clip-vit-base-patch32"
TEXT_MODEL = "sentence-transformers/clip-ViT-B-32-multilingual-v1"


def clip_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError:
        return False
    return True


def resolve_matcher(cfg: Config) -> str:
    choice = cfg["presentation"]["matcher"]
    if choice == "auto":
        return "clip" if clip_available() else "simple"
    return choice


@lru_cache(maxsize=1)
def _image_model():
    import torch
    from transformers import CLIPModel, CLIPProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    return CLIPModel.from_pretrained(IMAGE_MODEL).to(device).eval(), CLIPProcessor.from_pretrained(IMAGE_MODEL), device


@lru_cache(maxsize=1)
def _text_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(TEXT_MODEL)


def _unit(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)


def embed_images(frames: list[np.ndarray]) -> np.ndarray:
    import torch
    from PIL import Image

    model, processor, device = _image_model()
    out = []
    for i in range(0, len(frames), 32):
        imgs = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames[i:i + 32]]
        inputs = processor(images=imgs, return_tensors="pt").to(device)
        with torch.no_grad():
            feats = model.get_image_features(**inputs)
        out.append(feats.float().cpu().numpy())
    return _unit(np.concatenate(out))


def embed_texts(texts: list[str]) -> np.ndarray:
    return _unit(np.asarray(_text_model().encode(texts, convert_to_numpy=True), dtype=np.float32))


# --------------------------------------------------------------------------- index des plans

def index_dir(cfg: Config) -> Path:
    return cfg.work / "index"


def build_index(cfg: Config, matcher: str) -> list[dict]:
    """Un enregistrement par épisode : plans utilisables, mesures et (si CLIP) embeddings."""
    p = cfg["presentation"]
    min_shot = float(p["min_shot"])
    out = []
    index_dir(cfg).mkdir(parents=True, exist_ok=True)
    for ep_idx, ep in enumerate(episodes(cfg), start=1):
        cache = index_dir(cfg) / f"{ep.stem}.npz"
        meta, feats = load_analysis(cfg, ep)
        if cache.exists():
            with np.load(cache) as z:
                data = {k: z[k] for k in z.files}
            if matcher != "clip" or "emb" in data:
                out.append({"episode": ep_idx, "file": str(ep), "duration": meta["duration"], **data})
                continue
        hop = meta["hop"]
        _, valid = moment_scores(cfg, meta, feats)
        bounds = sorted({0.0, *meta["cuts"], meta["duration"]})
        starts, ends = [], []
        for s, e in zip(bounds, bounds[1:]):
            s2, e2 = s + 0.1, e - 0.1
            b0, b1 = int(s2 / hop), max(int(s2 / hop) + 1, int(e2 / hop))
            if e2 - s2 >= min_shot and valid[b0:b1].all():
                starts.append(s2)
                ends.append(e2)
        starts_a, ends_a = np.array(starts, dtype=np.float32), np.array(ends, dtype=np.float32)

        def shot_mean(key):
            arr = feats.get(key)
            if arr is None:
                return np.zeros(len(starts_a), dtype=np.float32)
            return np.array([arr[int(s / hop):max(int(s / hop) + 1, int(e / hop))].mean()
                             for s, e in zip(starts_a, ends_a)], dtype=np.float32)

        data = {"start": starts_a, "end": ends_a,
                "brightness": shot_mean("brightness"), "motion": shot_mean("motion"),
                "colorfulness": shot_mean("colorfulness"), "contrast": shot_mean("contrast")}
        if matcher == "clip" and len(starts_a):
            print(f"  … {ep.name} : description de {len(starts_a)} plans (CLIP)")
            frames = [grab_frame(ep, float(s + e) / 2, width=336) for s, e in zip(starts_a, ends_a)]
            blank = np.zeros((189, 336, 3), dtype=np.uint8)
            data["emb"] = embed_images([f if f is not None else blank for f in frames]).astype(np.float16)
        np.savez_compressed(cache, **data)
        out.append({"episode": ep_idx, "file": str(ep), "duration": meta["duration"], **data})
    return out


# --------------------------------------------------------------------------- plan de montage

def plan_slots(cfg: Config, sentences: list[Sentence], timings: list[dict], matcher: str) -> list[dict]:
    """Découpe la narration en créneaux (~2 s) et propose, pour chacun, les meilleurs plans."""
    p = cfg["presentation"]
    target, n_cand = float(p["slot_seconds"]), int(p["candidates"])
    idx = [e for e in build_index(cfg, matcher) if len(e["start"])]
    if not idx:
        raise SystemExit("Aucun plan utilisable : analysez d'abord des épisodes.")

    # Tableaux « à plat » de tous les plans de tous les épisodes
    n_eps = max(e["episode"] for e in idx)
    files = np.concatenate([[e["file"]] * len(e["start"]) for e in idx])
    ep_no = np.concatenate([np.full(len(e["start"]), e["episode"]) for e in idx])
    start = np.concatenate([e["start"] for e in idx]).astype(np.float64)
    end = np.concatenate([e["end"] for e in idx]).astype(np.float64)
    ep_dur = np.concatenate([np.full(len(e["start"]), e["duration"]) for e in idx])
    valid = np.ones(len(start), dtype=bool)
    bright = _robust_z(np.concatenate([e["brightness"] for e in idx]), valid)
    motion = _robust_z(np.concatenate([e["motion"] for e in idx]), valid)
    beauty = (_robust_z(np.concatenate([e["colorfulness"] for e in idx]), valid)
              + 0.5 * _robust_z(np.concatenate([e["contrast"] for e in idx]), valid))
    shot_mood = np.clip(0.5 * motion - 0.5 * bright, -3, 3) / 3  # -1 calme/lumineux … +1 sombre/agité
    story_pos = (ep_no - 1 + (start + end) / 2 / ep_dur) / n_eps  # position dans la série (0..1)
    emb = np.concatenate([e["emb"] for e in idx]).astype(np.float32) if matcher == "clip" else None

    w = p["weights"]
    total = timings[-1]["end"] if timings else 1.0
    used = np.zeros(len(start), dtype=bool)
    slots: list[dict] = []
    for si, (s, t) in enumerate(zip(sentences, timings)):
        dur = t["end"] - t["start"]
        n = max(1, round(dur / target))
        sem = np.zeros(len(start))
        if emb is not None:
            text_vec = embed_texts([s.text])[0]
            if s.visual:
                text_vec = _unit(0.35 * text_vec + 0.65 * embed_texts([s.visual])[0])
            sem = _robust_z(emb @ text_vec, valid)
        mood = -np.abs(shot_mood - s.mood)
        for k in range(n):
            slot_start = t["start"] + k * dur / n
            slot_dur = dur / n
            chrono = -np.abs(story_pos - slot_start / total)
            too_short = np.clip(slot_dur - (end - start), 0, None)  # le plan doit couvrir le créneau
            score = (w["semantic"] * sem + w["mood"] * mood + w["beauty"] * (beauty * (2.0 if s.title else 1.0))
                     + w["chronology"] * chrono - 2.0 * too_short)
            score = np.where(used, -np.inf, score)
            order = np.argsort(-score)
            cands = []
            for j in order:
                if not np.isfinite(score[j]) or len(cands) >= n_cand:
                    break
                # pas deux candidats tirés du même passage
                if any(c["file"] == files[j] and abs(c["start"] - start[j]) < 4 for c in cands):
                    continue
                cands.append({"file": str(files[j]), "episode": int(ep_no[j]), "start": round(float(start[j]), 3),
                              "end": round(float(end[j]), 3), "score": round(float(score[j]), 3)})
            if not cands:
                raise SystemExit("Pas assez de plans différents pour illustrer tout le script.")
            first = cands[0]
            used |= (files == first["file"]) & (np.abs(start - first["start"]) < 3)
            slots.append({"sentence": si, "start": round(slot_start, 3), "duration": round(slot_dur, 3),
                          "candidates": cands, "choice": 0})
    return slots
