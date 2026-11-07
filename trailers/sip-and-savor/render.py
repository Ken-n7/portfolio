"""Compose real recordings with Inter titles, phone/browser frames and gentle dissolves."""
import functools
import json
import math
import re
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
PREVIEWS = ROOT.parent.parent / "previews"
W, H, FPS = 1920, 1080, 30
BG = (11, 18, 33)
FG = (241, 245, 249)
MUTED = (159, 177, 199)
ACCENT = (96, 165, 250)
LINE = (36, 53, 76)
SCENES = json.loads((ROOT / "timeline.json").read_text())
CAPTURE = json.loads((ROOT / "capture.json").read_text())


def prepare_font():
    target = WORK / "inter.ttf"
    if target.exists():
        return target
    candidates = sorted(Path("/home/ken/Workspace/sip_and_savor/.next/static/media").glob("*.woff2"))
    candidates.append(ROOT.parent.parent / "brand/inter-sip.woff2")
    for candidate in candidates:
        face = TTFont(candidate)
        if 38 in face.getBestCmap():
            face.flavor = None
            face.save(target)
            return target
    raise RuntimeError("Inter font is unavailable")


FONT = prepare_font()


@functools.lru_cache(maxsize=80)
def font(size, weight=400):
    face = ImageFont.truetype(str(FONT), size)
    try:
        face.set_variation_by_axes([weight])
    except OSError:
        pass
    return face


def ease(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


@functools.lru_cache(maxsize=20)
def shadow(w, h, radius):
    pad = 36
    mask = Image.new("L", (w + pad * 2, h + pad * 2))
    ImageDraw.Draw(mask).rounded_rectangle((pad, pad + 9, w + pad, h + pad), radius, fill=170)
    return mask.filter(ImageFilter.GaussianBlur(18)), pad


@functools.lru_cache(maxsize=20)
def mask(w, h, radius):
    result = Image.new("L", (w, h))
    ImageDraw.Draw(result).rounded_rectangle((0, 0, w - 1, h - 1), radius, fill=255)
    return result


def surface(canvas, frame, x, y, width, radius=12):
    height = round(frame.height * width / frame.width)
    frame = frame.resize((width, height), Image.Resampling.LANCZOS)
    sh, pad = shadow(width, height, radius)
    canvas.paste((0, 0, 0), (x - pad, y - pad), sh)
    canvas.paste(frame, (x, y), mask(width, height, radius))
    return height


def window(canvas, frame, x, y, width):
    height = round(frame.height * width / frame.width)
    chrome = 34
    shell = Image.new("RGB", (width, height + chrome), BG)
    draw = ImageDraw.Draw(shell)
    draw.rectangle((0, 0, width, chrome), fill=(22, 33, 52))
    for i, color in enumerate([(114, 131, 154), (81, 104, 132), (56, 83, 115)]):
        draw.ellipse((16 + i * 19, 12, 26 + i * 19, 22), fill=color)
    draw.text((width / 2, 9), "sip-and-savor.vercel.app", font=font(16), fill=MUTED, anchor="mt")
    shell.paste(frame.resize((width, height), Image.Resampling.LANCZOS), (0, chrome))
    surface(canvas, shell, x, y, width, 14)


def phone(canvas, frame, x, y, screen_height=858):
    scale = screen_height / frame.height
    screen_width = round(frame.width * scale)
    bezel = 13
    body_w, body_h = screen_width + bezel * 2, screen_height + bezel * 2
    shell = Image.new("RGB", (body_w, body_h), (5, 9, 17))
    sh, pad = shadow(body_w, body_h, 45)
    canvas.paste((0, 0, 0), (x - pad, y - pad), sh)
    shell.paste(frame.resize((screen_width, screen_height), Image.Resampling.LANCZOS), (bezel, bezel), mask(screen_width, screen_height, 32))
    draw = ImageDraw.Draw(shell)
    draw.rounded_rectangle((0, 0, body_w - 1, body_h - 1), 45, outline=(64, 83, 110), width=2)
    canvas.paste(shell, (x, y), mask(body_w, body_h, 45))


def wrapped(text, face, max_width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if line and face.getlength(test) > max_width:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def lines(draw, text, x, y, size, width, color=FG, weight=600, spacing=1.14):
    face = font(size, weight)
    values = wrapped(text, face, width)
    for line in values:
        draw.text((x, y), line, font=face, fill=color)
        y += round(size * spacing)
    return y


@functools.lru_cache(maxsize=20)
def shot(name):
    return Image.open(WORK / name).convert("RGB")


def brand(canvas, x, y, size=56):
    logo = Image.open(ROOT.parent.parent / "brand/sip-mark-dark.webp").convert("RGBA")
    logo.thumbnail((size + 12, size + 12), Image.Resampling.LANCZOS)
    canvas.paste(logo, (x, y - 1), logo)
    ImageDraw.Draw(canvas).text((x + size + 25, y + 2), "Sip & Savor", font=font(size, 600), fill=FG)


@functools.lru_cache(maxsize=2)
def pair(outro=False):
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    if not outro:
        brand(canvas, 122, 87, 80)
        draw.text((225, 205), "Find your next favorite.", font=font(42, 400), fill=MUTED)
        window(canvas, shot("home-desktop.png"), 120, 310, 1190)
        phone(canvas, shot("cocktail-phone.png"), 1372, 115, 800)
        draw.text((1390, 945), "DESKTOP + MOBILE WEB", font=font(18, 600), fill=ACCENT)
    else:
        brand(canvas, 122, 95, 42)
        lines(draw, "Find your\nnext favorite.".replace("\n", " "), 124, 220, 76, 635, weight=600)
        draw.rounded_rectangle((125, 470, 495, 558), 44, fill=ACCENT)
        draw.text((182, 487), "Live site", font=font(40, 600), fill=BG)
        draw.line((424, 519, 448, 495), fill=BG, width=3)
        draw.line((432, 495, 448, 495, 448, 511), fill=BG, width=3)
        lines(draw, "Select the project button to open the website.", 126, 590, 28, 535, color=MUTED, weight=400)
        draw.text((126, 864), "Music: Bossa Antigua — Kevin MacLeod", font=font(18), fill=MUTED)
        draw.text((126, 893), "incompetech.com · CC BY 4.0", font=font(18), fill=MUTED)
        draw.text((126, 922), "creativecommons.org/licenses/by/4.0/", font=font(18), fill=MUTED)
        window(canvas, shot("browse-desktop.png"), 760, 323, 1035)
        phone(canvas, shot("saved-phone.png"), 1375, 115, 790)
    return canvas


class Footage:
    def __init__(self, shot_info):
        self.source = WORK / ("desktop.webm" if shot_info["source"] == "desktop" else "phone.webm")
        self.size = (1440, 780) if shot_info["source"] == "desktop" else (390, 780)
        self.cuts = shot_info["cuts"]
        self.clip = -1
        self.index = -1
        self.proc = None
        self.last = None

    def close(self):
        if self.proc:
            self.proc.stdout.close()
            self.proc.terminate()
            self.proc.wait()
            self.proc = None

    def at(self, seconds):
        residual = seconds
        target_clip = len(self.cuts) - 1
        for i, (begin, end) in enumerate(self.cuts):
            if residual < end - begin:
                target_clip = i
                break
            residual -= end - begin
        else:
            if self.last is not None:
                return self.last
            residual = max(0, self.cuts[-1][1] - self.cuts[-1][0] - 1 / FPS)
        if target_clip != self.clip:
            self.close()
            begin, end = self.cuts[target_clip]
            self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-threads", "1", "-ss", str(begin), "-i", str(self.source), "-t", str(end - begin), "-vf", "fps=30", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            self.index = -1
            self.clip = target_clip
        target = round(residual * FPS)
        width, height = self.size
        while self.index < target:
            data = self.proc.stdout.read(width * height * 3)
            if len(data) < width * height * 3:
                break
            self.last = Image.frombytes("RGB", self.size, data)
            self.index += 1
        if self.last is None:
            raise RuntimeError("No source frame could be read")
        return self.last


def phrases(scene):
    # Captions follow the narration's phrases; no new claims or extra tech copy.
    groups = []
    for clause in re.findall(r"[^,.!?]+[,.!?]?", scene["narration"]):
        clause = clause.strip()
        groups.extend(wrapped(clause, font(32), 1410))
    weights = [len(group) + 7 for group in groups]
    cursor = scene["voice_start"]
    result = []
    for group, weight in zip(groups, weights):
        duration = scene["voice_duration"] * weight / sum(weights)
        result.append((cursor, cursor + duration, group))
        cursor += duration
    return result


def caption(canvas, scene, seconds):
    draw = ImageDraw.Draw(canvas)
    for start, end, text in phrases(scene):
        if start <= seconds < end:
            width = round(font(32).getlength(text))
            left = (W - width) // 2 - 23
            draw.rounded_rectangle((left, 999, W - left, 1065), 12, fill=(15, 23, 41), outline=LINE, width=1)
            draw.text((W / 2, 1010), text, font=font(32), fill=FG, anchor="mt")
            break


def compose(scene, frame, seconds):
    kind = scene["layout"]
    if kind in ("pair", "outro"):
        canvas = pair(kind == "outro").copy()
    elif kind == "desktop":
        canvas = Image.new("RGB", (W, H), BG)
        window(canvas, frame, 192, 108, 1536)
        draw = ImageDraw.Draw(canvas)
        draw.text((192, 43), scene["title"], font=font(32, 600), fill=FG)
        draw.text((1728, 49), "SIP & SAVOR", font=font(20, 600), fill=ACCENT, anchor="rt")
    else:
        canvas = Image.new("RGB", (W, H), BG)
        brand(canvas, 165, 140, 40)
        draw = ImageDraw.Draw(canvas)
        draw.text((173, 259), "MOBILE WEB", font=font(22, 600), fill=ACCENT)
        finish = lines(draw, scene["title"], 168, 309, 68, 780, weight=600)
        draw.line((172, finish + 36, 244, finish + 36), fill=ACCENT, width=4)
        copy = "Browse. Read. Save." if scene["id"] == "mobile" else "Your favorites, in one place."
        lines(draw, copy, 170, finish + 75, 32, 700, color=MUTED, weight=400)
        phone(canvas, frame, 1130, 85, 858)
    if kind not in ("pair", "outro"):
        draw = ImageDraw.Draw(canvas)
        count = next(i for i, value in enumerate(SCENES, 1) if value["id"] == scene["id"])
        draw.text((W - 80, 45), str(count).zfill(2) + " / 08", font=font(18, 600), fill=MUTED, anchor="rt")
    caption(canvas, scene, seconds)
    return canvas


def srt_time(value):
    value = round(value * 1000)
    hours, value = divmod(value, 3600000)
    minutes, value = divmod(value, 60000)
    seconds, millis = divmod(value, 1000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"


def captions_file():
    entries = []
    for scene in SCENES:
        for begin, end, text in phrases(scene):
            entries.append(f"{len(entries) + 1}\n{srt_time(scene['start'] + begin)} --> {srt_time(scene['start'] + end)}\n{text}\n")
    (ROOT / "captions.srt").write_text("\n".join(entries))


def cover():
    poster = pair(False)
    poster.save(PREVIEWS / "sip-and-savor-demo-poster.jpg", quality=91)
    canvas = Image.new("RGB", (1500, 1000), BG)
    brand(canvas, 76, 65, 68)
    draw = ImageDraw.Draw(canvas)
    draw.text((165, 171), "Meals, cocktails, and your next favorite.", font=font(32), fill=MUTED)
    draw.rounded_rectangle((80, 245, 385, 294), 24, outline=LINE, width=2)
    draw.text((105, 255), "DESKTOP + MOBILE", font=font(21, 600), fill=ACCENT)
    window(canvas, shot("home-desktop.png"), 75, 341, 1120)
    phone(canvas, shot("cocktail-phone.png"), 1130, 266, 652)
    canvas.save(PREVIEWS / "sip-and-savor.jpg", quality=91)


def review():
    tiles = []
    for scene in SCENES:
        footage = Footage(CAPTURE["shots"][scene["id"]]) if scene["layout"] in ("desktop", "phone") else None
        try:
            at = min(2.4, scene["duration"] / 2)
            image = compose(scene, footage.at(at) if footage else None, at)
            image.thumbnail((640, 360), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (640, 404), BG)
            tile.paste(image, (0, 35))
            ImageDraw.Draw(tile).text((12, 8), scene["id"] + " / " + str(round(scene["duration"], 1)) + "s", font=font(19, 600), fill=FG)
            tiles.append(tile)
        finally:
            if footage:
                footage.close()
    sheet = Image.new("RGB", (1280, 404 * 4), BG)
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % 2) * 640, (i // 2) * 404))
    sheet.save(ROOT / "SipAndSavor-review.jpg", quality=91)


def render():
    captions_file()
    cover()
    review()
    command = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", "30", "-i", "-", "-an", "-c:v", "libx264", "-threads", "3", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(WORK / "picture.mp4")]
    with (WORK / "render-ffmpeg.log").open("w") as log:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=log)
        previous = None
        for scene in SCENES:
            footage = Footage(CAPTURE["shots"][scene["id"]]) if scene["layout"] in ("desktop", "phone") else None
            total = round(scene["duration"] * FPS)
            print("Rendering", scene["id"], total, "frames", flush=True)
            try:
                for i in range(total):
                    t = i / FPS
                    frame = compose(scene, footage.at(t) if footage else None, t)
                    if previous is not None and i < 9:
                        frame = Image.blend(previous, frame, ease((i + 1) / 9))
                    if scene["id"] == "intro" and i < 10:
                        frame = Image.blend(Image.new("RGB", (W, H), BG), frame, ease((i + 1) / 10))
                    if scene["id"] == "outro" and i >= total - 12:
                        frame = Image.blend(frame, Image.new("RGB", (W, H), BG), ease((i - total + 13) / 12))
                    process.stdin.write(frame.tobytes())
                previous = frame
            finally:
                if footage:
                    footage.close()
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("FFmpeg picture encode failed")
    print("Picture complete.", flush=True)


if __name__ == "__main__":
    if "--review" in sys.argv:
        cover()
        review()
    else:
        render()
