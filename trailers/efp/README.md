# EFP Supply Chain presentation

102-second narrated project walkthrough. 1920 × 1080, 24 fps, H.264 MP4,
48 kHz stereo AAC, approximately 6.1 MiB. Replaces `ledger-demo.mp4` in the
portfolio. English captions are burned into the picture and also available
as an embedded subtitle track, a WebVTT file, and a plain-text transcript.

- Video: [`../../previews/efp-presentation.mp4`](../../previews/efp-presentation.mp4)
- Poster: [`../../previews/efp-presentation-poster.jpg`](../../previews/efp-presentation-poster.jpg)
- Eight-frame review: [`EFP-presentation-review.jpg`](EFP-presentation-review.jpg)
- Script: [`scenes.json`](scenes.json), [`transcript.txt`](transcript.txt)
- Timings and provenance: [`timeline.json`](timeline.json), [`production.json`](production.json)
- Checks: [`audio-report.json`](audio-report.json), [`player-verification.json`](player-verification.json)

The story follows the dashboard, production batches, stock movements,
reconciliation, consignment summaries, reporting, role permissions, and audit
history. The 15 delivered / 13 sold / 2 unresolved example is present in the
application's own sample data.

## Research and tools

The complete production uses open-source tools:

- **[Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)** supplies the
  synthetic narrator. Its model weights are Apache-2.0 licensed. The stock
  `af_heart` voice runs locally through
  **[kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)**, whose wrapper
  is MIT licensed. Full-precision v1.0 weights, speed 0.97, complete paragraphs
  for natural phrasing, no voice cloning, and no time stretching. Both downloaded
  model and voice files were checked against their official release SHA-256.
- **[Piper](https://github.com/OHF-Voice/piper1-gpl)** was researched as another
  local speech engine. Kokoro was selected for this production; Piper was not
  used and no comparison benchmark is claimed.
- **[Playwright / Chromium](https://playwright.dev/)** captures the real Django
  application with its own sample records. A separate SQLite capture database
  replaces MySQL locally. All browser requests are restricted to the local app;
  public CSS, chart, table, and icon dependencies are cached first. No production
  database or environment file is used.
- **[Pillow](https://pillow.readthedocs.io/en/stable/)** and FontTools render
  the custom compositions, chapter markers, page dissolves, captions, and poster.
  The surrounding text uses Liberation Sans (regular and bold), installed at
  `/usr/share/fonts/truetype/liberation/`. The application's window title bar
  retains Commissioner; its OFL notice remains in
  `../../fonts/commissioner-OFL.txt`.
- **[NumPy](https://numpy.org/)** and **[SciPy](https://scipy.org/)** create a
  quiet original chord bed and a smooth envelope that lowers it beneath speech.
  There is no third-party music recording.
- **[FFmpeg](https://ffmpeg.org/ffmpeg-filters.html#loudnorm)** encodes the film
  and performs two-pass loudness mastering: target −16 LUFS, true-peak ceiling
  −1.5 dBTP, 65 Hz high-pass filter, and 48 kHz output. The final AAC stream
  measures **−16.02 LUFS / −1.49 dBTP**, with 3.4 LU loudness range.

The visuals use actual application screenshots with editorial titles and
transitions. They are a narrated presentation, rather than a continuous
screen recording of one user session. Captions use phrase-level timing derived
from each synthesized paragraph's duration.

## Source and verification

App: [Ken-n7/consignment-ledger](https://github.com/Ken-n7/consignment-ledger),
revision `4d5c4f74e0d8c9005f7ebc1061cc0d271a80a9cf`.
Feature statements were checked against its templates, seed command, and user
guide. Names and records on screen are the app's demonstration fixtures.

Full video and audio decode completed without FFmpeg errors. Chromium checks
open the EFP project from the portfolio, load the replacement, seek into the
film, play with audio, and close the dialog, at desktop and mobile viewport
sizes. See the saved verification JSON for measured results. These checks
cover Chromium viewport emulation, not physical iOS or Android hardware.

## Rebuild

Local intermediate files, models, virtualenv, sample database, app copy,
screenshots, and uncompressed audio live under ignored `work/`. The local
master MP4 is also ignored; the browser-ready video is tracked in `previews/`.

1. Install Python 3.12 and the packages in `requirements-speech.txt` in
   `work/venv`. Install `requirements-render.txt` for the Python interpreter
   running the rendering scripts. Install FFmpeg and Playwright Chromium.
2. Place the indicated application revision in `work/app`, excluding `.git`
   and `.env`. Add `config/capture_settings.py` importing its normal settings
   and overriding the database with local SQLite, a local-only secret, and
   localhost-only hosts. Migrate and run its `seed_data` command against that
   capture settings module only.
3. Run `python3 download_model.py`. Download `voices-v1.0.bin` from the same
   [official release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1)
   into `work/`. Expected hashes are recorded in `production.json`.
4. Run `python3 vendor_assets.py`. Serve `work/app` on localhost port 4195
   using `config.capture_settings`. Run `node capture.cjs`. Set
   `PLAYWRIGHT_MODULE` and `CHROMIUM_PATH` to the local installation paths if
   they differ from this machine.
5. Run `work/venv/bin/python narrate.py`, `python3 master_audio.py`,
   `python3 render.py`, and `python3 export.py`, in that order. Run
   `python3 render.py --review` for the contact sheet. Paths are resolved from
   the scripts; these commands assume the `trailers/efp` directory.

Delete the affected `work/*-voice.wav` cache files when changing the script
or voice, then rerun narration, mastering, rendering, and export. Keep the
same script revision between picture and audio renders so timings stay aligned.
