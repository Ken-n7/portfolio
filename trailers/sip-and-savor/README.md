# Sip & Savor demo

A 56.47-second narrated walkthrough of the updated web app. Desktop and mobile footage comes from the actual deployed website at https://sip-and-savor.vercel.app, app commit ccc882e.

## Deliverables

- Portfolio video: [sip-and-savor-demo.mp4](../../previews/sip-and-savor-demo.mp4)
- Card cover: [sip-and-savor.jpg](../../previews/sip-and-savor.jpg), 1500 × 1000
- Video poster: [sip-and-savor-demo-poster.jpg](../../previews/sip-and-savor-demo-poster.jpg), 1920 × 1080
- [Eight-scene review](SipAndSavor-review.jpg)
- [Narration and timing](timeline.json), [capture provenance](capture.json), [audio mastering](audio-report.json), [export properties](export-report.json)
- [English captions](captions.srt), burned into the picture and included as a subtitle stream

## Presentation

The film shows combined name search, category/cuisine browsing, meal ingredients and instructions, cocktail details, the mobile web layout, and saved-recipe filtering. The closing card and narration direct viewers to the existing **Live site** project button.

All app shots show the real website and real recipe-provider responses. Desktop recording size is 1440 × 780; mobile browser recording size is 390 × 780. Loading waits are cut out, and readable end frames are held where needed. Clips are not sped up. No cursor rings or touch markers are added.

The mobile view demonstrates the responsive website, not a native phone app. Its isolated browser profile carries the demonstration favorites; the film makes no cross-device synchronization claim.

The cover, poster, browser/phone frames, titles, captions, and transitions are composed with Pillow and FFmpeg using the app's Inter font, existing logo, and navy/blue palette. There are no generated photos, illustrations, stock app mockups, or generated video clips.

## Voice and music

- Narration reuses TagTune's stock **Kokoro af_heart** voice, en-us, speed 0.97, through the already installed kokoro-onnx engine. This is synthetic narration using the requested existing narrator; no voice cloning or time stretching.
- Music is **Bossa Antigua** by Kevin MacLeod, published 2017-11-17: a relaxed 70 BPM jazz recording with guitar, bass, and drums. It differs from the TagTune, EFP, and reLiveTV tracks.
- [Official music source](https://incompetech.com/music/royalty-free/index.html?Search=Search&isrc=USUAN1700069); [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).
- Music is excerpted, faded, and ducked beneath speech. The audible bed uses the portfolio's increased music-gain convention. The mix is mastered to about −16 LUFS with a −1.5 dBTP target.
- Attribution appears on the closing card, in the MP4 metadata, and in [music-credits.txt](../../previews/music-credits.txt). No new credit button is added to the portfolio.
- The source download URL, hash, and mix settings are recorded in [music.json](music.json). No music was generated.

## Rebuild

Prerequisites: FFmpeg, Pillow, fontTools, NumPy and SciPy; the existing speech environment/model in ../efp/work; and the app's Playwright installation. A built app supplies its Inter font; the existing portfolio Inter wordmark font is the fallback.

From this directory:

1. Run **../efp/work/venv/bin/python narrate.py**.
2. Install Playwright's video-recorder binary in the ignored work folder if needed:
   **PLAYWRIGHT_BROWSERS_PATH=$PWD/work/browsers node /home/ken/Workspace/sip_and_savor/node_modules/playwright/cli.js install ffmpeg**.
3. Run **PLAYWRIGHT_BROWSERS_PATH=$PWD/work/browsers node capture.cjs**. SIP_DEMO_URL can select another verified app deployment.
4. Run **python3 master_audio.py**, **python3 render.py**, then **python3 export.py**.
5. **python3 render.py --review** rebuilds the cover, poster and review sheet without encoding the full video.

Working captures, downloaded music, fonts, voice caches, intermediate WAV/MP4 files, and the local master are ignored by Git. The S3 staging script only packages public site files and the brand/fonts/previews directories; it excludes this authoring folder.

## Verification

The export is 56.466667 seconds, 1694 frames, 1920 × 1080 at 30 fps, H.264 with 48 kHz stereo AAC and an English subtitle stream. The web file is 4.16 MiB. A full FFmpeg decode passes. Exported audio measures −16.15 LUFS integrated and −1.39 dBTP.

The local portfolio was checked at 1440 × 1000 and 390 × 844: correct cover/poster, playback, seeking to the closing website reminder, visible Live site link, pause on dialog close, no horizontal overflow, and no browser page errors.

The S3 staging check includes all three media assets within 44 public files. Raw recordings, narration/model files, downloaded source music, caches, and authoring scripts are excluded.
