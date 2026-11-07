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
        self.path = path
        self.size = probe(path)
        self.crop = crop
        self.proc = None
        self.index, self.frame = -1, None

    def close(self):
        if self.proc:
            self.proc.stdout.close()
            self.proc.terminate()
            self.proc.wait()
            self.proc = None

    def at(self, t):
        w, h = self.size
        target = round(t * FPS)
        if self.proc is None or target < self.index or target - self.index > FPS:
            self.close()
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(target / FPS),
                                          "-i", str(self.path), "-f", "rawvideo", "-pix_fmt", "rgb24",
                                          "-r", str(FPS), "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.index = target - 1
        while self.index < target:
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
VIDEO = (31, 70, 1149, 699)  # the player picture inside the desktop take
# real channel footage, blurred behind the cards: (take time, playback speed); clean playback, no buffering
BACKDROPS = {"intro": (216.6, .65), "disclaimer": (158.4, .5), "outro": (216.9, .6)}  # Red Bull stays before 220.5, where an old-film effect starts
XFADE = 15  # frames of cross-fade at every scene change


def camera(img, cx, cy, z):
    """Crop toward (cx, cy) at zoom z and scale back to the frame: one resample from the 1:1 canvas."""
    if z <= 1.0005:
        return img
    w, h = W / z, H / z
    x, y = min(max(cx - w / 2, 0), W - w), min(max(cy - h / 2, 0), H - h)
    return img.resize((W, H), Image.BICUBIC, box=(x, y, x + w, y + h))


def backdrop(frame, t, length):
    small = frame.resize((256, 144), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4))
    z = 1.08 + .07 * t / length  # slow drift so the card never sits still
    w, h = 256 / z, 144 / z
    img = small.resize((W, H), Image.BICUBIC, box=((256 - w) / 2, (144 - h) / 2, (256 + w) / 2, (144 + h) / 2))
    return Image.blend(Image.new("RGB", (W, H), BG), img, .36)


def card(kind, t, length, base):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def fade(start, dur=0.5):
        return ease((t - start) / dur)

    def text_center(y, text, f, color, a):
        if a <= 0:
            return
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y + (1 - a) * 12), text, font=f, fill=color + (round(255 * a),))

    if kind in ("intro", "outro"):
        size = 200 if kind == "intro" else 150
        a = fade(0.3, 0.6)
        icon = ICON.resize((size, size), Image.LANCZOS)
        icon.putalpha(icon.getchannel("A").point(lambda v: round(v * a)))
        y0 = 250 if kind == "intro" else 230
        layer.alpha_composite(icon, ((W - size) // 2, y0))
        text_center(y0 + size + 30, "reLiveTV", font(96, True), TEXT, fade(0.7))
        if kind == "intro":
            text_center(y0 + size + 160, "free live TV from around the world", font(40), MUTED, fade(1.2))
        else:
            text_center(y0 + size + 160, "github.com/Ken-n7/reLiveTV", font(46, True), TEXT, fade(1.0))
            text_center(y0 + size + 230, "linux  ·  android  ·  android tv", font(34), MUTED, fade(1.3))
    elif kind == "disclaimer":
        text_center(250, "Good to know", font(64, True), TEXT, fade(0.2))
        lines = ["Channel availability can change.",
                 "Some channels may be offline or unavailable in your region.",
                 "Schedules may be inaccurate.",
                 "reLiveTV does not host any streams."]
        for i, line in enumerate(lines):
            text_center(380 + i * 88, line, font(40), (190, 190, 190), fade(0.6 + i * 0.25))
    img = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")
    if kind == "intro" and t < 0.6:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, ease(t / 0.6))
    if kind == "outro" and length - t < 0.5:
        img = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), img, ease((length - t) / 0.5))
    return img


def frames(picks=None):
    takes = {"bg": Take(WORK / "take.mp4", VIDEO)}
    last = None
    frame_number = 0
    for si, scene in enumerate(scenes):
        scene_last = None
        n = round(scene["duration"] * FPS)
        caps = phrases(scene["narration"], scene["voice_duration"])
        cuts = scene.get("cuts", [])
        source = scene.get("source", "desktop")
        cx, cy, z0, z1 = scene.get("zoom", (W / 2, H / 2, 1, 1))
        cut_last = None
        if cuts and source not in takes:
            takes[source] = Take(WORK / ("take.mp4" if source == "desktop" else "phone.mp4"),
                                 CROP if source == "desktop" else scene.get("crop"))
        for i in range(n):
            frame_number += 1
            # the tail of a skipped transition still needs the outgoing frame, so only skip once past it
            if picks is not None and frame_number - 1 not in picks and i >= XFADE:
                continue
            t = i / FPS
            if "card" in scene:
                at, speed = BACKDROPS[scene["card"]]
                img = card(scene["card"], t, scene["duration"],
                           backdrop(takes["bg"].at(at + t * speed), t, scene["duration"]))
            else:
                left, src, part = t, cuts[-1][1], len(cuts) - 1
                for k, (a, b) in enumerate(cuts):
                    if left < b - a:
                        src, part = a + left, k
                        break
                    left -= b - a
                frame = takes[source].at(src)
                img = desktop(frame) if source == "desktop" else phone(frame)
                if scene.get("note"):
                    img = note(img, scene["note"], ease((t - 0.6) / 0.4) * ease((scene["duration"] - t) / 0.4))
                img = camera(img, cx, cy, z0 + (z1 - z0) * ease(t / scene["duration"]))
                # a jump between cuts inside one scene dissolves too
                if part and left < XFADE / FPS and cut_last is not None:
                    img = Image.blend(cut_last, img, ease((left * FPS + 1) / (XFADE + 1)))
                elif left >= XFADE / FPS or not part:
                    cut_last = img
            scene_last = img
            if last is not None and i < XFADE:
                img = Image.blend(last, img, ease((i + 1) / (XFADE + 1)))
            v = t - scene["voice_start"]
            end = caps[-1][1]
            hit = next(((a, b, p) for a, b, p in caps if a <= v < (b if b < end else end + .25)), None)
            if hit:
                a, b, text = hit
                img = caption(img, text, min(ease((v - a) / 0.15), ease((b - v) / 0.15) if b < end
                                              else ease((end + .25 - v) / .25)))
            if picks is None or frame_number - 1 in picks:
                yield img
        if scene_last is not None:
            last = scene_last
    for take in takes.values():
        take.close()


def main():
    if "--review" in sys.argv:
        total = sum(round(s["duration"] * FPS) for s in scenes)
        picks = {round(total * k / 8 + total / 16) for k in range(8)}
        shots = [img.resize((W // 4, H // 4)) for img in frames(picks)]
        sheet = Image.new("RGB", (W // 2, H), BG)
        for k, s in enumerate(shots):
            sheet.paste(s, ((k % 2) * W // 4, (k // 2) * H // 4))
        sheet.save(ROOT / "reLiveTV-review.jpg", quality=88)
        return
    out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "16",
                            "-pix_fmt", "yuv420p", str(WORK / "picture.mp4")], stdin=subprocess.PIPE)
    for k, img in enumerate(frames()):
        out.stdin.write(img.tobytes())
        if k % 300 == 0:
            print(f"frame {k}", flush=True)
    out.stdin.close()
    if out.wait() != 0:
        raise RuntimeError("Picture encoding failed")


if __name__ == "__main__":
    main()
