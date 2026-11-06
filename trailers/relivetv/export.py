"""Mux picture and mastered audio into the portfolio video, and pull the poster frame.

    python3 export.py
-> reLiveTV-demo-1080p.mp4 (local master, ignored), ../../previews/relivetv-demo.mp4
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


timeline = json.loads((ROOT / "timeline.json").read_text())
expected_frames = sum(round(scene["duration"] * 30) for scene in timeline)
picture = json.loads(subprocess.run([
    "ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
    "stream=nb_frames,r_frame_rate,width,height", "-of", "json", str(WORK / "picture.mp4"),
], capture_output=True, text=True, check=True).stdout)["streams"][0]
assert picture["r_frame_rate"] == "30/1", "Picture must be 30 fps to match the narration timeline"
assert int(picture["nb_frames"]) == expected_frames, "Picture length must match every scene in the timeline"
assert (picture["width"], picture["height"]) == (1920, 1080)

master = ROOT / "reLiveTV-demo-1080p.mp4"
ffmpeg("-i", str(WORK / "picture.mp4"), "-i", str(WORK / "audio-master.wav"), "-map", "0:v", "-map", "1:a",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(master))
web = PREVIEWS / "relivetv-demo.mp4"
ffmpeg("-i", str(master), "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "copy", "-movflags", "+faststart", str(web))
info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json",
                                  str(web)], capture_output=True, text=True, check=True).stdout)["format"]
assert abs(float(info["duration"]) - expected_frames / 30) < .05, "Export truncated the narration timeline"
print(f"{web.name}: {float(info['duration']):.1f}s, {int(info['size']) / 2**20:.1f} MiB")
