# Editing spec (the quality contract)

The complete creative and technical spec behind the shorts. Follow all of it; speed comes from parallelism
(speed.md), never from dropping a rule. Where the user's request says something different, the user wins.

You make finished, ready-to-post 9:16 shorts (YouTube Shorts, Instagram Reels, TikTok) from a topic, material or a
script. There is no recording: every picture is a graphic you build, and the only sound is narration synthesized with
script-to-motion's TTS tools (Google Chirp 3 HD, `ko-KR-Chirp3-HD-Enceladus`). Everything is code: Python, Node,
ffmpeg and HyperFrames (npx --yes hyperframes). You may install what you need locally inside the project (npm packages
in the project folder, pip into its venv) without asking. Never install system-wide software.

**Language: Korean by default, for everything the viewer or the user reads or hears** — the narration, captions, cover,
on-screen copy, the report and the publishing copy. Another language only when the user asks (then the voice changes
too: references/narration.md).

WORK AUTONOMOUSLY — WITH ONE QUESTION
- Every judgement call (which facts, which moments, scenes, a source that disagrees, a UI behind a login) is yours: make
  the best call, keep going, and log it in the report.
- The one decision that is not yours is **recording the narration**: it is the user's decision and their quota
  (script-to-motion's rule). Build every short completely on silent placeholders, hand over the browser preview
  (`work/index.html`, written by `preview.py`) with the script (`narration/<sk>/script.txt`), and ask whether to record.
  Don't ask anything else, and don't stop earlier to get lines approved.
- **The MP4 is rendered by the user**, with `work/render.py`, after checking the preview in Chrome (script-to-motion's
  shape: the page first, the file on request). The agent prepares everything the render needs and says the command.
- If something fails, try another way (a different tool, method or fallback) rather than stopping. A missing tool is not
  a reason to stop: install it locally or use an alternative.
- If a real product UI is behind a login, rebuild it from public screenshots or docs and note it in the report.
- No voice possible (the user wants none, or gcloud can't sign in and they don't log in): make the shorts without
  narration (`"narration": false` in the short's script.json): every key line on screen, enough hold to read, and say so
  in the hand-off (references/narration.md).

INPUTS
- The topic, material (articles, notes, a planning doc, links, files) or a finished script. A script the user gives is
  used word for word: only `say` gets spoken forms. Files the user gives (logos, screenshots, photos) go to
  `work/gfx/assets/` and are listed in the report.
- How many shorts: follow the user. Otherwise the strongest self-contained ideas in the material, usually 3-5, never more
  than 5. What makes a short:
  - one question and its answer, which a stranger understands with no context; no two shorts on the same question
  - a hook with something concrete in it: a number or a jump ("6.7%에서 70%로"), a surprising cost, a question everyone
    has, a striking result
  - a payoff line at the end: the answer said plainly
  - things to show: real pages, UI, products, numbers for most lines (a short that would be only generic diagrams is a
    weaker pick)
  - about 30-50 s of narration; saying what needs saying comes first, there is no target length (script-writing.md)
- Cover title: the user's, otherwise written from the hook.

DELIVERABLES (in edit/)
- short-NN_<slug>/final.mp4: 1080x1920, 60 fps, H.264 high, AAC 48 kHz stereo
- short-NN_<slug>/thumbnail.jpg (section 8c), stems/voice.wav (the narration before the master), script.txt, report.md
- edit/PUBLISH.md: the publishing package for every short (section 8b)

1. RESEARCH AND THE SCRIPT
- A research subagent checks every figure the shorts will say against two or more reputable sources, captures the real
  source pages (article, docs, post, pricing page, repo) into `work/captures/` with an index (file -> URL, what it shows)
  and the fact check (each figure, its sources, any disagreement). Facts are no one's expression: the wording is yours.
- Write the narration by script-to-motion's rules (references/script-writing.md): spoken Korean for a listener who hears
  each line once; every name and term explained when first heard; one idea and one number per sentence; the conclusion
  first; no AI-style phrasing. Each line passes the first-time-listener gates and the cold-listener review (the Gemini
  app, Hydrogen, seeing only script.txt) before it can be recorded.
- `shorts.json`: per short a title, cover lines, highlights (keyword chips), an accent, and the lines: one line ≈ one
  sentence = one narration cue (`id`, `text` shown, `say` spoken, optional `gapAfter`), each with its `scene` and optional
  `switches`.

2. NARRATION (script-to-motion, unchanged — references/narration.md)
- Google Cloud TTS Chirp 3 HD, `ko-KR-Chirp3-HD-Enceladus`, speed 1; Fish Audio or edge-tts only when the user asks.
- Recording only on the user's word (`tts.mjs <dir> --approved`; `--only <ids>` for re-takes they ask for).
- Every take is kept exactly as returned. No code decides where silence or a word is: read each take with `wave.mjs`
  and write its `cut` (`"ranges": []` when nothing goes) and the `at` times of the phrases that must land on a word.
- Chirp's wrong phrase breaks: `phrasing-check.mjs`, then `[pause short]` (or joined words) in `say` and a re-take.
- No dead air: no silence of 0.4 s or more anywhere except the end hold. Fix it with a `cut` or a shorter `gapAfter`,
  never with a sound effect, never by speeding anything up.
- Never transcribe a take to judge its words or delivery; listening is the user's job. Tell them which lines to listen to
  first (numbers, names, English terms, re-takes).

3. THE TIMELINE AND THE RUNS
- The narration is the clock. `timeline.py` lays the runs on the cues: a new run where the `scene` changes, at the start
  of the line's cue or at a `switches` phrase, snapped down to the frame. END = the narration plus its end hold (`tail`).
- Every run is a full visual: a full-frame 1080x1920 graphic. Scene kinds: `capture` (a real page), `ui` (a product
  doing the thing), `diagram`, `number`, `logo`, `list`, or your own word. The rotation:
  - the hook (first line) is the strongest visual you have: the number, the real result, the striking page
  - no run over ~8 s; two runs in a row never share a scene kind; at least three kinds per short
  - the last line (the payoff) gets a calm, clear picture of the answer, held through the end hold
- Write the run plan (`brief_runs.py`) before building any graphic. A word's time is an estimate (character position)
  until its phrase has an `at`; anchor graphics on phrases, never on the printed seconds.

4. GRAPHICS (HyperFrames, one composition per run; parallel graphics agents)
The look is the stage theme (references/theme.md): a graphite stage lit from above, cards floating in it, and a camera
that moves through it.
- Surfaces: glass for diagrams and statements (`highlight` on one element per scene); white window / paper / media /
  capture for real UI, chats, files and pages; glossy icon tiles for categories. One accent per scene (azure; ember for
  limits and costs; mint for passes).
- Type: Pretendard for every word, nothing under 30 px; Geist Mono for Latin labels.
- A world camera moves over the cards: a glide (sine.inOut, scale change 0.04 at most), a step to the next item (0.5 s
  power3.inOut, starting 0.25 s before the phrase that names it), a push onto the card being talked about (1.2-2 s
  power2.inOut, up to ~1.6x), a pull back to reveal the bigger picture (1-2 s), and at most ONE whip per run (0.45 s out
  power3.in, 0.6 s in power3.out). Frame 0 of every run is the landing state, sharp, with the camera at rest.
- Depth of field: the card being read is in focus; neighbours blur up to 14 px and dim 30 % as the camera pushes. A new
  hero sends the old one back to a 9 px blur at 40 % opacity. Never blur a word the viewer needs to read.
- Motion blur: the viewport blurs along its screen velocity every frame (sigma = 0.29 x speed x 0.75/60, capped at
  24 px); renders capture at 60 fps by default (project.json `"render_fps"`: 120 or 240 blend 2 or 3 captures per frame for a
  stronger blur). A blurred frame at rest is a bug.
- Animate the action, never label it: no label pills or word rows restating the narration. A named product is its real
  UI (captured live or rebuilt from public screenshots) doing the action: typing, streaming, clicking. While a product
  window is the subject only a camera INSIDE it moves (1.15-1.4x, 0.4-0.7 s power2.inOut). Named-product intro: its
  official logo large and centred first, then the UI. Brand names and logos only when the narration names them.
- Anything that HAPPENED (a release, a quote, a number, a headline) shows its real source page with the cited line
  highlighted as it is said. A capture sits sharp in a fixed frame (x 24, y 160, 1032x1200, radius 36, white, shadowed)
  on a blurred, enlarged, washed clone of itself (blur 40 px, saturate .7, brightness 1.05, a 72 % white wash); the frame
  never moves, the page pans and zooms inside it. Draw the TRUE number when a number is drawn.
- **Every capture names its source on the capture itself** (the user, 2026-11-26): a dark chip `출처: <매체·사이트>` in
  its bottom-right corner (top-right when that corner covers the cited line), Pretendard 600 26 px, so a crop passed
  around still carries it. `capture_card(..., credit='출처: …')` and every theme's `capture_html(..., credit=…)` draw it
  and stop the build without it; any other real image of a source (a raw `<img>` hero) adds `credit_chip('출처: …')`.
- The frame's zones: content y 140-1395 (the main element's bottom edge at about 1360-1395), captions y 1410-1550, nothing below y 1560 (the platforms draw their title, description and music there), and no text or key element at x > 960 between y 1000 and 1700 (the like/comment/share column; config.LAYOUT ui_right). No decoration fills the bottom either (the old horizon wave of dots is gone). `*_r0` is also the
  cover frame: at frame 0 keep everything below y 620.
- Every move and landing is anchored on a phrase, `W(ws, '<phrase>')`, so the graphic follows the narration when it is
  recorded (graphics.md "Timing").
- Keep every scene sparse: one dominant subject, at most one supporting cue, smooth eased motion, never frantic.
- Duration of each composition = its run exactly. Check every draft's contact sheet before a full render.

5. COVER AND CAPTIONS
- Cover: frame 0 only. The title in Pretendard 600 (104 px) on a glass card with the accent line beneath, centred at
  y ~432 (references/theme.md).
- Captions burned in from the timeline's words, starting at 17 ms (frame 0 stays clean). 1-3 words (어절) per chunk,
  never across two cues, Pretendard 700 74 px, white, a 10 px graphite stroke, no box, one line. After every 2-3 normal
  chunks, one meaningful word or phrase (a product name, a number, the answer) becomes a keyword chip (shorts.json
  `highlights`, written as in the text; the last word may stop before a particle). Never two chips in a row, never
  particles or connectives alone. Each highlight is a chip once per short (its first occurrence the spacing allows): list
  one entry per moment, written as it appears there (e.g. "가치 모델이라고"), not a term that recurs in every line. In a recorded short every chip's phrase has an `at` (check_narration.py warns).
- Position: the caption band, y 1410-1550 (centre 1480), at most 840 px wide so it ends left of the button column (x 960); `"caption": "top"` on a line moves its run's captions to y 180-360 for a
  picture whose content sits low. A caption never covers the visual's main element.
- No CTA card. The short ends on its payoff line and the end hold; there is no "watch the full video", no comment box,
  no follow card (there is no other video to send anyone to).

6. SOUND
- The narration only (script-to-motion carried over as it is): no music, no sound effects, no riser, nothing from a
  library or the web, nothing generated by another service.
- `mix.py` masters it for the platforms and changes only the level: gain to -14 LUFS integrated, and a limiter only when
  the true peak would pass -1 dBTP. Never time-stretch, speed up or pitch anything.
- stems/voice.wav is the narration timeline before the master.

7. REPORT (edit/short-NN_<slug>/report.md, in Korean; `report_data.py <sk>` prints its numbers)
- Inputs: the topic or material, what the user provided, the research (sources per figure, disagreements).
- The script: every line with its `say` where it differs, and every judgement call in the wording.
- Narration: provider and voice; every cue with its take id, its cut, the phrase times set; re-takes and why; the
  phrasing-check results; the dead-air reading; the lines the user should listen to first.
- The run plan: runs tiling [0, END] with scene kind, times and durations.
- Graphics: one line per composition (what it shows, real sources used, camera moves, whips).
- Cover, captions (the chips) and the mix (loudness, true peak, whether the limiter ran).
- The thumbnail: its time and run, what it shows, and why it beat the other candidates.

8b. PUBLISHING PACKAGE (edit/PUBLISH.md, in Korean)
One file for the project, one section per short in order; on a re-run add or update only the sections of the shorts you
made. Write it after the short is final, from what the short actually says; every claim must hold against the fact check.
The shorts stand alone: never send viewers to a "full video", a channel, a link in bio or a community.

YouTube Shorts
- Title: 54 columns at most, Hangul counting 2 (about 27 Hangul), so the feed never cuts it. Its job is the click:
  - a word with pull (비밀, 진실, 드디어, 절대, 충격, 실수, 아무도, 진짜, 함정, 반전 ...)
  - an open loop the short closes: a bold statement, a surprising result, a question with something at stake; never
    the payoff itself
  - the tool, product or topic people search for, by its real name
  - bold but true; every title different; no emoji, no hashtags
- Description: one or two lines (about 150 characters) in natural, keyword-rich Korean, then a blank line, then exactly
  three hashtags about this short's content (the tool, its maker, the topic). No filler tags (#쇼츠, #추천, #fyp, #viral).

TikTok (one caption, no title; search reads all of it)
- First line: the hook, under 100 characters, the title's idea in a conversational voice (pull word and open loop).
- One or two lines with what people type into search for this topic, said naturally, with the real numbers and names.
- 3-5 hashtags on the last line (the subject tags, plus one community tag that fits, e.g. #개발자 #코딩). About 200
  characters in all. No URLs.

Instagram Reels
- First line: the hook, under 125 characters. Then two or three short lines, one idea each, separated by blank lines.
- 3-5 hashtags on the last line (Instagram allows at most 5). No URLs.

Layout of each section (every piece of copy in its own fenced block):
  ## Short NN: <slug>  (file: edit/short-NN_<slug>/final.mp4)
  **Thumbnail** (short-NN_<slug>/thumbnail.jpg, from <time> s: <what it shows>). The YouTube thumbnail and the Instagram
  cover; on TikTok, upload it as the cover or pick the frame at <time> s.

  ![Short NN thumbnail](short-NN_<slug>/thumbnail.jpg)

  ### YouTube Shorts
  **Title**
  ```
  <title>
  ```
  **Description**
  ```
  <1-2 lines>

  #태그1 #태그2 #태그3
  ```

  ### TikTok
  **Caption**
  ```
  <hook line>
  <1-2 keyword lines>

  #태그1 #태그2 #태그3 #태그4
  ```

  ### Instagram Reels
  **Caption**
  ```
  <hook line>

  <idea 1>

  <idea 2>

  #태그1 #태그2 #태그3 #태그4
  ```
`check_publish.py` must pass before the hand-over.

8c. THUMBNAIL (edit/short-NN_<slug>/thumbnail.jpg)
One frame from the finished short: the YouTube thumbnail, the Instagram cover and the TikTok cover. The candidates are
chosen while the short is built, never by scanning it afterwards.
- Clean: the picture alone, no captions or cover title.
- What it shows: what the short is about, recognisable at a glance: the product's official logo, its real UI doing the
  thing, the number or headline the short is built on, a striking result. The most eye-catching element, not the most
  typical frame. Not run 0's opening frames (the top 620 px is empty for the cover).
- The landing state only: the hero fully on screen, sharp, the camera at rest; nothing mid-entrance or cut off.
- It must read at feed size (about 180 px wide): one dominant subject, high contrast. Keep the subject inside the centre
  1080x1350 (y 285-1635): Instagram's feed shows the centre 4:5.
- How: every composition marks its eye-catching still moments (`thumb` windows, graphics.md); finish.sh renders those
  frames clean; LOOK at chk/<sk>_thumbs.png and pick with `thumbnail.py <sk> --pick <t> NN slug`. If none is strong,
  add moments with `thumbnail.py <sk> t1,t2` rather than settling.
- The file: 1080x1920 JPEG under 2 MB.
