# The sketch theme (hand-drawn schematics on paper)

A second look beside the stage theme (theme.md), made for explainers whose subject is a drawing: circuits, schematics,
block diagrams, mechanisms, a formula worked by hand. It looks like a page of an engineer's notebook or a textbook
drawn with a pen, and it moves the way a hand draws: wires are drawn on, words are written, a red pen circles and strikes
out, current flows. Developed with the user on a transistor-switch short (2026-11-20); the look-dev page and the motion
preview are `examples/gfx_sketch.py` and the user's approved choices below.

**Choose it** in `project.json` (`"theme": "sketch"`) when the user asks for it or the material is a drawing explained
step by step; every run, the captions, the chips and the cover follow. One look per short. A run may still set
`theme: 'stage'` in its cfg only if the user asks.

## Look
- **Paper**: #F3EFE6, a faint blue grid (54 px, rgba(143,179,201,.22)), paper grain, a warm vignette (build_gfx_common
  `SKETCH_CSS`). The grid moves with the camera (it is the page), the grain and vignette do not (they are the lens).
- **Ink**: #22201C pen lines 5 px (wires), 4.5 px circles, 7–8 px plates and bars; every stroke hand-drawn by rough.js
  (roughness 1.1, bowing 1.2) with a **fixed seed**, so a line has the same wobble in every frame.
- **Three pens, each with a job**:
  - **red** #D4382C: what changes or matters now (an annotation, a circle, a strike-out, the payoff word, the energised path);
  - **blue** #2A5DB0: the value before the change (a voltage, a state that will be struck out), a second category;
  - **highlighter** rgba(255,208,0,.55): the one key sentence on screen and the captions.
  - Orange #F08A2C only for a second, smaller current (a base current beside the main one).
- **Type**: Gaegu Bold for every Korean word and running text; Architects Daughter for the schematic's labels (pin
  names, CONTROL, OUT, +3V, R, C, E), uppercase like the textbook. Sizes on 1080x1920: title 92–116, annotation 52–64,
  labels 54–70, payoff word 80–96, nothing under 44 (the handwriting is thinner than Pretendard: 44 is the floor here,
  not 30). Gaegu reads smaller than its px size (the director read 52 px annotations as ~40 px on the PN short):
  annotations 60 px or more, key words 64–84. A slight rotation (−1° to −5°) on handwritten text; labels straight.
- **Captions, chips, cover** (compose.py and preview.py when the theme is sketch): captions in Gaegu 78 ink on a
  highlighter stroke (no outline); a keyword chip is the word in red Gaegu 88 on a stronger highlighter with a red pen
  line drawn in beneath; the cover is the title in Gaegu (up to 120, fitted to 880 px) in ink, each line on a
  highlighter stroke, a red pen line under it, centred at y 432.
- The zones are the same (content y 140–1395, captions y 1410–1550, nothing below 1560, nothing that reads at x > 960,
  y 1000–1700) and they hold in every camera position, close-ups included.

## The drawing kit (assets/gfx/sketch.js)
A sketch run's cfg has `theme: 'sketch'` (or the project default) and `sketch`: the JS body of `function (S)` that draws
the run with the helpers on `S` (the file's header lists them all). Coordinates are frame pixels at the rest camera
(1080x1920; build_gfx_common sets `cam0` to x 540, y 720, s 1), so the engine's `moves` push and pull the whole drawing.
Times are run-relative and come from the words: build the JS in Python with `W(ws, '구절')` filled in (example:
`examples/gfx_sketch.py`).

- `S.at(t0, d, () => {...}, kind)` — everything drawn inside appears over [t0, t0+d]: strokes drawn on like a pen
  (`'draw'`), text written left to right, or `'fade'` / `'pop'`. `S.out(t, d, items)` takes pieces away again.
- Parts: `res`, `cap`, `diode`, `npn` / `pnp` (return B, C, E and `inside`, the C→E path through the symbol), `gnd`,
  `vcc`, `port` (the schematic's pentagon flag), `chip` (an IC with numbered pins; returns pin positions), `dot`.
- Pen marks: `arrow`, `ellipse` (red circle), `strike` (red X), `marker` (a key line on the highlighter, shrinks to fit
  820 px), `note` (a sticky note), `text`.
- Current: `S.energize(t0, pts)` lays a translucent red band along the wire; `S.stream(t0, pts, {n, color, r, speed})`
  sends glowing charges along it (300 px/s, 10–12 on a long path; a smaller orange stream for a control current).

## Motion (what the user approved)
- **Drawing pace**: a whole circuit of ~12 parts is drawn in 4–5 s, a part in 0.35–0.7 s, a word written in 0.3–0.9 s.
  The first preview (13 s for the scene) was too fast, half that speed (26 s) drew too slowly; about 20 s was approved.
  Draw in the order a person explains: supply → load → node → output → the switch → ground → the control.
- **Current must be seen at a glance**: a band plus moving charges, never small chevrons or arrows that blink (the
  user: chevrons were "자세히 쳐다 봐야 할 정도", too faint to carry the meaning). The control current is smaller and
  orange, the main current larger and red, so "a small current switches a big one" reads without words.
- **Commit to the push**: a push-in goes all the way (2×) onto the thing being explained, with `ease: 'expo.inOut'`
  (slow start, fast middle, soft landing), holds while the change is written there, then pulls back (`power3.inOut`).
  A 1.3× push read as "당기다 그만 둔 느낌".
- **Camera budget: 4–5 pushes per short, no more** (the user, 2026-11-21, PN part 3: "눈이 너무 피곤하네요. 내용은
  정말 좋은데"). Push only on the key moments (the hook, the half-seen moment, the answer, the payoff); every other run
  keeps the camera at rest and lets the drawing change instead (drawn on, corrected, set aside). Every push is back at
  rest, or framed so the hero and every label sit inside the zones, before its run ends: never cut out of a run while
  zoomed. Part 3 had 50 moves over 31 runs (parts 1–2: 14 over 34) after a director's "1.0× everywhere is monotonous"
  was passed on as "a push in every run": it tired the eye and clipped labels at run ends. When a stretch is called
  static, answer with what the drawing does, not with the camera.
- **Show the change, not the result**: write the value before (blue `3V` beside OUT), then at the payoff circle it,
  strike it out in red and write the new value (`0V로 뚝!`). A changed state is drawn as a correction on the page.
- Something keeps moving while words go on (the charges flow until the run ends); the drawing never redraws itself.

## The hook frame (the first seconds of a sketch short)
The hook's words open a gap (script-writing.md → Short videos: the story spine); the first frame should open it too,
with the same pen marks the theme already uses. Draw fast here (a circuit in about 1.5 s): the viewer decides in
seconds.
- **The correction:** draw the battery–LED circuit, then a red X where the light should be and a red flip arrow over
  the battery, while the hook asks why. The page itself says "something is wrong here".
- **The break:** start on a finished, perfect thing (a lattice of four-handed silicon atoms), then erase one atom and
  dot in a different colour, while the hook says it has to be spoiled to work.
- **The result first:** draw the end state (the LED lit, the current flowing), then strike it out and go back to the
  blank page the explanation starts from.
Decide the hook frame with the hook (both go in the storyboard), and keep it inside the zones like every other frame.

## Checking a sketch run
The graphics checks (graphics.md "Checking") and the visual review (visual-review.md) apply; `render.py --screenshot`
films the preview the same way. Specific to the sketch theme:
- the frame at rest and at the end of every push: text and the key part inside the zones and left of the button column;
- after a push, the close-up still shows the circuit around the payoff (the node, its wire), not a lone word;
- the strokes do not shimmer between frames (a missing seed), text is not clipped early (fonts load late: sketch.js
  builds again once Gaegu and Architects Daughter are in);
- the drawing order follows the words: a part is fully drawn by the time it is named.

The elevation scores sketch shorts with the same rubric, read for this look (elevate.md §4, "The sketch theme").
