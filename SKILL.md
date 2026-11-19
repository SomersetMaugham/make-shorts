---
name: create-video-shorts
description: Make finished, ready-to-post 9:16 shorts (YouTube Shorts, Instagram Reels, TikTok) from a topic, material or a script, with no recording needed - researches and fact-checks, writes spoken-Korean narration by script-to-motion's rules, narrates it with script-to-motion's TTS tools (Google Chirp 3 HD Enceladus; recorded only when the user says so, after reviewing a silent draft), lays every run as a full-frame HyperFrames graphic in the stage theme (glass cards, real source captures, camera moves, motion blur) timed to the narration's phrases, burns in Korean captions with glass keyword chips and a cover, masters the narration to -14 LUFS, and delivers 1080x1920 60 fps MP4s with a thumbnail, a report and a Korean publishing package for YouTube Shorts, TikTok and Instagram Reels. Use it whenever the user wants shorts, reels, TikToks or vertical videos about a topic, an article, notes or a script ("이 내용으로 쇼츠 만들어줘", "릴스 몇 개 뽑아줘"), or wants to fix or re-edit a short made this way, even if they never mention a skill.
---

# create-video-shorts

You make finished vertical shorts from a topic, material or a script. There is no source video: every picture is a
graphic you build and the only sound is narration. Everything is code: Python, Node, ffmpeg and HyperFrames.

**The quality contract is `references/editing-spec.md`. Read all of it before planning anything.** It covers the
research and the script, the narration, the timeline and runs, the graphics, captions and cover, the sound, the report,
the publishing package and the thumbnail. Where the user's request differs from the spec, the user wins. Speed comes
from parallelism and incremental edits (`references/speed.md`), never from dropping a rule.

**Everything the viewer or the user reads or hears is Korean by default** (narration, captions, cover, on-screen copy,
report, publishing copy). Another language only when the user asks.

> **STOP before you write or change a single word of narration or on-screen copy (script-to-motion's absolute rule).**
> A viewer hears each line once, in order, at speaking pace, and knows nothing you know: not the research, not the
> files, not the cue ids, not the chat. For every line — first draft, one-word fix, batch edit — check who / what /
> when / which is inside the line, that every name and term was told, that every connective points at the line before,
> that it stands on sound alone, and that every claim is in the record. A short answers **one question**: no recap, no
> second topic. Then the seam pass, the internal-name list and the **cold-listener review** by a subagent that sees only
> `script.txt`. Never trust your own reading of your own line. The full rules: `references/script-writing.md`.

## The narration is script-to-motion's (read `references/narration.md` before step 3)
- Google Cloud TTS Chirp 3 HD, voice `ko-KR-Chirp3-HD-Enceladus` (gcloud sign-in, no key); Fish Audio or edge-tts only
  when the user asks. Speed is always 1.
- **Recording waits for the user.** Build every short completely on silent placeholders, hand over the review copy and
  the script, and ask whether to record. That is the only question you ask; every other call is yours (log it).
- Every take is kept exactly as returned. **No code decides where silence or a word is**: you read each take with
  `wave.mjs` and write its `cut` and the `at` times of the phrases that must land on a word. No dead air (0.4 s or more).
- Never transcribe a take to judge it; the one allowed use of speech-to-text is `phrasing-check.mjs` (where Chirp's
  pauses fall).
- No music, no sound effects. `mix.py` only masters the narration to -14 LUFS / -1 dBTP.

## Inputs and defaults
- **The material:** a topic, an article, notes, links, a planning doc or a finished script. The user's script is used
  word for word (only `say` gets spoken forms). Files they give (logos, screenshots) go to `work/gfx/assets/`.
- **The folder:** the user's, otherwise the current folder. It may be empty.
- **How many shorts:** follow the user; otherwise the strongest self-contained questions in the material, usually 3-5,
  never more than 5 (spec "INPUTS").
- **Cover title:** the user's, otherwise written from the hook.
- **No voice possible** (the user wants none, or gcloud can't sign in and they don't log in): `"narration": false` in the
  short's script.json; key lines on screen; say so in the hand-off.

## Workflow
Commands in detail: `references/pipeline.md`. `SKILL` is this skill's folder; everything runs inside `<folder>/work/`.

1. **Setup:** `bash SKILL/scripts/setup.sh <folder>` creates `.venv`, `work/` (scripts, the narration tools, the
   graphics engine, fonts) and `edit/`, downloads Pretendard once, and prints a 🔑 line for the gcloud sign-in. Needs
   ffmpeg, Node 22+ and uv.
2. **Research and the script, in parallel:** brief the **research subagent** (fact-check every figure against 2+ sources,
   capture the real source pages into `captures/` with an index and the fact check). Meanwhile pick the shorts and write
   their narration (`references/script-writing.md`; the gates and the cold-listener review before any line is final).
   Write `shorts.json`: per short `title`, `cover`, `highlights`, `accent`, and `lines` (`id`, `text`, `say`, `scene`,
   optional `switches`, `gapAfter`, `caption`). Example: `examples/shorts_example.json`.
3. **Timeline on placeholders:** `bash scripts/prep.sh` runs `narration_init.py` → `tts.mjs` (records nothing: silent
   placeholders with estimated lengths) → `sync.mjs` → `timeline.py` (cut.json, the runs) → captions. Read the runs it
   prints: no run over ~8 s, no two neighbours with the same scene kind (spec 3).
4. **Graphics, in parallel:** fill in `examples/GFX_BRIEF_template.md` as `GFX_BRIEF.md` and paste
   `$PY scripts/brief_runs.py` under its Compositions heading with one idea per composition. Start a FEW LONG-LIVED
   graphics agents (2-4, one per 1-2 shorts, grouped by kind: real sources, concept diagrams, one continuous world), each
   with a tag. Each follows `references/graphics.md` and `examples/gfx_s1.py`, anchors every time on a phrase
   (`W(ws, '구절')`), marks `thumb` windows, and renders 10 fps drafts with `render_draft.sh` (draft + contact sheet).
   No full renders yet: the recording will re-time everything.
5. **Preview in the browser:** `$PY scripts/preview.py` writes `work/index.html`: every short playing in Chrome with
   its live compositions, captions, chips and cover on the narration's clock (silent before recording). No render is
   needed, so a graphics fix shows after `build_gfx.py` and a reload. Check it yourself (headless Chrome with `?t=` and
   `&still`, pipeline.md), then hand the user `work/index.html` and `narration/<sk>/script.txt`, list the lines to listen
   to first once recorded, and **ask whether to record**.
6. **Record (on the user's word):** `node scripts/narration/tts.mjs narration/<sk> --approved`; then the after-recording
   pass (`references/narration.md`): read every take (`wave.mjs narration/<sk> --unreviewed`; `autocut.py` drafts a cut
   you correct), set each `cut` (in `narration/<sk>/script.json`), run `phrasing-check.mjs` and fix wrong breaks with
   `[pause short]` in the line's `say` **in shorts.json** (prep.sh copies it over) and `--only` re-takes, set `at` for every keyword chip and every phrase a graphic lands on, read the whole sound for dead air.
   Then `bash scripts/prep.sh <sk>`, `$PY scripts/build_gfx.py <tags>` and `$PY scripts/preview.py`: the runs, every
   graphic and the preview follow the takes. Hand over `work/index.html` again, now with the voice.
7. **The MP4 is the user's to render:** `python3 work/render.py s1 NN slug` (a copy of `scripts/render.py`): every
   composition at 240 fps with motion blur (`render_full.sh`, only those newer than their render), then `finish.sh`
   (check_text, check_narration, the master and the segments, concat, `verify_final.py`, thumbnail candidates, the copy
   into `edit/short-NN_<slug>/`). Don't run it yourself unless the user asks; prepare everything it needs and say the
   command. `finish.sh <sk> --draft` (a silent MP4 from the 10 fps drafts) is still there for when a file is wanted.
8. **Deliver (before the render):** `edit/PUBLISH.md` with the Korean copy for every short (spec 8b;
   `$PY scripts/check_publish.py` must pass) and the report's narration, script and graphics parts. **After the user's
   render:** look at `chk/<sk>_final.png` and `chk/<sk>_thumbs.png`, pick the thumbnail
   (`$PY scripts/thumbnail.py <sk> --pick <t> NN slug`) and finish `report.md` with the numbers of `report_data.py <sk>`.
   Tell the user which lines to listen to.
9. **Edits** are incremental: a wording change → `prep.sh` (the cue becomes a placeholder until the user OKs a re-take);
   a cut or `at` → `prep.sh`; a graphic → `build_gfx.py`; then `preview.py` and a reload. The next `render.py`
   re-renders only the compositions and segments whose inputs changed (pipeline.md "Edits").

## Things that are easy to get wrong
Read `references/lessons.md` before improvising. The biggest ones:
- **Recording without the user's word.** Never run `--approved` on your own, and never on a line that hasn't passed the
  first-time-listener gates.
- **Deciding silence in code.** Cuts and phrase times are yours, read off `wave.mjs`; `autocut.py` is only a draft.
- **Hard-coded seconds in graphics.** They break the moment the narration is recorded. Anchor on phrases.
- **Chips at estimated times.** In a recorded short every chip's phrase needs an `at` (check_narration.py warns).
- **Rendering the MP4 yourself.** The user checks `index.html` and renders with `render.py`; full renders by the agent
  only when asked, and never before the recording fixes the timeline.
- **Korean in a Latin-only font.** Figtree, Geist Mono and Poppins have no Hangul; everything on screen is Pretendard.
- **Frame 0:** the hero is already on screen when a run cuts in; only supporting cards land later. `*_r0` keeps the top
  620 px clear for the cover.
- **Brands:** logos and product names only when the narration names them.
- **Look at the finished frames,** not just the logs: drafts, contact sheets and full-resolution frames of anything with
  text.

## Files
- `scripts/`: the pipeline, run inside `work/`. Stage scripts: `setup.sh`, `prep.sh`, `render_draft.sh`,
  `render_full.sh`, `finish.sh`, and `render.py` (the user's MP4 render; setup.sh copies it into `work/`). Python:
  `preview.py` (`work/index.html`, the browser preview), `narration_init.py` (shorts.json → narration folders), `timeline.py` (cues →
  cut.json + voice.wav), `brief_runs.py`, `build_gfx.py` / `build_gfx_common.py` (compositions, `W()` phrase anchors),
  `compose.py` (captions, chips, cover, segments, `--draft`), `check_text.py`, `check_narration.py`, `mix.py`,
  `verify_final.py`, `thumbnail.py`, `report_data.py`, `check_publish.py`, `draftsheet.py`, `sheet.py`, `config.py`,
  `init_project.py`.
- `scripts/narration/`: script-to-motion's TTS tools (`tts.mjs`, `wave.mjs`, `sync.mjs`, `phrasing-check.mjs`,
  `autocut.py`, `lib/`), with `SOURCE.md` (provenance, local changes) and `sync_upstream.sh` (reports upstream changes).
- `assets/gfx/`: `engine.js` (world camera, depth of field, motion blur, captures, the stage theme), GSAP and the
  HyperFrames project files. `assets/fonts/`: Pretendard (downloaded by setup.sh), Geist Mono, and the Latin fonts of
  the old compositions.
- `examples/`: `shorts_example.json` (a plan), `GFX_BRIEF_template.md`, `gfx_s1.py` (full-visual compositions with
  phrase anchors).
- `references/`: `editing-spec.md` (the contract), `narration.md` (script-to-motion's narration rules),
  `script-writing.md` (script-to-motion's writing rules), `pipeline.md` (the commands), `graphics.md` (the engine API),
  `theme.md` (the stage look), `speed.md` (parallelism), `lessons.md`.
