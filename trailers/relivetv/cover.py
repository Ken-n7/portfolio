"""Card cover (3:2) and video poster (16:9) from one clean frame: Red Bull TV playing beside its schedule.

    python3 cover.py  -> ../../previews/relivetv.jpg, ../../previews/relivetv-demo-poster.jpg
"""
from PIL import Image

from render import BG, CROP, PREVIEWS, WORK, Take, desktop

FRAME = 225.0  # take time, well after Red Bull TV finished buffering

frame = Take(WORK / "take.mp4", CROP).at(FRAME)
desktop(frame).save(PREVIEWS / "relivetv-demo-poster.jpg", quality=90)

cw, ch, margin = 1500, 1000, 36
scale = (cw - 2 * margin) / frame.width
shot = frame.resize((round(frame.width * scale), round(frame.height * scale)), Image.LANCZOS)
cover = Image.new("RGB", (cw, ch), BG)
cover.paste(shot, (margin, margin))
cover.save(PREVIEWS / "relivetv.jpg", quality=88)
print("cover", cover.size)
