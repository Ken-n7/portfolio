"""Card cover (3:2) and video poster (16:9) from one clean frame of the finished download, no captions.

    python3 cover.py  -> ../../previews/tagtune.jpg, ../../previews/tagtune-demo-poster.jpg
"""
from PIL import Image

from render import BG, PREVIEWS, Take, W, H, window

FINISHED = 80.0  # take time: "[ok] Imagine Dragons - Believer" logged, Believer · Evolve on top of the library

frame = Take().at(FINISHED)
window(frame).save(PREVIEWS / "tagtune-demo-poster.jpg", quality=90)

# The card shows the top of its image (object-position: top center), so the window sits near the top.
cw, ch, margin = 1500, 1000, 36
scale = (cw - 2 * margin) / frame.width
shot = frame.resize((round(frame.width * scale), round(frame.height * scale)), Image.LANCZOS)
cover = Image.new("RGB", (cw, ch), BG)
cover.paste(shot, (margin, margin))
cover.save(PREVIEWS / "tagtune.jpg", quality=88)
print("cover", cover.size, "window height", shot.height)
