# Speed and parallelism

Target: produce the first draft review copy in 15–20 minutes, iterate quickly on 10 fps drafts, and complete final 240 fps rendering and assembly within 3–5 minutes once the voiceover is recorded. Any incremental edit after that should take under a minute.

Speed in this skill comes from architecture, not raw hardware:
1. **Building on silent placeholders with 10 fps drafts** so visual development never waits on audio or heavy renders.
2. **240 fps motion-blurred rendering only once**, after the user approves recording and locks the timeline.
3. **Automatic re-timing** via phrase anchors (`W()`) so recording never requires rewriting graphics code.
4. **Cached segment compositing** and **parallel worker pools**.

---

## 1. Reuse Before You Build
- Use the skill's scripts in `work/scripts/`: narration tools (`scripts/narration/`), timeline generator (`timeline.py`), HyperFrames world engine (`gfx/engine.js`), compositor (`compose.py`), mastering (`mix.py`), and thumbnail extractor (`thumbnail.py`).
- Keep per-project and per-short data in `shorts.json` and `narration/<sk>/script.json`, never hardcoded in scripts.

---

## 2. Two-Phase Execution: Drafts First, Heavy Renders Once

### Phase 1: Silent Placeholders and 10 fps Drafts
- Never call the TTS API or render 240 fps during initial planning and visual development.
- `prep.sh` creates silent placeholder cues with estimated lengths based on character position.
- Graphics subagents write compositions and render drafts with `bash scripts/render_draft.sh <rid...>`. A 10 fps draft renders in ~3–5 seconds and produces a contact sheet (`chk/<rid>_sheet.png`) for instant visual verification.
- Assemble the draft review copy with `bash scripts/finish.sh s1 --draft`. This produces `chk/s1_draft.mp4` (10 fps draft graphics held to 60 fps, silent, with captions and cover).
- Hand over the draft review copy and `narration/s1/script.txt` to the user to decide whether to record.

### Phase 2: Recording, Re-timing, and 240 fps Rendering
- Once the user approves recording, run `node scripts/narration/tts.mjs narration/s1 --approved`.
- Read take numbers with `wave.mjs --unreviewed`, set `"cut"` and phrase `"at"` times, then run `prep.sh`.
- Re-run `$PY scripts/build_gfx.py`. Because all graphics timing is anchored on phrases using `W(ws, '<phrase>')`, every move and landing re-times automatically to the real voiceover.
- Render at 240 fps (`bash scripts/render_full.sh <rid...>`) **only now**, when the timeline is final.

---

## 3. Parallel Subagents (Few Long-Lived Agents)

- Graphics work should be handled by 2–4 long-lived subagents by tag (`a`, `b`, ...), grouped by visual style or topic (e.g. real web captures, architecture diagrams, continuous world sequences). Never spawn one agent per composition.
- Each agent owns its assets (`scripts/prep_assets_<tag>.py`, `gfx/asset_dims_<tag>.json`) and its module (`scripts/gfx_<tag>.py`).
- Each subagent follows the cycle for all its compositions:
  1. Write and lint composition configs.
  2. Render 10 fps drafts with `render_draft.sh`.
  3. Inspect contact sheets (`chk/<rid>_sheet.png`) and fix issues.
  4. After recording approval, trigger `render_full.sh`.
- **Machine-wide throttling**: `render_full.sh` manages a slot budget across all running agents using lock files in `gfx/.render_slots`: at most `RENDER_SLOTS` (3) renders concurrently, with `HF_WORKERS` (8) Chrome browsers each. Multiple agents can call `render_full.sh` safely without overwhelming system resources.
- **Dedicated browser per worker**: Both `render_draft.sh` and `render_full.sh` export `PRODUCER_ENABLE_BROWSER_POOL=false`. This gives each worker its own Chrome instance, bypassing Chrome's single-GPU-process bottleneck during PNG capture (measuring 41+ fps at 8 workers vs ~15 fps when pooled).

---

## 4. Parallel Segment Compositing and Input Caching

- `compose.py s1 --segments` renders each run's segment in its own parallel process (`--jobs N`).
- **Input caching (`.key` files)**: For each run, `compose.py` hashes its inputs:
  - Run metadata (duration, scene, bounds).
  - Graphic video file size and modification timestamp (`gfx/out60/<sk>_r<i>.mp4` or draft equivalent).
  - Captions and highlight chips within the run.
  - Frame-0 cover card (for run 0).
  - Encoder settings and composite code hash.
- If a run's `.key` matches, segment rendering is skipped completely.
- **Stream-copy concatenation**: Once segments are ready, `compose.py --concat` stream-copies the H.264 video segments together and muxes the mastered AAC audio in seconds.
- **Frame seeking for previews and thumbnails**: `compose.py --preview <t>` and `thumbnail.py` seek frame-accurately directly to the required timestamp (`-ss t -i ... -frames:v 1`). Whole streams are never decoded to extract spot frames.

---

## 5. Background Parallelism in Assembly

`finish.sh` pipelines tasks concurrently:
1. `check_text.py` and `check_narration.py` run first as fast gates.
2. `mix.py` (gain adjustment + true peak limiting) runs in the background while `compose.py --segments` renders any pending visual segments.
3. `thumbnail.py` renders candidate clean frames in parallel while `compose.py --concat` joins the final segments.
4. `verify_final.py` checks video and audio streams on the assembled file.

---

## 6. Incremental Edits

Re-run only the specific stage affected by a change:
- **Graphic appearance or motion**: Edit `scripts/gfx_<tag>.py` → `build_gfx.py <tag>` → `render_full.sh <rid>` → `finish.sh`. Only that single run's segment re-composites.
- **Captions, highlight chips, or cover**: Edit `shorts.json` → `prep.sh` → `finish.sh`. Only runs with changed text re-render (graphics are untouched).
- **TTS take or phrasing**: Re-record only that cue (`tts.mjs --only <id> --approved`), re-cut, re-sync, and re-run `prep.sh`. Graphics re-time automatically.
- **Thumbnail change**: `$PY scripts/thumbnail.py s1 --pick <t> NN slug` extracts the new JPEG instantly without re-rendering video.

---

## 7. Check Cheaply, Fail Fast

- **Gate before rendering**: `check_text.py` catches text corruption or missing fonts, and `check_narration.py` catches stale sync or unreviewed takes before launching renders.
- **Contact sheets at 10 fps**: Verify layout, alignment, and type scale (≥ 30 px) on `chk/<rid>_sheet.png` during the draft stage. Never send an unverified draft to 240 fps full render.
