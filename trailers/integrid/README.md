# INTEGRID trailer

45.2-second, 1920×1080, 30 fps landscape trailer presenting the real portrait
game in animated phone frames. No narration. Music, native game sounds and
on-screen titles cover Relax, clues, completion, Expert and classroom Battle.

- Portfolio video: `../../previews/integrid-trailer.mp4`
- Poster: `../../previews/integrid-trailer-poster.jpg`
- Local master: `INTEGRID-trailer-1080p.mp4` (ignored)
- Six-frame review: `INTEGRID-trailer-preview.jpg`
- Source revision, timings, tools and credits: `production.json`

Music by Eric Matyas — www.soundimage.org. The existing app track, **Puzzle
Game 3 (Looping)**, is excerpted, faded and ducked around the completion sound.
The required credit appears inside the final video. Source:
https://soundimage.org/puzzle-music/. License:
https://soundimage.org/sample-page/.

Other sounds use the app's rendered feedback bank (GeneralUser GS instruments
by S. Christian Collins) and the supplied “Level win” recording by
Tuudurt / freesound_community, under the Pixabay Content License. See
`production.json` and the app's `public/sounds/README.md` for provenance.

## Rebuilding locally

The ignored `work/` directory contains an archive of game commit
`bfb9d2b2ffafd8d2d0c945cf65f263da217aad7e`, its dependency link, local capture
configuration, recordings and intermediate plates. No environment files or
cloud credentials are included. The original app repository is unchanged.

1. Serve `work/game` with `node node_modules/vite/bin/vite.js --config
   vite.config.capture.mjs --configLoader runner` on localhost port 4191.
   This isolated config disables Supabase values, skips PWA integration and
   uses a separate Vite cache. The isolated entry omits dev StrictMode to match
   production's effect lifecycle.
2. Run `node trailers/integrid/capture.cjs` from the portfolio root. It drives
   the actual controls, solves native CSV puzzles and relays native local
   Battle messages across isolated browser contexts. The existing `?unlock`
   preview switch opens all levels. No live records are created.
3. Run `python3 trailers/integrid/build_art.py`, then
   `node trailers/integrid/render_art.cjs`.
4. Remove only generated `work/render/scene-*.mp4` when changing footage or
   compositions, then run `python3 trailers/integrid/render.py`.
5. Run `python3 trailers/integrid/mix_audio.py`, then
   `python3 trailers/integrid/export.py`.

Requires FFmpeg/ffprobe, Python with NumPy/SciPy/Pillow, Playwright/Chromium and
the game's Nunito font/art. Browser paths in the two capture scripts point to
the installed local tools; adjust them on another machine. A workspace-local
`.preview-tmp` directory avoids the host `/tmp` quota during capture.

Capture aids add temporary touch rings and log native sound calls. The source
gameplay keeps its original speed. Any extra seconds hold the final frame;
footage never drifts into a later navigation step. Captures and audio cue
audits remain under ignored `work/`.
