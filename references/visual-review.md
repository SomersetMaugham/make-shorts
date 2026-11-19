# Visual review — looking at the short with render.py

Carried over from script-to-motion (references/visual-review.md), fitted to shorts: the picture is the preview
(index.html: the runs' compositions, the captions, the chips, the cover), filmed by `render.py --screenshot` with
headless Chrome. No MP4 is made for looking (the MP4 is the user's, after the review).

> **When to look, and when not.**
> - **Work you do on your own:** the first build, anything you decide to improve, a redesign you carry out. Look at it
>   with `render.py --screenshot` and keep improving until a pass finds nothing (and the elevation, elevate.md, has
>   scored it). Don't hand off what nobody has seen.
> - **A fix the user asks for (a review note):** implement it straight away; don't run a new round of looking. Run the
>   cheap gates (`check_narration.py`, `check_text.py`), say what changed at which time and cue, and hand back.
> - **When the user asks you to look** (or pastes the player's **A** command), run it and open the images.
>
> **render.py --screenshot is the only way to look at the picture.** No screenshot code of your own, no ffmpeg frame
> grabs, no probe pages: every need has its option below.

## 1. Tools at a glance (run in work/)

```bash
python3 render.py --screenshot --short s1 --gapframe 120 --fast --jobs 3                 # the whole short, one tile every 2 s
python3 render.py --screenshot --short s1 --from 40 --to 62 --gapframe 30 --fast --jobs 3  # one section: enter, hold, leave
python3 render.py --screenshot --run s1_r9 --gapframe 10 --fast --jobs 3                  # one run (a graphic's own check)
python3 render.py --screenshot --short s1 --from 46.6 --to 47.6 --gapframe 3 --fast --jobs 3  # a run boundary / camera move, frame by frame
python3 render.py --screenshot --short s1 --at 12.5,43.9 --res full                       # exactly these moments, 1080x1920, one image each
python3 render.py --screenshot --short s1 --from 40 --to 47 --gapframe 6 --out chk/before # keep a set (before / after)
```

| to see | gap at 60 fps |
|---|---|
| a run boundary, a flash, a one-frame jump, text colliding | 1–6 over 1–2 s |
| how one beat enters, holds and leaves | 15–30 over the beat |
| a section | 30–60 |
| the whole short at a glance | 120 |

Each tile is labelled `m:ss.ss [cue]`: the same time and cue the player's **S** key copies, so you, the director and
the user name the same moment. Run boundaries are in `cut.json` (`runs[].T0/T1`); phrase times in the runs' words.

## 2. The review loop (step 5, before the elevation)

1. **Whole short** — `--gapframe 120`: variety of framing, scale and colour, or the same layout over and over? Does the
   picture escalate with the story? Where the narration goes on but nothing on screen follows the words, fix it.
2. **Section by section** — `--gapframe 30`, read against the script, cue by cue.
3. **Key moments** — every beat the story depends on (the hook, a reveal, a number, the payoff): from 0.5 s before to
   0.5 s after its phrase at `--gapframe 3`; the element is readable at or before the phrase's time (§5).
4. **Run boundaries and camera moves, frame by frame** — `--gapframe 1–3`: one-frame jumps, elements flashing their
   default state before their entrance, two runs muddily overlapping, a hero missing at a run's frame 0.
5. **Fix, then shoot the same stretch again** (§6). Repeat until a pass finds nothing.

**Who looks.** Steps 3–4 are dozens of images: they go to the motion reviewer (Gemini Neon,
`python3 scripts/art_director.py motion <round> <images…>`, elevate.md §1), which reports the frames and what is
wrong with them. You open only the frames it names, confirm, and fix. Steps 1–2 you skim yourself on the sheets; the
judging of A and B is the director's (elevate.md).

**A one-tile flash is a suspect, not a finding.** Every tile is its own headless Chrome load, and now and then one
catches a composition before it has taken its time (it shows the run's frame 0 for one tile, in the middle of a run).
Before fixing a "one-frame jump" or "wrong state for one frame", shoot that moment and its neighbours again
(`--at T-0.05,T,T+0.05 --jobs 1`): a flash that does not come back was the camera, not the short. A flash exactly at a run
boundary that does come back is real (the next run's frame 0 differs from the last run's end). The motion reviewer is
told the same, and its flash findings are confirmed this way before anything is changed (GRPO, 2026-11-20: four
reported flashes, three gone on a re-shoot).

## 3. What to look at in every frame

- **Not a slide**: strip the motion away. Would this frame pass as a PPT slide (a title card, cards of text, bullets,
  a table, boxes with arrows)? Then the run is rebuilt, not polished.
- **Story**: does the frame show what the line says right now? Is the key word or number the biggest thing on screen
  when it is said?
- **The shot**: the camera moving only where the words give it a reason; screen direction kept.
- **Focus**: one clear focal point; nothing important under the captions, off the edge, or behind another element.
- **Text**: 30 px or more, readable contrast, not overlapping, not cut, Korean words not split, no orphan syllable.
- **Zones**: content y 140–1395, captions y 1410–1550 (top captions y 180–360), nothing below 1560, and no text or key element at x > 960, y 1000–1700 (the like/comment/share column the platforms draw over the right edge).
- **Captions and chips**: a chip never covers the hero; caption chunks break at phrase boundaries.
- **Attached things stay attached**: labels on their objects, glows on their lights through every camera move.
- **Composition**: balanced, safe margins, intentional empty space vs accidental emptiness.
- **Continuity**: counters, colours and states right for this point; the same object looks the same across runs.
- **First and last frame**: run 0 frame 0 is the cover (everything below y 620); the last frame holds.

## 4. The automatic checks

`check_text.py` (text sizes, zones), `check_narration.py` (the narration gate) and the graphics checks in graphics.md
"Checking" run before every hand-off; each finding comes with the moment to shoot.

## 5. Checking sync

A visual should land **with or slightly before** the words it illustrates. The phrase's time is `W(ws, '구절')` in the
run (measured `at`, or the estimate before recording). Shoot from 0.5 s before to 0.5 s after at `--gapframe 3` and
find the first tile where the element is readable: it is at or before the phrase.

## 6. Iterating: before / after

```bash
python3 render.py --screenshot --short s1 --from 40 --to 47 --gapframe 6 --out chk/before
# … fix, build_gfx.py, preview.py …
python3 render.py --screenshot --short s1 --from 40 --to 47 --gapframe 6 --out chk/after
```

## 7. What a sheet can't tell you

- **Motion blur**: it comes from the render (render_full.sh), not the preview.
- **Smoothness** on the user's machine, and **audio** (read takes as numbers with `wave.mjs`).
Say these limits in the hand-off and ask the user to watch the moments that depend on them.
