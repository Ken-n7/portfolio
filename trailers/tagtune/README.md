# TagTune demo

58.1-second narrated walkthrough. 1920 × 1080, 30 fps, H.264 MP4, 48 kHz
stereo AAC, about 2.9 MiB. Captions are burned into the picture.

- Video: [`../../previews/tagtune-demo.mp4`](../../previews/tagtune-demo.mp4)
- Poster: [`../../previews/tagtune-demo-poster.jpg`](../../previews/tagtune-demo-poster.jpg)
- Card cover: [`../../previews/tagtune.jpg`](../../previews/tagtune.jpg)
- Eight-frame review: [`TagTune-review.jpg`](TagTune-review.jpg)
- Script: [`scenes.json`](scenes.json); timings: [`timeline.json`](timeline.json); loudness: [`audio-report.json`](audio-report.json)

## What's real

Every app shot is one continuous recording of the actual app
([Ken-n7/tagtune](https://github.com/Ken-n7/tagtune), `main` at `e5052c8`)
doing a real download of *Imagine Dragons – Believer (Official Music Video)*.
It found the official audio on YouTube Music and tagged it from MusicBrainz,
exactly as the log line on screen says. The download took about 70 seconds on
a slow connection, so the film keeps three real-time moments of it (searching,
downloading, finding tags) joined by hard cuts. Nothing is sped up or mocked.

The demo ran with `HOME` pointed at `work/home`, a copy of a small real
library, so it never touched the real `~/Music` or settings. The only change
to what the app drew is the folder path, shown as `~/Music/tagtune` instead of
the long scratch path.

## Tools

All open source, all local:

- **FFmpeg** `x11grab -window_id` records the TagTune window (an XWayland
  window, so recording the screen area comes out black on GNOME Wayland).
- **[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)** via
  **kokoro-onnx** reads the narration with the stock `bm_george` voice
  (British English) at speed 0.97, picked by ear from twelve samples, using the
  model files already downloaded for the EFP film in `../efp/work`. Synthetic,
  no voice cloning, no time stretching.
- **Pillow** composes the picture: the recorded window on a plain backdrop in
  the app's own colors, typed `$ tagtune` title cards and captions in DejaVu
  Sans Mono, which is the font the app itself renders in.
- **NumPy/SciPy** make a quiet original Am7–Fmaj7–Cmaj7–G6 chord bed, ducked
  under the voice. No third-party music, and no song audio from the download.
- **FFmpeg loudnorm**, two passes: −16 LUFS integrated, −1.5 dBTP ceiling.

## Rebuild

From this folder, with `work/home` seeded with a few tagged MP3s:

1. `HOME=$PWD/work/home ~/Workspace/tagtune/.venv/bin/python drive.py` runs
   the app, does the download, uses the filter, switches themes, and records
   `work/take.mp4` plus `work/take.json` (when each step happened).
2. Check the cut points in `scenes.json` against the new take. Each scene's
   `cuts` are `[start, end]` seconds of the take.
3. `../efp/work/venv/bin/python narrate.py`, then `python3 master_audio.py`,
   `python3 render.py`, `python3 export.py` and `python3 cover.py`.
   `python3 render.py --review` writes the contact sheet.

Delete `work/*-voice.wav` after changing any narration.
