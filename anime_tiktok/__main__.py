"""Ligne de commande : python -m anime_tiktok <commande> [options]

Commandes :
  analyze   analyse les épisodes (plans, son, mouvement, génériques)
  select    propose les meilleurs extraits (work/selection/clips.csv + review.html)
  make      rend les extraits retenus (vertical, 4K, 120/240 fps) et fait le montage du style choisi
  run       enchaîne analyze + select + make
  backends  affiche les outils détectés (GPU, RIFE, Real-ESRGAN, encodeur)
"""

from __future__ import annotations

import argparse
import os

from .config import load_config
from .media import require_ffmpeg


def main() -> None:
    parser = argparse.ArgumentParser(prog="anime_tiktok", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["analyze", "select", "make", "run", "backends", "serve"])
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--set", action="append", default=[], metavar="CLE=VALEUR",
                        help="surcharge une valeur de config, ex. --set render.fps=240")
    parser.add_argument("--style", default="brut", help="style de montage défini dans config.yaml")
    parser.add_argument("--music", help="musique à utiliser pour les styles rythmés")
    parser.add_argument("--only", nargs="*", help="ids d'extraits à traiter (par défaut : tous ceux avec keep=1)")
    parser.add_argument("--force", action="store_true", help="refait l'analyse même si elle existe déjà")
    parser.add_argument("--port", type=int, default=8000, help="serve : port HTTP")
    parser.add_argument("--token", help="serve : mot de passe de l'application (sinon ANIME_TIKTOK_TOKEN ou aléatoire)")
    parser.add_argument("--tunnel", action="store_true", help="serve : adresse publique https via Cloudflare")
    parser.add_argument("--ntfy-topic", help="serve : sujet ntfy.sh pour publier l'adresse et les notifications")
    args = parser.parse_args()

    if args.command == "serve":
        from .server import serve
        serve(args.config, args.set, args.port, args.token, args.tunnel, args.ntfy_topic)
        return

    cfg = load_config(args.config, args.set)
    local_ffmpeg = cfg.path("tools") / "ffmpeg" / "bin"
    if local_ffmpeg.is_dir():  # ffmpeg récent (avec NVENC) installé par scripts/setup_tools.sh
        os.environ["PATH"] = f"{local_ffmpeg}{os.pathsep}{os.environ['PATH']}"
    require_ffmpeg()

    if args.command in ("analyze", "run"):
        from .analyze import run_analysis
        run_analysis(cfg, force=args.force)
    if args.command in ("select", "run"):
        from .select import run_selection
        run_selection(cfg)
    if args.command in ("make", "run"):
        from .montage import run_montage
        run_montage(cfg, args.style, music=args.music, only=args.only)
    if args.command == "backends":
        from .enhance import resolve_backends
        from .media import pick_encoder
        interp, up = resolve_backends(cfg)
        print(f"interpolation : {interp}\nagrandissement : {up}\nencodeur : {pick_encoder(cfg['render']['encoder'])}")


if __name__ == "__main__":
    main()
