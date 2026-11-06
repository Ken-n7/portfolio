"""Record Discover on a connected Android phone using scrcpy.

Open reLiveTV's Discover tab and scroll to the top before running this script.
The app must have network access so channel artwork can finish loading.
"""
import subprocess
import time
from pathlib import Path

WORK = Path(__file__).resolve().parent / "work"
WORK.mkdir(exist_ok=True)


def adb(*args):
    return subprocess.check_output(["adb", "shell", *args], text=True).strip()


touches = adb("settings", "get", "system", "show_touches")
rec = None
try:
    adb("settings", "put", "system", "show_touches", "0")
    rec = subprocess.Popen([
        "scrcpy", "--no-playback", "--no-audio", "--max-fps=30",
        "--video-bit-rate=12M", "--stay-awake", "--time-limit=18",
        f"--record={WORK / 'phone-vfr.mp4'}",
    ])
    time.sleep(5)
    adb("input", "tap", "165", "430")
    time.sleep(4)
    adb("input", "keyevent", "KEYCODE_BACK")
    time.sleep(4)
    adb("input", "tap", "810", "2080")
    if rec.wait(timeout=30):
        raise RuntimeError("Phone recording failed")
finally:
    if rec is not None and rec.poll() is None:
        rec.terminate()
        rec.wait()
    if touches == "null":
        adb("settings", "delete", "system", "show_touches")
    else:
        adb("settings", "put", "system", "show_touches", touches)

# Android's encoder emits no new frames while the UI is still. Preserve those
# pauses at 30 fps, including the final hold, for accurate editorial timecodes.
subprocess.run([
    "ffmpeg", "-v", "error", "-y", "-i", str(WORK / "phone-vfr.mp4"),
    "-vf", "fps=30,tpad=stop_mode=clone:stop_duration=8", "-t", "15",
    "-c:v", "libx264", "-preset", "fast", "-crf", "16",
    "-pix_fmt", "yuv420p", str(WORK / "phone.mp4"),
], check=True)
