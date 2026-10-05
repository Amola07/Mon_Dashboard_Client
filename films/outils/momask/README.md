# MoMask : un mouvement de personnage à partir d'une phrase

Génère des articulations 3D (22 points, 20 images/s) que `films/styles/demo_momask.py` rend au faisceau.
Tourne sur processeur, sans carte graphique : environ 10 s pour 3 mouvements de 4 s.

## Installation (une fois)

```bash
git clone --depth 1 https://github.com/EricGuo5513/momask-codes
cp films/outils/momask/generer_mouvements.py momask-codes/
cp -r films/outils/momask/shim momask-codes/
cd momask-codes
# vieux alias numpy retirés des versions récentes
grep -rln "np\.float\b\|np\.int\b\|np\.bool\b" --include=*.py . | xargs sed -i -E 's/np\.float\b/np.float64/g; s/np\.int\b/np.int64/g; s/np\.bool\b/np.bool_/g'
pip install torch transformers einops tqdm huggingface_hub
python -c "
from huggingface_hub import snapshot_download, hf_hub_download
snapshot_download('geedog/momask-codes-models', allow_patterns=['t2m/*'], local_dir='checkpoints')
snapshot_download('openai/clip-vit-base-patch32', allow_patterns=['*.json','*.txt'], local_dir='clip_hf')
hf_hub_download('openai/clip-vit-base-patch32', 'pytorch_model.bin', local_dir='clip_hf')"
```

`shim/clip.py` remplace le paquet `clip` d'OpenAI (poids hébergés hors de Hugging Face) par le même modèle
ViT-B/32 servi par Hugging Face.

## Générer

```bash
python generer_mouvements.py sorties "a person falls hard to the ground and lies down#80"
```

Une phrase en anglais par mouvement, suivie de `#` et du nombre d'images (multiple de 4, 80 = 4 s, 196 au plus).
Les fichiers `sorties/m0.npy`, `m1.npy`… vont dans `films/mouvements/`.

Limite : le modèle a appris sur des mouvements au sol (HumanML3D) ; « flotter en apesanteur » donne des bras qui
s'agitent mais des pieds au sol. Pour l'apesanteur et les chocs, le pantin physique (`films/styles/pantin_physique.py`).
