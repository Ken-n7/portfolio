# reLiveTV demo

98.3-second narrated walkthrough. 1920 × 1080, 30 fps, H.264 MP4, 48 kHz
stereo AAC, about 7 MiB. Captions are burned into the picture.

- Video: [`../../previews/relivetv-demo.mp4`](../../previews/relivetv-demo.mp4)
- Poster: [`../../previews/relivetv-demo-poster.jpg`](../../previews/relivetv-demo-poster.jpg)
- Card cover: [`../../previews/relivetv.jpg`](../../previews/relivetv.jpg)
- Eight-frame review: [`reLiveTV-review.jpg`](reLiveTV-review.jpg)
- Script: [`scenes.json`](scenes.json); timings: [`timeline.json`](timeline.json); loudness: [`audio-report.json`](audio-report.json)

## What's real

One continuous recording of the actual Linux app
([Ken-n7/reLiveTV](https://github.com/Ken-n7/reLiveTV), `main` at `920e75f`),
driven by a Flutter integration test (`integration_test/demo_trailer_test.dart`
in that repo, kept out of its test suite) while FFmpeg records the window.

- **Playback** is real and limited to free channels their broadcasters stream
  themselves: BBC News, DW, Bloomberg TV and Red Bull TV. Each one was left to
  buffer for five seconds after it started before any of its footage is used,
  so no spinner or stutter makes the cut. On a slow connection streams took up
  to a minute to start; those waits are cut, not sped up.
- **Paid channels** (Cartoon Network, Disney XD, Animax and others) appear
  only as saved cards in My List, never playing. The list is Ken's own, copied
  into the demo's settings by `record.sh` from `my-list.json`.
- **The BBC News stretch** was picked for a calm business segment; the hold
  around it ran into other footage that was left out.
- **The phone shot** is the same app at phone size on the laptop (Flutter draws
  the same compact layout on Android), shown in a plain phone frame. The phone
  itself was offline, so a real screenshot would have shown empty logo boxes.
- **Disclaimers** (schedules may be inaccurate; channels may be offline or
  geo-blocked; no streams are hosted) are both on screen and spoken.

The app ran with `HOME` pointed at `work/home` (fresh settings, a copy of the
channel cache) so Ken's own settings were never touched. Channel logos were
loaded in an unrecorded warm-up pass first.

## Tools

All open source, all local:

- **Flutter integration_test** drives the real UI; **python-xlib** resizes the
  window to 1600 × 900 (`xresize.py`); **FFmpeg** `x11grab -window_id` records
  it (run with `GDK_BACKEND=x11`, since Wayland windows can't be grabbed).
- **Kokoro-82M** via **kokoro-onnx**, stock `bm_george` voice, en-gb, speed
  0.97. Synthetic, no voice cloning. `say` lines in `scenes.json` spell out
  "re-live TV" and "I P T V org" for the voice; captions keep the real names.
- **Pillow** composes the picture in Ubuntu Sans, the font the app renders in on
  Linux. **NumPy/SciPy** make the quiet original chord bed. **FFmpeg loudnorm**
  masters to −16 LUFS / −1.5 dBTP.

## Rebuild

1. `./record.sh` (needs a venv with `python-xlib`; set `XPY` to its python)
   records `work/take.mp4`, `work/take.json` and `work/phone-discover.png`.
2. Re-pick the cuts in `scenes.json` from the `clean:` marks in `take.json`.
3. `../efp/work/venv/bin/python narrate.py`, `python3 master_audio.py`,
   `python3 render.py`, `python3 export.py`, `python3 cover.py`.
