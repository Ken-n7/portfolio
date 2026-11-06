"""Mux picture and mastered audio into the portfolio video, and pull the poster frame.

    python3 export.py
-> TagTune-demo-1080p.mp4 (local master, ignored), ../../previews/tagtune-demo.mp4, ../../previews/tagtune-demo-poster.jpg
"""
import sys
from pathlib import Path

if "--audio-only" in sys.argv:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from music_audio import export_audio_only
    export_audio_only(Path(__file__).resolve().parent)
    raise SystemExit(0)

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
PREVIEWS = ROOT.parent.parent / "previews"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


master = ROOT / "TagTune-demo-1080p.mp4"
ffmpeg("-i", str(WORK / "picture.mp4"), "-i", str(WORK / "audio-master.wav"), "-map", "0:v", "-map", "1:a",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(master))
web = PREVIEWS / "tagtune-demo.mp4"
ffmpeg("-i", str(master), "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
       "-c:a", "copy", "-movflags", "+faststart", str(web))
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json",
                                  str(web)], capture_output=True, text=True, check=True).stdout)["format"]
print(f"{web.name}: {float(info['duration']):.1f}s, {int(info['size']) / 2**20:.1f} MiB")
