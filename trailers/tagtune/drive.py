"""Run the real TagTune app, act out the demo and record its window.

Run with TagTune's own interpreter, HOME pointed at work/home so the demo has its own library and settings:
    HOME=$PWD/work/home ~/Workspace/tagtune/.venv/bin/python drive.py
Writes work/take.mp4 (the window, 30 fps, no mouse) and work/take.json (when each step happened).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
sys.path.insert(0, str(Path("/home/ken/Workspace/tagtune")))

from tagtune import gui  # noqa: E402

URL = "https://www.youtube.com/watch?v=7wtfhZwyrcc"  # Imagine Dragons - Believer (Official Music Video)
SHOWN_HOME = "~/Music/tagtune"
app = None
marks = []
t0 = None
rec = None


def mark(name):
    marks.append({"t": round(time.monotonic() - t0, 3), "step": name})
    print(f"{marks[-1]['t']:7.2f}  {name}", flush=True)


original_init = gui.App.__init__


def init(self, root):
    global app
    original_init(self, root)
    app = self
    # The demo library lives under work/home; show it as the path a normal user would see.
    real = str(self.out_dir)
    for label in (self.stats, self.status):
        configure = label.configure

        def tidy(*a, _configure=configure, **k):
            if isinstance(k.get("text"), str):
                k["text"] = k["text"].replace(real, SHOWN_HOME)
            return _configure(*a, **k)
        label.configure = label.config = tidy
    self.check_folder()
    self.url.set("")
    root.geometry("1440x810+60+60")
    root.after(2500, start_recording)


gui.App.__init__ = init


def start_recording():
    global rec, t0
    root = app.root
    root.update()
    wid = next(line.split()[3] for line in subprocess.run(["xwininfo", "-name", "TagTune"], capture_output=True,
                                                         text=True).stdout.splitlines() if "Window id" in line)
    rec = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "x11grab", "-draw_mouse", "0",
                            "-framerate", "30", "-window_id", wid, "-i", ":0", "-c:v", "libx264", "-preset", "veryfast",
                            "-crf", "10", "-pix_fmt", "yuv444p", str(WORK / "take.mp4")], stdin=subprocess.PIPE)
    t0 = time.monotonic()
    mark("record")
    steps(root)


def steps(root):
    plan = []
    at = lambda s, fn: plan.append((s, fn))  # noqa: E731

    def paste():
        app.url.set(URL)
        app.entry.icursor("end")
        app.entry.focus_set()
        mark("paste")

    def press():
        app.go.state(["pressed", "active"])
        mark("press")

    def download():
        app.go.state(["!pressed", "!active"])
        app.start()
        mark("download")
        wait_done()

    at(1.8, paste)
    at(3.4, press)
    at(3.6, download)
    for s, fn in plan:
        root.after(int(s * 1000), fn)


def wait_done():
    if app.running:
        app.root.after(100, wait_done)
        return
    mark("done")
    after_download()


def after_download():
    root = app.root
    t = 3000
    word = "dragons"
    root.after(t, lambda: (app.tree.focus_set(), mark("filter")))
    for i in range(1, len(word) + 1):
        root.after(t + 300 + i * 110, lambda i=i: app.query.set(word[:i]))
    t += 300 + len(word) * 110 + 3200
    root.after(t, select_row)
    t += 2600
    root.after(t, lambda: (app.query.set(""), app.tree.selection_set(()), mark("clear")))
    t += 1800
    root.after(t, lambda: (app.toggle_theme(), mark("light")))
    t += 3000
    root.after(t, lambda: (app.toggle_theme(), mark("dark")))
    t += 2200
    root.after(t, finish)


def select_row():
    rows = app.tree.get_children()
    if rows:
        app.tree.selection_set(rows[0])
    mark("select")


def finish():
    mark("end")
    rec.communicate(b"q", timeout=30)
    (WORK / "take.json").write_text(json.dumps(marks, indent=2) + "\n")
    app.root.destroy()


if __name__ == "__main__":
    from tagtune.__main__ import main
    main()
