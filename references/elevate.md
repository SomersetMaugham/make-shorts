# Elevate — the aesthetic pass (고도화), with look development and the art director

Carried over from script-to-motion (references/elevate.md, cinematic-look.md §4, claude-roles.md §4), fitted to shorts:
1080x1920 runs on the stage theme, the preview (index.html) instead of a rendered video, and the art director run by
Gemini Neon (agy, `gemini-4-neon-medium`; the user's choice, 2026-11-20) through `scripts/art_director.py`.

**Defect-free is the floor, not the goal.** The user's verdict on videos that had passed every check: "연출에 대한 아쉬움,
더 섬세한 그래픽 디자인 모션의 표현 등등 전체적으로 미적인 부분에서 큰 아쉬움들이 있어." The graphics checks (graphics.md
"Checking": frame 0, 30 px, the zones) find what is *wrong*; this pass keeps going until the short is *designed*.

An elevation that judges each frame against the frame before it tends to add layers to the same compositions, and the
result is barely different from the first build. So the director scores against an **absolute bar** — a still a motion
studio would put in its reel — never against the previous round, and a round that only decorates does not count.

## Contents
1. Where it runs: three points
2. Two roles: the builder and the art director
3. What the director gets
4. The rubric: direction, graphic design, motion
5. What the director returns
6. What the builder does with it
7. Rounds, stopping, reporting

## 1. Where it runs: three points

| point | when (SKILL.md) | images | axes | gate |
|---|---|---|---|---|
| **look development** (`lookdev`) | step 4, before the graphics agents build every run | one hero frame per section of the short (3–5), `--at T --res full` | B 디자인 + world check | ≥ 4 on B, then the rest is built (up to 3 rounds) |
| **visual review** (`motion`) | step 5, after the whole build passed the graphics checks | every transition and camera move frame by frame, every key moment around its word (visual-review.md) | C 모션, sync, the floor | nothing left on the floor |
| **elevate** (`whole`) | step 5, before index.html goes to the user | whole-short sheet (`--gapframe 120`), each section's sheet (`--gapframe 30`), key moments `--res full` | A 연출 + B 디자인 per section, the floor, ranked upgrades | ≥ 4 on A and B (and C from the motion pass) in every section, or 3 rounds |

It is not optional and it does not wait for the user: it runs on the first build, after a redesign you carry out, and on
any stretch the user calls flat ("밋밋해", "아쉬워"). It needs no recording (placeholders are fine) and makes no MP4.
A fix the user asks for in the review is implemented straight away, without a new round (visual-review.md).

**Sections** are the short's story beats, written in GFX_BRIEF.md (e.g. hook · problem · mechanism · example · payoff),
3–5 per short, each a run of consecutive runs. Score per section, never per run.

## 2. Two roles: the builder and the art director

You built the picture, so you are the worst judge of it. The **art director** is Gemini Neon with no stake in the code:
it looks at the images, scores them and asks for changes. It never edits files and sees nothing but the images, the
rubric, the script and the brief: `scripts/art_director.py` runs it read-only (agy `--add-dir` on the images and the
project, no write grant, no shell). Heavy looking — dozens of frames, frame-by-frame transitions — goes to it, not to
you; you read its report and open only the frames it names to confirm a finding before you act on it.

When agy is missing or fails twice, do the director's job yourself in a separate, written step with the same rubric
and the same output, score as a stranger would, and say so in the hand-off.

## 3. What the director gets

Shoot fresh images for the round into `chk/elevate-<n>/` (`render.py --screenshot … --out chk/elevate-<n>`):
- the whole short at `--gapframe 120`; each section at `--gapframe 30`;
- the hero frame of each section and every moment named by an upgrade at `--at T --res full` (1080x1920, one image
  each; on a grid sheet the tiles are small and Gemini reads them loosely);
- for the motion pass: every run boundary and camera move at `--from A --to B --gapframe 3`.

`art_director.py` adds the rubric (this file), `narration/<sk>/script.txt`, GFX_BRIEF.md and, per image, its time, cue
and the line spoken there (from cut.json). Nothing else: no code, no logs. When an earlier round exists, pass its
images too (`--before DIR`) and the director checks that changed stretches really look different at phone size.

## 4. The rubric: direction, graphic design, motion

Score every section 1–5 on each axis (5 = a motion designer would put it in a reel), with the image names that justify
the score. **The scale is absolute**: 3 is competent explainer graphics, 4 is a crafted world with material, light and
depth that a viewer finds beautiful on its own, 5 is reel-worthy. The look-fors are prompts, not a checklist.

The stage theme (graphite stage, glass cards, accents; theme.md) is the material, not a score: a glass card that holds
a centred title and a line of text is a slide, whatever its hairline and bloom, and scores at most 2 on B. The
infographic look (thin lines and small diagrams on a dark gradient, a label column beside them) scores at most 2 on B.

**A. 연출 — direction**
- The concept object/idea is present and keeps changing role; each section has a world, not a backdrop.
- Shots vary (wide · medium · close-up · insert); the key gesture of each beat gets its close-up; no layout three runs
  in a row; nothing holds the same composition for more than ~2 s while words go on, unless the stillness means
  something. A short is watched on a phone: the hero fills the content zone (y 140–1395), not the upper half.
- The camera moves for a reason in the words (push-in on what is named, pull-out for the whole) and stays still
  otherwise; no habitual drift.
- Staging: one focal point per moment; the eye is led — where it lands at a cut is where the next run starts; reveals
  are withheld and land on the word; the captions (y 1410–1550) are part of the frame, never fighting the hero.
- Rhythm: density follows the story (hook → build → peak → resolve); the peaks are visibly peaks. The first 2 s are
  the hook: the strongest frame of the short, not a title card.
- Joins: something survives the cut (match cut, morph, the travelling object); no hard pop, no fade-swap of unrelated
  layouts.

**B. 그래픽 디자인 — the finish of the frame**
- Composition: a grid and balance you can name; negative space that is chosen, not left over; vertical centre of mass
  in the content zone; alignment between elements that belong together.
- Scale and hierarchy: one hero, clearly the largest thing when its word is said (on 1080 wide: 120–260 px type, or
  an object filling half the frame); support legible (never under 30 px); a clear second and third level, not ten
  equal labels.
- Typography (Pretendard): weight and size contrast inside a line; tracking for display sizes; line breaks at phrase
  boundaries, no orphan syllable; hero lines with a treatment that says what they say; numerals set as numerals.
- Colour and light: one accent per scene with a job; value contrast that reads on a phone; a key light or glow that
  makes the focal point; temperature that changes with the story.
- World, material and depth: background, mid-ground and foreground layers with focus (depth of field) and haze;
  falloff, rim and contact shadow; objects drawn with material — never thin lines floating on flat black; real
  captures shown as real objects in the space, not pasted rectangles.
- Detail: consistent stroke weights, icon language and radii; things that touch actually touch; nothing meaningless
  on screen.

**C. 모션 — the expression of movement** (the motion pass, on frame-by-frame sheets; stills cannot show it)
- Easing with intent: confident entrances (`expo.out`, `power4.out`), quicker exits, no linear start/stop.
- Choreography: hierarchy in time (the focal element first and most), overlaps of 0.2–0.4 s, staggers in the rhythm of
  the speech; never everything at once with one tween.
- Physicality: anticipation before big moves, overshoot and settle on arrival, follow-through.
- Continuity: elements travel, transform and hand over rather than fade out and in; across a run boundary the eye
  finds the next focal point where the last one was.
- Life: while words go on, the thing they name moves; ambient life is subtle and never the only motion.
- Sync: a visual lands with or slightly before its word (`W(ws, '구절')`), never after.

**D. The floor — any hit is a must-fix, whatever the scores**
A frame that would pass as a slide or a document page; the infographic look; text under 30 px; anything outside the
zones (content y 140–1395, captions y 1410–1550, nothing below 1560) or under the captions; text or the key element under the platforms' button column (x > 960, y 1000–1700); overlaps and clipping;
run 0 frame 0 not cover-safe or a hero missing at a run's frame 0; a stretch frozen for lack of a plan; three runs in a
row with the same layout; an effect landing after its word; a one-frame jump or a flash of the wrong state at a run
boundary; against an earlier round, a stretch that looks the same at phone size.

## 5. What the director returns

```
## Round <n> — scores
| section (runs) | A 연출 | B 디자인 | C 모션 (motion pass only) | why (image names) |

## World check
- does each section read as a place in one lit, material world? where it reads as an infographic or a slide instead

## Must-fix (the floor)
- <image name> — what is wrong

## The upgrades that matter most (ranked by impact, 6–10)
1. <cue / run / time span> — what the image shows now → what it should become, concretely: the shot, the layout,
   the move, the type treatment, the material and light

## Keep
- what already works and must survive the changes
```

Concrete means buildable: "s1_r9 (c07, 0:43–0:46): two equal cards and a title card stacked like a slide → one answer
card fills the frame, the 1점 badge lands huge on '1점' and flips to 0점 as the second answer slides in" — not "make it
more dynamic".

## 6. What the builder does with it

- Fix the floor first, then take the upgrades from the top.
- **Re-create, don't decorate**: a weak beat is redesigned from its concept (a new shot, a new picture of the idea,
  real material and light), not given small added effects or labels. A round that only adds layers to the same frames
  does not count.
- Keep what the director said to keep; keep timing on phrases (`W()`), the zones and the frame-0 rules.
- Rebuild (`build_gfx.py <tags>`, `preview.py`), re-shoot exactly the stretches you changed into
  `chk/elevate-<n+1>/` and pass the previous round's images with `--before`.
- You may disagree with an upgrade: say why in one line in the next round's `--note`; the director decides. Accuracy
  and the first-time-listener rules outrank a design request.

## 7. Rounds, stopping, reporting

- Up to three rounds by default. Stop earlier when every section scores at least 4 on A, B and C **on the absolute
  scale** and nothing is left on the floor; go past three only when a round still raised scores and the user asked
  for the best possible.
- `review/elevate.md` keeps each round: scores, the upgrades done, the image folders; the director's reports stay in
  `review/art-<point>-<round>.md`.
- The hand-off (and report.md) reports the elevation: rounds, the scores before → after per axis, the most visible
  changes with their before/after images, and what the director still wanted that was not done (and why).
- Time: each round costs fresh images and rebuilds. It is the part of the job the user notices most; spend it.
