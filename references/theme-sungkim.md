# The Sungkim theme (`"theme": "sungkim"`)

**When:** the user asks for "성킴 스타일" / "성킴스타일" / "성킴 테마" (e.g. "오늘 화제가 된 클로드의 새로운 모델 발표
소식을 성킴스타일로 쇼츠 제작해줘"). For news and research explainers: a headline per section, one picture with its
exact source, and the key facts landing as cards.

**Where it comes from (2026-11-23):** first written from the user's HTML mock-up, then rebuilt from the creator's real
Short "AI가 스스로 자식을 낳고 진화했다?" (youtube.com/shorts/UE1C-fwapU0, 120 s), analysed by agy Hydrogen frame by
frame and checked by Claude on the frames: `/Users/admin/project/shorts/sungkim-ref/analysis.md` (scene table,
measurements) and `sheet.png`. Read the scene table when in doubt: it is the reference.

The kit: `scripts/sungkim_kit.py` (`section`, `sungkim_cover`, `sungkim_page`, the card builders, `PALETTE`,
`SOURCE_KINDS`) and `assets/gfx/sungkim.js`.

## The frame
| zone | y (px) | what |
|---|---|---|
| cover (run 0 only) | full frame | dark `#020611` (an optional darkened image behind), kicker 38 px `#CFD4DF` at y 150, 2-3 title lines Pretendard 900 112 px white with the **last line gold `#F9CA60`**, an orange pill `#E0532E` with the one concrete fact at y 1190, a small dark note pill under it |
| header | 91-300, x 56 | kicker (700, 46 px, `#5D6268`) and the title (800, 112 px, **the section colour**, one line, shrinks to 72 px) |
| upper card `#skVis` | 368-921, x 56-1024 | 968 x 553: white `#FDFDFD`, faint border, radius 20, a soft drop shadow; `vis_dark=True`: dark, radius 44 |
| source line `#skSrc` | 930-966, x 72 | 30 px `#484644`: always `<kind> · <exact source>` |
| lower cards `#skCards` | 984-1384, x 56-1024 | the cards (below), 14 px apart; text ends left of x 960 |
| captions | 1410-1550 | black Pretendard 700 50 px on the paper with a thin paper-coloured outline (readable on the dark cover too), no box; the keyword in teal 800, no box |
| — | 1560-1920 | empty |

Background `#F6F3E9`. compose.py lays nothing over frame 0: run 0 is the cover (`sungkim_cover`).

## Sections and the header
- The short is 5-8 **sections** of 2-5 runs (the reference: 7 sections, ~17 s each). Kicker and title change only
  at a section start; the upper card and the cards change inside it.
- **Kicker** frames the topic or the turn ("생명이란", "그럼 위험할까", "그래도 아직은", "이 연구가 중요한 이유").
- **Title** = the section's takeaway, 6-11 characters, one line: a hook question ("자식을 낳았다?"), a number
  ("5.5% → 92%", "실력의 3분의 1"), a three-part summary ("복제 · 변이 · 선택") or a conclusion ("진화를 먼저 연구한다").
- **Colour per section** (`section(kicker, title, color)`): teal, blue, gold, red (the risk section), purple, and
  back to teal for the ending. The title, the badges, the card borders and the big numbers share it.

## The upper card: which picture for which sentence
| the sentence | the picture | source kind |
|---|---|---|
| a claim from a paper or a post, who did it | the real page, cropped to its title or the cited paragraph (capture) | `실제 자료` · paper, arXiv id, date, review status |
| how it works | the paper's own figure | `실제 그림` · paper, figure number |
| a trend or comparison | a chart you draw from the paper's values (line draws on over ~4 s, bars fill over ~2.7 s) | `계산해서 그린 그림` · which figure's values, the condition |
| the hook, a question, the closing | a concept picture (dark, `vis_dark=True`) | `개념 그림` · what it is, that it is illustrative |
One picture stays 3-19 s; a section uses 1-3. Pictures change by a hard cut. A concept picture must not pass for
evidence: its source line says it is illustrative. (The reference used AI-generated pictures; this skill makes no
images by another service, so a concept picture is drawn or a darkened real capture, unless the user supplies one.)

## The lower cards (`cards=[(W(ws,'구절'), card), …]`)
| builder | when | example in the reference |
|---|---|---|
| `badge_card(badge, text)` (h 118) | the default: a keyword line, numbered steps ("① 복제") | 연구자 · 스웨덴 인공생명 연구자 아렌트 힌체 |
| `statement_card(text, sub, badge, round_)` (h 250) | a conclusion, a question (`color='grey'`, `round_=True`), the closing card | 아무도 그렇게 하라고 / 시키지 않았다 |
| `quote_card(badge, quote, sub)` (h 250) | an exact quote, with its meaning or place | AI에게 준 한 문장 · "Let there be life!" |
| `number_card(badge, value, sub)` (h 250) | the number of the section | 16세대 만에 · 5.5% → 92% |
| `bars_card(title, rows)` | a comparison of 1-3 values (bars fill after landing) | 스스로 복사본을 띄운 비율: 50% / 90% |
| `pair_card(left, right)` (h 320) | two facts side by side (lost vs gained) | 스스로 버린 부품 · 어텐션 / 복사 비용 · 2만 배 ↓ |
| `units_card(badge, groups, summary)` (h 300) | n of m, filling in one by one | 자식 20개 중 · 14 gold + 6 red |
| `tiles_card(title, tiles)` (h 340) | four outcomes landing one after another | RepliBench: 잘함 / 일부 / 약함 / 막힘 |

- **Card text is a distillation, never the spoken sentence**: a keyword phrase, parallel short phrases for a list,
  the exact quote, the number. At most 3 cards stacked (or one pair / units / tiles card); usually 1-2.
- **Clear often**: the lower area is rebuilt every run from the list passed. Keep earlier cards (t 0) while the
  sub-topic goes on; drop them when it turns (question → answer, a stack → a summary card, a new experiment). The
  reference cleared mid-section 17 times.
- **Timing**: a card's t is its phrase; the kit lands it 0.3 s before (the reference: 0.1-0.5 s early), fading in and
  rising 16 px over 0.4 s.
- **Badge colour**: the section's; grey for a question or neutral framing ("질문"); red for an error, a mutation, a
  discarded part or a risk, even inside another section. Badge text white, 800, 30 px, a full pill.

## Ending
The last section returns to the concept picture in the upper card and ends on one `statement_card(…, round_=True)`
with no badge (the reference: "번식하는 AI, / 막을 방법도 우리가 먼저" + "진화를 먼저 연구하는 이유").

## Deliberate differences from the reference
Captions are the skill's 1-3 word chunks (the reference shows a whole clause); keywords become teal words (the
reference has no chips); text stays at 30 px or more (the reference's source line is ~26 px); card text ends left of
x 960 (the like/comment column). The cover is run 0 for its whole length (the reference: 3 s with no captions; here
the captions run over it).
