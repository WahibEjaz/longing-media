"""Make a reel cover (thumbnail) with a "PART N" badge, from Part 3 onwards.

usage: python3 make_cover.py reel.mp4 seconds part_number out.jpg

Takes the frame at `seconds` (pick a hook frame with text on screen), and adds a
"PART N" badge low in the centre, inside the 3:4 area the Instagram profile grid
keeps (y 240 to 1680 of a 1080 x 1920 frame), so it shows on the grid, in the feed
and in the Reels tab. Upload the result next to the reel and pass it as cover_url.
"""
import subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REEL, T, PART, OUT = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from pathlib import Path
FD = str(Path(__file__).resolve().parent.parent / "fonts") + "/"
W, H = 1080, 1920

subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{T:.2f}", "-i", REEL, "-frames:v", "1", "/tmp/_cover_frame.png"], check=True)
img = Image.open("/tmp/_cover_frame.png").convert("RGBA").resize((W, H))

f_word = ImageFont.truetype(FD + "Inter-Bold.otf", 70)
f_num = ImageFont.truetype(FD + "CrimsonText-SemiBoldItalic.ttf", 120)
word, num = "PART", str(PART)
spacing = 12
word_w = sum(f_word.getlength(c) for c in word) + spacing * (len(word) - 1)
num_w = f_num.getlength(num)
gap = 26
total = word_w + gap + num_w
pad_x, box_h = 64, 150
cy = 1470                                  # badge centre, inside the grid's 3:4 crop
box = (int((W - total) / 2 - pad_x), int(cy - box_h / 2), int((W + total) / 2 + pad_x), int(cy + box_h / 2))

layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
d.rounded_rectangle(box, radius=box_h // 2, fill=(6, 10, 22, 190), outline=(143, 216, 255, 150), width=3)
img = Image.alpha_composite(img, layer)

# glow behind the number, like the blue words in the reels
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
x0 = (W - total) / 2
gd = ImageDraw.Draw(glow)
gd.text((x0 + word_w + gap, cy - 78), num, font=f_num, fill=(26, 86, 176, 255))
img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(10)))

d = ImageDraw.Draw(img)
x = x0
for c in word:
    d.text((x, cy - 42), c, font=f_word, fill=(255, 255, 255, 255))
    x += f_word.getlength(c) + spacing
d.text((x0 + word_w + gap, cy - 78), num, font=f_num, fill=(143, 216, 255, 255))
img.convert("RGB").save(OUT, quality=92)
print("cover", OUT)
