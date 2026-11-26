# The Brief theme (`"theme": "brief"`)

**When:** the user asks for "브리프 스타일" / "브리프 테마" / "매거진 스타일" / `brief` theme. Designed for news,
paper and research explainers that want a **Modern Research Magazine (Print Editorial)** identity — keeping the
proven four-tier briefing skeleton (header → evidence figure → source → distilled cards) while standing cleanly apart
from the Sungkim theme (`theme-sungkim.md`).

**Design decisions locked by the user (2026-11-24):**
- **Name**: `brief` (separated from `sungkim`, which stays intact)
- **Type**: 3-tier hierarchy — **Hahmlet 700** (cover headline, section title, big numbers, pull-quotes, sting wordmark) +
  **Pretendard** (body, cards, captions) + **Geist Mono** (section progress `01 / 06`, source metadata, card indices)
- **Header title colour**: section dark colour (1-B) over a 3 px + 1 px editorial double ink rule
- **Cover (Run 0)**: light magazine cover on `#F5F4F0` newsprint paper (seamless cut into Run 1; no dark flash, no orange pill)
- **Sting**: magazine-native **Minimal Ink & Rule Sting** (`assets/gfx/brief_sting.js`, default `BRIEF.` / `RESEARCH · ANALYSIS · INSIGHT`)

The kit: `scripts/brief_kit.py` (`section`, `brief_cover`, `brief_page`, `brief_sting`, the card builders,
`PALETTE`, `LAYOUTS`, `SOURCE_KINDS`) and `assets/gfx/brief.js` + `assets/gfx/brief_sting.js`.

## The frame
| zone | y (px) | what |
|---|---|---|
| cover (run 0 only) | full frame | light `#F5F4F0` paper, double-rule masthead (`BRIEF.` + `RESEARCH BRIEFING` + `NO. 01 · 2026`), left-aligned kicker + 2-3 line **Hahmlet 700 100 px** title (last line accented with editorial underline), sharp-framed hero figure (`y 636–1070`), left-bar `KEY FINDING` fact strip (`y 1106–1320`, text left of `x 950`) |
| progress bar | 60–82, x 60–1020 | segmented section bar (current segment in section accent, past segments grey) + `01 / 06` (`Geist Mono 600 25 px`) |
| header `#brHdr` | 98–308, x 60–1020 | square-marked kicker (`Pretendard 700 34 px`, section accent) + one-line title (`Hahmlet 700 84 px`, shrinks to 56 px, **section dark colour**), closed by a 3 px + 1 px double ink rule |
| upper card `#brVis` | 332+, x 60–1020 | crisp framed figure (`radius 6`, `1.5 px solid #161618`, `#FCFBF8` sheet; `vis_dark=True`: `#14171D`). Height by `layout`: `default` 548 px, `visual_tall` 656 px, `cards_tall` 416 px |
| source strip `#brSrc` | 16 px below `#brVis` | archive chip (`실제 자료`/`실제 그림` solid dot, `계산해서 그린 그림` outline, `개념 그림` dashed) + exact source text |
| lower cards `#brCards` | 68 px below `#brSrc` | editorial cards (bottom ≤ y 1380; outer frame aligns to `x 1020`, **all text padded left of `x 950`**) |
| captions | 1410–1550 | ink `#161618` `Pretendard 700 50 px` with newsprint `#F5F4F0` outline; keyword highlights in **the run's section colour** with a flat sweeping rule (no glow) |
| — | 1560–1920 | empty |

Background `#F5F4F0` with a subtle newsprint grain (`#brGrain`). `compose.py` lays nothing over frame 0: run 0 is the
cover (`brief_cover`).

## Colour palette (`PALETTE`: dark / main / wash)
| name | dark (title / big figure) | main (rule / bar / chip / caption keyword) | typical section role |
|---|---|---|---|
| `crimson` | `#8F1D1D` | `#B42323` | cover default, core issue, risk, anomaly |
| `navy` | `#16335B` | `#204A80` | research background, structure, explanation |
| `forest` | `#154D3D` | `#1E6B55` | verification, gain, conclusion, closing |
| `ochre` | `#8A560F` | `#B07016` | numbers, trends, comparisons, turning point |
| `plum` | `#4E3161` | `#6A4382` | implication, broader meaning, outlook |
| `slate` | `#424B57` | `#5D6878` | neutral question, framing, conceptual caveat |

`brief_page` and `brief_cover` automatically write each run's colour into `gfx/brief_colors.json`, which `compose.py`
and `preview.py` read so every keyword highlight chip follows its run's section colour.

## Sections and vertical presets
- Pass `index` and `total` to `section(kicker, title, color, index=1, total=6)` so the top progress bar tracks the
  narrative beat (`01 / 06` → `06 / 06`).
- Vary `layout` across sections to prevent visual fatigue on 60–120 s shorts while keeping the editorial column locked:
  - `'default'`: upper 548 px / lower 416 px (standard captures, charts, 1–3 stacked cards)
  - `'visual_tall'`: upper 656 px / lower 308 px (dense paper figures, multi-series charts + 1–2 compact cards)
  - `'cards_tall'`: upper 416 px / lower 548 px (compact schematic + `pair_card` + takeaway `badge_card`, or `tiles_card`)

## Captures (`capture_html`)
Same readability and crop-safety rules as `sungkim` (`scripts/capture_marks.py`, `MIN_CAPTURE_TEXT = 26 px`, `keep`
boxes, bare numbers with no `~` or `약`), and the required `credit='출처: <source>'` chip on the capture's bottom-right
corner (`credit_pos='tr'`: top-right; a raw `<img>` of a source adds `credit_chip(...)`), with two magazine upgrades:
- `mark_style='highlight'` (default): sweeps a translucent `multiply` wash band + crisp 4 px underline in the section
  colour under the cited phrase (`mark_style='underline'` draws the underline only).
- `dim=True`: gently dims bands above and below the cited sentence on white paper captures so the eye snaps directly to
  the evidence.

## Lower cards (`cards=[(W(ws, '구절'), card), …]`)
- `badge_card(badge, text, idx='', color=None)` (h 126): left 6 px accent bar, tinted tag + concise summary. **Leave `idx=''` empty by default** (the user, 2026-11-24: do not put `01`/`02` numbers on lower badge cards unless explicitly asked for numbered steps).
- `number_card(badge, value, sub='', prev='', color=None, count_from=..., count_to=..., suffix='%')` (h 282): top 5 px accent rule, optional `prev →` before/after, huge `Hahmlet 700` metric with optional smooth count-up roll.
- `quote_card(badge, quote, sub='', color=None)` (h 264): left 6 px accent bar + `Hahmlet 700` exact quotation.
- `statement_card(text, sub='', badge='', color=None, quote_mark=True)` (h 264): magazine pull-quote framed by a double ink top rule and bottom ink rule.
- `bars_card(title, rows, color=None)` / `pair_card(left, right)` (h 336) / `units_card(...)` (h 308) / `tiles_card(...)` (h 344).
- All cards land `LEAD = 0.3 s` before their phrase (`t=0` = visible on frame 0). Clear lower cards on sub-topic turns.
- **No empty cards zone after a cut** (the user, 2026-11-26): within 1.0 s of a run's start its lower cards zone is at
  least 35 % filled, or 20 % is already in place at frame 0 (one `badge_card` at `t=0`). `brief_page` prints
  `⚠ s1_rN: the lower cards zone is under 35% filled …` otherwise; fix every such warning before the preview.

## Intro and outro sting (`brief_sting`)
- **Intro (optional, on cover run 0)**: `brief_sting(t0=0.15, mode='intro', accent='crimson')` — a subtle 1.4 s crimson
  registration glint gliding across the cover masthead hairline without delaying the hook.
- **Outro (on the final run)**: set `script.json` `"tail": 3.4` and pass
  `stings=[brief_sting(t0=r['dur'] - 2.9, mode='outro')]` (customizable via `brand='...'`, `tagline='...'`, `accent='...'`).
  Fades the frame cleanly to `#F5F4F0` paper over 0.35 s, then plays the 2.8 s Minimal Ink & Rule Sting (silent).

## Thumbnail candidates (`thumb`)
Every `brief_page` and `brief_cover` marks a thumbnail candidate by default, so `chk/<sk>_thumbs.png` is never empty
(the HN BRIEF short, 2026-11-24: no run was marked and the sheet came out blank). The default window is the last 1.5 s
of the run, starting no earlier than the moment the last lower card is at rest (`_card_settle`: entrance 0.6 s,
`number_card` count-up, `bars_card` fills, `units_card` / `tiles_card` steps), ending 0.2 s before the run ends or
0.1 s before an outro sting; on the cover, after the intro sting (1.6 s). Pass `thumb=[...]` to choose the moment
yourself (a run-relative time or a window `[a, b]`); the upper visual's own `vis_js` motion is not tracked, so mark it
by hand when that animation runs to the run's end.
