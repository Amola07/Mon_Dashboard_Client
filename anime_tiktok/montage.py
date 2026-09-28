"""Étape 4 : montage final selon le style du jour, puis livraison (vidéos + légendes)."""

from __future__ import annotations

import datetime as dt
import random
import re
from pathlib import Path

import numpy as np

from .config import Config
from .enhance import render_clip, resolve_backends
from .media import AUDIO_EXTS, encoder_args, ffmpeg, list_media, pick_encoder, probe, read_audio
from .select import load_selection

BEAT_RATE = 22050
BEAT_HOP = 512


# --------------------------------------------------------------------------- détection des temps

def detect_beats(path: Path) -> tuple[float, list[float]]:
    """Tempo (BPM) et instants des temps d'une musique : flux spectral + autocorrélation."""
    y = read_audio(path, BEAT_RATE)
    n_fft = 2048
    n_frames = 1 + (len(y) - n_fft) // BEAT_HOP
    if n_frames < 10:
        return 120.0, [i * 0.5 for i in range(240)]
    idx = np.arange(n_fft)[None, :] + BEAT_HOP * np.arange(n_frames)[:, None]
    mag = np.log1p(np.abs(np.fft.rfft(y[idx] * np.hanning(n_fft), axis=1)))
    env = np.maximum(0, np.diff(mag, axis=0)).sum(axis=1)
    env = (env - env.mean()) / (env.std() + 1e-6)
    fps = BEAT_RATE / BEAT_HOP

    lags = np.arange(int(fps * 60 / 180), int(fps * 60 / 70) + 1)
    ac = np.array([np.dot(env[:-lag], env[lag:]) for lag in lags])
    # Légère préférence autour de 120 BPM pour éviter les doubles/moitiés de tempo.
    bpm = 60 * fps / lags
    ac *= np.exp(-0.5 * (np.log2(bpm / 120) / 0.9) ** 2)
    coarse = float(lags[int(np.argmax(ac))])

    # Affinage : période non entière et phase qui alignent le mieux la grille sur les attaques
    # (une erreur de 2 % décalerait les coupes d'une demi-seconde au bout de 30 s).
    best = (-np.inf, coarse, 0.0)
    for period in np.linspace(coarse * 0.97, coarse * 1.03, 61):
        n = int(len(env) / period) - 1
        if n < 2:
            continue
        for phase in np.arange(0, period, 0.5):
            idx = np.round(phase + period * np.arange(n)).astype(int)
            score = env[idx[idx < len(env)]].mean()
            if score > best[0]:
                best = (score, period, phase)
    _, period, phase = best
    beats = [(phase + k * period) / fps for k in range(int((len(env) - phase) / period))]
    return 60 * fps / period, beats


# --------------------------------------------------------------------------- briques de filtres

def _segment(label_in: str, label_out: str, start: float, dur: float, fps: float, size: tuple[int, int],
             punch: float = 0.0, flash: bool = False, fade_in: float = 0.0, fade_out: float = 0.0) -> str:
    w, h = size
    chain = [f"trim=start={start:.4f}:duration={dur:.4f}", "setpts=PTS-STARTPTS"]
    if punch > 0:
        chain += [f"scale=w='trunc({w}*(1+{punch}*max(0\\,1-t/0.25))/2)*2':h=-2:eval=frame:flags=bicubic",
                  f"crop={w}:{h}"]
    if flash:
        chain.append("fade=t=in:st=0:d=0.12:color=white")
    if fade_in > 0:
        chain.append(f"fade=t=in:st=0:d={fade_in}")
    if fade_out > 0:
        chain.append(f"fade=t=out:st={max(0.0, dur - fade_out):.3f}:d={fade_out}")
    chain += [f"fps={fps}", "format=yuv420p", "setsar=1"]
    return f"[{label_in}]{','.join(chain)}[{label_out}]"


def _audio_segment(label_in: str, label_out: str, start: float, dur: float) -> str:
    return (f"[{label_in}]atrim=start={start:.4f}:duration={dur:.4f},asetpts=PTS-STARTPTS,"
            f"aformat=sample_rates=48000:channel_layouts=stereo[{label_out}]")


def _encode(cfg: Config, inputs: list[Path], graph: str, out: Path, v: str, a: str) -> None:
    r = cfg["render"]
    codec = pick_encoder(r["encoder"])
    args = []
    for p in inputs:
        args += ["-i", p]
    ffmpeg(*args, "-filter_complex", graph, "-map", f"[{v}]", "-map", f"[{a}]",
           *encoder_args(codec, int(r["quality"]), float(r["fps"])),
           "-c:a", "aac", "-b:a", r["audio_bitrate"], out)


# --------------------------------------------------------------------------- styles

def montage_single(cfg: Config, style: dict, clip: dict, src: Path, out: Path) -> None:
    """Un extrait = une vidéo, avec en option une accroche (moment fort) en ouverture."""
    r = cfg["render"]
    fps, size = float(r["fps"]), (int(r["width"]), int(r["height"]))
    dur = probe(src).duration
    hook = float(style.get("hook_seconds", 0) or 0)
    flash = bool(style.get("flash"))
    fade = float(style.get("fade", 0) or 0)
    parts_v, parts_a, graph = [], [], []
    n_parts = 2 if hook > 0 and dur > hook * 3 else 1
    graph.append(f"[0:v]split={n_parts}" + "".join(f"[v{i}]" for i in range(n_parts)))
    graph.append(f"[0:a]asplit={n_parts}" + "".join(f"[a{i}]" for i in range(n_parts)))
    if n_parts == 2:
        h0 = float(np.clip(clip["peak"] - hook / 2, 0, dur - hook))
        graph.append(_segment("v0", "hv", h0, hook, fps, size, punch=0.08, fade_in=fade))
        graph.append(_audio_segment("a0", "ha", h0, hook))
        parts_v.append("hv")
        parts_a.append("ha")
    last = n_parts - 1
    graph.append(_segment(f"v{last}", "mv", 0, dur, fps, size, flash=flash and n_parts == 2,
                          fade_in=fade if n_parts == 1 else 0, fade_out=fade))
    graph.append(_audio_segment(f"a{last}", "ma", 0, dur))
    parts_v.append("mv")
    parts_a.append("ma")
    n = len(parts_v)
    graph.append("".join(f"[{v}][{a}]" for v, a in zip(parts_v, parts_a)) + f"concat=n={n}:v=1:a=1[outv][outa]")
    _encode(cfg, [src], ";".join(graph), out, "outv", "outa")


def montage_beats(cfg: Config, style: dict, clips: list[dict], srcs: list[Path], music: Path, out: Path) -> None:
    """Edit rythmé : coupes sur les temps de la musique, en piochant autour des moments forts."""
    r = cfg["render"]
    fps, size = float(r["fps"]), (int(r["width"]), int(r["height"]))
    target = float(style.get("video_seconds", 30))
    per_cut = int(style.get("beats_per_cut", 2))
    tempo, beats = detect_beats(music)
    beats = [b for b in beats if b <= target + 2]
    cut_times = beats[::per_cut] if len(beats) > per_cut else [i * 1.0 for i in range(int(target) + 1)]
    music_start = cut_times[0]
    bounds = [t - music_start for t in cut_times if t - music_start <= target]
    if bounds[-1] < target - 0.5:
        bounds.append(target)
    print(f"    musique {music.name} : {tempo:.0f} BPM, {len(bounds) - 1} coupes")

    durations = [probe(s).duration for s in srcs]
    uses = [0] * len(clips)
    graph, labels = [], []
    n_cuts = len(bounds) - 1
    count_per_clip = [0] * len(clips)
    for k in range(n_cuts):
        count_per_clip[k % len(clips)] += 1
    for i, n in enumerate(count_per_clip):
        if n:
            graph.append(f"[{i}:v]split={n}" + "".join(f"[s{i}_{j}]" for j in range(n)))
    punch = float(style.get("punch_zoom", 0) or 0)
    flash = bool(style.get("flash"))
    for k in range(n_cuts):
        i = k % len(clips)
        seg = bounds[k + 1] - bounds[k]
        # Utilisations successives d'un même extrait : on avance autour de son moment fort.
        start = clips[i]["peak"] - seg / 2 + uses[i] * seg
        start = float(np.clip(start, 0, max(0.0, durations[i] - seg)))
        graph.append(_segment(f"s{i}_{uses[i]}", f"c{k}", start, seg, fps, size, punch=punch, flash=flash and k > 0))
        uses[i] += 1
        labels.append(f"c{k}")
    graph.append("".join(f"[{l}]" for l in labels) + f"concat=n={n_cuts}:v=1:a=0[cat]")
    total = bounds[-1]
    graph.append(f"[cat]trim=duration={total:.4f}[outv]")
    m = len(srcs)
    graph.append(f"[{m}:a]atrim=start={music_start:.3f}:duration={total:.3f},asetpts=PTS-STARTPTS,"
                 f"afade=t=out:st={max(0, total - 1.5):.3f}:d=1.5,aformat=sample_rates=48000:channel_layouts=stereo[music]")
    orig = float(style.get("original_audio", 0) or 0)
    if orig > 0:
        # Son d'origine discret sous la musique (pris sur l'extrait le mieux noté).
        graph.append(f"[0:a]atrim=duration={total:.3f},asetpts=PTS-STARTPTS,volume={orig},"
                     f"aformat=sample_rates=48000:channel_layouts=stereo[orig]")
        graph.append("[music][orig]amix=inputs=2:duration=first:normalize=0[outa]")
    else:
        graph.append("[music]anull[outa]")
    _encode(cfg, [*srcs, music], ";".join(graph), out, "outv", "outa")


# --------------------------------------------------------------------------- livraison

def _caption(cfg: Config, episodes: list[int]) -> str:
    d = cfg["delivery"]
    anime = d.get("anime", "")
    tag = re.sub(r"[^0-9a-zA-ZÀ-ÿ]", "", anime.lower()) or "anime"
    ep = ", ".join(str(e) for e in sorted(set(episodes)))
    return d["caption"].format(anime=anime, anime_tag=tag, episode=ep, fps=int(float(cfg["render"]["fps"])))


def run_montage(cfg: Config, style_name: str, music: str | None = None, only: list[str] | None = None) -> Path:
    style = cfg.style(style_name)
    clips = load_selection(cfg)
    if only:
        clips = [c for c in clips if c["id"] in only]
    if not clips:
        raise SystemExit("Aucun extrait retenu (keep=1) dans la sélection.")

    backends = resolve_backends(cfg)
    r = cfg["render"]
    print(f"Style « {style_name} » : {len(clips)} extrait(s), rendu {r['width']}x{r['height']} @ {r['fps']} fps")
    print(f"  interpolation : {backends[0]} · agrandissement : {backends[1]} · encodeur : {pick_encoder(r['encoder'])}")

    out_dir = cfg.path("output") / f"{dt.datetime.now():%Y-%m-%d_%H%M}_{style_name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    mode = style.get("reframe", "crop")

    rendered = []
    for n, clip in enumerate(clips, start=1):
        print(f"  [{n}/{len(clips)}] rendu de {clip['id']} ({clip['duration']:.0f} s)")
        rendered.append(render_clip(cfg, clip, mode, backends))

    layout = style.get("layout", "single")
    if layout == "single":
        for clip, src in zip(clips, rendered):
            out = out_dir / f"{clip['id']}.mp4"
            print(f"  montage {out.name}")
            montage_single(cfg, style, clip, src, out)
            out.with_suffix(".txt").write_text(_caption(cfg, [clip["episode"]]), encoding="utf-8")
    elif layout == "beats":
        tracks = [Path(music)] if music else list_media(cfg.path("music"), AUDIO_EXTS)
        if not tracks:
            raise SystemExit(f"Le style « {style_name} » a besoin d'une musique : --music fichier.mp3 "
                             f"ou des fichiers dans {cfg.path('music')}")
        group = int(style.get("clips_per_video", 8))
        order = sorted(range(len(clips)), key=lambda i: clips[i]["score"], reverse=True)
        for g, start in enumerate(range(0, len(order), group), start=1):
            idx = order[start:start + group]
            track = random.choice(tracks)
            out = out_dir / f"edit_{g:02d}.mp4"
            print(f"  montage {out.name} ({len(idx)} extraits)")
            montage_beats(cfg, style, [clips[i] for i in idx], [rendered[i] for i in idx], track, out)
            out.with_suffix(".txt").write_text(_caption(cfg, [clips[i]["episode"] for i in idx]), encoding="utf-8")
    else:
        raise SystemExit(f"Layout inconnu : {layout!r} (single ou beats)")

    print(f"Terminé → {out_dir}")
    return out_dir
