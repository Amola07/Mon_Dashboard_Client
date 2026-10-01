"""Construit films/gpu/rendu_cosmos.ipynb : un notebook autonome pour Kaggle ou Colab (GPU gratuit).

Les scènes Blender (films/gpu/scenes/*.py) y sont recopiées telles quelles : pas besoin de cloner le dépôt.
python -m films.gpu.construire_notebook
"""
import json
import os

ICI = os.path.dirname(os.path.abspath(__file__))
SCENES = ["commun.py", "nebuleuse.py", "planete.py", "hyperespace.py", "galaxie.py"]


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


INTRO = """
# Rendu cosmos sur GPU (Kaggle / Colab)

**Avant de lancer** (Kaggle) : *Settings* → *Accelerator* : **GPU T4 x2** (ou P100) · *Internet* : **On**.
Puis **Run All**. Les vidéos finies apparaissent dans `/kaggle/working/videos` (onglet *Output* → télécharger).

Modifie seulement la cellule **« Plans à rendre »** : chaque ligne = un plan (scène, durée, réglages).
Durée indicative sur T4 en 1080×1920 : hyperespace et planètes ≈ 5–15 s par image, galaxie et nébuleuses
≈ 20–60 s par image. Les 7 plans par défaut (≈ 18 s de vidéo) prennent donc quelques heures : lance d'abord
**APERCU = True** (≈ 15 min) pour vérifier les cadrages, puis le rendu final (une session Kaggle dure jusqu'à 12 h).
"""

INSTALL = r'''
import os, re, subprocess, sys, urllib.request, shutil, time
ROOT = "/kaggle/working" if os.path.isdir("/kaggle/working") else "/content"
os.makedirs(f"{ROOT}/scenes", exist_ok=True)
print(subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"], capture_output=True, text=True).stdout)

def latest_blender(series="4.5"):
    for base in ("https://download.blender.org/release", "https://mirrors.ocf.berkeley.edu/blender/release",
                 "https://ftp.halifax.rwth-aachen.de/blender/release"):
        try:
            html = urllib.request.urlopen(f"{base}/Blender{series}/", timeout=30).read().decode()
            names = sorted(set(re.findall(rf"blender-{re.escape(series)}\.(\d+)-linux-x64\.tar\.xz", html)), key=int)
            if names:
                return f"{base}/Blender{series}/blender-{series}.{names[-1]}-linux-x64.tar.xz"
        except Exception as e:
            print("miroir indisponible :", base, e)
    return None

BLENDER = f"{ROOT}/blender/blender"
if not os.path.exists(BLENDER):
    url = latest_blender()
    print("Téléchargement :", url)
    subprocess.run(f"wget -q -O /tmp/blender.tar.xz '{url}' && mkdir -p {ROOT}/blender && "
                   f"tar -xf /tmp/blender.tar.xz -C {ROOT}/blender --strip-components=1 && rm /tmp/blender.tar.xz",
                   shell=True, check=True)
    subprocess.run("apt-get -qq update && apt-get -qq install -y libxi6 libxxf86vm1 libxfixes3 libxrender1 libgl1 "
                   "libsm6 libxkbcommon0 ffmpeg > /dev/null", shell=True)
print(subprocess.run([BLENDER, "--version"], capture_output=True, text=True).stdout.splitlines()[0])
'''

PLANS = r'''
# ---- Plans à rendre ------------------------------------------------------------------------------
# scène : nebuleuse | planete | hyperespace | galaxie      secondes : durée du plan
# options : celles de la scène (voir l'en-tête de chaque fichier) — ex. "--palette feu", "--type glace"
# Astuce : commence par APERCU = True (petit, rapide) pour vérifier, puis passe à False pour le rendu final.
APERCU = False
PLANS = [
    ("hyperespace", 3.0, "--vitesse 1.0"),
    ("nebuleuse",   2.5, "--palette bleu --seed 1"),
    ("planete",     2.5, "--type gazeuse --inclinaison 24"),
    ("nebuleuse",   2.5, "--palette feu --seed 4"),
    ("galaxie",     3.0, "--bras 2"),
    ("planete",     2.5, "--type glace --seed 3"),
    ("nebuleuse",   2.5, "--palette rose --seed 7"),
]
ECHANTILLONS = {"nebuleuse": 128, "planete": 96, "hyperespace": 64, "galaxie": 128}
'''

RENDER = r'''
import glob
os.makedirs(f"{ROOT}/videos", exist_ok=True)
t_all = time.time()
for i, (scene, secs, opts) in enumerate(PLANS, 1):
    frames = max(2, int(round(secs * 30)))
    name = (f"{i:02d}_{scene}_" + re.sub(r"[^a-z0-9]+", "-", opts.lower())).strip("-_")
    out_dir = f"{ROOT}/frames/{name}"
    os.makedirs(out_dir, exist_ok=True)
    samples = 24 if APERCU else ECHANTILLONS.get(scene, 96)
    res = 40 if APERCU else 100
    cmd = (f"'{BLENDER}' -b -P {ROOT}/scenes/{scene}.py -- --out {out_dir}/f_ --frames {frames} "
           f"--samples {samples} --res {res} {opts}")
    print(f"\n▶ {name} : {frames} images, {samples} échantillons")
    t0 = time.time()
    for essai, extra in enumerate(("", " --debruitage aucun")):   # plan B : sans débruitage si ça échoue
        p = subprocess.run(cmd + extra, shell=True, capture_output=True, text=True)
        log = (p.stdout + p.stderr).splitlines()
        print("\n".join(l for l in log if "[rendu]" in l or "[calibrage]" in l or "Error" in l))
        n = len(glob.glob(f"{out_dir}/f_*.png"))
        if n >= frames:
            break
        print("   ⚠ échec, dernières lignes :\n   " + "\n   ".join(log[-6:]))
        if essai == 0:
            print("   → nouvel essai sans débruitage")
    print(f"   {n} images en {time.time() - t0:.0f} s")
    if n:
        subprocess.run(f"ffmpeg -y -v error -framerate 30 -i {out_dir}/f_%04d.png -c:v libx264 -pix_fmt yuv420p "
                       f"-crf 14 -preset slow {ROOT}/videos/{name}.mp4", shell=True)
print(f"\nTerminé en {(time.time() - t_all) / 60:.1f} min →", sorted(os.listdir(f"{ROOT}/videos")))
'''

ZIP = r'''
shutil.make_archive(f"{ROOT}/videos_cosmos", "zip", f"{ROOT}/videos")
print("Archive :", f"{ROOT}/videos_cosmos.zip")
try:
    from google.colab import files  # Colab : téléchargement direct
    files.download(f"{ROOT}/videos_cosmos.zip")
except ImportError:
    pass
'''


def build():
    cells = [md(INTRO), code(INSTALL)]
    for name in SCENES:
        src = open(os.path.join(ICI, "scenes", name), encoding="utf-8").read()
        cells.append(code(f"%%writefile {{ROOT}}/scenes/{name}\n" + src))
    cells += [md("## Plans à rendre"), code(PLANS), md("## Rendu"), code(RENDER), code(ZIP)]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}, "accelerator": "GPU"},
          "nbformat": 4, "nbformat_minor": 5}
    path = os.path.join(ICI, "rendu_cosmos.ipynb")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    return path


if __name__ == "__main__":
    print(build())
