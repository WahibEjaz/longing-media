"""Render a narrated reel from several still images ("motion comic"), with kinetic text.

usage: python3 render3.py script.json narration.wav out.mp4

The script's "scenes" list says which image is on screen and how the camera moves:
  {"img": path, "from": first sentence index it covers,
   "cam0": [cx, cy, zoom], "cam1": [cx, cy, zoom],   # pixels of the image scaled to 768 wide; zoom 1 = full width
   "shade": "top" | "bottom",                        # dark gradient behind the text
   "dim": 0.3, "dim_from": sentence index}           # optional darkening (e.g. a warning line)
A scene starts 0.25 s before its first sentence and cross-fades over 0.35 s.
Captions work exactly as in render2.py: in "cap", ' | ' = new block, ' / ' = new line,
*word* = accent (blue italic serif), **word** = bold; "y" = top of the block; "cont" continues a block.
"byline": true (every 5th reel) adds "a story by Wahib" under the LONGING title at the end.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT, WAV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DATA = json.load(open(SCRIPT))
SC = DATA["sentences"]
T = json.load(open(WAV.replace(".wav", ".timing.json")))
WORDS = json.load(open(WAV.replace(".wav", ".words.json")))
S = T["sentences"]
assert [s["text"] for s in S] == [s["text"] for s in SC], "script and narration differ"
FPS, W, H = 30, 1080, 1920
DUR = T["duration"] + 0.6
XF, LEAD = 0.35, 0.25
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
ROOT = str(Path(SCRIPT).resolve().parent) + "/"   # scene images are relative to the script's folder

# ---------- scenes ----------
def load_img(path):
    """Open an image and bring it to 768 px wide (Flow's 9:16 size), so camera numbers
    work whatever size it was downloaded at. Wider-than-9:16 images are centre-cropped."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if h / w < 16 / 9 - 0.02:
        nw = int(h * 9 / 16)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        w = nw
    if w != 768:
        im = im.resize((768, round(h * 768 / w)), Image.LANCZOS)
    return im

IMGS = {}
scenes = []
for i, sc in enumerate(DATA["scenes"]):
    if sc["img"] not in IMGS:
        IMGS[sc["img"]] = load_img(os.path.join(ROOT, sc["img"]))
    start = 0.0 if i == 0 else S[sc["from"]]["start"] - LEAD
    scenes.append({**sc, "start": start})
for i, sc in enumerate(scenes):
    sc["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else DUR
    if "dim_from" in sc:
        sc["dim_t"] = S[sc["dim_from"]]["start"] - 0.2

def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)

def fade(t, a, b, d=0.4):
    if t < a or t > b:
        return 0.0
    return min(1.0, (t - a) / d, (b - t) / d)

def grad(top_to, top_a, bottom_from, bottom_a):
    a = np.zeros((H, W, 4), dtype=np.uint8)
    for y in range(H):
        v = 0
        if y < top_to:
            v = int(top_a * (1 - y / top_to) ** 0.85)
        if y > bottom_from:
            v = max(v, int(bottom_a * min(1, (y - bottom_from) / (H - bottom_from)) ** 0.8))
        a[y, :, 3] = v
    return Image.fromarray(a, "RGBA")

SHADES = {"top": grad(980, 225, 1500, 110),        # text near the top, over sky
          "bottom": grad(260, 90, 1080, 225)}       # text near the bottom, over ground

def shot(sc, t):
    img = IMGS[sc["img"]]
    IW, IH = img.size
    k = ease((t - sc["start"]) / max(0.1, sc["end"] + XF - sc["start"]))
    (x0_, y0_, z0), (x1_, y1_, z1) = sc["cam0"], sc["cam1"]
    cx, cy, z = x0_ + (x1_ - x0_) * k, y0_ + (y1_ - y0_) * k, z0 + (z1 - z0) * k
    vw = IW / z
    vh = vw * H / W
    x0 = min(max(cx - vw / 2, 0), IW - vw)
    y0 = min(max(cy - vh / 2, 0), IH - vh)
    fr = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + vw, y0 + vh)).convert("RGBA")
    dim = sc.get("dim", 0) * fade(t, sc["dim_t"], sc["end"] + 1, 0.4) if "dim_t" in sc else 0
    if dim:
        fr = Image.blend(fr, Image.new("RGBA", (W, H), (10, 6, 12, 255)), dim)
    return Image.alpha_composite(fr, SHADES[sc.get("shade", "top")])

# ---------- end card ----------
GF = str(REPO / "fonts")
F_BIG = ImageFont.truetype(f"{GF}/Cardo-Regular.ttf", 120)
F_SUB = ImageFont.truetype(f"{GF}/Inter-Light.otf", 32)

def spaced(d, text, font, cy, fill, spacing):
    w = sum(font.getlength(c) for c in text) + spacing * (len(text) - 1)
    x = (W - w) / 2
    for c in text:
        d.text((x, cy), c, font=font, fill=fill)
        x += font.getlength(c) + spacing

def layer(draw_fn, blur=8):
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(sh), True)
    draw_fn(ImageDraw.Draw(fg), False)
    return Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)), fg)

BYLINE = DATA.get("byline", False)
def _endcard(d, s):
    spaced(d, "LONGING", F_BIG, 840 + (4 if s else 0), (0, 0, 0, 230) if s else (255, 255, 255, 245), 26)
    if BYLINE:
        spaced(d, "a story by Wahib", F_SUB, 1000 + (3 if s else 0), (0, 0, 0, 230) if s else (255, 255, 255, 215), 4)
ENDT = layer(_endcard, blur=10)
cta_i = next(i for i, s in enumerate(SC) if s["part"] == "cta")
cta_start = S[cta_i]["start"] - 0.3

def with_alpha(im, a):
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im

def frame(t):
    cur = next(i for i, sc in enumerate(scenes) if sc["start"] <= t < sc["end"] or i == len(scenes) - 1)
    img = shot(scenes[cur], t)
    if cur > 0 and t < scenes[cur]["start"] + XF:            # cross-fade from the previous scene
        prev = shot(scenes[cur - 1], t)
        img = Image.blend(prev, img, ease((t - scenes[cur]["start"]) / XF))
    dim = fade(t, cta_start + 0.2, DUR + 1, 0.6) * 0.55
    if dim:
        img = Image.blend(img, Image.new("RGBA", (W, H), (8, 12, 24, 255)), dim)
    e = fade(t, cta_start + 0.4, DUR + 1, 0.6)
    if e:
        img = Image.alpha_composite(img, with_alpha(ENDT, e))
    out = min(fade(t, -1, DUR, 0.6), 1.0)
    if t < 0.3:
        out = min(out, 0.35 + t / 0.3 * 0.65)                # quick fade-in from near black
    if out < 1:
        img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, out)
    return img.convert("RGB").tobytes()

# ---------- kinetic captions (ASS), same as render2 ----------
def ts(x):
    x = max(0, x)
    return f"{int(x // 3600)}:{int(x % 3600 // 60):02d}:{x % 60:05.2f}"

BASE = r"\fnInter Medium\b0\i0\fs72\c&H00FFFFFF&\3c&H00000000&\bord3\blur5"
BOLD = r"\fnInter\b1\i0\fs92\c&H00FFFFFF&\3c&H00000000&\bord3\blur5"
ACC = r"\fnCrimson Text\b1\i1\fs112\c&H00FFD88F&\3c&H00B0561A&\bord5\blur9"
ACC_BIG = r"\fnCrimson Text\b1\i1\fs220\c&H00FFD88F&\3c&H00B0561A&\bord8\blur14"

FD = str(REPO / "fonts") + "/"
MEASURE = {"base": ImageFont.truetype(FD + "Inter-Medium.otf", 72),
           "bold": ImageFont.truetype(FD + "Inter-Bold.otf", 92),
           "acc": ImageFont.truetype(FD + "CrimsonText-SemiBoldItalic.ttf", 112),
           "accbig": ImageFont.truetype(FD + "CrimsonText-SemiBoldItalic.ttf", 220)}
def line_width(line):
    sp = MEASURE["base"].getlength(" ")
    return sum(MEASURE[t["st"]].getlength(t["w"]) for t in line) + sp * (len(line) - 1)

blocks = []
for si, (sent, meta) in enumerate(zip(S, SC)):
    ws = [w for w in WORDS if w["si"] == si]
    k = 0
    for bi, bstr in enumerate(meta["cap"].split(" | ")):
        lines = []
        for lstr in bstr.split(" / "):
            line, mode = [], None
            for tok in lstr.split():
                if mode is None:
                    if tok.startswith("**"):
                        mode, tok = "bold", tok[2:]
                    elif tok.startswith("*"):
                        mode, tok = ("accbig" if meta.get("big") else "acc"), tok[1:]
                st, closing = mode or "base", False
                if mode == "bold" and tok.endswith("**"):
                    tok, closing = tok[:-2], True
                elif mode in ("acc", "accbig") and tok.endswith("*"):
                    tok, closing = tok[:-1], True
                if closing:
                    mode = None
                assert tok == ws[k]["w"], (tok, ws[k]["w"])
                line.append({"w": tok, "st": st, "s": ws[k]["s"], "e": ws[k]["e"]})
                k += 1
            lines.append(line)
        if bi == 0 and meta.get("cont") and blocks:
            blocks[-1]["lines"].extend(lines)
        else:
            blocks.append({"y": meta.get("y", 330), "lines": lines})
    assert k == len(ws), meta["text"]

STY = {"base": BASE, "bold": BOLD, "acc": ACC, "accbig": ACC_BIG}
events = []
for bi, b in enumerate(blocks):
    toks = [t for line in b["lines"] for t in line]
    start = toks[0]["s"] - 0.05
    if bi + 1 < len(blocks):
        nxt = blocks[bi + 1]["lines"][0][0]["s"] - 0.04
        end = nxt if nxt - toks[-1]["e"] < 0.8 else toks[-1]["e"] + 0.5
    else:
        end = DUR
    for n, tok in enumerate(toks):
        s0 = start if n == 0 else tok["s"]
        e0 = toks[n + 1]["s"] if n + 1 < len(toks) else end
        if e0 <= s0:
            continue
        out_lines, idx = [], 0
        for line in b["lines"]:
            parts = []
            for t in line:
                tag = "{\\r" + STY[t["st"]]
                if idx > n:
                    tag += "\\alpha&HFF&"
                elif idx == n:
                    tag += "\\alpha&HFF&\\t(0,140,\\alpha&H00&)"
                parts.append(tag + "}" + t["w"].replace("{", "").replace("}", ""))
                idx += 1
            out_lines.append(" ".join(parts))
        events.append(f"Dialogue: 0,{ts(s0)},{ts(e0)},Base,,0,0,0,,{{\\an8\\pos(540,{b['y']})}}" + "\\N".join(out_lines))

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Inter Medium,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,0,8,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + "\n".join(events) + "\n"
ASS_PATH = OUT.replace(".mp4", ".ass")
open(ASS_PATH, "w").write(ass)
for b in blocks:
    widest = max(line_width(l) for l in b["lines"])
    flag = "  <-- TOO WIDE" if widest > 1000 else ""
    print(b["y"], f"{widest:4.0f}px", " / ".join(" ".join(t["w"] for t in l) for l in b["lines"]), flag)
for sc in scenes:
    print(f"scene {sc['img'].split('/')[-1]:16s} {sc['start']:6.2f} -> {sc['end']:6.2f}")

fonts = str(REPO / "fonts")
cmd = ["ffmpeg", "-y", "-v", "error",
       "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", WAV,
       "-filter_complex",
       f"[0:v]ass={ASS_PATH}:fontsdir={fonts},format=yuv420p[v];"
       f"[1:a]apad=whole_dur={DUR},loudnorm=I=-15:TP=-1.5:LRA=7,aresample=48000[a]",
       "-map", "[v]", "-map", "[a]", "-t", f"{DUR:.2f}",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    p.stdin.write(frame(i / FPS))
p.stdin.close()
p.wait()
print("done", OUT, f"{DUR:.2f}s", len(blocks), "text blocks", len(scenes), "scenes")
