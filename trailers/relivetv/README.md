# reLiveTV demo

70.2-second narrated walkthrough. 1920 × 1080, 30 fps, H.264 MP4,
48 kHz stereo AAC. Burned-in captions, Fable narration, and an original
licensed instrumental recording.

- Video: [`../../previews/relivetv-demo.mp4`](../../previews/relivetv-demo.mp4)
- Poster: [`../../previews/relivetv-demo-poster.jpg`](../../previews/relivetv-demo-poster.jpg)
- Card cover: [`../../previews/relivetv.jpg`](../../previews/relivetv.jpg)
- Eight-frame review: [`reLiveTV-review.jpg`](reLiveTV-review.jpg)
- Script and source cuts: [`scenes.json`](scenes.json)
- Final timing: [`timeline.json`](timeline.json)
- Audio measurements: [`audio-report.json`](audio-report.json)

## Edit

The existing dark background, desktop window framing, phone framing, title
cards, typography, and caption band are retained. Shorter feature narration
and separate news, markets, and sports beats bring the edit down from 98.3
seconds. Playback stays at its original speed. Buffering waits and test click
indicators are excluded through source selection.

The narration describes the viewing experience: Home, Discover, search,
schedules, channel variety, the mini player, filters, saved favourites, and
Android availability. The closing disclaimer covers changing availability,
offline or region-restricted channels, inaccurate schedules, and the fact
that reLiveTV hosts no streams. It is both spoken and displayed.

## Footage

Desktop scenes use the existing recording of the actual Linux app
([Ken-n7/reLiveTV](https://github.com/Ken-n7/reLiveTV), `920e75f`).
Only broadcaster-provided free channels play: BBC News, DW, Bloomberg TV,
and Red Bull TV. Other channels appear only as saved cards.

The phone scene is a new recording of the actual Android app running on a
Realme RMX1851, captured over USB with scrcpy. Channel artwork is loaded,
the Android country filter opens and closes naturally, and Android touch indicators are disabled during
capture. The crop removes system notifications and the system navigation bar;
the app's real header, content, and bottom navigation remain. The phone scene
uses moving footage rather than the previous resized desktop still.

## Audio

Kokoro v1.0 **bm_fable**, en-gb, speed 0.97: the Fable voice from the existing
voice sample set. Narration is regenerated with voice-and-script keyed caches
so earlier George recordings cannot be reused accidentally. Speech stays at
its generated speed.

The background recording is **“Chill Wave” by Kevin MacLeod**, published in
2016: a relaxed 100 BPM groove with synths, bass, drums and guitar. It replaces
the generated instrumental. The music is excerpted, faded and ducked under
Fable. Two-pass FFmpeg loudness mastering targets −16 LUFS and −1.5 dBTP.

## Rebuild

Existing desktop source: `work/take.mp4` and `work/take.json`.
For a new phone take, open Discover on the connected Android phone, scroll to
the top, and let the artwork load. Then run `python3 record_phone.py`.
This restores the original touch-indicator setting after capture and
normalizes the variable-frame-rate recording to 30 fps, preserving still holds.

```sh
../efp/work/venv/bin/python narrate.py
python3 master_audio.py
python3 render.py
python3 export.py
python3 render.py --review
```

`python3 cover.py` rebuilds the existing sports poster and card cover.
Working recordings, generated audio, and the local master stay in ignored paths.

## Music-only update

The current portfolio MP4 was updated by copying its existing H.264 video
stream, preserving every frame, clip boundary, title, caption and transition.
The existing narration WAV is reused without regeneration or time stretching.
EFP's embedded subtitle stream is also copied unchanged. No visual render,
new speech synthesis or poster change is needed for this audio-only update.

- Track: [Chill Wave](https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1600048) — Kevin MacLeod (incompetech.com).
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- Full attribution: [`../../previews/music-credits.txt`](../../previews/music-credits.txt),
  linked from the project's details and embedded in the MP4's metadata.
- Original publication: 2016-08-20. No generated music is used.
- Exact download URL, source SHA-256 and mix settings: [`music.json`](music.json).
- Preservation checks: ignored `work/music-verification.json` records the
  unchanged video stream hash and original narration hash.

To rebuild just the music mix and replace the audio:

```sh
python3 master_audio.py
python3 export.py --audio-only
```

The downloaded MP3 is cached in ignored `work/music-source.mp3`; if missing,
mastering downloads it from the official URL and checks its SHA-256. Keep
`work/before-online-music.mp4` as the original picture source for this update.
The existing full-picture rebuild instructions above remain available for
intentional future visual changes.
