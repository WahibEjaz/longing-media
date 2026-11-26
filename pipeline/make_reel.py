"""Build one finished reel from a part folder, with checks.

usage: python3 pipeline/make_reel.py parts/part_03

The folder needs script.json (sentences + scenes) and the images its scenes name.
Steps: narrate (Soft American voice) -> check every line with Whisper -> render ->
"PART N" cover (from Part 3 on) -> loudness and frame checks.
Writes into the folder: narration.wav (+ .timing/.words/.check json), reel.mp4,
cover.jpg, qa_frames.jpg, qa.json. Exits with code 2 if any line is misheard
(fix that sentence with a "say" field and run again).
"""
import json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PIPE = REPO / "pipeline"
part = (REPO / sys.argv[1]).resolve() if not Path(sys.argv[1]).is_absolute() else Path(sys.argv[1])
script = part / "script.json"
data = json.load(open(script))
voice, speed = data.get("voice", "af_bella"), str(data.get("speed", 1.0))
n = int(data["reel_number"])
wav = part / "narration.wav"
reel, cover = part / "reel.mp4", part / "cover.jpg"

def run(*args):
    print("+", " ".join(map(str, args)), flush=True)
    return subprocess.run(list(map(str, args)), check=True, capture_output=True, text=True)

# 1. voice and word check
run(sys.executable, PIPE / "narrate.py", script, voice, wav, speed)
run(sys.executable, PIPE / "align.py", wav)
check = json.load(open(str(wav).replace(".wav", ".check.json")))
bad = [c for c in check if not c["ok"]]
for c in check:
    print(("OK  " if c["ok"] else "BAD ") + c["text"] + "   | heard: " + c["heard"])
if bad:
    print("\nMisheard lines: add a \"say\" field to these sentences and run again.")
    sys.exit(2)

# 2. render
r = run(sys.executable, PIPE / "render3.py", script, wav, reel)
print(r.stdout[-1500:])
if "TOO WIDE" in r.stdout:
    print("A caption line is too wide: split it with ' / ' in its cap and run again.")
    sys.exit(3)

# 3. cover with PART N (Parts 1 and 2 were posted without one)
timing = json.load(open(str(wav).replace(".wav", ".timing.json")))["sentences"]
hook_end = max(s["end"] for s in timing if s.get("part") == "hook")
cover_t = data.get("cover_time", round(hook_end - 0.05, 2))
if n >= 3:
    run(sys.executable, PIPE / "make_cover.py", reel, cover_t, n, cover)

# 4. loudness and a sheet of frames (one per sentence end) to look at
ff = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(reel), "-af", "ebur128", "-f", "null", "-"],
                    capture_output=True, text=True).stderr
lufs = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", ff)[-1])
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(reel)],
                           capture_output=True, text=True).stdout)
from PIL import Image
times = [s["end"] - 0.05 for s in timing]
thumbs = []
for k, t in enumerate(times):
    f = f"/tmp/_qa_{k}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(reel), "-frames:v", "1", "-vf", "scale=216:384", f], check=True)
    thumbs.append(Image.open(f))
cols = 6
sheet = Image.new("RGB", (216 * cols, 384 * ((len(thumbs) + cols - 1) // cols)))
for i, im in enumerate(thumbs):
    sheet.paste(im, ((i % cols) * 216, (i // cols) * 384))
sheet.save(part / "qa_frames.jpg", quality=85)

qa = {"part": n, "duration_s": round(dur, 2), "loudness_lufs": lufs, "lines_ok": len(check), "cover": cover.name if n >= 3 else None,
      "cover_time_s": cover_t}
json.dump(qa, open(part / "qa.json", "w"), indent=1)
print("\nQA", json.dumps(qa))
if not (25 <= dur <= 60):
    print("WARNING: length outside 25 to 60 seconds")
if abs(lufs + 15) > 1.5:
    print("WARNING: loudness not near -15 LUFS")
