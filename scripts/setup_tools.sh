#!/usr/bin/env bash
# Télécharge les outils du pipeline dans ./tools (Kaggle, Colab ou Linux avec GPU NVIDIA) :
#   - ffmpeg récent avec NVENC (encodage GPU)          -> tools/ffmpeg/bin
#   - RIFE ncnn (interpolation 120/240 fps, Vulkan)    -> tools/rife-ncnn-vulkan
#   - Real-ESRGAN ncnn (agrandissement, Vulkan)        -> tools/realesrgan-ncnn-vulkan
#   - modèle Real-ESRGAN animevideov3 pour PyTorch     -> tools/models
#   - détecteur de visages d'animé (recadrage)         -> tools/models
# Relancer le script ne retélécharge pas ce qui est déjà présent.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"
mkdir -p "$TOOLS/models"
cd "$TOOLS"

fetch() {  # fetch URL DEST
  [ -s "$2" ] && return 0
  echo "  téléchargement de $(basename "$2")"
  curl -fsSL --retry 3 -o "$2.part" "$1" && mv "$2.part" "$2"
}

if command -v apt-get >/dev/null 2>&1; then
  echo "Paquets système (Vulkan, unzip)…"
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get -qq update >/dev/null 2>&1 || true
  $SUDO apt-get -qq install -y libvulkan1 libgomp1 unzip xz-utils >/dev/null 2>&1 || true
fi

echo "ffmpeg…"
if [ ! -x ffmpeg/bin/ffmpeg ]; then
  fetch https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz ffmpeg.tar.xz
  mkdir -p ffmpeg && tar -xJf ffmpeg.tar.xz -C ffmpeg --strip-components=1 && rm ffmpeg.tar.xz
fi

echo "RIFE (ncnn-vulkan)…"
if [ ! -x rife-ncnn-vulkan/rife-ncnn-vulkan ]; then
  fetch https://github.com/nihui/rife-ncnn-vulkan/releases/download/20221029/rife-ncnn-vulkan-20221029-ubuntu.zip rife.zip
  unzip -q -o rife.zip && rm rife.zip
  rm -rf rife-ncnn-vulkan && mv rife-ncnn-vulkan-20221029-ubuntu rife-ncnn-vulkan
  chmod +x rife-ncnn-vulkan/rife-ncnn-vulkan
fi

echo "Real-ESRGAN (ncnn-vulkan)…"
if [ ! -x realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan ]; then
  fetch https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip esrgan.zip
  mkdir -p realesrgan-ncnn-vulkan && unzip -q -o esrgan.zip -d realesrgan-ncnn-vulkan && rm esrgan.zip
  chmod +x realesrgan-ncnn-vulkan/realesrgan-ncnn-vulkan
fi

echo "Modèles…"
fetch https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-animevideov3.pth models/realesr-animevideov3.pth
fetch https://raw.githubusercontent.com/nagadomi/lbpcascade_animeface/master/lbpcascade_animeface.xml models/lbpcascade_animeface.xml

echo
echo "Outils prêts. Ajoutez ffmpeg au PATH :"
echo "  export PATH=\"$TOOLS/ffmpeg/bin:\$PATH\""
