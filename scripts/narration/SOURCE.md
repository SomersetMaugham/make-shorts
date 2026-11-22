# Where these files come from

Copied from the script-to-motion skill (`/Users/admin/.hermes/skills/creative/script-to-motion`) on 2026-11-19, so the shorts narration works exactly as it does there:
Google Cloud TTS Chirp 3 HD (`ko-KR-Chirp3-HD-Enceladus`) by default, Fish Audio or edge-tts on request, recording only
on the user's decision (`--approved`), takes kept as returned, cuts and phrase times read by the agent off `wave.mjs`
and applied by `tts.mjs` / `sync.mjs`. The rules are in `references/narration.md`.

Messages in these scripts still name script-to-motion's files (`check.mjs`, `references/sound.md`). Here they mean:
`check.mjs` → `scripts/check_narration.py`; `references/sound.md`, `google-tts.md`, `fish-audio.md` →
`references/narration.md`.

## Local changes (everything else is byte-for-byte the upstream file)
- `wave.mjs`: no browser. Upstream opens the project's `index.html` to mix in clips; a shorts narration folder has no
  page and no clips, so the whole sound is `audio/narration.wav` timed by `js/cues.js`. `parseArgs` is inlined, and
  `lib/browser.mjs` (Playwright) is not copied.
- `lib/env.mjs`: `SKILL_ENV` goes one folder further up, so the skill's own `.env` is still the skill root's `.env`
  (git-ignored; where a Fish Audio key lives if the user ever asks for Fish).
- `lib/generated.mjs`: `projectOf` also accepts a folder with `script.json` and `.tts-cache/` (a shorts narration folder
  has no `index.html`). Without it, tts.mjs never recorded new takes in `generated.json` and then warned that they were
  "cached before the tools kept it", telling the agent to ask the user about `--record-cache` (found on the first real
  recording, 2026-11-19).

- `phrasing-check.mjs`: prints a verdict per cue (`lib/breaks.mjs`, local: lines the heard text up with `say` and
  checks every comma, pause tag and sentence end for a silence), writes `<dir>/phrasing.json` and exits 1 on a missing
  pause (2026-11-20). It also reads `js/cues.js` for each cue's take, so the verdict goes stale when the take changes.
- `autocut.py`: a `[pause]` / `[pause long]` in `say` keeps the longest silence(s) at 0.55 / 0.8 s instead of 0.27 s
  (2026-11-20, PN a03). Lines without those tags are cut exactly as upstream cuts them.

- `tts.mjs`: a re-take whose `say` did not change has the same take id, so it used to overwrite the take it replaces.
  That take now moves to `.tts-cache/replaced/<take>.<cue>.<time>.pcm` first, so the take a review note was about can
  still be measured (2026-11-20; on the PN short the take heard as too fast was lost this way).

## Upstream sha256 at copy time
- `tts.mjs`  1942000ee5ad2acad8582a82f3973aed00ed9da53613c77e655d574cc7dd50d0
- `wave.mjs`  7c87578787812a023f953c68d1341c47b452b52fd19f94d425ad4c4ed2b77039
- `sync.mjs`  553ae71178e763b6381456c943e2a5b994d6808d5bdfaf23ee065628ea059b11
- `phrasing-check.mjs`  0270f1868252136e9e311a2245a765db443383c00d262a55724b1e9a5f6c0829
- `autocut.py`  b117b2c2bbdf44961ebf09cf2083af789e603811fbe7b31637a4a61f051e2e1a
- `lib/env.mjs`  0d75406fe492fe911c40c760fcf2796fc672d3432ddff63adf92f3198e7e0f7c
- `lib/generated.mjs`  74a9bef9ea7c2f4b0889d872f9c1a2a16c9ec723620b90d1b3ac213d87b20f00
- `lib/phrases.mjs`  bef87224abb65a760a98e466a23976d4c7c769d4f26b9371451973ef31303a88
- `lib/scriptsig.mjs`  ad74125845d0a09afdb66006098af8565a692ddeb34ea6d434bf326b0c0fc176

`sync_upstream.sh` compares each file with the upstream copy and lists what changed there since; it never overwrites.
- `tts.mjs` (2026-11-23): paragraph recording, Google only. `"tts": {"paragraphs": 5}` (or named groups) records up to 5
  consecutive cues in one request and cuts the take into one take per cue at script.json `"splits"` (proposed from
  pauses and syllable counts when absent, then confirmed with phrasing-check). Each piece is an ordinary
  `.tts-cache/<take>.pcm`, so cut / at / wave / sync / checks are unchanged. `--only` re-takes the whole paragraph; the
  paragraph take it replaces moves to `.tts-cache/replaced/`. Without `"paragraphs"` the script behaves exactly as before
  (PN part 4 rebuilt byte-identical). Why: references/narration.md, Google §6.
