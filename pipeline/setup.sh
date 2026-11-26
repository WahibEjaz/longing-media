#!/usr/bin/env bash
# One-time setup in a fresh workspace: Python packages, the Kokoro voice model
# (Soft American = af_bella) and the Whisper model used for the word check.
set -euo pipefail
cd "$(dirname "$0")/.."
pip install --break-system-packages -q kokoro-onnx==0.6.1 soundfile faster-whisper==1.2.1 scipy pillow numpy
mkdir -p .cache/kokoro
HF=https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/resolve/main
[ -s .cache/kokoro/model.onnx ] || curl -sSfL -o .cache/kokoro/model.onnx "$HF/onnx/model.onnx"
[ -s .cache/kokoro/af_bella.bin ] || curl -sSfL -o .cache/kokoro/af_bella.bin "$HF/voices/af_bella.bin"
python3 -c "import numpy as np; v=np.fromfile('.cache/kokoro/af_bella.bin', dtype=np.float32).reshape(-1, 1, 256); np.savez('.cache/kokoro/voices.npz', af_bella=v)"
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')" >/dev/null
ffmpeg -hide_banner -filters > /tmp/_ffmpeg_filters.txt 2>/dev/null
grep -q " ass " /tmp/_ffmpeg_filters.txt || { echo "ffmpeg has no subtitle (ass) filter"; exit 1; }
echo "setup ok"
