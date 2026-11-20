# Lessons (hard-won; read before improvising)

## Timeline and Narration (Rework Lessons)

- **Spell acronyms as one word in `say`.** "지 알 피 오", "피 피 오", "에이 아이 엠 이" with spaces made Chirp 3 HD break
  inside them ("지 ‖ 알피오", "에이 아이 엠 ‖ 이"); "지알피오", "피피오", "에이아이엠이" read as one name, and the take
  got shorter (14.6 s -> 10.0 s). Check with phrasing-check.mjs either way (GRPO short, 2026-11-19).
- **A highlight is a chip once.** A term repeated in many lines ("GRPO", "평균") became a chip every time (18 chips in
  2.5 min). compose.py now uses each highlight once; list one entry per moment, written as it appears there.
- **Intonation is not measured; only the user's ear catches it.** On the PN short the user flagged an opening subject
  read with emphasis ("실리콘 원자는", "그래서 공학자들은" higher than "그래서"), a particle that jumped ("남아도"의 "도")
  and one line faster than the rest. A pitch check was tried on the 26 first takes (2026-11-20, Praat via
  praat-parselmouth, syllable nuclei): only the raised opening of c04 stood out (+8.5 st over the line, with 2 unflagged
  lines also over +6 st); "공학자들은" and "도" sat inside the ±8 st that Korean phrase intonation moves anyway. So no
  pitch gate. Two cheap habits instead: hand the user the lines that open with "그래서/이렇게 + subject는" to listen to
  first (both emphasis notes were such openings), and since takes replaced by a re-take are now kept in
  `.tts-cache/replaced/`, a later check can be measured on the takes the notes were about.
- **Read with phrasing-check before trusting your own reading of a pause.** A 0.35 s pause read off wave.mjs as the comma
  break was, by phrasing-check, after the topic word instead.

- **Run boundaries snap DOWN to the frame**:
  In `scripts/timeline.py`, run boundary cuts snap to the video frame using floor rounding:
  ```python
  def fr(t):
      return math.floor(t * FPS + 1e-6) / FPS
  ```
  If boundaries rounded up or to the nearest frame, a line's cue audio could start a fraction of a frame before its visual run began, causing the first syllable of dialogue to be heard over the previous scene's graphic. Snapping down guarantees the visual cut happens at or just before the audio onset.
- **Keyword chips need an `"at"` in recorded cues**:
  Keyword chips (`shorts.json` `highlights`) pop onto the screen exactly when the word is spoken. While cues are silent placeholders, word timings are estimated from character positions. Once cues are recorded, any chip whose first word still has `est: true` will pop at an approximate time, visually desynchronized from the voice. `scripts/check_narration.py` treats this as a warning. Always measure the phrase in `node scripts/narration/wave.mjs narration/<sk> --cue <id> --step 0.01` and write its `"at"` time into `script.json`.
- **Figtree and Geist Mono have no Hangul**:
  Figtree and Geist Mono only contain Latin glyphs. Using them for Korean text produces missing glyphs (tofu/rectangles) or unpredictable system font fallbacks. Pretendard (SIL OFL 1.1, variable TTF) must be used for all Korean on-screen text (`.display`, `.h1`, `.h2`, `.sub`, `.body`, captions, and cover). Geist Mono is reserved exclusively for uppercase Latin labels (`.label`), with Pretendard declared as fallback: `font-family: 'Geist Mono', Pretendard`.
- **No dead air of 0.4 s or more**:
  TTS takes occasionally contain trailing pauses or unnatural mid-sentence gaps. After setting cuts, run `wave.mjs` across the full narration. Any silent gap ≥ 0.4 s (excluding the 1.5 s `tail` hold at the very end) breaks pacing and must be trimmed in `script.json` `"cut"` or re-taken with `[pause short]`.

---

## HyperFrames and Rendering

- **Headless Chrome keeps the window at least ~500 px wide.** A 360 px screenshot of index.html laid the page out at
  500 px and cropped it; render.py --screenshot shoots at 540 px or wider.
- **The 240 fps capture is inherited, not measured.** It came from the original spec ("240 fps, blend 3 of every 4"); it
  quadruples capture time. render_full.sh takes RENDER_FPS=240|120|60 (render.py --fps); engine.js's own viewport blur
  is computed from the camera's time derivative, so it is the same at every capture rate. Compare before changing the
  default (the GRPO short has a 60 fps twin for that, 2026-11-19).

- **engine.js must not assume the HyperFrames runtime.** It wrote `window.__timelines[id]` and threw in a plain browser,
  where that object doesn't exist, so `__render` was never set and the preview froze every composition at t = 0. It now
  creates the object when missing.

- **Standalone compositions**:
  Render compositions with `hyperframes render -c file.html`. HyperFrames `snapshot` only inspects `index.html`. Always use 10 fps draft renders (`render_draft.sh`) and contact sheets (`chk/<rid>_sheet.png`) for rapid development and inspection.
- **Driving the timeline**:
  The world engine drives time through a GSAP timeline proxy setter:
  ```javascript
  const tl = gsap.timeline({ paused: true });
  tl.fromTo(st, { t: 0 }, { t: cfg.dur, duration: cfg.dur, ease: 'none' }, 0);
  ```
  A tween setter fires on every seek, whereas `onUpdate` callbacks can be skipped during rapid seeks.
- **Right-edge 8 px strip workaround**:
  HyperFrames' MP4 render path leaves an 8 px black column at x 1072–1079 on 1080-wide output, and captures frames as lossy JPEG. `render_full.sh` avoids this by capturing `--format png-sequence` (lossless PNG frames) at 240 fps, then using FFmpeg `tmix=frames=3:fps=60` to produce the final motion-blurred 60 fps MP4 in `gfx/out60/<rid>.mp4`. Drafts (`render_draft.sh`) use MP4 directly for speed.
- **One browser per worker**:
  By default, `hyperframes render --workers N` creates N tabs inside a single Chrome instance (`PRODUCER_ENABLE_BROWSER_POOL=true`), which serializes all PNG captures through one Chrome GPU process (capping capture at ~15 fps regardless of worker count). Both `render_draft.sh` and `render_full.sh` set:
  ```bash
  export PRODUCER_ENABLE_BROWSER_POOL=false
  ```
  This spawns a dedicated Chrome process per worker, scaling throughput to 41–51 fps at 8 workers.
- **Worker throttling**:
  More workers do not scale indefinitely; launching too many concurrent browsers exhausts memory and GPU queues. `render_full.sh` enforces a machine-wide budget via directory locks in `gfx/.render_slots`: at most `RENDER_SLOTS` (3) renders concurrently, each using `HF_WORKERS` (8) browsers.
- **Heavy pages and blurred backdrops**:
  A full-resolution capture paired with a blurred backdrop clone can exceed Chrome's memory limits. Use a 640 px wide downscaled copy for the blurred backdrop, and run Node with `NODE_OPTIONS=--max-old-space-size=16384`.
- **Never composite while re-rendering**:
  If a visual segment is composited while `gfx/out60/<rid>.mp4` is being written, FFmpeg reads a truncated stream. `compose.py --segments` verifies that each segment's frame count matches its run duration exactly, failing immediately on a mismatch.
- **Accurate still extraction**:
  When extracting still frames with FFmpeg, use output seeking (`-ss <t-0.5> -i src -ss 0.5 -frames:v 1`). Pure input seeking can land a frame early on an incomplete transition.

---

## Graphics Craft and Layout

- **Frame-0 landing state**:
  The hero element must ALREADY be visible on screen at frame 0 (camera at rest, element sharp). "Nothing lands at frame 0" means you must not start an entrance animation at frame 0; it does NOT mean starting an entrance at 0.05 s (which leaves black or empty frames after the cut). Secondary supporting elements (chips, icons, message bubbles) may land later with a pop.
- **Run 0 frame 0 is cover-safe**:
  Run 0 frame 0 serves as the video cover frame. Keep all graphics elements below y 620 to provide clear space for the glass title cover card (centred at y ~432).
- **Isolated blend modes**:
  CSS blend modes are isolated per card when filters or opacity are present. To create an azure highlight wash on light pages, place a `<div class="band">` under an `<img style="mix-blend-mode:multiply">` inside the same card's HTML, and reveal it with `scaleX` on the keyword phrase.
- **Highlights on dark UI**:
  A `multiply` wash is invisible against dark backgrounds. On dark UI, re-ink the text dark on an azure wash and reveal with a left-to-right wipe, or apply an azure border outline with a subtle outer glow.
- **Type scale**:
  On a 9:16 mobile canvas (1080×1920), never use type smaller than 30 px. For wide multi-column UI (e.g. chat bubbles or terminal sessions), crop or pan into the critical line rather than shrinking the entire view until text is unreadable.

---

## Compositing and Performance

- **Captions word spacing**:
  Captions are rendered with an extra 16 px spacing between words. Without this buffer, the 10 px dark stroke (`STAGE950`) swallows the space characters, merging words together visually.
- **Parallel segment rendering**:
  `compose.py --segments` processes each run as an independent subprocess, then concatenates them via stream copy. This is ~2× faster than a single sequential process and enables incremental rendering.
- **Input caching (`.key` files)**:
  Each run's segment is cached against a hash of its run configuration, graphics video file modification time and size, captions, cover card, and compositor code hash. If unchanged, the segment is preserved.
- **Never set `bufsize=10**8` on frame pipes**:
  Opening FFmpeg raw video pipes in Python with an oversized buffer causes pipe reads to stall on Windows (~130 MB/s vs ~1.6 GB/s with default system buffers). Leave `bufsize` at default.
- **RGBA layer bounds caching**:
  Alpha compositing 1080×1920 float arrays on every frame is expensive. `compose.py` calculates the non-zero bounding box of RGBA overlays (chips, cover, captions) once and blends only within that sub-rectangle.

---

## Environment and Text Encoding

- **Windows text encoding**:
  Python defaults to the system code page (e.g. `cp1252`) on Windows when opening files without an explicit encoding, corrupting Korean text into mojibake. Every script must open text and JSON with `encoding='utf-8'`, and all shell scripts must export `PYTHONUTF8=1`. `check_text.py` verifies all on-screen strings before rendering starts.
- **Git Bash heredocs**:
  In Git Bash on Windows, `\n` inside a Python heredoc expands into a literal newline character, breaking string literals. Write complex configurations using Python scripts or file tools directly rather than inline bash heredocs.
- **Subshell directory changes**:
  Running background tasks with `cd W && a & b` backgrounds the directory change, leaving subsequent commands running in the parent directory. Use explicit subshells: `(cd W && a && b) &`.
