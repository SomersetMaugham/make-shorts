# Look development, the craft guide and the defect check

**No score decides anything** (the user, 2026-11-21). Taste belongs to the user and to what the user already approved
(the theme files, the approved look-development frames, the parts catalogue sheet, `lessons.md`, the camera budget).
The defect checker — Gemini Neon through agy (`gemini-4-neon-medium`), `scripts/defect_check.py` — only finds defects.
It does not score, rank upgrades or ask for more camera moves or effects. The craft of the frame is the builder's job,
guided by §6, and the user judges it in the review.

Why: the earlier art director scored every section 1–5 and the build could not go on below 4. Its taste replaced the
user's: on PN part 3 its "1.0× everywhere is monotonous" became a push in every run (50 moves) and the user said "눈이
너무 피곤하네요". A score also invites decorating frames to raise a number.

## Contents
1. Where it runs: three points
2. Roles: the builder, the defect checker, the user
3. The floor: what is a defect
4. Consistency rules
5. What the checker returns
6. The craft guide (for the builder, not a score)
7. Rounds, stopping, reporting

## 1. Where it runs: three points

| point | when (SKILL.md) | images | gate |
|---|---|---|---|
| **look development** (`lookdev`) | step 4, after one hero run per section (3–5) is built | the hero frame of each section, `--at T --res full` | no must-fix left, and you compared the frames with the approved look (§2); then the rest is built |
| **motion** (`motion`) | step 5, after the whole build passed the graphics checks | every run boundary and camera move frame by frame, every key moment around its word (visual-review.md) | no must-fix left |
| **whole** (`whole`) | step 5, before index.html goes to the user | whole-short sheet (`--gapframe 120`), each section's sheet (`--gapframe 30`), key moments `--res full` | no must-fix left |

It needs no recording (placeholders are fine) and makes no MP4. A fix the user asks for in the review is implemented
straight away (visual-review.md); re-check only the stretches you changed.

**Sections** are the short's story beats, written in GFX_BRIEF.md (e.g. hook · problem · mechanism · example · payoff),
3–5 per short, each a run of consecutive runs.

## 2. Roles: the builder, the defect checker, the user

- **The builder** (you and the graphics agents) designs every frame with §6 and the approved references, and owns it.
  At look development, put the hero frames next to the approved references of the theme (the theme file's approved
  look, earlier parts of the same series, the parts catalogue) and fix what does not match before going on.
- **The defect checker** has no stake in the code: it looks at the images, the rules here, the script and the brief,
  and lists defects. `defect_check.py` runs it read-only (agy `--add-dir` on the images and the project, no write grant,
  no shell). Heavy looking — dozens of frames, frame-by-frame transitions — goes to it, not to you.
  **Confirm every finding** by opening the frame it names before you act: Gemini has been wrong on these shorts. A
  finding that is really a taste request (a new shot, more motion, "monotonous") is not a defect: drop it and log why.
- **The user** judges the look in the review. When they call a stretch flat ("밋밋해", "아쉬워"), redesign it from its
  concept with §6 (re-create, don't decorate), then run the checker on the changed stretch.

When agy is missing or fails twice, run the same check yourself in a separate, written step with the same rules and
the same output, and say so in the hand-off.

## 3. The floor: what is a defect

Any hit is a must-fix:
- Text under 30 px (stage theme) or under 44 px (sketch theme).
- Anything outside the zones (content y 140–1395, captions y 1410–1550, nothing below 1560) or under the captions; text
  or the key element under the platforms' button column (x > 960, y 1000–1700). These hold in every camera position.
- Overlaps and clipping; things that should touch and do not (a wire that misses its pin).
- Run 0 frame 0 not cover-safe, or a hero missing at a run's frame 0.
- A frame that is a slide or a document page (a title and bullet lines on a card or on paper); the stage theme's
  infographic look (thin lines and small diagrams on a dark gradient beside a label column).
- A drawing that appears all at once in the sketch theme (it must be drawn on).
- Three runs in a row with the same layout; a stretch frozen for lack of a plan (the same picture for more than ~2 s
  while the words move on to something else).
- An effect or reveal landing after its word.
- Motion: a one-frame jump, a flash of the wrong state at a run boundary, a jerk (a camera move packed into a few frames,
  e.g. `expo`/`power3+` easing on the camera), a run that ends while zoomed, a muddy overlap of two states.
- More than 4–5 camera pushes in the short (count them from cut.json/the compositions yourself; the checker sees only
  images).
- Against an earlier round (`--before`): a stretch you changed that looks the same at phone size.

## 4. Consistency rules

- **The same part looks the same everywhere.** In the sketch theme every circuit part and matter drawing comes from the
  kit (assets/gfx/sketch.js) and matches the approved parts catalogue sheet: a battery, resistor, meter or atom drawn
  differently from its catalogue shape, or two different versions of one part in the short, is a defect.
- The pens keep their jobs (theme-sketch.md): red = what changes now, the main current; blue = before; orange = the
  control current; the highlighter = the one key line. A colour used for another job is a defect.
- Polarity: + in red, − in blue.
- Captions, chips and the cover follow the theme of the short.

## 5. What the checker returns

```
## Must-fix
- <image number and label> — <rule from §3/§4> — what is wrong and where in the frame

## Suspect
- <image number and label> — what may be wrong (a possible capture glitch, or too small to be sure at this size)

## Clean
- the image numbers with nothing found
```

No scores, no upgrades, no opinions on taste. `defect_check.py` saves it to `review/defects-<point>-<round>.md` and
prints the must-fix list.

## 6. The craft guide (for the builder, not a score)

What a designed short looks like. Use it while building and when the user asks for a redesign; nobody grades it.

**Direction**
- The concept object or idea is present and keeps changing role; each section has a world, not a backdrop.
- Shots vary (wide, medium, close-up, insert); the key gesture of each beat gets its close-up, within the camera budget.
  The camera moves for a reason in the words (push-in on what is named, pull-out for the whole) and rests otherwise;
  a resting camera with a drawing that changes is good, not monotonous.
- One focal point per moment; the eye is led — where it lands at a cut is where the next run starts; reveals land on
  the word; the captions are part of the frame.
- Density follows the story (hook → build → peak → resolve). The first 2 s are the hook: the strongest frame, not a
  title card. The hero fills the content zone (y 140–1395), not the upper half.
- Joins: something survives the cut (match cut, morph, the travelling object).

**Graphic design**
- Composition with a grid and balance you can name; chosen negative space; centre of mass in the content zone.
- One hero, clearly the largest thing when its word is said; a clear second and third level, not ten equal labels.
- Typography: weight and size contrast; line breaks at phrase boundaries; hero lines with a treatment that says what
  they say.
- Colour: one accent per scene with a job; value contrast that reads on a phone.
- Stage theme: layers with depth, light and material; real captures shown as objects in the space.
- Sketch theme: the drawing fills the content zone as one figure; the hand's order follows the words; the current is
  seen at a glance (band and moving charges); a push lands on its close-up and the change is written there.
- Detail: consistent stroke weights and icon language (in the sketch theme: the kit's parts only).

**Motion**
- Easing with intent on elements (`expo.out`, `power4.out` entrances, quicker exits); the camera is slow and even
  (`sine.inOut`, theme-sketch.md).
- Hierarchy in time: the focal element first; overlaps of 0.2–0.4 s; staggers in the rhythm of the speech.
- Elements travel, transform and hand over rather than fade out and in.
- While words go on, the thing they name moves; a visual lands with or slightly before its word (`W(ws, '구절')`).

**Re-create, don't decorate:** a beat the user calls weak is redesigned from its concept (a new shot, a new picture of
the idea), not given small added effects or labels.

## 7. Rounds, stopping, reporting

- Fix every confirmed must-fix, rebuild (`build_gfx.py <tags>`, `preview.py`), re-shoot exactly the stretches you changed
  into `chk/<point>-<n+1>/` and run the checker on them with `--before` the previous images.
- Stop when nothing confirmed is left on the floor. After three rounds with defects still found, stop and report them.
- `review/defects.md` keeps each round: the findings, which were confirmed or dropped (and why), the fixes, the image
  folders. The checker's own reports stay in `review/defects-<point>-<round>.md`.
- The hand-off (and report.md) says how many rounds ran, what was fixed, and anything left.
