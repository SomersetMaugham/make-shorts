# Pipeline: exact commands

This skill creates standalone 9:16 vertical shorts (YouTube Shorts, TikTok, Instagram Reels) from a topic, material, or finished script without any source video or talking-head footage.

Narration is spoken Korean generated via Google Cloud TTS Chirp 3 HD (`ko-KR-Chirp3-HD-Enceladus`). Every run is a full visual (`mode: 'fv'`), rendered with HyperFrames in the neutral stage theme ([references/theme.md](theme.md)). Audio consists of the narration alone, mastered to −14 LUFS integrated / true peak ≤ −1 dBTP.

Conventions:
- `SKILL`: this skill's folder.
- `P`: the project folder (it may be empty).
- `W`: `P/work`. Every command runs with `W` as the working directory.
- `PY`: `../.venv/Scripts/python.exe` (Windows), or `../.venv/bin/python` elsewhere.
- `NODE`: Node.js (v22+).
- Shorts are named `s1`, `s2`, and so on. Graphic runs are named `<sk>_r<run index>`.

Contents: [0 Setup](#0-setup) · [1 Research & Plan](#1-research-and-plan) · [2 Prep](#2-prep-placeholder-timeline) · [3 Graphics Fan-out](#3-graphics-fan-out) · [4 Review Copy](#4-review-copy-the-single-user-gate) · [5 Recording & Re-timing](#5-recording-and-re-timing) · [6 Final Assembly](#6-final-assembly-and-delivery) · [7 Incremental Edits](#7-incremental-edits) · [8 Environment](#8-environment-and-windows-notes)

---

## 0. Setup

```bash
bash "$SKILL/scripts/setup.sh" "$P"       # default: current directory
```

Setup creates:
- `P/.venv`: local virtual environment containing `numpy`, `scipy`, `soundfile`, `pyloudnorm`, `opencv-python`, `pillow`, and `fonttools`.
- `SKILL/assets/fonts/PretendardVariable.ttf`: variable Korean typeface (SIL OFL 1.1), downloaded and verified against its sha256 checksum.
- `P/work/`: working directory containing `scripts/`, `scripts/narration/` (TTS and wave tools), `gfx/` (HyperFrames engine), `fonts/`, and `project.json`.
- `P/edit/`: destination for final deliverables.
- Checks Google Cloud authentication (`gcloud auth print-access-token`) for Chirp 3 HD and prints a `🔑` status line.

---

## 1. Research and Plan

1. **Input**: a topic, raw materials, notes, or a finished script.
   - If the user provides a script, use it word for word.
   - If writing the script autonomously, follow [references/script-writing.md](script-writing.md) (spoken Korean, ~75% ~니다 / ~25% ~요, one idea and at most one number per sentence, topic-change cushions).
2. **Research subagent**:
   - Fact-checks every claim and number against 2+ sources (`research.md`).
   - Captures source web pages, docs, pricing tables, and dashboards as 2x PNGs into `work/captures/` (`captures/index.json`, `captures/facts.json`).
   - Downloads official product/project logos into `work/captures/logos/`.
3. **Plan in `shorts.json`**:
   - 1–5 shorts, each structured around one question answered with the story spine (hook, turns, answer, a three-sentence ending; script-writing.md).
   - Per short:
     - `title`: short title.
     - `cover`: 1–2 title lines for the frame-0 glass card (centred at y ~432).
     - `accent`: `'azure'` (default), `'ember'` (limits/costs), `'mint'` (success), or `'iris'`.
     - `highlights`: list of 1–3 word phrases for glass keyword chips (longest first).
     - `lines`: list of dialogue lines:
       - `id`: cue identifier (`L1`, `L2`, etc.).
       - `text`: exact display text in Korean.
       - `scene`: visual category (`capture`, `ui`, `diagram`, `number`, `logo`).
       - `switches`: optional list of `[{"at": "<phrase>", "scene": "..."}]` to cut visual scene mid-cue.
       - `caption`: set to `'top'` (y 180–360) if the picture's content sits low; defaults to the caption band (y 1410–1550).
4. **Visual rotation rules**:
   - Every run is a full visual (`mode: 'fv'`). No cameras, no splits, no face mattes.
   - No run exceeds ~8 s.
   - Two consecutive runs must never share the same scene type.
   - The hook (`r0`) is the strongest visual (a key number, real capture, or striking result).
   - The short ends on the last line and its end hold (`tail`, 1.5 s). No CTA card, no "watch full video" prompt, no comment box.

---

## 2. Prep (Placeholder Timeline)

```bash
cd "$W"
bash scripts/prep.sh s1 [s2 ...]         # all shorts in shorts.json if none specified
```

What `prep.sh` executes:
1. `narration_init.py`: writes `narration/<sk>/script.json` from `shorts.json` lines (defaults: Google Chirp 3 HD `ko-KR-Chirp3-HD-Enceladus`, `leadIn 0.3`, `gap 0.12`, `tail 1.5`).
2. `scripts/narration/tts.mjs`: creates silent placeholder cues in `narration/<sk>/js/cues.js` with estimated lengths (API calls are blocked without `--approved`).
3. `scripts/narration/sync.mjs`: writes `narration/<sk>/js/sync.js`.
4. `scripts/timeline.py`: generates `cut.json` (runs, word boundaries, `END`) and `<sk>/voice.wav` (silent 48 kHz audio). Word timings are estimated from character positions with script-to-motion weights. Run boundaries snap down to the frame (`fr(t) = math.floor(t * FPS) / FPS`) so audio never leads into the previous run.
5. `compose.py <sk> --events-only`: writes `<sk>/captions.json` (1–3 어절 chunks, highlight chips).

Then print the run brief:
```bash
$PY scripts/brief_runs.py s1
```
This lists every run, its scene, duration, and words with run-relative start times (`~` indicates character-position estimates). Copy [examples/GFX_BRIEF_template.md](../examples/GFX_BRIEF_template.md) to `GFX_BRIEF.md`, paste the output under `## Compositions`, and add one `Idea:` line per run.

---

## 3. Graphics Fan-out

Spawn 2–4 long-lived graphics subagents by tag (`a`, `b`, ...), grouped by topic or visual style.
Each tag owns:
- `scripts/prep_assets_<tag>.py`: crops stills/clips into `gfx/assets/<tag>_*` and writes `gfx/asset_dims_<tag>.json`.
- `scripts/gfx_<tag>.py`: builds compositions using `scripts/build_gfx_common.py`.

```bash
$PY scripts/build_gfx.py [tag]              # builds gfx/<rid>.html and gfx/thumbs.json
$PY scripts/preview.py                      # work/index.html with the new compositions
python3 render.py --screenshot --run s1_r3 --gapframe 20 --fast --jobs 3   # PNG contact sheet of one run, captions on
```

Graphics rules ([references/graphics.md](graphics.md)):
- Every composition is `mode: 'fv'` at 1080×1920.
- **Timing**: ALWAYS anchor moves, steps, and landings on Korean phrases with `W(ws, '<phrase>')`, never on hardcoded seconds.
- **Frame 0 of r0**: keep all elements below y 620 so the glass title cover card (centred at y ~432) remains unobstructed.
- **Pretendard font**: use Pretendard for all Korean text; Geist Mono is reserved for uppercase Latin labels (`.label`).
- Inspect the contact sheet (`chk/shot_<sk>_<from>-<to>.png`) to verify typography (≥ 30 px), alignment and the zones.
- **No MP4 before the review is complete**: `render_draft.sh`, `render_full.sh` and `finish.sh` refuse to run unless
  render.py calls them, and render.py is the user's, after the review.

---

### 3b. Look development, visual review, defect check (references/elevate.md, references/visual-review.md)
Hero run per section first → compare with the approved look + `defect_check.py lookdev` (Gemini Neon, defects only) →
the rest of the build → the frame-by-frame motion check (`defect_check.py motion`) → the whole check
(`defect_check.py whole`, up to 3 rounds) → only then the preview goes to the user. No score gates anything. No MP4
anywhere in this.

## 4. Browser Preview (The Single User Gate)

```bash
$PY scripts/preview.py            # -> work/index.html (every short; ?s=s2 picks one)
```

`index.html` stacks each run's live composition (`gfx/<sk>_r<i>.html`) as an iframe and drives it by the narration's
clock (`narration/<sk>/audio/narration.mp3`, silent before recording), with the captions, keyword chips and cover drawn
where `compose.py` puts them. It opens from `file://` (the page sends each composition its time by `postMessage`; the
listener is in every page `build_gfx_common.page()` writes). The player is script-to-motion's (its look and keys):
Space play/pause · ←/→ 0.5 s, Shift 5 s · `.`/`,` one frame · 0/Home start · R from the top at 1× · Shift+`>`/`<` speed
0.25×–3× · F fullscreen · C captions · S copy "time / length [cue · run +time] line" · A copy the screenshot command for
±1 s · D the debug bar (click to seek; Shift + mouse move scrubs). No motion blur (that comes from the render);
otherwise it is the short. A graphics fix shows after `build_gfx.py` and a reload.

Check it yourself before handing it over: a contact sheet of any stretch, shot from the page with headless Chrome
(no render, no extra install; the A key copies exactly this for the moment on screen):
```bash
python3 render.py --screenshot --short s1 --from 12.0 --to 14.0 --gapframe 10 --fast --jobs 4   # -> chk/shot_s1_12.00-14.00.png
```

**User Gate**: hand over `work/index.html` and `narration/s1/script.txt` and ask whether to record. This is the **only
question** the skill asks. Then the review loop on the review desk (`scripts/review_server.py`, SKILL.md step 5): the user reviews index.html, you fix and rebuild the preview, until the
user says the review is complete. No MP4 before that.

---

## 5. Recording and Re-timing

Once the user approves recording:

1. **Record the audio**:
   ```bash
   node scripts/narration/tts.mjs narration/s1 --approved
   ```
   Calls Google Cloud TTS Chirp 3 HD (`ko-KR-Chirp3-HD-Enceladus`). Takes are cached in `narration/s1/.tts-cache/`.
   Up to 5 lines go in one request (`"paragraphs": 5`) so they share one pace; tts.mjs prints 🧩 proposed split times.
   Confirm them with step 3's `phrasing-check.mjs` (each cue starts and ends with its own words), fix a wrong one with
   `wave.mjs`, and write them into `narration/s1/script.json` `"splits"` (references/narration.md, Google §6).

2. **Review takes and set cuts**:
   ```bash
   node scripts/narration/wave.mjs narration/s1 --unreviewed
   ```
   Inspect RMS and ZCR numbers. `autocut.py` suggests draft cuts; write each take's `"cut"` into `narration/s1/script.json` (`"ranges": []` if nothing to cut).

3. **Check phrasing**:
   ```bash
   node scripts/narration/phrasing-check.mjs narration/s1
   ```
   Examines pause placement via STT. If Chirp placed an unnatural pause, insert `[pause short]` in the line's `say` **in
   `shorts.json`** (prep.sh copies `text` and `say` from there into script.json; an edit made only in script.json is
   overwritten), run `bash scripts/prep.sh s1`, and re-record that cue (a fix of a wrong break found right after the
   recording the user approved counts as their decision; any other re-take needs their OK first):
   ```bash
   node scripts/narration/tts.mjs narration/s1 --only <id> --approved
   ```

4. **Verify silence rules**:
   Run `wave.mjs narration/s1` across the full track. Ensure no silence gap meets or exceeds 0.4 s (excluding the 1.5 s `tail` hold).

5. **Set phrase timing (`at`)**:
   For every keyword chip in `shorts.json` `highlights` and every phrase a graphic lands on, measure the exact time in `wave.mjs` (`--cue <id> --step 0.01`) and enter it in `script.json` `"at"`.

6. **Update sync, timeline, and graphics**:
   ```bash
   node scripts/narration/sync.mjs narration/s1
   bash scripts/prep.sh s1
   $PY scripts/build_gfx.py
   ```
   `prep.sh` updates `cut.json` and `<sk>/voice.wav`. Because graphics timing uses `W(ws, '<phrase>')`, re-running `build_gfx.py` automatically pulls in the new recorded times.

---

## 6. Final Assembly and Delivery (the user runs render.py)

After recording: `prep.sh`, `build_gfx.py`, `preview.py`; hand over `work/index.html` again. The user renders:
```bash
python3 work/render.py s1 01 slug-name     # = render_full.sh for every stale composition, then finish.sh s1 01 slug-name
python3 work/render.py s1 --fps 60         # graphics capture rate: 60 (default; no blend), 120 (2 per frame, blended), 240 (4, 3 blended)
                                           # a project's default can be set in project.json "render_fps"
python3 work/render.py --list              # which shorts are ready
```
The two steps it runs, for reference (run them yourself only when the user asks):

1. **Render full graphics (60 fps capture by default)**:
   ```bash
   bash scripts/render_full.sh s1_r0 s1_r1 ...
   ```
   Renders lossless PNG sequences at the capture rate (60 by default; 120 or 240 are blended down to 60 fps) into `gfx/out60/<rid>.mp4`. Throttled by `RENDER_SLOTS` (3) × `HF_WORKERS` (8) browsers.

2. **Assemble and package**:
   ```bash
   bash scripts/finish.sh s1 01 slug-name
   ```
   What `finish.sh` executes:
   - `check_text.py`: validates on-screen Korean text.
   - `check_narration.py`: confirms no placeholders, no unreviewed takes, matching sync, and no unanchored keyword chips.
   - `mix.py`: masters `<sk>/voice.wav` to −14.0 LUFS integrated and true peak ≤ −1.0 dBTP (gain + limiter only) -> `<sk>/stems/voice.wav`, `<sk>/mix.wav`.
   - `compose.py --segments --no-concat`: renders each run segment in parallel, cached by `.key` files.
   - `compose.py --concat`: stream-copies segments with `mix.wav` -> `<sk>/final_video.mp4`.
   - `thumbnail.py`: renders clean thumbnail candidate frames into `chk/<sk>_thumbs.png`.
   - `verify_final.py`: verifies 1080×1920, 60 fps, AAC 48 kHz stereo, loudness, and writes `chk/<sk>_final.png`.
   - Copies deliverables to `../edit/short-01_slug-name/` (`final.mp4`, `stems/voice.wav`, `script.txt`).

3. **Select thumbnail**:
   Inspect `chk/<sk>_thumbs.png` (displays candidates at 1/3 size and Shorts-feed size with Instagram 4:5 guide). Pick the best frame:
   ```bash
   $PY scripts/thumbnail.py s1 --pick <time_seconds> 01 slug-name
   ```
   Outputs `../edit/short-01_slug-name/thumbnail.jpg` (1080×1920 JPEG under 2 MB) and `thumbnail.json`.

4. **Publishing copy and reports**:
   - Write `../edit/short-01_slug-name/report.md` (TTS provider, voice, take IDs, cuts, `at` points, loudness, mix stats from `$PY scripts/report_data.py s1`).
   - Write `../edit/PUBLISH.md` (Korean title, description, and hashtags for YouTube Shorts, TikTok, and Instagram Reels; no external community links, no full-video CTA, no related video).
   - Validate publishing package:
     ```bash
     $PY scripts/check_publish.py
     ```

Deliverables in `edit/short-NN_<slug>/`:
- `final.mp4`: 1080×1920, 60 fps, H.264 high quality, AAC 48 kHz stereo.
- `thumbnail.jpg`: clean 1080×1920 cover image (< 2 MB).
- `stems/voice.wav`: 48 kHz stereo dialogue track before mastering.
- `script.txt`: full spoken script.
- `report.md`: production metrics and audit report.
- `../edit/PUBLISH.md`: multi-platform posting copy.

---

## 7. Incremental Edits

Change the smallest component and re-run only what it affects. `finish.sh` caches unchanged segments:

| Change | Re-run Steps | What Re-renders |
|---|---|---|
| **Script wording (before recording)** | Edit `shorts.json` → `bash scripts/prep.sh <sk>` → update `W()` if phrases changed → `bash scripts/finish.sh <sk> --draft` | Only modified runs re-render. |
| **Script wording (after recording)** | Edit `text` / `say` in `shorts.json` → `prep.sh` (the cue becomes a silent placeholder) → **ask the user**; on their OK `tts.mjs narration/<sk> --approved --only <id>` → `wave.mjs` (set `cut`, `at`) → `prep.sh` → `build_gfx.py` → `render_full.sh` (the runs from that cue on) → `finish.sh` | The line's paragraph (up to 5 lines) re-recorded; the runs after it move, so their graphics re-render. |
| **Re-take / phrasing adjustment** | Edit `say` in `shorts.json` (`[pause short]`, joined words) → `prep.sh` → `tts.mjs --approved --only <id>` (user's report or OK) → `wave.mjs` (set `cut`, `at`) → `prep.sh` → `build_gfx.py` → `render_full.sh` (changed runs) → `finish.sh` | The line's paragraph (up to 5 lines) re-recorded: every line in it needs new cuts and `at`, and the user hears them again; graphics re-timed by their phrase anchors. |
| **Cut or `at` adjustment** | Edit `cut` / `at` in `narration/<sk>/script.json` (kept across prep.sh runs) → `prep.sh` (runs tts.mjs and sync.mjs) → `build_gfx.py` → `render_full.sh` for runs whose length or anchors changed → `finish.sh` | Timeline updates; only changed segments re-composite. |
| **Graphics visual or animation fix** | Edit `scripts/gfx_<tag>.py` → `$PY scripts/build_gfx.py <tag>` → `bash scripts/render_full.sh <rid>` → `bash scripts/finish.sh <sk> NN slug` | Only that graphic and its composite segment re-render (~30–60 s). |
| **Captions, highlights, or cover** | Edit `shorts.json` → `bash scripts/prep.sh <sk>` (or `$PY scripts/compose.py <sk> --events-only`) → `bash scripts/finish.sh <sk> NN slug` | No graphics re-render; only composite segments with changed captions re-render. |
| **Change thumbnail pick** | `$PY scripts/thumbnail.py <sk> --pick <new_time> NN slug` | Instant JPEG export. No video re-render. |
| **Publishing metadata** | Edit `../edit/PUBLISH.md` → `$PY scripts/check_publish.py` | Text edit only. No rendering. |

---

## 8. Environment and Windows Notes

- **UTF-8 everywhere**: Python scripts default to UTF-8 (`PYTHONUTF8=1` exported in all shell scripts). Always open JSON and text files with `encoding='utf-8'` to prevent Korean characters from corrupting into mojibake. `check_text.py` halts assembly if corrupted characters are detected.
- **Git Bash syntax**: Never embed heredocs containing real newlines or Korean characters in Git Bash commands. Use dedicated Python scripts or file tools.
- **Subshell backgrounding**: When running background commands with directory changes, use subshells: `(cd work && command1 && command2) &`.
- **Frame pipes**: Never set `bufsize=10**8` on FFmpeg raw video pipes; default pipe buffers read at ~1.6 GB/s, whereas oversized buffers degrade throughput to ~130 MB/s on Windows.
- **Chrome browser pool**: Both `render_draft.sh` and `render_full.sh` set `PRODUCER_ENABLE_BROWSER_POOL=false` to assign each HyperFrames worker its own Chrome instance, preventing screenshot bottlenecks.
