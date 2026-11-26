"""Narrate a reel script sentence by sentence with Kokoro (free, open source).

usage: python3 narrate.py script.json voice out.wav [speed]
Writes out.wav plus out.timing.json with each sentence's start/end time.
A sentence may have "say": the text the voice reads, when it differs from the on-screen
text (e.g. "Except one boy ." with a space fixes a swallowed vowel in some voices).
Names from the book are respelled automatically (NAMES below), so scripts can use the real spelling.
"""
import json, re, sys
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

script, voice, out = sys.argv[1], sys.argv[2], sys.argv[3]
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 0.95
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
K = Kokoro(str(REPO / ".cache/kokoro/model.onnx"), str(REPO / ".cache/kokoro/voices.npz"))

# How the voice should say the book's names (checked by phonemes; "Aenor" alone reads as "EE-ner").
NAMES = {"Aenor": "Eh-nor"}

def spoken(text):
    for k, v in NAMES.items():
        text = re.sub(rf"\b{k}\b", v, text)
    return text

LANG = "en-gb" if voice.startswith("b") else "en-us"   # British voices need British phonemes
data = json.load(open(script))
sr = 24000
lead_in = 0.25
chunks = [np.zeros(int(lead_in * sr), dtype=np.float32)]
t = lead_in
timing = []
for s in data["sentences"]:
    audio, sr = K.create(spoken(s.get("say", s["text"])), voice=voice, speed=speed, lang=LANG)
    audio = np.asarray(audio, dtype=np.float32)
    # trim leading/trailing near-silence so pauses are exactly what the script says
    nz = np.where(np.abs(audio) > 0.01)[0]
    if len(nz):
        audio = audio[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.06 * sr)]
    dur = len(audio) / sr
    timing.append({**s, "start": round(t, 3), "end": round(t + dur, 3)})
    chunks.append(audio)
    t += dur
    gap = s.get("pause", 0.35)
    chunks.append(np.zeros(int(gap * sr), dtype=np.float32))
    t += gap

full = np.concatenate(chunks)
peak = np.abs(full).max()
if peak > 0:
    full = full / peak * 0.89
sf.write(out, full, sr)
json.dump({"voice": voice, "speed": speed, "duration": round(len(full) / sr, 3), "sentences": timing},
          open(out.replace(".wav", ".timing.json"), "w"), indent=1)
print(f"{voice}: {len(full)/sr:.2f}s")
