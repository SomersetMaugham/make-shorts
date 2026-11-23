# The code-reel theme (`"theme": "reel"`)

**When:** the user asks for the "코드 릴 스타일" / code-reel look, or a short explains code, an algorithm or a formula
step by step and the user wants the line being discussed shown in code. Made on 2026-11-23 for the weight-decay short
(a Korean remake of a reference YouTube Short, "Machine Learning from Scratch"); the layout was approved by the user
the same day (layout option 1: top card kept at 608 px, a divider, the code card grown to 514 px).

The kit: `scripts/reel_kit.py` (`reel_setup`, `reel_page`, `COL`) and `assets/gfx/reel.js` (the runtime). The example:
`/Users/admin/project/shorts/weight-decay/work/scripts/gfx_g.py` (37 runs; written on the old layout, 2026-11-23).

## The frame (fixed in every run)
| zone | y (px) | what |
|---|---|---|
| header | 36-214 | series label (Pretendard 800, 32 px, red `#E0342C`, +0.04em), title (650, 80 px, white, one line), subtitle (400, 30 px, `#94A3B8`) |
| top card `#top` | 228-836, x 40-1040 | the run's diagram; inner box 1000 x 608, fill `#0A121E`, 2 px border `#1A2235`, radius 28 |
| divider | 850, x 80-1000 | 2 px `#212639` |
| code card `#code` | 866-1380, x 40-1040 | title bar (three dots pink/amber/green, file name, language, Geist Mono 30 px) + up to 8 lines, Geist Mono 32 px on 54 px lines, line numbers `#64748B` |
| captions | 1410-1550 | compose.py's stage captions (white with a graphite stroke) and glass chips |
| — | 1560-1920 | empty (the platforms draw their UI there) |

Background: flat `#080E16`, no beams, no vignette. Frame 0 of run 0 is the cover (the stage cover card); the header and
the top card appear from the second frame (`cover_safe`, automatic for `*_r0`).

## Colour roles (`COL`)
blue `#3B82F6` / `#60A5FA` = positive values, data, the normal curve · pink `#F0718C` = negative values, the bad case
(overfitting, error) · amber `#F5A524` = the thing the short is about (the decay, the penalty, λ) · green `#34D399` only
for a third value · text `#F1F5F9`, secondary `#94A3B8`, axes `#64748B` / `#1A2235`. Code: keywords purple `#C084FC`,
function names `#60A5FA`, numbers amber, comments `#64748B` italic.

## Rules
- **The code is the short's spine.** `reel_setup(code=[…])` holds at most 8 lines, each ending left of x 960 (about 40
  Latin characters; Hangul in a comment is wider). `code_hl=[(W(ws,'구절'), [line numbers]), …]` moves the white box
  (3 px, radius 12) to the line the narration is on; lines outside it dim to 32 %. An entry at t 0 is in place on frame 0.
- **One diagram may continue across several runs**: the next run starts exactly where the previous one ended (same
  positions, values, colours); an element no longer needed fades out over 0.4 s from t 0.25; a new one fades in on its
  phrase. Never let something appear or vanish at a cut. The defect checker is told this is by design.
- Diagram style: flat vector, lines 2-3 px, curves 4-5 px, dots radius 9-12, small boxes radius 10, no shadows, a soft
  ring only on an active dot. Labels: at most 2 on screen, at most 12 Korean characters, at least 30 px. Numbers are the
  true ones (compute them; never invent a curve).
- No camera moves. `top_js` is a pure function of t: no state, no CSS transitions, no timers.
- Same layout every run means the runs differ only in the diagram: keep each run's diagram change clearly tied to its
  words.
