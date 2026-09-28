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
  echo "Paquets système (Vulkan, unzip, espeak-ng pour la voix, polices)…"
  SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
  $SUDO apt-get -qq update >/dev/null 2>&1 || true
  $SUDO apt-get -qq install -y libvulkan1 libgomp1 unzip xz-utils espeak-ng fonts-dejavu-core >/dev/null 2>&1 || true
fi

echo "ffmpeg…"
# Les builds récents de ffmpeg exigent un pilote NVIDIA récent pour NVENC (encodage GPU).
# On essaie du plus récent au plus ancien et on garde le premier dont NVENC marche sur ce GPU.
BTBN=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest
nvenc_ok() {
  "$1" -hide_banner -loglevel error -f lavfi -i color=c=black:s=256x256:d=0.2 -c:v hevc_nvenc -f null - 2>/dev/null
}
if [ ! -x ffmpeg/bin/ffmpeg ] || { command -v nvidia-smi >/dev/null && ! nvenc_ok ffmpeg/bin/ffmpeg; }; then
  for build in ffmpeg-master-latest-linux64-gpl ffmpeg-n7.1-latest-linux64-gpl-7.1 \
               ffmpeg-n7.0-latest-linux64-gpl-7.0 ffmpeg-n6.1-latest-linux64-gpl-6.1; do
    rm -rf ffmpeg.try && mkdir ffmpeg.try
    if curl -fsSL --retry 3 "$BTBN/$build.tar.xz" | tar -xJ -C ffmpeg.try --strip-components=1 2>/dev/null; then
      if ! command -v nvidia-smi >/dev/null || nvenc_ok ffmpeg.try/bin/ffmpeg; then
        rm -rf ffmpeg && mv ffmpeg.try ffmpeg && echo "  $build (NVENC ok)" && break
      fi
      echo "  $build : NVENC indisponible avec ce pilote, essai d'une version plus ancienne"
      [ -x ffmpeg/bin/ffmpeg ] || { rm -rf ffmpeg && mv ffmpeg.try ffmpeg; }  # garde au moins un ffmpeg
    fi
  done
  rm -rf ffmpeg.try
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
