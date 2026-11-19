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
   - 1–5 shorts, each structured around "one question, one answer".
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
       - `caption`: set to `'top'` (y 365–634) if lower third contains important visual details; defaults to lower third (y 1290–1560).
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
bash scripts/render_draft.sh s1_r0 s1_r1    # 10 fps draft MP4 + contact sheet chk/<rid>_sheet.png
```

Graphics rules ([references/graphics.md](graphics.md)):
- Every composition is `mode: 'fv'` at 1080×1920.
- **Timing**: ALWAYS anchor moves, steps, and landings on Korean phrases with `W(ws, '<phrase>')`, never on hardcoded seconds.
- **Frame 0 of r0**: keep all elements below y 620 so the glass title cover card (centred at y ~432) remains unobstructed.
- **Pretendard font**: use Pretendard for all Korean text; Geist Mono is reserved for uppercase Latin labels (`.label`).
- Inspect `chk/<rid>_sheet.png` to verify typography (≥ 30 px), alignment, and layout bounds before full renders.

---

## 4. Review Copy (The Single User Gate)

```bash
bash scripts/finish.sh s1 --draft
```

What `finish.sh --draft` does:
1. `check_text.py`: verifies that all text is valid UTF-8 without mojibake.
2. `check_narration.py s1 --draft`: verifies narration state, permitting silent placeholder cues.
3. `mix.py s1`: outputs silent `<sk>/mix.wav`.
4. `compose.py s1 --segments --draft`: renders segments using 10 fps draft graphics held to 60 fps with captions and cover.
5. `compose.py s1 --concat --draft`: produces `chk/s1_draft.mp4`.

**User Gate**: Hand over `chk/s1_draft.mp4` and `narration/s1/script.txt` to the user and ask:
> "Draft review copy and script are ready. Shall I proceed with recording the voiceover?"

This is the **only question** the skill asks the user.

---

## 5. Recording and Re-timing

Once the user approves recording:

1. **Record the audio**:
   ```bash
   node scripts/narration/tts.mjs narration/s1 --approved
   ```
   Calls Google Cloud TTS Chirp 3 HD (`ko-KR-Chirp3-HD-Enceladus`). Takes are cached in `narration/s1/.tts-cache/`.

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

## 6. Final Assembly and Delivery

1. **Render full graphics (240 fps)**:
   ```bash
   bash scripts/render_full.sh s1_r0 s1_r1 ...
   ```
   Renders lossless 240 fps PNG sequences and blends them to 60 fps motion-blurred video in `gfx/out60/<rid>.mp4`. Throttled by `RENDER_SLOTS` (3) × `HF_WORKERS` (8) browsers.

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
| **Script wording (after recording)** | Edit `text` / `say` in `shorts.json` → `prep.sh` (the cue becomes a silent placeholder) → **ask the user**; on their OK `tts.mjs narration/<sk> --approved --only <id>` → `wave.mjs` (set `cut`, `at`) → `prep.sh` → `build_gfx.py` → `render_full.sh` (the runs from that cue on) → `finish.sh` | One take re-recorded; the runs after it move, so their graphics re-render. |
| **Re-take / phrasing adjustment** | Edit `say` in `shorts.json` (`[pause short]`, joined words) → `prep.sh` → `tts.mjs --approved --only <id>` (user's report or OK) → `wave.mjs` (set `cut`, `at`) → `prep.sh` → `build_gfx.py` → `render_full.sh` (changed runs) → `finish.sh` | One take re-recorded; graphics re-timed by their phrase anchors. |
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
