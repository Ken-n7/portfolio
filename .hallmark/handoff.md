# Hallmark portfolio redesign

Full redesign of the existing static portfolio, on `design/hallmark-portfolio`.

The original charcoal/sage identity and Commissioner face remain. The opening
now leads with a clickable Lakbayin gameplay frame, followed by an asymmetric
project grid, plain captions, open technology lists, and direct contact details.
Each project appears once. Consignment Ledger has a full-width feature row,
and short summaries explain the projects before their dialogs open.
Commissioner headings use weight 600 for a softer hierarchy. No images,
metrics, testimonials, customer logos, or project claims were invented.

## Verification

- Hallmark full-page sweep: **0 Floor failures, 0 open Reflex findings, 0 warnings**.
- One documented exception: existing media-sized project buttons remain fully
  clickable rather than shrinking their targets to text-button height (39b).
- Existing links **18/18**, script hooks **28/28**, headings **7/7**, and figures **2/2** retained against the first redesign.
- Original headline and punctuation edits, the updated project action, and new
  summaries are listed in `copy-changes.json`.
- All six project descriptions, technology lists, posters, media URLs, and
  project IDs preserved. Browser sources are unchanged. The Lakbayin and Swarm
  thumbnails now use frames from their existing videos; original assets remain
  in the repository. Provenance is recorded in `refinement.json`.
- Six dialogs open, close with Escape, return their content, and stop playback,
  on desktop and mobile. The EFP presentation plays with audio.
- Light and dark contrast pairs pass: body text, muted text on both surfaces,
  primary-button text, and focus rings. Theme switching works.
- With JavaScript disabled all six descriptions and their project links remain
  available. No runtime script errors were observed.
- The project-image flight now uses transforms rather than animated dimensions.
- CSP hash for the inline theme initializer verified against its actual bytes.

The first iteration fixed the mobile Stack link and envelope icon. This
refinement also scopes the technology-icon fill rule correctly, so unrelated
SVGs keep their own fill and color. Fresh hero and finish reviews both returned **ship**, with no requested
changes and no material gap. Results are in `reviews.json`;
browser results are in `verification.json`.

## Files

Edited: `index.html`, `styles.css`, and the presentation animation/theme metadata
in `script.js`. Added: `tokens.css`, `base.css`, and these Hallmark records.
This refinement edits `index.html`, `styles.css`, and `tokens.css`, and adds
`previews/lakbayin-gameplay.webp` and `previews/swarm-upload.webp`. It does not
change the existing JavaScript or media players.
No existing source files or routes were deleted. The page still has no build
step and no runtime package dependencies.

Native project-wordmark glyphs are outlined from the existing font assets in
the markup, preserving their shapes without extra running font families.
Theme and dialog logic, media playback controls, project links and contact
links remain in place.

## Preview and compare

Serve the repository root with `python3 -m http.server 4177` and open
`http://localhost:4177/`. Hallmark captures at 320–1920 pixels; review images
include 1280×800, 1440×900, 1920×1080, and a full mobile page at 375 pixels.

The generated before/after comparison is `.hallmark/compare.html`, comparing
this refinement with the first redesign. The earlier captures are archived
locally in `.hallmark/iteration-1/`. Its captures
and comparison HTML are local review artifacts, excluded from commits by
Hallmark's own ignore file. To regenerate a sweep with the skill installed:

```sh
HALLMARK_PUPPETEER=/path/to/puppeteer-project CHROME_PATH=/path/to/chrome \
node /path/to/hallmark/scripts/sloplint.mjs \
  index.html styles.css tokens.css base.css --genre editorial --render
```

The local Linux capture wrapper permits standalone-file font loading; the
localhost captures use the site's normal CSP and same-origin font loading.

## Material

No stand-ins or unfilled picture slots. Every visible project image comes from
the existing portfolio or its video recordings. An optional personal portrait would be the one new
piece of material most useful for introducing the person behind the work.
