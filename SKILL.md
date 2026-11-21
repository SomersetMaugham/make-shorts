---
name: create-video-shorts
description: Make finished, ready-to-post 9:16 shorts (YouTube Shorts, Instagram Reels, TikTok) from a topic, material or a script, with no recording needed - researches and fact-checks, writes spoken-Korean narration by script-to-motion's rules, narrates it with script-to-motion's TTS tools (Google Chirp 3 HD Enceladus; recorded only when the user says so, after reviewing a silent draft), lays every run as a full-frame HyperFrames graphic in the stage theme (glass cards, real source captures, camera moves, motion blur) or the sketch theme (hand-drawn schematics on paper, drawn on with flowing current, for circuits and diagrams) timed to the narration's phrases, burns in Korean captions with glass keyword chips and a cover, masters the narration to -14 LUFS, and delivers 1080x1920 60 fps MP4s with a thumbnail, a report and a Korean publishing package for YouTube Shorts, TikTok and Instagram Reels. Use it whenever the user wants shorts, reels, TikToks or vertical videos about a topic, an article, notes or a script ("이 내용으로 쇼츠 만들어줘", "릴스 몇 개 뽑아줘"), or wants to fix or re-edit a short made this way, even if they never mention a skill.
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
> that it stands on sound alone, and that every claim is in the record. A short answers **one question** as a story:
> a hook that opens a gap (two hooks tried, facts checked, first frame decided), turns instead of a list, the answer,
> and an ending of at most three sentences (answer, a new-angle line, the next part's question); no recap, no
> announcement, no second topic. Then the seam pass, the internal-name list and the **cold-listener review** by a subagent that sees only
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
- **The look:** the stage theme (theme.md) by default; the sketch theme (theme-sketch.md: hand-drawn schematics on
  paper) when the user asks for a hand-drawn look or the subject is a circuit or diagram explained step by step. Set
  `"theme"` in `project.json` before the first build; captions, chips and cover follow it.
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
   their narration (`references/script-writing.md`, **Short videos: the story spine**; the gates, the cold-listener
   review and the pull checklist before any line is final). Shorts that split one topic are a series: write the series
   flow first (each part one answer and one next question).
   Write `shorts.json`: per short `title`, `cover`, `highlights`, `accent`, and `lines` (`id`, `text`, `say`, `scene`,
   optional `switches`, `gapAfter`, `caption`). Example: `examples/shorts_example.json`.
3. **Timeline on placeholders:** `bash scripts/prep.sh` runs `narration_init.py` → `tts.mjs` (records nothing: silent
   placeholders with estimated lengths) → `sync.mjs` → `timeline.py` (cut.json, the runs) → captions. Read the runs it
   prints: no run over ~8 s, no two neighbours with the same scene kind (spec 3).
4. **Graphics, in parallel:** fill in `examples/GFX_BRIEF_template.md` as `GFX_BRIEF.md` and paste
   `$PY scripts/brief_runs.py` under its Compositions heading with one idea per composition. Start a FEW LONG-LIVED
   graphics agents (2-4, one per 1-2 shorts, grouped by kind: real sources, concept diagrams, one continuous world), each
   with a tag. Each follows `references/graphics.md` and `examples/gfx_s1.py`, anchors every time on a phrase
   (`W(ws, '구절')`), marks `thumb` windows, and checks its work on PNG contact sheets of the preview
   (`$PY scripts/preview.py`, then `python3 render.py --screenshot --run s1_r3 --gapframe 20 --fast --jobs 3`). **No MP4 of any kind is made
   before the user has finished reviewing** (the MP4 scripts refuse to run outside render.py).
   **Look development first** (references/elevate.md §1): GFX_BRIEF.md names the short's 3–5 sections; the agents build
   ONE hero run per section first, you shoot its hero moment (`python3 render.py --screenshot --short s1 --at T,… --res
   full --out chk/lookdev-1`), compare it with the approved look (the theme, earlier parts of the series, the parts
   catalogue) and run the defect check (`python3 scripts/defect_check.py lookdev 1 chk/lookdev-1`, Gemini Neon, in the
   background). The rest is built when no confirmed must-fix is left. **No score decides anything** (the user,
   2026-11-21): the checker finds defects only; taste is the user's and the approved references'.
5. **Preview in the browser:** `$PY scripts/preview.py` writes `work/index.html`: every short playing in Chrome with
   its live compositions, captions, chips and cover on the narration's clock (silent before recording; script-to-motion's
   player and keys). No render is needed, so a fix shows after `build_gfx.py`, `preview.py` and a reload.
   **Before the user sees it, look and check, on your own** (references/visual-review.md, references/elevate.md):
   (a) the visual review — the whole short and each section on sheets, then every run boundary, camera move and key
   moment frame by frame, checked by the defect checker (`defect_check.py motion <n> chk/motion-<n>`); fix the floor;
   (b) the whole check — fresh images into `chk/whole-<n>` (whole `--gapframe 120`, sections `--gapframe 30`, key
   moments `--at … --res full`), `defect_check.py whole <n> chk/whole-<n> [--before chk/whole-<n-1>]` lists the
   defects; confirm each by opening its frame (drop taste requests), fix, re-shoot the changed stretches, check again,
   until nothing confirmed is left (at most three rounds, then report what is left). The heavy looking (dozens of
   frames) is Gemini Neon's (`gemini-4-neon-medium`); you open only the frames it names. Design every frame by the craft
   guide (elevate.md §6). Log the rounds in `review/defects.md`. Then hand the user `work/index.html` and `narration/<sk>/script.txt`,
   list the lines to listen to first once recorded, and **ask whether to record**.

   **The review loop, on the review desk:** start `python3 -u scripts/review_server.py > review/server.log 2>&1` (in work/,
   in the background, binds 127.0.0.1 only) and watch the log apart from it (Claude Code: Monitor on
   `tail -n 0 -F review/server.log | grep --line-buffered -E 'BATCH|NOTE|USER|Error|Traceback'`, re-armed when it expires;
   a watcher that runs the server itself kills it on expiry) and hand the user the `REVIEW http://127.0.0.1:…` link it prints,
   not the file. On the page the user presses Space while it plays (pause and write; drag on the picture to mark the spot;
   Enter keeps the note and plays on) or holds V (say it). **Notes are collected by default** (status `queued`, nothing
   printed): the user watches to the end, then presses "검수 끝 · 일괄 수정 요청" in the L list, and you get one
   `BATCH b1 s1: N notes (…)` line followed by a `NOTE n003 s1 12.34s [c05 · s1_r6 +1.20s] text | box … | shot review/n003.png`
   line per note. Fix the batch together: look at every shot first, group the notes by run and by kind, resolve notes that
   pull against each other, gather every spoken-line change into **one** recording question in the chat (status
   `recording`; **a note is never the user's word to record**), rebuild once (`build_gfx.py`; `prep.sh`/`compose.py`
   + `preview.py`), then `review.py reply n003 --status done "what changed"` for each and
   `review.py announce "N개 반영 · L에서 '반영된 곳 이어 보기'"`. The page plays each fixed moment in turn and the user
   answers 확인 or 다시 (`USER n003 open: …` lines: the next round). A note sent with "바로 고치기" ticked arrives alone at
   once (a NOTE line with no BATCH): fix just that one. Unclear → `--status question "…"`.
   A note that fixes **how a word is read or split** ("일쩜", "마이너스극", a pause the user wants) that would come
   back in another line or short also goes into the pronunciation lexicon (`work/pronunciation.json` for this
   project, `references/pronunciation.json` when it holds for any short); narration_init.py applies it from then on.
   Without the server, index.html still works from file:// (S copies the moment, A the screenshot command).
   The loop runs until the user says the review is complete. Only then is an MP4 made, and the user makes it.
6. **Record (on the user's word):** `node scripts/narration/tts.mjs narration/<sk> --approved`; then the after-recording
   pass (`references/narration.md`; before the recording question, `prep.sh` has already printed `say_lint.py`'s
   👂 lines: fix those in shorts.json first): read every take (`wave.mjs narration/<sk> --unreviewed`; `autocut.py` drafts a cut
   you correct), set each `cut` (in `narration/<sk>/script.json`), run `phrasing-check.mjs` until its verdict is ok
   for every cue (commas are tagged before recording; check_narration.py refuses a MISSING) and fix wrong breaks with
   `[pause short]` in the line's `say` **in shorts.json** (prep.sh copies it over) and `--only` re-takes, set `at` for every keyword chip and every phrase a graphic lands on, read the whole sound for dead air.
   Then `bash scripts/prep.sh <sk>`, `$PY scripts/build_gfx.py <tags>` and `$PY scripts/preview.py`: the runs, every
   graphic and the preview follow the takes. Hand over `work/index.html` again, now with the voice, and run the review
   loop (step 5) until the user says the review is complete.
7. **After the review is complete, the user renders the MP4:** `python3 work/render.py s1 NN slug` (a copy of
   `scripts/render.py`): every composition with motion blur (`render_full.sh`, only those stale or made at another
   `--fps`), then `finish.sh` (check_text, check_narration, the master and the segments, concat, `verify_final.py`,
   thumbnail candidates, the copy into `edit/short-NN_<slug>/`). render.py is the only way these steps run (they refuse
   otherwise); never run it before the review is complete, and only when the user asks you to. Give the command.
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
- **Handing over a short nobody has looked at.** Shoot it, run the defect check (step 5, references/elevate.md) and fix
  every confirmed defect before the user sees it. Build it to the craft guide (elevate.md §6); a glass card holding a
  title and a line of text is a slide. **Letting a score or a reviewer's taste decide** — no score gates anything, and a
  "more motion / monotonous" request from the checker is dropped (PN part 3: 50 camera moves tired the eye).
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
  `preview.py` (`work/index.html`, the browser preview), `review_server.py` + `review.py` (the review desk: notes on the page, live reload), `narration_init.py` (shorts.json → narration folders), `timeline.py` (cues →
  cut.json + voice.wav), `brief_runs.py`, `build_gfx.py` / `build_gfx_common.py` (compositions, `W()` phrase anchors),
  `compose.py` (captions, chips, cover, segments, `--draft`), `check_text.py`, `check_narration.py`, `mix.py`,
  `verify_final.py`, `thumbnail.py`, `report_data.py`, `check_publish.py`, `draftsheet.py`, `sheet.py`, `config.py`,
  `init_project.py`.
- `scripts/narration/`: script-to-motion's TTS tools (`tts.mjs`, `wave.mjs`, `sync.mjs`, `phrasing-check.mjs`,
  `autocut.py`, `lib/`), with `SOURCE.md` (provenance, local changes) and `sync_upstream.sh` (reports upstream changes).
- `assets/gfx/`: `engine.js` (world camera, depth of field, motion blur, captures, the stage theme), `sketch.js` +
  `rough.js` (the sketch theme's drawing kit), GSAP and the HyperFrames project files. `assets/fonts/`: Pretendard,
  Gaegu and Architects Daughter (downloaded by setup.sh), Geist Mono, and the Latin fonts of the old compositions.
- `examples/`: `shorts_example.json` (a plan), `GFX_BRIEF_template.md`, `gfx_s1.py` (full-visual compositions with
  phrase anchors), `gfx_sketch.py` (a sketch-theme run: the transistor switch).
- `references/`: `editing-spec.md` (the contract), `narration.md` (script-to-motion's narration rules),
  `script-writing.md` (script-to-motion's writing rules, and the story spine for shorts), `story-ko.md` (the Korean
  shapes of hooks, turns and endings), `pipeline.md` (the commands), `graphics.md` (the engine API),
  `theme.md` (the stage look), `theme-sketch.md` (the sketch look: paper, pens, the drawing kit), `speed.md` (parallelism), `lessons.md`.
