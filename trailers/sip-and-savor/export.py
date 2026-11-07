"""Mux the edited picture, mastered narration/music and English captions."""
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
PREVIEWS = ROOT.parent.parent / "previews"

def run(*args):
    return subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "warning", "-y", *map(str, args)], check=True)

music = json.loads((ROOT / "music.json").read_text())
master = ROOT / "SipAndSavor-demo-1080p.mp4"
run("-i", WORK / "picture.mp4", "-i", WORK / "audio-master.wav", "-i", ROOT / "captions.srt",
    "-map", "0:v:0", "-map", "1:a:0", "-map", "2:s:0", "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-c:s", "mov_text",
    "-metadata:s:s:0", "language=eng", "-metadata:s:s:0", "title=English",
    "-disposition:s:0", "0",
    "-metadata", "title=Sip & Savor — Meals, cocktails, and your next favorite",
    "-metadata", "comment=" + music["attribution"],
    "-metadata", "copyright=Music: Kevin MacLeod, CC BY 4.0; see comment.",
    "-movflags", "+faststart", master)
web = PREVIEWS / "sip-and-savor-demo.mp4"
run("-i", master, "-map", "0", "-c:v", "libx264", "-threads", "3", "-preset", "slow", "-crf", "22",
    "-pix_fmt", "yuv420p", "-c:a", "copy", "-c:s", "copy", "-movflags", "+faststart", web)
details = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(web)]))
video = next(stream for stream in details["streams"] if stream["codec_type"] == "video")
audio = next(stream for stream in details["streams"] if stream["codec_type"] == "audio")
duration = sum(scene["duration"] for scene in json.loads((ROOT / "timeline.json").read_text()))
assert (video["width"], video["height"], video["r_frame_rate"]) == (1920, 1080, "30/1")
assert abs(float(video["duration"]) - duration) < .05
assert abs(float(audio["duration"]) - duration) < .1
assert audio["sample_rate"] == "48000" and audio["channels"] == 2
assert "Bossa Antigua" in details["format"]["tags"]["comment"]
report = {
    "duration_seconds": float(video["duration"]), "width": 1920, "height": 1080, "fps": 30,
    "video_codec": video["codec_name"], "audio_codec": audio["codec_name"],
    "audio_sample_rate": 48000, "audio_channels": 2,
    "size_mib": round(int(details["format"]["size"]) / 2**20, 2),
    "english_subtitle_track": any(stream["codec_type"] == "subtitle" for stream in details["streams"]),
    "burned_captions": True, "music_attribution_embedded": True,
}
(ROOT / "export-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report), flush=True)
