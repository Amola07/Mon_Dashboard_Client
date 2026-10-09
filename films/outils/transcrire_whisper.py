"""Transcription d'une vidéo ou d'un son avec Whisper large-v3-turbo (sherpa-onnx, sur processeur).

Huggingface est bloqué ici ; le modèle vient des « releases » GitHub de sherpa-onnx :
    pip install sherpa-onnx
    curl -L https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2 | tar xj
    WHISPER_DIR=sherpa-onnx-whisper-turbo python -m films.outils.transcrire_whisper video.mp4 …
"""
import os
import subprocess
import sys

import numpy as np
import sherpa_onnx
M = os.path.join(os.environ.get("WHISPER_DIR", "sherpa-onnx-whisper-turbo"), "turbo-")
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+"encoder.int8.onnx", decoder=M+"decoder.int8.onnx",
        tokens=M+"tokens.txt", language="fr", task="transcribe", num_threads=8)
SR = 16000
for f in sys.argv[1:]:
    a = np.frombuffer(subprocess.run(["ffmpeg","-loglevel","error","-i",f,"-ac","1","-ar",str(SR),"-f","f32le","-"],
                      capture_output=True).stdout, np.float32)
    e = np.convolve(a**2, np.ones(1600)/1600, "same")
    i, coupes = 0, [0]
    while len(a) - i > 25*SR:
        j = i + 15*SR + int(np.argmin(e[i+15*SR:i+25*SR]))   # coupe au point le plus calme entre 15 et 25 s
        coupes.append(j); i = j
    coupes.append(len(a))
    print(f"=== {f}")
    for x0, x1 in zip(coupes, coupes[1:]):
        s = rec.create_stream(); s.accept_waveform(SR, a[x0:x1]); rec.decode_stream(s)
        print(f"[{x0/SR:5.1f}] {s.result.text.strip()}", flush=True)
