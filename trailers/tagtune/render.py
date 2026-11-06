"""Compose the picture: the real recorded window on a plain backdrop, typed title cards, burned captions.

    python3 render.py            -> work/picture.mp4 (no audio)
    python3 render.py --review   -> TagTune-review.jpg, eight frames for a quick look
Needs timeline.json (from narrate.py) and work/take.mp4 + work/take.json (from drive.py).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
PREVIEWS = ROOT.parent.parent / "previews"
W, H, FPS = 1920, 1080, 30
BG, TEXT, MUTED, ACCENT = (9, 13, 11), (198, 242, 210), (95, 138, 108), (74, 222, 128)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
font = lambda size, bold=False: ImageFont.truetype(MONO_BOLD if bold else MONO, size)  # noqa: E731

scenes = json.loads((ROOT / "timeline.json").read_text())
probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(WORK / "take.mp4")], capture_output=True, text=True, check=True)
RW, RH = map(int, probe.stdout.strip().split(","))
CROP = (25, 24, 1465, 872)  # the window itself; the rest of the recording is the black margin GNOME keeps for its shadow
TW, TH = CROP[2] - CROP[0], CROP[3] - CROP[1]
BASE = ((W - TW) // 2, 60)  # window position at normal size; the band below it holds the captions


class Take:
    """Reads the recording front to back; every scene asks for later times than the one before."""

    def __init__(self):
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(WORK / "take.mp4"), "-f", "rawvideo",
                                      "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.index, self.frame = -1, None

    def at(self, t):
        want = round(t * FPS)
        while self.index < want:
            raw = self.proc.stdout.read(RW * RH * 3)
            if len(raw) < RW * RH * 3:
                break  # past the end: keep the last frame
            self.frame, self.index = raw, self.index + 1
        return Image.frombytes("RGB", (RW, RH), self.frame).crop(CROP)


def shadow():
    pad = 80
    img = Image.new("L", (TW + 2 * pad, TH + 2 * pad), 0)
    ImageDraw.Draw(img).rounded_rectangle((pad, pad + 14, pad + TW, pad + TH + 14), 14, fill=150)
    return img.filter(ImageFilter.GaussianBlur(28)), pad


SHADOW, SPAD = shadow()


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def window(frame, scale=1.0, focus=None, amount=0.0):
    """The window on the backdrop; with focus, zoom in on that point of the window by amount (0..1)."""
    canvas = Image.new("RGB", (W, H), BG)
    s = 1 + (scale - 1) * amount
    x, y = BASE
    if focus and amount:
        fx, fy = focus
        # move so the focus point drifts toward the middle of the picture as it grows
        tx, ty = W / 2 - fx * scale, H * 0.3 - fy * scale
        x, y = x + (tx - x) * amount, y + (ty - y) * amount
    if s != 1:
        frame = frame.resize((round(TW * s), round(TH * s)), Image.LANCZOS)
    sh = SHADOW if s == 1 else SHADOW.resize((round(SHADOW.width * s), round(SHADOW.height * s)))
    canvas.paste((0, 0, 0), (round(x - SPAD * s), round(y - SPAD * s)), sh)
    canvas.paste(frame, (round(x), round(y)))
    return canvas


def phrases(text, total):
    """Split narration into caption phrases, timed by their share of the characters."""
    parts, line = [], ""
    for piece in re.findall(r"[^,.]+[,.]?", text):
        piece = piece.strip()
        if line and len(line) + len(piece) > 46:
            parts.append(line)
            line = piece
        else:
            line = f"{line} {piece}".strip()
    parts.append(line)
    weights = [len(p) + 6 for p in parts]
    t, out = 0, []
    for p, w in zip(parts, weights):
        d = total * w / sum(weights)
        out.append((t, t + d, p.rstrip(",")))
        t += d
    return out


CAPTION_FONT = font(32)


def caption(canvas, text, alpha):
    if not text or alpha <= 0:
        return canvas
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    w = d.textlength(text, font=CAPTION_FONT)
    y = H - 72
    d.rectangle((W / 2 - w / 2 - 18, y - 10, W / 2 + w / 2 + 18, y + 46), fill=BG + (round(215 * alpha),))
    d.text((W / 2 - w / 2, y), text, font=CAPTION_FONT, fill=TEXT + (round(255 * alpha),))
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


def card(kind, t, length):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    big = font(104 if kind == "intro" else 72, bold=True)
    word = "tagtune"
    typed = word[:max(0, min(len(word), int((t - 0.45) / 0.075)))]
    prompt_w = d.textlength("$ ", font=big)
    full_w = prompt_w + d.textlength(word, font=big)
    x = (W - full_w) / 2
    y = H / 2 - (110 if kind == "intro" else 120)
    d.text((x, y), "$", font=big, fill=ACCENT)
    d.text((x + prompt_w, y), typed, font=big, fill=TEXT)
    cx = x + prompt_w + d.textlength(typed, font=big) + 8
    asc, desc = big.getmetrics()
    done = len(typed) == len(word)
    if not done or int(t / 0.5) % 2 == 0:
        d.rectangle((cx, y + 8, cx + big.size * 0.55, y + asc + 6), fill=ACCENT)
    if kind == "intro":
        lines = [("youtube link in, tagged mp3 out", MUTED, font(38))]
    else:
        lines = [("github.com/Ken-n7/tagtune", ACCENT, font(44, bold=True)),
                 ("open source  ·  linux desktop", MUTED, font(32))]
    appear = 0.45 + len(word) * 0.075 + 0.35
    ly = y + asc + desc + 54
    for i, (text, color, f) in enumerate(lines):
        a = ease((t - appear - i * 0.3) / 0.5)
        if a > 0:
            w = d.textlength(text, font=f)
            c = tuple(round(BG[k] + (color[k] - BG[k]) * a) for k in range(3))
            d.text(((W - w) / 2, ly + (1 - a) * 10), text, font=f, fill=c)
        ly += f.size + 26
    fade_out = ease((length - t) / 0.45) if kind == "outro" else 1
    if fade_out < 1:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, fade_out)
    return img


def frames():
    take = Take()
    last = None
    for si, scene in enumerate(scenes):
        n = round(scene["duration"] * FPS)
        caps = phrases(scene["narration"], scene["voice_duration"])
        cuts = scene.get("cuts", [])
        zoom = scene.get("zoom")
        for i in range(n):
            t = i / FPS
            if "card" in scene:
                img = card(scene["card"], t, scene["duration"])
            else:
                # walk through the cuts in order; once they run out, hold the last frame
                left, src = t, cuts[-1][1]
                for a, b in cuts:
                    if left < b - a:
                        src = a + left
                        break
                    left -= b - a
                amount = 0.0
                if zoom:
                    amount = ease(t / 0.9) * ease((scene["duration"] - t) / 0.9)
                img = window(take.at(src), zoom["scale"] if zoom else 1.0, zoom and zoom["focus"], amount)
            # cross-fade out of a card, into the outro card
            if last is not None and i < 14 and (scenes[si - 1].get("card") == "intro" or scene.get("card") == "outro"):
                img = Image.blend(last, img, ease(i / 14))
            v = t - scene["voice_start"]
            text = next((p for a, b, p in caps if a <= v < b), None)
            if text:
                a, b, _ = next(c for c in caps if c[2] == text)
                img = caption(img, text, min(ease((v - a) / 0.15), ease((b - v) / 0.15) if b < caps[-1][1] else 1))
            yield img
        last = img


def main():
    if "--review" in sys.argv:
        total = sum(round(s["duration"] * FPS) for s in scenes)
        picks = {round(total * k / 8 + total / 16) for k in range(8)}
        shots = [img.resize((W // 4, H // 4)) for k, img in enumerate(frames()) if k in picks]
        sheet = Image.new("RGB", (W // 2, H), BG)
        for k, s in enumerate(shots):
            sheet.paste(s, ((k % 2) * W // 4, (k // 2) * H // 4))
        sheet.save(ROOT / "TagTune-review.jpg", quality=88)
        return
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                            "-pix_fmt", "yuv420p", str(WORK / "picture.mp4")], stdin=subprocess.PIPE)
    for k, img in enumerate(frames()):
        out.stdin.write(img.tobytes())
        if k % 150 == 0:
            print(f"frame {k}", flush=True)
    out.stdin.close()
    out.wait()


if __name__ == "__main__":
    main()
