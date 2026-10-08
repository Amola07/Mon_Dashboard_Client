"""Rendre seulement un extrait d'un épisode oscilloscope (image + son), pour tester une scène sans tout rendre.

    from films.outils.extrait import rendre_extrait
    rendre_extrait(M, 14.0, 27.2, "output/extrait.mp4")                  # M = le module moteur de l'épisode

Même rendu que M.render (persistance, transitions, sous-titres, écran, flashs, secousses), limité à [t0, t1].
Le son est le mixage complet de l'épisode, coupé aux mêmes instants.
"""
import os
import subprocess
import tempfile

import skia

from films.styles.oscillo_ascenseur import P, ease


def rendre_extrait(M, t0, t1, out, tableaux=None, chocs=None):
    voix = M.preparer()
    tabs = tableaux() if tableaux else M.tableaux()
    flashs, secousses = chocs() if chocs else M.chocs()
    W, H, FPS = M.W, M.H, M.FPS
    tmp = tempfile.mkdtemp()
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                           "-preset", "medium", f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
    surf = skia.Surface(W, H)
    prec = None
    for fr in range(int(round(t0 * FPS)), int(round(t1 * FPS))):
        t = fr / FPS
        k = max(i for i, x in enumerate(tabs) if x[0] <= t)
        t_tab, fn, trans = tabs[k]
        dt = t - t_tab
        c = surf.getCanvas()
        c.clear(skia.Color(2, 8, 4))
        if prec is not None:
            c.drawImage(prec, 0, 0, skia.SamplingOptions(), P((0, 0, 0), 0, getattr(M, "ALPHA_PERSISTANCE", 150), fill=True))
        c.save()
        for ts, d in secousses:
            if ts <= t < ts + d:
                c.translate(M.RNG.normal(0, 7), M.RNG.normal(0, 3))
        if trans == "balayage" and dt < 0.35:
            c.clipRect(skia.Rect(0, 0, W, H * ease(dt / 0.35)))
        fn(c, t)
        c.restore()
        prec = surf.makeImageSnapshot()
        M.sous_titres(c, t)
        M.ecran(c, t, flashs)
        ff.stdin.write(surf.makeImageSnapshot().tobytes())
    ff.stdin.close()
    ff.wait()
    dur = M.SEG[-1][1] + 1.8
    M.mixage(f"{tmp}/a.wav", voix, dur, tabs)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{tmp}/v.mp4", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}",
                    "-i", f"{tmp}/a.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", M.volume_cible(f"{tmp}/a.wav"), "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out],
                   check=True)
    print("OK", out)
