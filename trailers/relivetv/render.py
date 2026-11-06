"""Compose the picture: the real recorded window(s) on a plain backdrop, title cards, burned captions.

    python3 render.py            -> work/picture.mp4 (no audio)
    python3 render.py --review   -> reLiveTV-review.jpg, eight frames for a quick look
Needs timeline.json (from narrate.py), work/take.mp4 (desktop, from record.sh) and, for phone scenes,
work/phone.mp4 (from record_phone.sh).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
PREVIEWS = ROOT.parent.parent / "previews"
W, H, FPS = 1920, 1080, 30
BG, TEXT, MUTED, LINE = (14, 14, 14), (242, 242, 242), (150, 150, 150), (60, 60, 60)
SANS = "/usr/share/fonts/truetype/ubuntu/UbuntuSans[wdth,wght].ttf"


def font(size, bold=False):
    f = ImageFont.truetype(SANS, size)
    try:
        f.set_variation_by_axes([100, 700 if bold else 400])
    except OSError:
        pass
    return f


scenes = json.loads((ROOT / "timeline.json").read_text())


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    return tuple(map(int, out.strip().split(",")))


class Take:
    """Reads a recording front to back, cropped; every scene asks for later times than the one before."""

    def __init__(self, path, crop=None):
        self.size = probe(path)
        self.crop = crop
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-f", "rawvideo", "-pix_fmt", "rgb24",
                                      "-r", str(FPS), "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.index, self.frame = -1, None

    def at(self, t):
        w, h = self.size
        while self.index < round(t * FPS):
            raw = self.proc.stdout.read(w * h * 3)
            if len(raw) < w * h * 3:
                break  # past the end: keep the last frame
            self.frame, self.index = raw, self.index + 1
        img = Image.frombytes("RGB", self.size, self.frame)
        return img.crop(self.crop) if self.crop else img


CROP = (26, 23, 1574, 872)  # the window itself; the rest is the transparent margin GNOME keeps for its shadow
TW, TH = CROP[2] - CROP[0], CROP[3] - CROP[1]
BASE = ((W - TW) // 2, 52)  # window position; the band below holds the captions


def shadow(w, h, radius):
    pad = 80
    img = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
    ImageDraw.Draw(img).rounded_rectangle((pad, pad + 14, pad + w, pad + h + 14), radius, fill=170)
    return img.filter(ImageFilter.GaussianBlur(28)), pad


SHADOW, SPAD = shadow(TW, TH, 14)


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def desktop(frame):
    canvas = Image.new("RGB", (W, H), BG)
    canvas.paste((0, 0, 0), (BASE[0] - SPAD, BASE[1] - SPAD), SHADOW)
    canvas.paste(frame, BASE)
    return canvas


PH_H = 900  # phone screen height on the canvas


def phone(frame):
    """The phone's screen recording inside a plain phone body, centered."""
    s = PH_H / frame.height
    screen = frame.resize((round(frame.width * s), PH_H), Image.LANCZOS)
    bez, r = 16, 46
    bw, bh = screen.width + 2 * bez, screen.height + 2 * bez
    x, y = (W - bw) // 2, 40
    canvas = Image.new("RGB", (W, H), BG)
    sh, pad = shadow(bw, bh, r)
    canvas.paste((0, 0, 0), (x - pad, y - pad), sh)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((x, y, x + bw, y + bh), r, fill=(5, 5, 5), outline=(70, 70, 70), width=3)
    mask = Image.new("L", screen.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, screen.width - 1, screen.height - 1), r - bez, fill=255)
    canvas.paste(screen, (x + bez, y + bez), mask)
    return canvas


def phrases(text, total):
    parts, line = [], ""
    for piece in re.findall(r"[^,.]+[,.]?", text):
        piece = piece.strip()
        if line and len(line) + len(piece) > 52:
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


CAPTION_FONT = font(34)
NOTE_FONT = font(26)


def overlay(canvas, draw_fn):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    return Image.alpha_composite(canvas.convert("RGBA"), layer).convert("RGB")


def caption(canvas, text, alpha):
    if not text or alpha <= 0:
        return canvas

    def draw(d):
        w = d.textlength(text, font=CAPTION_FONT)
        y = H - 74
        d.rounded_rectangle((W / 2 - w / 2 - 20, y - 10, W / 2 + w / 2 + 20, y + 48), 10,
                            fill=(0, 0, 0, round(200 * alpha)))
        d.text((W / 2 - w / 2, y), text, font=CAPTION_FONT, fill=TEXT + (round(255 * alpha),))
    return overlay(canvas, draw)


def note(canvas, text, alpha):
    """A small boxed note over the footage, top left: the schedule disclaimer."""
    def draw(d):
        w = d.textlength("Note:  " + text, font=NOTE_FONT)
        x, y = BASE[0] + 28, BASE[1] + 70
        d.rounded_rectangle((x, y, x + w + 36, y + 56), 12, fill=(0, 0, 0, round(215 * alpha)),
                            outline=(255, 255, 255, round(90 * alpha)), width=2)
        d.text((x + 18, y + 12), "Note:  " + text, font=NOTE_FONT, fill=TEXT + (round(255 * alpha),))
    return overlay(canvas, draw)


ICON = Image.open(PREVIEWS / "relivetv.png").convert("RGBA")


def card(kind, t, length):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    def fade(start, dur=0.5):
        return ease((t - start) / dur)

    def text_center(y, text, f, color, a):
        if a <= 0:
            return
        w = d.textlength(text, font=f)
        c = tuple(round(BG[k] + (color[k] - BG[k]) * a) for k in range(3))
        d.text(((W - w) / 2, y + (1 - a) * 12), text, font=f, fill=c)

    if kind in ("intro", "outro"):
        size = 200 if kind == "intro" else 150
        a = fade(0.3, 0.6)
        icon = ICON.resize((size, size), Image.LANCZOS)
        icon.putalpha(icon.getchannel("A").point(lambda v: round(v * a)))
        y0 = 250 if kind == "intro" else 230
        img.paste(icon, ((W - size) // 2, y0), icon)
        text_center(y0 + size + 30, "reLiveTV", font(96, True), TEXT, fade(0.7))
        if kind == "intro":
            text_center(y0 + size + 160, "free live TV from around the world", font(40), MUTED, fade(1.2))
        else:
            text_center(y0 + size + 160, "github.com/Ken-n7/reLiveTV", font(46, True), TEXT, fade(1.0))
            text_center(y0 + size + 230, "open source  ·  linux, android & android tv", font(34), MUTED, fade(1.3))
    elif kind == "disclaimer":
        text_center(250, "Good to know", font(64, True), TEXT, fade(0.2))
        lines = ["Channels come and go: some may be offline or",
                 "geo-blocked in your country at times.",
                 "Schedules come from public guide data and may not be accurate.",
                 "reLiveTV doesn't host any streams. It plays links",
                 "that iptv-org lists publicly."]
        y = 380
        for i, line in enumerate(lines):
            text_center(y, line, font(40), MUTED if i != 2 else MUTED, fade(0.6 + i * 0.25))
            y += 62 + (24 if i in (1, 2) else 0)
    if kind == "outro" and length - t < 0.5:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, ease((length - t) / 0.5))
    return img


def frames():
    takes = {}
    last = None
    for si, scene in enumerate(scenes):
        n = round(scene["duration"] * FPS)
        caps = phrases(scene["narration"], scene["voice_duration"])
        cuts = scene.get("cuts", [])
        source = scene.get("source", "desktop")
        still = None
        if scene.get("still"):
            still = Image.open(WORK / scene["still"]).convert("RGB").crop(scene["still_crop"])
            # the still is the app at phone size in logical pixels; scale up cleanly before framing
            still = still.resize((still.width * 3, still.height * 3), Image.LANCZOS)
            source = "phone"
        if cuts and source not in takes:
            takes[source] = Take(WORK / "take.mp4", CROP)
        for i in range(n):
            t = i / FPS
            if "card" in scene:
                img = card(scene["card"], t, scene["duration"])
            elif still is not None:
                img = phone(still)
            else:
                left, src = t, cuts[-1][1]
                for a, b in cuts:
                    if left < b - a:
                        src = a + left
                        break
                    left -= b - a
                frame = takes[source].at(src)
                img = desktop(frame) if source == "desktop" else phone(frame)
                if scene.get("note"):
                    img = note(img, scene["note"], ease((t - 0.6) / 0.4) * ease((scene["duration"] - t) / 0.4))
            # cross-fade from and to cards, and between desktop and phone
            prev = scenes[si - 1] if si else {}
            if last is not None and i < 14 and ("card" in prev or "card" in scene
                                                 or prev.get("source", "desktop") != source):
                img = Image.blend(last, img, ease(i / 14))
            v = t - scene["voice_start"]
            hit = next(((a, b, p) for a, b, p in caps if a <= v < b), None)
            if hit:
                a, b, text = hit
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
        sheet.save(ROOT / "reLiveTV-review.jpg", quality=88)
        return
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
                            "-pix_fmt", "yuv420p", str(WORK / "picture.mp4")], stdin=subprocess.PIPE)
    for k, img in enumerate(frames()):
        out.stdin.write(img.tobytes())
        if k % 300 == 0:
            print(f"frame {k}", flush=True)
    out.stdin.close()
    out.wait()


if __name__ == "__main__":
    main()
