"""Rend un plan de l'épisode 12 et l'encode en clip 1080×1920 avec lueur néon.

    python -m films.episodes.ep12_pyramide.blender.rendu 11            # plan complet → clips/11.mp4
    python -m films.episodes.ep12_pyramide.blender.rendu 11 --test     # 3 images en 25 % → planche PNG
"""
import os
import subprocess
import sys
import tempfile

from . import neon as N
from .plans import PLANS, TIMES

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARGE = 0.4
GLOW = ("scale=1080:1920:flags=lanczos,format=gbrp,split[a][b];[b]gblur=sigma=18[g];"
        "[a][g]blend=all_mode=screen:all_opacity=0.6,format=yuv420p")


def main():
    import bpy
    num = sys.argv[1]
    test = "--test" in sys.argv
    t0, t1 = TIMES[num]
    n = int(round((t1 - t0 + MARGE) * N.FPS))
    N.reset()
    PLANS[num](n)
    N.setup(n, pct=25 if test else 50)
    sc = bpy.context.scene
    work = os.environ.get("EP12_WORK") or tempfile.mkdtemp(prefix=f"ep12_{num}_")
    os.makedirs(work, exist_ok=True)
    if test:
        outs = []
        for f in (1, n // 2, n):
            sc.frame_set(f)
            sc.render.filepath = os.path.join(work, f"t_{f:04d}.png")
            bpy.ops.render.render(write_still=True)
            outs.append(sc.render.filepath)
        dst = os.path.join(work, f"planche_{num}.png")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + sum([["-i", o] for o in outs], []) +
                       ["-filter_complex", "hstack=inputs=3", dst], check=True)
        print("PLANCHE", dst)
        return
    sc.render.filepath = os.path.join(work, "f_")
    bpy.ops.render.render(animation=True)
    clips = os.path.join(HERE, "clips")
    os.makedirs(clips, exist_ok=True)
    out = os.path.join(clips, f"{num}.mp4")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-framerate", str(N.FPS), "-i", os.path.join(work, "f_%04d.png"),
                    "-vf", GLOW, "-c:v", "libx264", "-crf", "17", "-preset", "slow", out], check=True)
    print("CLIP", out)


if __name__ == "__main__":
    main()
