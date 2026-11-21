# Graphics brief (shared by every graphics subagent) — TEMPLATE
<!-- Copy to work/GFX_BRIEF.md, fill every <...>, and delete what doesn't apply.
     Start 2-4 LONG-LIVED graphics agents (grouped by visual kind: real sources/captures, concept diagrams, or continuous worlds),
     each with a prompt: "Read GFX_BRIEF.md and every reference it lists; your tag is <a>; your compositions are <ids>".
     Never spawn one agent per 2-3 compositions: use few long-lived agents who build, draft, check, and fix their own runs. -->

You build HyperFrames compositions for <N> standalone vertical shorts (1080x1920, 60 fps) about <topic/title of shorts, with exact product names, tools, and technical terms in Korean>. The shorts are created without any source video; every run is a full visual (`mode: 'fv'`). Work autonomously; make every judgement call yourself and report it.

## Paths
- Work folder (run every command from here): `<absolute path of project>/work`
- Python: `../.venv/Scripts/python.exe` (Windows) or `../.venv/bin/python` (`$PY`).
- Skill references (READ FIRST):
  - [references/graphics.md](../references/graphics.md) (Theme, Timing & Phrase Anchors, CFG)
  - [references/theme.md](../references/theme.md) (Tokens, surfaces, Pretendard typography), or for a sketch short
    [references/theme-sketch.md](../references/theme-sketch.md) (paper, pens, the drawing kit, the approved motion) and
    [references/parts.md](../references/parts.md) (circuit parts come from the kit only; attach the catalogue PNGs)
  - [references/lessons.md](../references/lessons.md) (HyperFrames, text encoding, craft)
  - [examples/gfx_s1.py](gfx_s1.py) (Reference implementation)
  - `scripts/build_gfx_common.py` and `gfx/engine.js` in the work folder.
- `cut.json` (runs, word timings) and `shorts.json` (script and plan) are READ-ONLY for you.

## Assets and Real Sources
- Real web pages, documentation, and pricing tables: `captures/` (`captures/index.json` maps file -> URL; `captures/facts.json` lists fact checks). Reuse these captures; do not re-capture.
- Official product and tool logos: `captures/logos/`. Use `logo_html('assets/<logo_file>')`.
- Copy assets you use into `gfx/assets/` prefixed with your `<tag>_` (e.g. `gfx/assets/a_pricing.png`).
- Fact-check figures: <list key numbers, claims, and verified true figures from research.md>. Display the true number in graphic text.
- Never display unofficial logos, competitors not mentioned in the narration, or placeholder images.

## Your Files (never edit another agent's files)
- `scripts/prep_assets_<tag>.py`: crops stills and clips into `gfx/assets/<tag>_*` and writes `gfx/asset_dims_<tag>.json` (build_gfx_common merges all `asset_dims*.json`).
- `scripts/gfx_<tag>.py`: contains a `build()` function that defines your assigned compositions (e.g. `s1_r0`, `s1_r1`) using `build_gfx_common` (`words`, `W`, `page`, `capture_card`, `logo_html`, `tile_html`).
- Build command:
  ```bash
  $PY scripts/build_gfx.py <tag>
  ```
- Check command (PNG only — **no MP4 of any kind before the user's review is complete**; the MP4 scripts refuse):
  ```bash
  $PY scripts/preview.py && python3 render.py --screenshot --run <id> --gapframe 20 --fast --jobs 3
  ```
  Writes `chk/shot_<sk>_<from>-<to>.png` from index.html with captions on. LOOK at each sheet before proceeding.
  Wait for `done <id>` output. `render_full.sh` throttles itself machine-wide (3 render slots × 8 browsers). Never run `prep.sh`, `finish.sh`, or `compose.py`.

## Rules That Matter Most
- **Every run is a full visual (`mode: 'fv'`)**: No split layouts, no cameras, no face cutouts.
- **Duration**: Matches `r['dur']` from `words(sk, ri)` exactly.
- **Timing with `W()`**: Cue every animation, camera move, and landing with `W(ws, '<Korean phrase>')` (e.g. `W(ws, '요금제') - 0.25` for a step). Never hardcode seconds. All timings re-time automatically when narration is recorded.
- **Frame 0 landing state**: The hero card must ALREADY be visible at t = 0 (sharp, camera at rest). Entrance animations (`land`) are only for secondary supporting elements.
- **Frame 0 of r0 is cover-safe**: Keep all graphic elements below y 620 so the glass title cover card (centred at y ~432) has clear space.
- **Typography in Pretendard**: Use Pretendard for all Korean text (`.display`, `.h1`, `.h2`, `.sub`, `.body`, `.caption`). Geist Mono is strictly for uppercase Latin labels (`.label`), falling back to Pretendard for Hangul. Nothing under 30 px.
- **Zones** (`LAYOUT`): content y 140–1395 (main element's bottom edge ~1360–1395), captions y 1410–1550 (or y 180–360 with `"caption": "top"`), nothing below y 1560 (platform UI), and no text or key element at x > 960 between y 1000 and 1700 (the platforms' like/comment/share column; build_gfx warns). Use the room: a hero card is big, not floating in the upper half.
- **Theme**: Graphite stage (`#18191C` to `#0B0C0E`), glass cards for diagrams (`highlight: True` for accent hairline + bloom), white windows/paper for real UI, glossy icon tiles (`tile_html`). One accent per scene (`azure`, `ember`, `mint`, `iris`).
- **Highlight bands**: Put `.band` (azure wash) under a `<img style="mix-blend-mode:multiply">` inside the card, revealed with `scaleX` on the keyword phrase. On dark UI, re-ink text or use an outline with glow.
- **Camera**: `glide`, `step` (0.5 s, starting 0.25 s before word), `push` (to ~1.6×), `pull`, at most one `whip` per run. Never blur readable text.
- **Thumbnails**: Add `thumb=[[a, b]]` (run-relative window where hero is landed and still) on compositions with high visual impact.
- **No SFX**: Do not add sound effects or SFX arrays to CFG. The short audio consists of narration only.

## Compositions
<!-- Paste the output of `$PY scripts/brief_runs.py` here.
     Add one "Idea:" line per composition: what it shows, real capture used, and what lands on which phrase. -->

### Short s1 "<Title>" · END <dur> s
- `s1_r0` number <dur> s - cover-safe frame 0 (keep everything below y 620 at t 0): <words with @times>
  Idea: <what it shows, key statistic, camera push on phrase>
- `s1_r1` capture <dur> s: <words with @times>
  Idea: <real page capture, inner camera zoom, highlight band on phrase>
- `s1_r2` diagram <dur> s: <words with @times>
  Idea: <glass diagram cards, icon tile, step to outcome on phrase>
- `s1_r3` logo <dur> s: <words with @times>
  Idea: <official logo lockup, transition to product interface on phrase>

## Sections and hero frames (look development; references/elevate.md)
<!-- 3-5 story sections of the short, each a span of runs, and the ONE hero run + moment per section that is built first.
     The rest is built after these hero frames match the approved look and the defect check finds nothing. -->
- hook: `s1_r0`–`s1_r2` · hero `s1_r1` @ <phrase> — <what the frame is>
- <section>: `s1_r3`–`s1_r8` · hero `s1_r5` @ <phrase> — <what the frame is>

## The bar
The craft guide (elevate.md §6) and the approved references of the theme; nothing is scored. A glass card holding a
title and a line of text is a slide. One hero per moment,
filling the content zone; vary the shots (wide · medium · close-up · insert); camera moves only for a reason in the words.

## Assignment
- Agent A (tag `a`): `s1_r0`, `s1_r1` - real captures and statistic cards
- Agent B (tag `b`): `s1_r2`, `s1_r3` - concept diagrams and product lockups

## Report Back (short)
Per composition:
1. What it displays and real captures/sources used.
2. Camera moves and whip transitions.
3. Thumbnail window (`thumb=[[a, b]]`).
4. Confirmation that the preview contact sheet of each composition was inspected.
