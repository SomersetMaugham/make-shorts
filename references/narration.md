# Narration (carried over from script-to-motion)

The shorts' only sound is narration made with script-to-motion's TTS tools, copied into `scripts/narration/`
(provenance and the two local changes: `scripts/narration/SOURCE.md`). Below are script-to-motion's own rules for it,
copied unchanged on 2026-11-19: its SKILL.md steps 3 and 4, then `references/sound.md`, `references/google-tts.md`,
`references/fish-audio.md` and `references/edge-tts-voice.md`.

## How the copied text maps onto this skill

| script-to-motion says | here |
|---|---|
| `<skill>/scripts/tts.mjs`, `wave.mjs`, `sync.mjs`, `phrasing-check.mjs`, `autocut.py` | `scripts/narration/…` (run from `work/`) |
| `<dir>`, the project | `narration/<sk>` — one narration folder per short, written by `scripts/narration_init.py` from `shorts.json` |
| a cue's `text`, `say`, `gapAfter` in script.json | edit them in **`shorts.json`**: `narration_init.py` (prep.sh) copies them into script.json and overwrites edits made there. `cut`, `at` and the top-level settings (`tts`, `leadIn`, `gap`, `tail`, `narration`) live in script.json and are kept |
| `check.mjs` refuses the hand-off | `scripts/check_narration.py` (finish.sh runs it) refuses the final assembly |
| `cue(id).when('phrase')`, the scenes follow the cues | `timeline.py` turns the cues into the runs, the words and the captions; graphics anchor on `W(ws, '<phrase>')` |
| "build and verify the whole video on silent placeholders", "hand it off and ask whether to record" | `finish.sh <sk> --draft` → `chk/<sk>_draft.mp4` + `narration/<sk>/script.txt`; then ask. This is the only question the skill asks. |
| `smoke.mjs`, `errscan.mjs`, `render.py`, clips, footage, dubs, `MEDIA_SRC` | not part of this skill: ignore those sentences |
| "Fish takes come out around −22 LUFS; that is the reference" | the takes stay as recorded; `mix.py` only masters the finished narration to −14 LUFS / −1 dBTP (gain and limiter, never speed) |

After the copied text: the order of work in this skill is in references/pipeline.md.

---

### 3. Write the cues into script.json

Read `references/google-tts.md` first, then §2–§3 of `references/fish-audio.md` (splitting cues and writing `say`
hold for every voice). **If the user gave you a topic or material rather than a finished script**
(a sentence or two, an article, notes, a planning doc, "이 내용으로 영상 만들어줘"), you write the narration.
Read `references/script-writing.md` before drafting, starting with §0: research and the plan. Interpret the numbers
instead of reading them out, explain jargon for newcomers, give every topic change its cushion (close, turn, open with
the reason — **Every topic change gets a cushion**; a cushion is never filler), and use the creator's own sign-off.
Don't show the draft and wait; carry on to the finished video. The essentials:
- **Keep the user's words** when they gave a script, and any wording they dictate later. Split it into
  cues and don't rewrite the content. You only change *how it's
  pronounced* in `say` (numbers, units and English terms in spoken Hangul; sparse expression tags;
  `[break]` pauses). `text` keeps the original spelling for display.
- **The user's own script is used exactly as given.** Don't reword it, and don't offer rewrites. Only `say` gets
  spoken forms.
- **A script you write is speech for a listener who hears it once** (script-writing.md). The first rule is that the
  listener understands it the first time they hear it, and accuracy always comes before convenience:
  - **Order:** conclusion and count first; a one-line recap at the end of a section only in a long or multi-topic
    video (script-writing.md §5) — never in a short one-question video (**Short videos: one question, one answer**).
  - **Sentences:** one idea per sentence, no stacked modifiers or noun chains, one number per sentence, and the screen
    showing what is being said (§5).
  - **Terms:** every technical term is said exactly and explained in plain words when it is first heard (§3).
  - **Names:** one thing, one exact official name, with no convenient shortening and no coined term presented as
    established (§3b).
  - **Spoken Korean, not written** (§5b):
    - sentence endings about **75 % ~니다 · 25 % ~요**;
    - no words or endings that only belong on paper (formal Sino-Korean, paper connectives, 해라체 and report endings,
      passives);
    - no symbols or brackets in `say`;
    - **filler words only where they do a job** (자, = a new beat, 사실 = a truth against expectation, 그러니까 =
      a summary …), never as a quota;
    - never a word the user doesn't say (솔직히);
    - **no AI-style phrasing** in narration or on-screen copy: nothing that sounds polished but makes the listener
      stop and work out what it means. Say literally who did what, what changed and by how much (§5b).
  - You judge all of this yourself, line by line. No script scores wording.
  - **Before a single line is recorded or handed off, it passes the first-time-listener gates** (SKILL.md → Every line
    is for a first-time listener; script-writing.md §0b): the five questions, the neighbours, the seam pass (**Every
    topic change gets a cushion**), the internal-name list and the cold-listener review. No line skips them. That
    includes a line you fix later and every line of a batch edit.
- One cue ≈ one sentence: the unit of visual sync. A long sentence is split at a clause boundary into two cues, never
  shortened.
- Use `gapAfter` to give scene changes and questions a breath, longer than the beat inside a thought. The silence you
  hear is the gap plus the edges the two takes keep after your cuts, so choose it by reading the result with `wave.mjs`,
  not by a number: 0.4 s or more is dead air unless something sounds in it (a clip, a transition sound) — the user's
  rule. The user trims every such gap (references/sound.md §3).
- Stage directions in the script ("[장면 1]", "(화면: …)") are for your storyboard, not for `say`.

### 4. Narration (Google Chirp 3 HD, Enceladus) — recorded only when the user decides, after reviewing the finished video

```bash
node <skill>/scripts/tts.mjs <dir>              # until the user decides: every new cue is a silent placeholder, no API call
node <skill>/scripts/tts.mjs <dir> --approved   # the user reviewed the finished video and said to record: records the takes
```

Every run of `tts.mjs` also writes `script.txt`: the script as plain text, one cue per line, with no ids or times.

**Before `--approved`, every line about to be recorded has passed the first-time-listener gates** (the box at the top;
**Every line is for a first-time listener**). A take costs the user's quota, and a line that only you understand
gets recorded, timed, animated and has to be done again. Never run `--approved` on a line you have not put through the
five questions, its neighbours, the seam pass, the internal-name list and the cold-listener review.

Narration is made with **Google Cloud Text-to-Speech, Chirp 3 HD**, voice **`ko-KR-Chirp3-HD-Enceladus`** (the user's
choice, 2026-11-13; read references/google-tts.md). Don't switch to another voice or another TTS unless the user asks.
Chirp 3 HD often ignores commas and breaks at the wrong word: after recording, check the breaks with
`scripts/phrasing-check.mjs` and fix them with `[pause short]` in `say` (references/google-tts.md). Expression tags and
`<|...|>` directions are Fish-only and are stripped before Google sees the text.

- **Sign-in.** Google needs no key: `tts.mjs` uses `gcloud auth print-access-token` and the gcloud default project
  (Text-to-Speech API enabled, billing on; free for the first 1M characters a month). When the token fails, ask the user
  to run `! gcloud auth login`.
- **Fish Audio instead** (only when the user asks): `"tts": {"provider":"fish"}`, model `drama-3`, the user's own
  voice. Their `FISH_API_KEY` and `FISH_VOICE` are kept in the skill's own `.env` (git-ignored — never in a tracked file,
  a project, output or memory); `tts.mjs` reads them from there (after the environment and any `.env` in the project or
  its parents). Put the voice id in `script.json` `"voice"` too. A project made before 2026-11-13 with a Fish `"voice"`
  and no `"tts"` stays on Fish.
- **The recording waits for the user (default).** Never generate narration on your own: it is their decision and their
  quota. Don't stop earlier to get the lines approved, either.
  - Build and verify the whole video on silent placeholders: `tts.mjs <dir>` without a flag gives each cue an estimated
    timing, and the captions show the lines.
  - Hand it off with the script (`script.txt`) and ask whether to record it now.
  - When the user says to record ("녹음해", "승인"), run `--approved`, then the after-recording pass (below).
  - Some requests count as the decision for those cues (`--approved --only <ids>`): "이 줄 다시 녹음해줘", or a line
    they dictate in an already recorded video.
  - A re-take or rewording you propose needs their OK first.
- **Which voice is used is what `tts.mjs` says** — its `🔑` line on every run names the provider (Google: the voice and
  the gcloud sign-in; Fish: where it found key and voice, or everywhere it looked). Run `tts.mjs <dir>` before deciding;
  never conclude "no key" from one `.env` file (a key in a parent folder's `.env` counts).
- **No voice possible** (the user wants none, or gcloud cannot sign in and they don't log in; on Fish, the `🔑` line says
  not found) → make the video **without narration**: set `"narration": false` in `script.json` and run
  `tts.mjs`. It writes silent audio and times each cue by its estimated reading time; the cues still drive every
  scene. Plan for it: the message must be readable on screen (key lines as on-screen text, or captions on), with
  enough hold time to read. In the hand-off, say the video has no narration and that it can be voiced later.

`tts.mjs` enforces it: without `--approved` it records nothing new (and on Fish, without key and voice it never calls Fish Audio).

**No code decides where silence, a pause or a word is** — the user's rule, without exceptions. The tools only prepare the
level data (`wave.mjs` prints it as numbers); you read it and decide; the tools apply exactly what you wrote in
script.json. Every take is kept exactly as the provider returned it, its edges included:
- **What comes out of a take** (the silence before the first word and after the last, a pause that is dead air) is its
  `cut`, read off `wave.mjs <dir> --unreviewed` / `--cue <id>` — `"ranges": []` when nothing goes (references/sound.md §1).
  A new take without a cut is `unreviewed: true` in js/cues.js, and check.mjs refuses the hand-off until it has one.
- **When a phrase is spoken**, for every phrase the scenes anchor with `cue(id).when('phrase')`, is the second you read off
  the take and write as the cue's `at`; `sync.mjs` turns it into `js/sync.js` (references/sound.md §2). Until then
  `when()` estimates by character position (the player warns for a recorded cue). Never transcribe a take.
- **No dead air**: no silence ≥ 0.4 s anywhere in the finished sound except pauses inside footage shown whole — keep
  `gapAfter` short, and judge the sound yourself by reading it as numbers with `wave.mjs` (references/sound.md §1).

**After-recording pass.** Once the takes are recorded, the cues move to the takes' real lengths and the scenes follow
their labels. Then:
1. Read every new take (`wave.mjs <dir> --unreviewed`), set each one's `cut` (edges included; `"ranges": []` when nothing
   goes) and the `at` times of the phrases `when()` uses, then `tts.mjs`, `sync.mjs`, `check.mjs`, `smoke.mjs` (re-anchor
   any `when()` phrase it reports), then read the whole sound with `wave.mjs` and fix every dead air you find
   (references/sound.md §1: a `cut`, or `gapAfter`).
2. Google voice: run `node <skill>/scripts/phrasing-check.mjs <dir> <new ids>`; where a pause is missing at a comma or
   falls inside a phrase, put `[pause short]` after the comma in `say` (or join the two words in `say` when there is no
   comma), take those cues again with `--approved --only`, redo their cuts, and check again (references/google-tts.md).
3. Tell the user the new length and which takes to listen to first.

You can't hear the audio. **Never transcribe it to judge a take's words or delivery** (no Fish ASR, no speech-to-text
for that) — judging takes is the user's job, not yours. One exception, the user's decision (2026-11-13): with Google,
`scripts/phrasing-check.mjs` cuts each cue at its silences and has Speech-to-Text read each piece, only to show where
the pauses fall ("piece ‖pause‖ piece"), because Chirp 3 HD breaks at the wrong word so often (references/google-tts.md). Lines with expression tags, numbers,
English terms or names are what you ask the user to listen to first. When they report a bad
line, respell `say` or take again with `--approved --only <ids>`. Then search every cue for the same pattern (a
missing pause after a connective, a name run into its version, a verbless list) and fix those too
(google-tts.md; fish-audio.md §3). Re-running is cheap: unchanged cues come from the cache.


---

# Sound — no dead air, timing to the word

What the viewer hears is the narration plus the footage's own sound. This file covers the rules for that mix: dead air
and timing to the word. In both, **no code decides where silence, a pause or a word is** — the tools only prepare the
level data (`wave.mjs`); you read it and decide, and the tools apply exactly what you wrote.

## Contents
1. No dead air (the user's rule)
2. Timing visuals to the word: phrase times you set (`sync.mjs`)
3. Gaps, chapter windows and re-timing
4. Loudness
5. Reporting numbers

## 1. No dead air (the user's rule)

**No silence of 0.4 s or longer anywhere in the finished sound** — narration and footage together; room tone too quiet
to hear counts as silence. The user trims every such gap when editing by hand and called a 9 s pause after an episode
"너무한다".

- The one exception: pauses **inside** footage the video shows whole (a generated clip's own beats between lines). Never
  cut inside it. Where a clip ends on a silent hold, start the next line over the hold while the picture plays out.
- **The end hold** — from the last sound to the video's end (`tail`, the last frame holding) — is not dead air.

**You judge it; no script does.** Deciding by a fixed level or length in code makes mistakes, so nothing in the skill
says "this is silence" — not at a take's edges, not inside it, not in the footage. Every take is kept exactly as the TTS (Google by default, or Fish Audio)
returned it, the silence before its first word and after its last included, until your cut says otherwise.
`wave.mjs` only measures and prints the sound as numbers, and you read them:

```bash
node <skill>/scripts/wave.mjs <dir>                    # the finished sound: one line per second, the level of every 50 ms
node <skill>/scripts/wave.mjs <dir> --from 60 --to 120  # a stretch of it
node <skill>/scripts/wave.mjs <dir> --cue c05[,c06]     # takes as recorded, in seconds of the take (for a cut, an "at")
node <skill>/scripts/wave.mjs <dir> --unreviewed        # every take not read yet (after recording)
node <skill>/scripts/wave.mjs <dir> --no-narration      # the footage's own sound alone (a dub's rooms, dub.mjs)
```

- **What it prints.** Each number is the level (RMS, dBFS, rounded) of 50 ms of what the viewer hears: the narration plus
  every clip playing its own sound, at its placement and volume. `-inf` is digital silence. Marks sit before the window
  they fall in: `|c05` a cue starts, `c05|` it ends, `|c05(placeholder)` a cue not recorded yet (silent), `[clip:key …
  clip:key]` a clip with sound, `✂` where a cut take was joined, `END` the video's end. 20 numbers are one second, so 14
  in a row are 0.4 s.
- **Zero-crossing rate.** A take (`--cue`, `--unreviewed`) prints every window as `level/zcr`, e.g. `-27/7.6`; the whole
  sound does with `--zcr`. zcr is how many times the waveform changes sign per millisecond — how fast it swings. It is
  measured, never judged: the tool says nothing about what the window is.
- **How to read it.** Compare every stretch with the voice right before and after it. Silence is what a listener hears
  as nothing said and nothing sounding: digital silence, the floor of a take, room tone too quiet to hear, and a lone
  breath in a pause (the listener is still waiting). A soft syllable or a word's fading end is voice, not silence — tell
  them apart by reading the stretch's level and zcr against the voice around it and the words of `say` you expect
  there. Count the windows of each silence; 8 or more (0.4 s) is dead air,
  unless it is the exception or the end hold above.
- **Reading zcr with the level.** The level says how loud a window is; the zcr says how fast its waveform swings. What
  they mean physically: voiced sound (vowels, a hum) is periodic with its energy low in frequency, so it swings
  comparatively slowly; noise-like sound (breath, hiss, the friction of ㅅ ㅈ ㅊ ㅎ, a take's floor) carries more high
  frequencies and swings faster; digital silence does not swing (`0.0`). There is no number that makes a window one or
  the other: read each window against the windows around it in the same take, and against the words of `say` you
  expect there — whether a quiet, fast-swinging stretch is a word's first consonant, a breath or the floor is your
  reading. A worked reading of the user's take op01 ("자 이전…", `--step 0.01`, from 0 s): `-63/2.7 -64/5.6 -59/5.7
  -54/8.6 -41/11.0 -30/12.2 -34/11.2 -39/5.9 -33/1.9 -30/0.8 -21/1.2`. The windows from 0.03 s swing much faster than
  the vowel windows that follow and lead straight into them, and the line begins with 자 — so they were read as its ㅈ,
  and the word as starting at 0.03 s, not where the level jumps.
- **After recording, every new take** (`--unreviewed` lists them; js/cues.js marks them `unreviewed: true`): decide
  what comes out of it — the silence before the first word, after the last, and any pause inside that is dead air — and
  write the cue's `cut` (below), `"ranges": []` when nothing goes. `tts.mjs` applies it; `check.mjs` refuses the hand-off
  while any take is unread, and `dub.mjs` refuses a dub track. Takes cached before 2026-11-09 had their edges cut by the
  old tts.mjs (`--cue` says so): read them like the others; what was cut from them is gone.
- **When.** After recording and every re-take, after any re-timing (`gapAfter`, `leadIn`, `tail`, chapter windows), after
  a clip is placed or moved — and over the whole video before the hand-off whenever it has recorded takes or clip sound.
  While cues are placeholders their stretches are silent by design; the gaps between them are exactly their `gapAfter`
  (§3), so read again once they are recorded.
- **Fix it by where it is** (the marks tell you):
  - **at a take's start or end** (from `|c05` to its first voice, or from its last voice to `c05|`): read the take with
    `--cue c05`, choose where the voice begins and ends — keep the breath into the first word and the fading end of the
    last; cut only in the silence, never into the voice — and cut `[0, a]` and/or `[b, <the take's length as --cue
    prints it>]`; nothing of an edge stretch is kept (no crossfade there);
  - **between two lines** (the silence spans `c04| … |c05`): first the edges of both takes (above), then shorten `gapAfter` of the earlier cue (`leadIn` before the
    first line), run `tts.mjs`, read again;
  - **inside a take** (between `|c05` and `c05|`, with no cue mark inside it): read the take with `--cue c05`, choose the
    stretch to take out — inside the silent run only, never into the voice, leaving enough of the silence on each side that it
    still sounds like a pause between those words (how much is your reading of the pause and the words around it) — and write it as the cue's `cut` in script.json, with the take id that `--cue` printed:
    ```json
    { "id": "c05", "say": "…", "cut": { "take": "d525479975b02b635b5afc45", "ranges": [[1.35, 2.05]] } }
    ```
    `tts.mjs` takes exactly those stretches out (a 10 ms crossfade at each join) and moves the later cues up; then
    `sync.mjs`, and read again. A cut belongs to its take: after a re-take `tts.mjs` says the cut was not applied —
    read the new take and set it again. Another way is a re-take with a reworded `say`, which costs credits: only
    when the user decides;
  - **at a clip's silent tail**: start the next line over it;
  - never by inserting sound effects, never by speeding anything up.

## 2. Timing visuals to the word: phrase times you set (`sync.mjs`)

Only what must land on a spoken word uses `when()` — a number as it is said, a highlight on the word, an item as it is
named; what only follows the line uses a cue label, `at(f)` or `about('phrase')` (references/player-api.md), and needs no
time. Read only the stretch around a phrase: `--from` / `--to` (seconds in the take).

`cue(id).when('phrase')` estimates by character position until you set the phrase's time. No code looks for words or
pauses in a take: you read the take and say where the phrase starts.

1. **Read the take** at 10 ms: `node <skill>/scripts/wave.mjs <dir> --cue c05 --step 0.01 [--from 1 --to 2.5]` — seconds in the take as
   recorded, the clock a `cut` uses. Find where the phrase's first syllable starts: where the voice rises after the pause
   before it, or, inside a run of voice, by counting the syllables of `say` across it against the pauses you see. Read the
   zcr with the level (§1) where the level alone does not show where a syllable begins — compare each window with the
   ones around it and with the sound the phrase begins with in `say`; where it starts is your reading. Then check the
   reading against the words: the syllables of `say` between two points you are sure of (a pause, a clear consonant)
   must fit the time between them at the pace the rest of the take is spoken — a phrase placed so that its syllables
   would have to be said far faster or slower than their neighbours is misplaced (a closure read as a nasal, a dip read
   as a boundary): read it again.
2. **Write it** in script.json, with the take id `--cue` printed and the phrase exactly as it is in the cue's `text`
   (what `when()` looks up):
   ```json
   { "id": "c05", "say": "…", "at": { "take": "d525479975b02b635b5afc45", "phrases": { "천억": 1.35, "영상 그 자체": 3.02 } } }
   ```
3. **`node <skill>/scripts/sync.mjs <dir>`** writes `js/sync.js`: each time moved back by the stretches the cue's cut
   takes out before it. It refuses a phrase that isn't in the text, a time inside a cut or past the take's end.

From then on `when()` returns that moment — numbers land on the word that says them, a highlighter sweeps under the
spoken word. Set a time for every phrase the scenes anchor with `when()` on a recorded cue: for any other the player
uses the estimate and warns once (errscan.mjs lists them); check.mjs warns when `js/sync.js` doesn't say what
script.json sets. An `at` belongs to its take, like a cut: after a re-take sync.mjs reports it unused — read the new
take and set it again. A changed cut needs `tts.mjs` then `sync.mjs` (the times stay: they are on the take's own clock).
Placeholder cues have no take; their `when()` keeps the estimate until they are recorded.

## 3. Gaps, chapter windows and re-timing

- Defaults (`new_project.mjs`, `tts.mjs`): `leadIn` 0.3 s, `gap` 0.25 s between lines, `tail` 1.5 s — the end hold,
  where the last frame holds after the last line (not dead air, §1).
- **The silence you hear is longer than the gap.** Between two lines it is the silence the earlier take keeps after its
  last word + `gapAfter` + the silence the next take keeps before its first word — the takes' edges as your cuts left
  them (§1). Don't add it up: read it with `wave.mjs`, counting the windows from the last voice of one line to the first
  voice of the next. (Takes cached before 2026-11-09 were cut by the old tts.mjs itself, to 0.04 s before the
  first sample above −38 dBFS and 0.12 s after the last.)
- `gapAfter` gives a scene change or a question a breath, longer than the beat inside a thought. Choose it by reading
  the result: with the edges around it the whole silence stays under 0.4 s (§1) unless something sounds in it.
- Changing gaps re-times without new API calls: edit script.json, run `tts.mjs` (unchanged takes come from the cache),
  then `sync.mjs`, `check.mjs`, and read the sound with `wave.mjs` (§1).
- Chapter transitions (long-form.md) start `lead` s before the chapter's first line but never more than 0.25 s before the
  previous line ends — the transition plays under the end of the last sentence, not in a silent gap.
- A hook that plays an output (an episode, a demo) starts it right after the line that introduces it
  ("먼저 보시죠" → the clip starts as that line's last word ends — read where with `wave.mjs`) and the next line starts as soon as the clip's sound ends.

## 4. Loudness

- Fish takes come out around −22 LUFS integrated; that is the reference (`MEDIA_SRC.level`). Footage is level-matched
  to it per clip (`lufs`), then shaped by its envelope (references/footage.md §7).

## 5. Reporting numbers

When you hand over audio, report **every** factor that changes it: early starts, level changes, re-takes and why. There is
never a speed factor to report — no TTS speed, no time-stretch, no playback rate on anything with sound. Say what the user should listen to first (the lines with the largest change, numbers and
names, tags).

---

# Narration with Google Cloud TTS (Chirp 3 HD) — the default voice

Since 2026-11-13 (the user's choice) narration is made with Google Cloud Text-to-Speech, Chirp 3 HD, Korean male voice
**Enceladus**. Fish Audio (references/fish-audio.md) and edge-tts (references/edge-tts-voice.md) are used only when the
user asks for them. §2–§3 of fish-audio.md (splitting the script into cues, writing `say`) hold for every voice; its
drama-3 directions and expression tags do not apply here.

## 1. Settings

script.json (new_project.mjs writes this):

    "tts": { "provider": "google", "voice": "ko-KR-Chirp3-HD-Enceladus" },
    "gap": 0.12,            // and "gapAfter": 0.12 per cue — Google takes keep pauses of their own

A script.json without `"tts"` and without a Fish `"voice"` gets the same default. Optional: `"lang"` (default ko-KR),
`"gcloud"` (path to the CLI; or GCLOUD_BIN).

- **Sign-in, no key.** tts.mjs takes a token from `gcloud auth print-access-token` and the project from
  `gcloud config get project`. The project needs the Text-to-Speech API enabled and billing on. Chirp 3 HD is free for the
  first 1M characters a month. The token lasts about an hour: on an auth error the user runs `! gcloud auth login`.
- **Other Korean male Chirp 3 HD voices** (only if the user asks to change): Achird Algenib Algieba Alnilam Charon
  Enceladus Fenrir Iapetus Orus Puck Rasalgethi Sadachbia Sadaltager Schedar Umbriel Zubenelgenubi
  (`ko-KR-Chirp3-HD-<Name>`; list with GET /v1/voices?languageCode=ko-KR).
- Speed stays 1. Recording still waits for the user's decision (`--approved`), as in SKILL.md step 4.

## 2. What a Google take is like

- Lead silence 0.3–1.0 s, a trailing floor, and 0.3–1.0 s pauses between phrases. Every take needs a `cut`: lead and
  tail to ~0.06 s, interior pauses over ~0.35 s down to ~0.27 s (shorter pauses stay — flattening them all erases the
  difference between a sentence break and a phrase break, which the user heard as wrong phrasing). Then scan
  audio/narration.wav for runs below −55 dBFS of 0.4 s or more: exactly 0.4 s counts as dead air.
- **Not deterministic**: the same text gives a different take on every call. A re-take is a new reading, so the approved
  takes exist only in the project's `.tts-cache/` — commit it (don't git-ignore it) or keep it safe.
- A cue whose `say` did not change keeps the **same take id** when it is taken again (`--only`), so its old `cut` silently
  lands on the new audio. Redo the cut after every re-take.

## 3. Wrong phrase breaks — the main problem, and the fix

Chirp 3 HD often ignores commas: it runs on through a comma and breaks one or two words later
("깎고 ‖ 녹이면 바위", "새 없이 비가 ‖ 새 물을", "다음에 ‖ 바닷물을 맛보게 되면 오랜 세월"). On the seawater video 16 of 25
cues had it. Extra commas do not help, a plain re-take is a coin flip, and "..." gives a ~0.9 s pause.

- **Fix:** put `[pause short]` right after the comma in the cue's `say`: `"녹이면, [pause short] 바위 속의"`. tts.mjs sends
  Google a `markup` input when `say` contains `[pause]`, `[pause short]` or `[pause long]` (other `[..]` tags are still
  stripped). The tag is not read aloud and it also pulls the words before it into one phrase. `text` (the caption) gets
  no tag.
- **A break where there is no comma** ("바다 ‖ 바닥에"): join the words in `say` only (`바다바닥에`).
- **A pause the user asks for** ("'양도 강이' 사이에 쉼표"): `"양도, [pause short] 강이"` in `say`, and the comma in `text`.
- The user confirmed the result: "다른 부분은 거의 완벽할 정도로 고쳐졌어요."

## 4. Checking the breaks (you can't hear)

    node <skill>/scripts/phrasing-check.mjs <project> [c01 c02 …]

It cuts each audio/cues/<id>.wav at its silences (−42 dB, ≥ 0.15 s) and has Speech-to-Text v2, model chirp_2
(us-central1), read each piece, printing `piece ‖pause‖ piece` under the cue's `say`. A comma with no ‖ after it, or a
‖ inside a phrase, is a wrong break. Needs `gcloud services enable speech.googleapis.com` once (60 min a month free).
This is the one speech-to-text use the user allowed: only where the pauses fall, never to judge words or delivery.
Do not read the STT word timestamps instead: in v1 and v2 they shift by about a word around a pause.

## 5. The loop

1. Tag (`[pause short]`) or join words in `say` for every wrong break found.
2. `node <skill>/scripts/tts.mjs <dir> --approved --only <ids>` (the user's report or OK is the decision).
3. Cuts for the new takes: `python3 <skill>/scripts/autocut.py <dir> <id,id,…>` writes a first draft of each cut
   (lead to 0.06 s before speech, 0.10 s tail, interior −50 dB runs over 0.35 s down to ~0.27 s; it matched hand cuts
   within 0.1 s). The cut is still yours (SKILL.md: no code decides where silence is): read each take with
   `wave.mjs <dir> --cue <id>` and correct the numbers before keeping them.
4. `tts.mjs <dir> --approved` (applies the cuts), then `phrasing-check.mjs` on those cues; repeat for what is left.
5. Dead-air scan, `check.mjs`, then ask the user to listen — intonation and speed are not checked by any of this.

---

# Narration with Fish Audio (only when the user asks for it)

The default voice is Google Chirp 3 HD Enceladus (references/google-tts.md). Use this page when script.json has
`"tts": {"provider": "fish"}` (or a project from before 2026-11-13 with a Fish `"voice"` and no `"tts"`). §2–§3 (cues, `say`)
hold for every voice.

How to turn the user's script into `script.json`, how `tts.mjs` talks to Fish Audio, and what to do
when a take is wrong.

## Contents
1. script.json
2. Splitting the script into cues
3. Writing `say` (pronunciation, tags, pauses)
4. What tts.mjs does
5. Reviewing takes you can't hear
6. API facts & troubleshooting

---

## 1. script.json

```json
{
  "title": "웹이 곧 영상이다",
  "lang": "ko",
  "voice": "<the user's Fish Audio voice model id>",
  "model": "drama-3",
  "temperature": 0.7,
  "leadIn": 0.3,
  "gap": 0.25,
  "tail": 1.5,
  "cues": [
    { "id": "c01", "say": "[calm] 영상은 더 이상 파일이 아닙니다.", "text": "영상은 더 이상 파일이 아닙니다." },
    { "id": "c02", "say": "이천이십육 년, 브라우저가 렌더러가 됩니다.", "text": "2026년, 브라우저가 렌더러가 됩니다.", "gapAfter": 0.3 }
  ]
}
```

| field | meaning |
|---|---|
| `narration` | `false` = a video without narration (no Fish Audio call; silent audio; cues timed by estimated reading time). Use it when the user didn't provide their Fish Audio API key and voice id. Default: narration on. |
| `voice` | Fish Audio voice model id (`reference_id`) — **the user's, required**. The user keeps it as `FISH_VOICE` in the skill's `.env` (git-ignored) with `FISH_API_KEY`; copy the id into `script.json`. Never choose or guess a voice; `tts.mjs` only calls the API with a voice id and the user's API key. |
| `model` | **`drama-3`** — the user's model, the default: directed in plain language (below). Docs: https://docs.fish.audio/features/text-to-speech and https://docs.fish.audio/features/text-to-speech/drama-3. Sent as the `model` request header; a missing or misspelt header does **not** fail — it silently falls back to `s2.1-pro`, so keep the exact name. Other models (`s2.1-pro`, `s2-pro`) only when the user asks. |
| (speed) | **None — the voice is never slowed down or sped up** (the user's absolute rule). `tts.mjs` always sends `prosody.speed` 1 and refuses a `speed` other than 1 in `script.json` or on a cue. A take that sounds rushed gets pauses in its `say` — a comma, or `...` between two sentences (`코드깎는 노인이었습니다... 감사합니다.` gave a 0.4 s pause where the plain text gave none) — or a fresh take (`--only <id>`); a line too long for its slot is reworded. |
| `temperature` | 0–1 expressiveness/variation. 0.7 default; lower (0.5) if takes sound inconsistent across cues. |
| `leadIn` | seconds of silence before the first cue (the opening visual gets a moment). |
| `gap` | default silence between cues. |
| `tail` | seconds after the last cue before the video ends (final frame hold). |
| cue `id` | alphanumeric, starts with a letter: `c01`, `c02`… (they become timeline labels). |
| cue `say` | exactly what the TTS reads (may contain tags / phonetic spellings). |
| cue `text` | what a viewer reads: captions, `when()` phrase lookup. Defaults to `say` without tags. |
| cue `gapAfter` | silence after this cue (overrides `gap`). |
| cue `captions` | optional list of one-line caption segments for this cue, e.g. `["아무 말 없이 지나가면", "조금 전까지 인사하던 사람이", "갑자기 쌀쌀맞아진 것 같다."]`. Without it the player splits `text` automatically. |

## 2. Splitting the script into cues

- **Keep the user's words.** The script is theirs: don't paraphrase, shorten, reorder or "improve" it.
  You split it and adjust only *how it's pronounced* in `say`. If something seems wrong (typo, a
  sentence that obviously doesn't belong), keep it and mention it in your summary.
- One cue ≈ one sentence. Split a long sentence at a natural clause boundary (after `-고,` `-며,` `-지만,` `, `
  etc.) so visuals can change with the thought. Splitting never removes words (SKILL.md → Content first, never time).
- Merge a fragment that carries no thought of its own into its neighbour, unless it is a deliberate punch line.
- Headings or labels in the script that aren't meant to be spoken (e.g. "[장면 1]", "(자막: …)",
  "#인트로") are directions for you, not narration — use them in the storyboard, leave them out of `say`.
- `gapAfter`: a shorter beat inside a thought, a breath at a scene/section change or after a question. What is heard is
  the gap plus the edges the two takes keep after your cuts — read it with `wave.mjs` rather than adding numbers. Never 0.4 s or more
  in silence: that is dead air (references/sound.md §1) — when a change needs a longer beat, fill it with sound (the next
  clip, a transition sound) or start the next line under the transition.

## 3. Writing `say`

Fish's text normalisation is tuned for English and Chinese, so spell out anything a Korean reader
would read differently from how a model might:

| display (`text`) | `say` |
|---|---|
| 2026년 | 이천이십육 년 |
| 3.5배 · 70.6% | 삼쩜오 배 · 칠십쩜육 퍼센트 (decimal as one word with `쩜`; spaced "삼 점 오" is read choppily) |
| Sonnet 5.5 · iPhone 17 · GPT-6 (name + version) | 소넷오쩜오 · 아이폰십칠 — **no space** between name and number, or the voice pauses after the name. Decide once whether a version is read in Korean or English ("소넷파이브") and keep it consistent |
| 1,280,000명 | 백이십팔만 명 |
| 15% | 십오 퍼센트 |
| 10~20분 | 십 분에서 이십 분 |
| 3시 30분 | 세 시 삼십 분 |
| 1위 / 2개 / 3명 | 일 위 / 두 개 / 세 명 (native vs Sino-Korean counters!) |
| A/B 테스트 | 에이비 테스트 |
| AI, API, UX | 에이아이, 에이피아이, 유엑스 (common ones usually work as-is; spell out if a take comes back wrong) |
| → , · , / | 그리고, 쉼표, 또는 — or restructure the sentence |
| URLs, emails | say them the way a person would ("fish 점 audio"), or leave them on screen only |

Spoken register (script-writing.md §5b): a filler word at the start of a line takes a comma in `say` (`자, 결과를
볼게요` / `사실, …`) so the voice breathes after it; hesitation sounds (`음…`) go in `say` only.

Punctuation shapes delivery: commas are short pauses, periods longer, `?` rises. Avoid ellipses and
exclamation marks unless the script has them.

**Pauses and grouping (Korean).** The voice groups words by spacing and punctuation, and a wrong group
changes the meaning. Put commas in `say` only; `text` keeps normal punctuation for captions. Each rule
below came from a real misreading:

| problem | `say` fix |
|---|---|
| a sentence-initial connective runs into the next word ("대신 같은 일을" heard as one phrase) | comma after it: `먼저,` `대신,` `반대로,` `다만,` `특히,` `결국,` |
| a long modifier clause runs into a name or term ("…해내는지 보는 터미널 벤치에서") | comma before the name: `…해내는지 보는, 터미널 벤치에서,` |
| a verbless list of short nouns ("코딩, 실무, 컴퓨터 조작까지.") gets garbled or skipped | rewrite as a clause: `코딩과 실무, 그리고 컴퓨터 조작까지, …` |
| homophones: "2점" is read `이 점`, heard as "this point"; `이 위`, `일 등` similar | rephrase ("사실상 동점", "두 번째 자리") or keep the number on screen only |
| a line ends on a particle ("…단가로.") and sounds cut off | finish the sentence (script-writing.md §5) |

When the user reports one of these on one line, **search all cues for the same pattern** and fix them
together, then list which lines you changed so they can listen.

**Expression tags** (S2 models; free-form natural language in square brackets, not spoken):
- emotion: `[calm]` `[confident]` `[warm]` `[excited]` `[serious]` `[sad]` `[hopeful]` `[surprised]` …
- tone: `[soft]` `[whispering]` `[emphasis]` `[hurried]` `[shouting]`
- effects: `[laughing]` `[sighing]` `[chuckling]`
- pauses: `[break]` (short), `[long-break]`

Put a tag at the start of the sentence it colours; combine at most 2–3. Use them where the script's
mood actually shifts (the hook, the turn, the closing line), not on every cue — over-tagging sounds
theatrical. A calm, confident explainer usually needs almost none.

## 4. What tts.mjs does

```
node <skill>/scripts/tts.mjs <project> [--approved [--only c03,c07 | --force]] [--placeholder]
```

1. Hashes each cue's (model, voice, say, temperature) → `.tts-cache/<hash>.pcm`. Unchanged
   cues are reused; editing one cue only re-synthesises that cue. `--only` forces new takes for the
   listed cues (the voice samples randomly, so a new take differs); `--force` redoes all.
2. Calls `POST https://api.fish.audio/v1/tts` (header `model`, body `reference_id`, `format: "pcm"`,
   44.1 kHz), 3 requests in parallel, retrying 429/5xx.
3. Keeps each take exactly as Fish Audio returned it — no code decides where its silence is. What comes out (the silence
   before the first word and after the last included) is your `cut`, read off `wave.mjs` (references/sound.md §1); a new
   take without one is marked `unreviewed: true` in js/cues.js and check.mjs refuses the hand-off until you set it.
4. Applies the cuts, then lays cues out: `start = leadIn`, then `end + gapAfter` for each next cue.
5. Writes `audio/cues/<id>.wav`, `audio/narration.wav` (t=0 aligned) and `narration.mp3` (ffmpeg), and
   `js/cues.js`.
6. Prints the timeline.

`--placeholder` makes silent audio with estimated timing and marks the data `placeholder: true`;
tts.mjs and check.mjs warn about it. Use it only to build visuals while waiting for a key, and always
regenerate before delivering.

## 5. Reviewing takes you can't hear

You can't listen, and TTS occasionally mispronounces, skips or repeats words. **Never transcribe the
takes** — no Fish ASR (`/v1/asr`), no other speech-to-text service or model. It costs API credits,
and judging whether a take is right is the user's job; the audio is only ever sent to the TTS endpoint
that creates it.

What you can do:
- **Prevent misreadings up front** with careful `say` spellings (§3) — this is where most problems are
  avoided.
- **Ask the user to listen.** In the hand-off, point to `audio/narration.mp3` and to the specific
  `audio/cues/<id>.wav` files worth checking: lines with expression tags, numbers,
  English terms, names.

When the user reports a bad line: if it's a misreading, respell `say` (phonetic Hangul, split the
sentence, add a comma) and re-run; if `say` is fine, take again with `--approved --only <id>` (their report is the decision).

## 6. API facts & troubleshooting

- Auth: `Authorization: Bearer <key>`. The script reads `FISH_API_KEY` (or `FISH_AUDIO_API_KEY`) and `FISH_VOICE` from
  the environment, else from a `.env` in the project folder or any parent folder, else from **the skill's own `.env`**,
  where the user keeps their keys (git-ignored). Never copy a key into the deliverable, a tracked file, output, a URL
  or memory. When the user gives a new key in chat and asks to keep it, replace the line in the skill's `.env` only.
  No key and voice id → the video is made without narration (SKILL.md step 4).
- `drama-3` and `s2.1-pro` support Korean and many other languages; output 16-bit mono (`format: "pcm"`).
- No word-level timestamps are returned — you read phrase times off the takes with `wave.mjs` and set them
  (script.json `at`, then `sync.mjs`; references/sound.md §2).
- 401 → key invalid. 402 → account out of credit (tell the user; don't retry). 429/503 → retried
  automatically; if it keeps failing, wait and re-run (cached cues are kept).
- A voice that sounds wrong for every cue → check `voice` in script.json.
- Uneven loudness between cues is normalised by the API (`prosody.normalize_loudness` default).

## 7. After the takes

- Read every new take (`wave.mjs <dir> --unreviewed`) and set its `cut` — the edges included, `"ranges": []` when nothing
  goes — then `tts.mjs` again (references/sound.md §1).
- Set the time of every phrase the scenes anchor with `cue(id).when()` (script.json `at`, read off `wave.mjs --cue`),
  then `sync.mjs` (references/sound.md §2). Again after every new take.
- Dead air ≥ 0.4 s (the user's rule) is judged by you, reading the sound as numbers with `wave.mjs` (references/sound.md §1).

## 8. Directing drama-3

drama-3 takes directions inside the text (none of them are spoken):
- **Delivery in plain words**, in brackets before the words it applies to — written like a brief to a voice actor, in
  Korean or English: `[호기심을 확 끄는 유튜버 오프닝, 자신 있게]`, `[barely holding it together, forcing a smile]`.
  Keep them sparse: the opening, a turn, a reveal, the sign-off — not every line.
- **Sounds and pauses where they happen**: `[짧은 웃음]`, `[small laugh]`, `[sigh]`, `[shaky breath]`, `[short pause]`.
- **Only some words**: paired tags `<emphasis>…</emphasis>`, `<whisper>`, `<soft>`, `<stress>`, `<forceful>` — e.g.
  `딱 <emphasis>두 배</emphasis>죠`. **Never `<fast>` / `<slow>`**: they change the speaking speed, and the voice is always
  generated at 1× (tts.mjs refuses them). For pace, use pauses (`,` `...` `[short pause]`) or reword.
- **Pronunciation**: phoneme tags `<|phoneme_start|>…<|phoneme_end|>` (English Arpabet, Chinese pinyin, Japanese
  romaji); for Korean, respell in Hangul instead (§3).
- **Another language for a phrase** (experimental): `<english>…</english>`; prefer writing the term as it is said.
- Directions go in `say` only; `text` stays clean for captions (and for the phrases `when()` and `at` use).

## 9. Recording waits for the user's decision

Narration is generated only when the user decides to record (SKILL.md step 4). That happens after they have reviewed the
finished video, which you build and verify on silent placeholders without stopping to show the lines. `tts.mjs <dir>`
without `--approved` records nothing new: new cues are silent placeholders with estimated timing, and `--only` /
`--force` refuse to run without it. Hand off the finished video with `script.txt`, ask whether to record, and on their
word run `tts.mjs <dir> --approved`, then the after-recording pass (SKILL.md step 4).

---

# edge-tts voice (only when the user asks for it)

The default voice is Google Chirp 3 HD Enceladus — references/google-tts.md. This page is for edge-tts, kept as an option.

scripts/tts.mjs accepts in script.json (with "narration": true; takes still need `--approved`; speed stays 1):

    "tts": { "provider": "edge",   "voice": "ko-KR-InJoonNeural" }          # `edge-tts` CLI on PATH (or EDGE_TTS_BIN); unofficial Microsoft endpoint, commercial terms unclear
    "tts": { "provider": "google", "voice": "ko-KR-Chirp3-HD-Enceladus" }  # Google Cloud TTS; needs `gcloud auth login`, a project with the Text-to-Speech API enabled and billing on

Google settings, takes and phrase-break fixes: references/google-tts.md.

Both carry lead silence (0.3-1.0 s), a trailing floor and 0.3-1.0 s pauses between phrases. Set a `cut` for every take (lead and tail to ~0.06 s, interior pauses >= 0.3 s to ~0.2 s), use `gapAfter` ~0.1, then scan audio/narration.wav for runs below -55 dBFS of 0.4 s or more: a pause of exactly 0.4 s counts as dead air. A cut names the take id, so changing the voice needs every cut redone.
