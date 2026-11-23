"""Write each short's narration folder from shorts.json: narration/<sk>/script.json, the file script-to-motion's
tts.mjs reads. One shorts.json line = one cue (≈ one sentence).
usage: python scripts/narration_init.py [s1 s2 ...]        (every short in shorts.json when none is given)

What comes from shorts.json, per line: id, text (shown: captions), say (spoken: numbers, units and English terms in
spoken Hangul, [pause short] where Chirp 3 HD breaks wrongly; defaults to text), gapAfter and noPause (optional).
The readings in the pronunciation lexicon (scripts/lexicon.py) are applied first. Every comma in say gets a
[pause short] after it here, before any recording (Chirp 3 HD ran on through 16 of 19 commas
on the PN short and the user had to find them by ear; references/narration.md §3). A comma already followed by a tag
keeps it, and so does a line already in script.json with the same untagged say (a take recorded before this rule
stays valid). Off for one line: "noPause": true on the shorts.json line; off for a short: "autoPause": false in script.json.
What is never touched once it is in script.json: every cue's "cut" and "at" (the agent read them off the takes; they
belong to a take) and the top-level narration settings ("tts", "voice", "narration", "leadIn", "gap", "tail" ...),
so a re-run after a wording change keeps everything the takes already have. A cue whose say changed gets a new take
on the next recording and tts.mjs reports its cut as not applied (references/narration.md)."""
import json, os, re, sys

sys.path.insert(0, 'scripts'); import config as C, lexicon, prosody_prep

S = json.load(open('shorts.json', encoding='utf-8'))
DEFAULTS = {
    # narration: Google Cloud TTS, Chirp 3 HD, Korean male voice Enceladus (script-to-motion's default since
    # 2026-11-13; gcloud sign-in, no key). Fish Audio instead: "tts": {"provider": "fish"} + the user's voice id in "voice".
    # paragraphs: up to 5 consecutive lines recorded in one request so they share one pace (2026-11-23, the user's
    # choice after the PN part 4 test: line-to-line sd 0.49 -> 0.19 syl/s; references/narration.md, Google §6)
    'tts': {'provider': 'google', 'voice': 'ko-KR-Chirp3-HD-Enceladus', 'paragraphs': 5},
    'lang': 'ko',
    'leadIn': 0.3,
    'gap': 0.12,      # Google takes keep 0.3-1.0 s pauses of their own: a short gap avoids dead air
    'tail': 1.5,      # the end hold after the last line (not dead air)
}

COMMA = re.compile(r'(?<!\d),(?!\d)(?!\s*\[pause)\s*(?=\S)')   # not 1,000; not one already tagged; not at the end


LEX = lexicon.load()


def auto_pause(say):
    return COMMA.sub(', [pause short] ', say)


def spoken(say):
    """the readings the user already corrected (lexicon.py), then a pause after every comma"""
    return auto_pause(lexicon.apply(say, LEX))


for sk in sys.argv[1:] or list(S):
    sh = S[sk]
    d = C.ndir(sk); os.makedirs(d, exist_ok=True)
    p = f'{d}/script.json'
    old = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
    out = {k: v for k, v in old.items() if k != 'cues'}
    for k, v in DEFAULTS.items(): out.setdefault(k, v)
    out['title'] = sh.get('title', out.get('title', ''))
    prev = {c['id']: c for c in old.get('cues', [])}
    cues, changed, pmap = [], [], {}
    for L in sh['lines']:
        c = dict(prev.get(L['id'], {}))
        say = L.get('say') or L['text']
        allow_pause = bool(out.get('autoPause', True) and not L.get('noPause'))
        # new or reworded lines only: a line whose say is already in script.json untagged keeps it (its take stays good)
        if c.get('say') != say:
            say = lexicon.apply(say, LEX) if not allow_pause else spoken(say)
            say, entry, warns = prosody_prep.prepare_cue(say, text=L['text'], insert_pauses=allow_pause, cue_id=L['id'])
            for w in warns: print(f'⚠ {sk} {L["id"]}: {w}')
        else:
            entry = prosody_prep.analyze_cue(say, text=L['text'])
        pmap[L['id']] = entry
        if c and (c.get('say') != say or c.get('text') != L['text']): changed.append(L['id'])
        c.update(id=L['id'], text=L['text'], say=say)
        if 'gapAfter' in L: c['gapAfter'] = L['gapAfter']
        if L.get('noPause'): c['noPause'] = True
        else: c.pop('noPause', None)
        cues.append(c)
    gone = [i for i in prev if i not in {c['id'] for c in cues}]
    out['cues'] = cues
    json.dump(out, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    prosody_prep.write_prosody_map(f'{d}/prosody_map.json', pmap)
    print(f'{sk}: {len(cues)} cues -> {p}' + (f'; text/say changed: {", ".join(changed)}' if changed else '') +
          (f'; removed: {", ".join(gone)}' if gone else '') + f'  next: {C.NODE} {C.NARRATION}/tts.mjs {d}')
