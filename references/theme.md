# The stage theme (the skill's own look)

The graphics, captions, chips and cover share one look: a graphite stage lit from above with cards floating in it and a
camera moving through it. It is the skill's neutral default (`theme: 'stage'` in the engine). The code implements it in
`scripts/build_gfx_common.py` (CSS tokens and type classes), `assets/gfx/engine.js` (stage, shadows, camera) and
`scripts/compose.py` (captions, chips, cover). A user's own brand guide, when they give one, replaces these tokens.

## Stage
- Background #18191C at the top to #0B0C0E at the bottom, a soft overhead spotlight, two faint light beams, a vignette.
- No decoration at the bottom: the frame's zones are content y 140-1400, captions y 1430-1610, and below y 1610 only
  the stage itself (the platforms draw their UI there). The old horizon wave of dots is gone.
- No light theme. (`theme: 'paper'`, the old white world, exists only for a user who asks for it.)

## Colour tokens
| token | value | use |
|---|---|---|
| stage-950 / 900 / 800 / 700 / 600 | #0B0C0E #111214 #18191C #212226 #2C2D31 | stage, glass fill, wells |
| text / text-secondary / text-muted | #FFFFFF #A3A6AD #7E818A | type on the stage |
| ink / ink-2 | #111214 #5F636B | type on paper and windows |
| azure (+ ink, wash) | #2F95FF #1560D0 #E8F2FF | the default accent |
| ember | #FF8A5B #B8461A #FFEFE7 | limits, costs, warnings |
| mint | #4FD6A0 #0F7A52 #E3F8EF | passes, checks, success |
| iris | #9C7CFF #5B3FD1 #F0EBFF | icon tiles, a second category |

One accent per scene. A highlight band on a captured light page is the azure wash (#CFE4FF) under a `mix-blend-mode:
multiply` screenshot, revealed with `scaleX` on the phrase.

## Surfaces
- **glass** (`kind: 'glass'`) for diagrams and statements: stage-800 at 62 % with a 24 px backdrop blur, a white hairline,
  the long panel shadow; `highlight: True` adds the accent hairline and bloom (one element per scene). Radius 32.
- **window / paper / media / capture** for real UI, pages, chats, files and captures: white, radius 24 (capture 36).
- **tiles** (`tile_html`): glossy icon tiles in azure, iris, ember or mint, radius 28.5 %.

## Type
- **Pretendard** (SIL OFL 1.1, downloaded by setup.sh) for every word: the outputs are Korean, and its Latin and digits
  keep names and numbers in the same voice. Weights: 600 for what you read, 500 for subtitles, 400 for body.
- Sizes on the 1080x1920 canvas: display 128, headline 96 (-0.03em), title 54 (-0.025em), subtitle 46 in the accent,
  body 32 in text-secondary; nothing under 30 px. Keep Korean lines at -0.02em or looser; `word-break: keep-all` (set
  on the root) breaks lines between 어절, never inside a word.
- **Geist Mono** 500 for uppercase Latin labels (0.14em tracking); Hangul in a label falls back to Pretendard.
- Captions: Pretendard 700, 74 px, white with a 10 px stage-950 stroke, no box. Keyword chips: Pretendard 600, 70 px,
  -0.025em, on stage-800 glass at 88 % with the accent hairline, bloom and top highlight, radius 28, the accent line
  drawn in beneath (pops in over 0.18 s; the line sweeps from 0.08 s over 0.32 s).
- Cover (frame 0): Pretendard 600, 104 px, -0.03em, on a stage-800 glass card with the accent hairline and bloom, radius
  36, the accent line beneath, centred at y ~432 (inside y 262-603 for two lines).

Figtree, Poppins and Instrument Serif are still in `assets/fonts/` for old compositions and the paper theme; they have no
Hangul, so never put Korean in them.
