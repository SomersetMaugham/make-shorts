# Graphics: the HyperFrames world engine

Every run is a standalone HyperFrames composition: `gfx/<sk>_r<i>.html`.

Compositions are generated from compact Python configs by `scripts/build_gfx.py [tag]`, which imports `scripts/gfx_<tag>.py`. Each page loads the shared `gfx/engine.js`, implementing the skill's stage theme, world camera, depth of field, and motion blur, driven by a `window.CFG` object. The reference implementation for a complete short is [examples/gfx_s1.py](../examples/gfx_s1.py).

Contents: [Theme](#theme-the-neutral-stage-look) · [Timing & Phrase Anchors](#timing-and-phrase-anchors) · [Build Helpers](#build-helpers-scriptsbuild_gfx_commonpy) · [CFG Schema](#cfg-schema) · [Cards](#cards-and-surfaces) · [Camera Moves](#camera-moves) · [Depth of Field](#depth-of-field) · [Motion Blur](#motion-blur) · [Real Captures](#real-captures-in-full-visual) · [Thumbnails](#thumbnail-moments) · [Checking](#checking-and-validation)

---

## Theme: the neutral stage look

`theme: 'stage'` (the default; `'paper'` restores the white style only on explicit request) applies the skill's neutral dark look ([references/theme.md](theme.md)):
- **Ground**: graphite stage (#18191C at top to #0B0C0E at bottom), soft overhead spotlight, two faint angled beams, subtle vignette.
- **No horizon wave**: the old accent dot wave under the captions is gone (it only took room); pages have no `#wave` canvas.
- **Accents**: `'azure'` (default #2F95FF), `'ember'` (limits, costs #FF8A5B), `'mint'` (passes, success #4FD6A0), `'iris'` (#9C7CFF). Use one accent per scene.
- **Typography**:
  - **Pretendard** (SIL OFL 1.1) for every word on screen. The shorts are in Korean, and Pretendard keeps Hangul, Latin, and numbers in the same clean voice.
  - Type classes: `.display` 128px, `.h1` 96px (-0.03em), `.h2` 54px (-0.025em), `.sub` 46px (accent color), `.body` 32px, `.caption` 30px.
  - Spacing: Keep Korean lines at -0.02em or looser; `word-break: keep-all` breaks between 어절, never mid-word.
  - **Geist Mono** 500 for uppercase Latin labels (`.label`), falling back to Pretendard for any Hangul characters.
  - Minimum size: nothing under 30 px.
- **Cards**: `glass` (diagrams, architecture, statements; `highlight: True` adds accent hairline and bloom), `window` / `paper` / `media` / `capture` (white surfaces for product UI, chats, code, and captures), `tile` (glossy 3D icon tiles via `tile_html`), `plain`.
- **Layout bounds** (`LAYOUT` in build_gfx_common, from config.py): every run is a full visual (`mode: 'fv'`). Content y 140–1395 (main element's bottom edge ~1360–1395); captions y 1410–1550 (or y 180–360 with `"caption": "top"`); nothing below y 1560, where the platforms draw their title and description; and no text or key element at x > 960 between y 1000 and 1700, under the platforms' like/comment/share column (`ui_right`; a card's frame or the background may pass under it; build_gfx warns).

---

## Timing and Phrase Anchors

Before voiceover recording, all cue lengths and word timings are estimates based on character positions (`est: true`). Recording with Chirp 3 HD changes the cadence and length of every cue.

To prevent re-timing from breaking animations or requiring manual edits, all graphics timing is anchored on phrases:

```python
r, ws = words('s1', 0)
t_phrase = W(ws, '핵심 구절')
```

### Semantics
1. **`words(sk, ri)`**: Returns `(run, ws)`. Each item in `ws` is `dict(w=..., t=..., est=...)`, where `t` is the run-relative start time in seconds and `est` indicates whether the time is an estimate (`True`) or locked by an `"at"` measurement (`False`).
2. **`W(ws, '<phrase>', n=1)`**: Returns the run-relative start time of the n-th occurrence of `<phrase>`.
   - The phrase is written as in the Korean cue text.
   - Punctuation is ignored.
   - Trailing particles may be omitted: `W(ws, '하네스')` matches `'하네스가'`.

### The Re-time Loop
1. Graphics subagents draft animations and camera moves using `W(ws, '<phrase>')` against placeholder cues.
2. The user approves recording. Real takes are recorded with `tts.mjs --approved`.
3. The agent reviews takes with `wave.mjs`, sets `"cut"` and `"at"` points in `script.json`, and runs `prep.sh`.
4. The agent re-runs `python scripts/build_gfx.py`. Every `W()` call re-evaluates against the newly measured times in `cut.json`.
5. Every move, landing, and reveal lands on the real spoken phrase automatically—without modifying graphics code.

> [!IMPORTANT]
> Never hardcode seconds for animations or landings that correspond to speech. Always anchor on `W(ws, '<phrase>')` or simple offsets (e.g. `W(ws, '요금제') - 0.25` for a camera step).

---

## Build Helpers (`scripts/build_gfx_common.py`)

- **`words(sk, ri)`**: returns `(run_dict, word_list)` for run `ri` of short `sk`.
- **`W(ws, phrase, n=1)`**: returns the run-relative start time for `phrase`.
- **`page(rid, cfg, extra_html='', extra_css='', videos=(), backdrop=None, extra_js='')`**: writes `gfx/<rid>.html`.
  - `videos=[(card_id, 'assets/clip.mp4', fw, fh)]`: attaches video footage to a card.
  - `backdrop=('img'|'video', src, fw, fh)`: creates a blurred, enlarged clone behind captures.
- **`capture_card(cid, fw, fh, x=540, y=720, inner0=None, inner=(), backdrop=True, land=None, **kw)`**: generates the standard capture card: 1032×1200, radius 36, centred at (540, 760) (y 160–1360).
- **`logo_html(src)`**: returns a responsive SVG/PNG logo tag (`<img src="{src}" style="width:100%;height:100%;object-fit:contain;display:block">`).
- **`tile_html(color='azure', glyph='code', size=140, tilt=-8, svg=None)`**: generates a glossy 3D icon tile with inner shadow and top highlight. Glyphs: `code`, `arrow`, `check`, `shield`, `sparkle`, `bolt`, `bars`, `eyes`, or custom SVG.
- **`D`**: dictionary of asset dimensions loaded from `gfx/asset_dims.json` and `gfx/asset_dims_<tag>.json`.

---

## CFG Schema

```python
cfg = dict(
  id='s1_r0', dur=r['dur'],             # run duration exactly
  mode='fv',                            # every run is a full visual ('fv')
  anchor=[540, 720],                    # screen anchor point (default: [540, 720])
  cam0=dict(x=540, y=720, s=1.0),       # frame-0 camera position
  cards=[...],                          # list of card objects
  moves=[...],                          # list of world camera moves
  heroes=[dict(t=0, id='hero_card')],   # depth of field targets
  pushRef=1.0,                          # camera scale threshold for neighbor blur
  reveals=[dict(el='band1', t=W(ws, '반값'), dur=0.5, type='scaleX')],
  typings=[dict(el='cmd', t0=0.3, cps=18, text='npm run build', caret=True)],
  thumb=[[1.2, 3.4]],                   # thumbnail candidate windows
)
```

> [!NOTE]
> The CFG `sfx` field is ignored. Shorts have no sound effects, risers, or music; audio is narration only.

---

## Cards and Surfaces

```python
dict(
  id='card1', kind='glass'|'window'|'paper'|'media'|'capture'|'tile'|'plain',
  x=540, y=720, w=1032, h=640,          # world coordinates, centre-based
  img='assets/shot.png' | html='...',
  radius=32,                            # corner radius (defaults per kind)
  land=dict(t=W(ws, '시작'), dur=0.55), # entrance animation (power3.out, +70px dy, scale 0.92->1)
  exit=dict(t=W(ws, '종료'), dur=0.35), # exit animation
  inner0=dict(fx=500, fy=400, k=1.0),   # initial inner footage camera
  inner=[dict(t=W(ws, '확대')-0.25, dur=0.6, fx=600, fy=450, k=1.4)],
  overlay='<div ...>',                  # HTML layer moving with inner camera
  backdrop={'tIn': -1},                 # blurred clone fade-in
  noDof=True, forceSharp=True,
)
```

- **Frame 0 landing state**: The hero card must ALREADY be on screen at t = 0. Never animate a hero's landing starting at 0.05 s (which leaves black or empty frames after the cut). `land` is only for secondary supporting cards that enter later.
- **Frame 0 of r0 (cover safe)**: Run 0 frame 0 is also the video cover frame. Keep all graphics elements below y 620 so the glass title cover card (centred at y ~432) has full clearance.
- **Highlight bands on captures**: Blend modes are isolated per card. Place an azure wash `<div id="band" class="band">` under a `<img style="mix-blend-mode:multiply">` inside the card's `html`, then reveal it with `scaleX` on the keyword phrase. On dark UI, re-ink the text dark on the wash, or use an accent outline with soft glow.

---

## Camera Moves

`moves` contains objects: `dict(t, dur, kind, to=dict(x, y, s), ease=None)`.

| kind | purpose | default ease | timing |
|---|---|---|---|
| `glide` | gentle holding drift | sine.inOut | scale change ≤ 0.04 |
| `step` | shift focus to next item | power3.inOut | 0.5 s, starting 0.25 s before the phrase |
| `push` | zoom in on active element | power2.inOut | 1.2–2.0 s, up to ~1.6× |
| `pull` | zoom out to reveal broader layout | power2.inOut | 1.0–2.0 s |
| `whip` | rapid pan across world | power3.in / power3.out | 0.45 s out, 0.6 s in (`to` and `via`), max 1 per run |

---

## Depth of Field

`heroes=[dict(t, id)]` specifies which card has focal focus at time `t`:
- As the camera pushes (`cam.s > pushRef`), non-hero cards blur up to 14 px and dim by 30%.
- A previous hero fades to a 9 px blur at 40% opacity.
- `id='none'` disables depth of field (keeps all cards sharp).
- Never blur text the viewer needs to read.

---

## Motion Blur

Motion blur is computed per-frame based on screen velocity. Full renders are captured at 240 fps and temporally blended to 60 fps via FFmpeg `tmix` in `render_full.sh`. A frame at rest is completely sharp.

---

## Real Captures in Full Visual

Show real sources whenever discussing articles, docs, benchmarks, pricing, or releases:
- Real 2x PNG screenshots from `captures/`.
- Standard capture card via `capture_card`: frame centred at (540, 760), 1032×1200, radius 36.
- The outer card remains stationary while the content pans and zooms inside using `inner` keyframes (`fx`, `fy`, `k`). The engine automatically clamps the inner view to the footage boundaries.

---

## Thumbnail Moments

The thumbnail is picked from moments marked in compositions, avoiding post-render scans.
Add `thumb` to each CFG:
- A run-relative time window `[[a, b]]` where the composition's primary visual is landed and the camera is at rest (e.g. key statistic large, real UI fully displayed, chart complete).
- `build_gfx_common.py`'s `still()` helper automatically clips out camera moves, landings, focus shifts, and reveals.
- Mark 1–2 candidates per composition that has strong visual impact; omit `thumb` on transitional runs.

---

## Checking and Validation

Before handing the preview over (no MP4 is made before the user's review is complete):
1. Rebuild and refresh the preview: `$PY scripts/build_gfx.py <tag>` and `$PY scripts/preview.py`.
2. Shoot a contact sheet of the run from the preview and inspect it:
   `python3 render.py --screenshot --run <sk>_r<i> --gapframe 20 --fast --jobs 3` → `chk/shot_<sk>_<from>-<to>.png`.
3. Verify:
   - Frame 0 landing state: hero card is already visible at t = 0.
   - Run 0 frame 0: all elements stay below y 620.
   - Text legibility: all text ≥ 30 px.
   - Zones: content y 140–1395, captions y 1410–1550, nothing below 1560; no text or key element at x > 960, y 1000–1700 (the button column).
   - Timing: animations step and land on the intended phrase.
