"""Génère de faux épisodes (même opening + passages calmes/agités) et une musique à 120 BPM pour les tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

W, H, R = 640, 360, 24
OP_SECONDS = 45


def _run(args: list[str]) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-y", "-loglevel", "error", *args], check=True)


def make_episode(path: Path, seed: int) -> None:
    melody = "0.4*sin(2*PI*(220+55*mod(floor(t*2)\\,8))*t)"
    pad = 0.13 * seed  # opening décalé d'un épisode à l'autre, comme dans la réalité
    segs = [
        (f"color=c=black:s={W}x{H}:r={R}:d={pad}", f"anullsrc=r=48000:cl=stereo,atrim=duration={pad}"),
        (f"testsrc2=s={W}x{H}:r={R}:d={OP_SECONDS}", f"aevalsrc='{melody}':s=48000:d={OP_SECONDS}"),
        (f"color=c=0x2040{seed * 30 % 256:02x}:s={W}x{H}:r={R}:d=20", f"sine=f={300 + 40 * seed}:r=48000:d=20,volume=0.02"),
    ]
    for k in range(6):  # scène d'action : plans de 2 s, bruit fort, mouvement
        segs.append((f"life=s={W}x{H}:r={R}:mold=10:ratio=0.3:seed={seed * 10 + k}:death_color=0x{(k * 40) % 256:02x}0030,trim=duration=2",
                     f"anoisesrc=a=0.6:r=48000:seed={seed * 10 + k}:d=2"))
    segs.append((f"color=c=0x402020:s={W}x{H}:r={R}:d=15", f"sine=f={200 + 30 * seed}:r=48000:d=15,volume=0.02"))
    args, graph = [], []
    for i, (v, a) in enumerate(segs):
        args += ["-f", "lavfi", "-i", v, "-f", "lavfi", "-i", a]
        graph.append(f"[{2 * i}:v]format=yuv420p,setsar=1[v{i}];[{2 * i + 1}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
    concat = "".join(f"[v{i}][a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=1:a=1[v][a]"
    _run([*args, "-filter_complex", ";".join(graph + [concat]), "-map", "[v]", "-map", "[a]",
          "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", str(path)])


def make_music(path: Path, seconds: int = 40) -> None:
    click = "0.8*sin(2*PI*80*t)*exp(-30*mod(t\\,0.5))+0.2*sin(2*PI*440*t)*exp(-10*mod(t+0.25\\,0.5))"
    _run(["-f", "lavfi", "-i", f"aevalsrc='{click}':s=44100:d={seconds}", "-c:a", "libmp3lame", str(path)])


def main(root: Path) -> None:
    eps = root / "input" / "episodes"
    music = root / "input" / "music"
    eps.mkdir(parents=True, exist_ok=True)
    music.mkdir(parents=True, exist_ok=True)
    for n in range(1, 4):
        make_episode(eps / f"episode_{n:02d}.mp4", n)
    make_music(music / "beat120.mp3")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
