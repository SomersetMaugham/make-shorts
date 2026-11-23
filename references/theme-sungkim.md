# The Sungkim theme (`"theme": "sungkim"`)

**When:** the user asks for "성킴 스타일" / "성킴 테마" (e.g. "오늘 화제가 된 클로드의 새로운 모델 발표 소식을
성킴스타일로 쇼츠 제작해줘"). Suited to news and tech explainers: a headline, one picture, where it comes from, and the
key facts stacking up as cards. Taken on 2026-11-23 from the user's own template
(`/Users/admin/project/shorts/gemini-code-1795429352680.html`) and fitted to the skill's frame zones; that file's player
(its timer, audio upload, Web Speech TTS and subtitle box) is not used: the narration, captions and preview are the
skill's.

The kit: `scripts/sungkim_kit.py` (`sungkim_page`, `card`, `capture_html`, `COL`) and `assets/gfx/sungkim.js`.

## The frame (fixed in every run)
| zone | y (px) | what |
|---|---|---|
| header `#skHdr` | 120-270, x 64-1016 | kicker (Pretendard 700, 34 px, `#4A4F5A`) and the title (900, 78 px, `#16181D`, -0.03em, **one line**: shrinks by 2 px until it fits, at least 48 px) |
| visual box `#skVis` | 290-850, x 64-1016 | the run's picture; inner box 952 x 560, fill `#FFFDF8`, 1.5 px border `#E3DDD0`, radius 24 |
| source line `#skSrc` | 862-898 | "출처: …" Pretendard 500, 30 px, `#767C89`, one line |
| info cards `#skCards` | 920-1380, x 64-1016 | up to 3 cards, 16 px apart, stacking down |
| captions | 1410-1550 | white Pretendard 700 64 px on a dark box (`rgba(20,22,27,.88)`, radius 16); keyword chips white 800 on solid blue `#1D5BFF` |
| — | 1560-1920 | empty (the platforms draw their UI there) |

Background: flat warm paper `#F7F4EC`. Cover (frame 0 only): the title in Pretendard 900 ink on a paper card
(`#FFFDF8`, 3 px `#E3DDD0`, radius 28) with a blue line beneath, centred at y ~432; in run 0 the header, visual box and
source line appear from the second frame.

## Cards (`card(title, body, metric, kind)`)
Title Pretendard 800 36 px; optional metric 900 56 px blue (red on `warn`), right-aligned; body 500 30 px `#4A4F5A`,
one line. Left edge 8 px: `''` plain (warm grey), `'blue'`, `'accent'` (blue-tinted card for the key number),
`'warn'` (red: a limit, a caveat, what is not proven yet). Card text ends at x 942 (left of the button column).
A card lands on the phrase that says it (`(W(ws, '구절'), card(...))`): rises 24 px and fades in over 0.24 s. Within a
section the cards accumulate: a later run passes the earlier cards again with t 0 so they are in place on frame 0. A
new section (new kicker and title) starts with an empty card area.

## Rules
- **Every news claim shows its real source** in the visual box: `capture_html('assets/<tag>_page.png', w, h,
  focus=(x, y), zoom=…)` crops the capture around the cited line; the source line names the page. Concept pictures
  (bars, steps, grids like the template's mesh / bar / pipeline visuals) are for the explanation, not for the news.
- The header changes per section, not per run: one kicker + title for 2-5 runs. The title is a statement or question
  the viewer reads in one glance (at most about 18 Korean characters at full size).
- Colours: ink `#16181D`, secondary `#4A4F5A`, muted `#767C89`, blue `#1D5BFF` (the point), red `#D9483B` (caveats),
  card `#FFFDF8`, accent card `#EEF4FF`, borders `#E3DDD0` / `#BFD4FF`, bar tracks `#ECE7DC`. One blue thing per moment.
- Text at least 30 px everywhere. No camera moves, no shadows. `vis_js` is a pure function of t.
