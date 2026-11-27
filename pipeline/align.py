"""Time every script word against the narration (per sentence, so no drift).

usage: python3 align.py narration.wav   (reads narration.timing.json, writes narration.words.json
and narration.check.json: what Whisper heard per sentence and whether it matches the script)
Uses Whisper word timestamps inside each sentence; falls back to spreading words
by length when the recognised words don't line up with the script.
"""
import json, re, sys, difflib
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

wav = sys.argv[1]
timing = json.load(open(wav.replace(".wav", ".timing.json")))
audio, sr = sf.read(wav, dtype="float32")
model = WhisperModel("small.en", device="cpu", compute_type="int8")

NUM = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six", "7": "seven", "8": "eight",
       "9": "nine", "10": "ten", "11": "eleven", "12": "twelve", "16": "sixteen", "450": "fourhundredfifty"}

# Words that sound the same: Whisper may spell them either way, so they count as a match.
SAME = {"too": "two", "to": "two", "blonde": "blond", "your": "you're", "board": "bored"}

def norm(w):
    w = re.sub(r"[^a-z0-9']", "", w.lower())
    w = NUM.get(w, w)
    return SAME.get(w, w)

out = []
report = []
for si, s in enumerate(timing["sentences"]):
    words = s["text"].split()
    st, en = s["start"], s["end"]
    seg = audio[int(max(0, st - 0.05) * sr): int((en + 0.1) * sr)]
    idx = np.arange(0, len(seg), sr / 16000)
    a16 = np.interp(idx, np.arange(len(seg)), seg).astype(np.float32)
    segs, _ = model.transcribe(a16, word_timestamps=True, vad_filter=False,
                               initial_prompt="Lunar Land. Allen. Aenor. Asara. Mason. Alice.")
    heard = [w for x in segs for w in (x.words or [])]
    offset = max(0, st - 0.05)
    a = [norm(w) for w in words]
    b = [norm(w.word) for w in heard]
    times = [None] * len(words)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                hw = heard[j1 + k]
                times[i1 + k] = (offset + hw.start, offset + hw.end)
    # fill gaps by spreading over the free span, weighted by word length
    k = 0
    while k < len(words):
        if times[k] is not None:
            k += 1
            continue
        j = k
        while j < len(words) and times[j] is None:
            j += 1
        left = times[k - 1][1] if k > 0 else st
        right = times[j][0] if j < len(words) else en
        span = max(0.05, right - left)
        weights = [len(norm(w)) + 2 for w in words[k:j]]
        tot = sum(weights)
        t = left
        for n, wgt in enumerate(weights):
            d = span * wgt / tot
            times[k + n] = (t, t + d)
            t += d
        k = j
    matched = sum(1 for tag in difflib.SequenceMatcher(None, a, b).get_opcodes() if tag[0] == "equal")
    for w, (ws, we) in zip(words, times):
        out.append({"w": w, "s": round(max(st, ws), 3), "e": round(min(en + 0.05, we), 3),
                    "si": si, "part": s["part"], "style": s.get("style", "")})
    heard_txt = " ".join(w.word.strip() for w in heard)
    ok = [x for x in a if x] == [x for x in b if x]
    report.append({"i": si, "text": s["text"], "heard": heard_txt, "ok": ok})
    print(f"{si:2d} {'OK ' if ok else 'XX '}{s['text'][:40]:40s} heard: {heard_txt}")

json.dump(out, open(wav.replace(".wav", ".words.json"), "w"), indent=0)
json.dump(report, open(wav.replace(".wav", ".check.json"), "w"), indent=1)
print("words:", len(out))
