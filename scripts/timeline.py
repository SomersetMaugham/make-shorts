"""The short's timeline from its narration: cut.json[sk] (runs, words, END) and <sk>/voice.wav.
usage: python scripts/timeline.py s1 [s2 ...]         (after tts.mjs, and after sync.mjs when phrase times changed)

The narration folder (narration/<sk>/, written by script-to-motion's tts.mjs) is the clock: js/cues.js gives every
cue's start and end (the takes' real lengths once recorded, estimated reading times while they are placeholders) and
js/sync.js the phrase times the agent set in script.json "at". Nothing is measured here and no code decides where a word
is (script-to-motion's rule, references/narration.md):

- A word's time is ESTIMATED by its character position in the cue's text, with exactly the weight script-to-motion's
  player uses for when()/about() (spaces and . , ! ? · … quotes brackets - don't count). Where the agent set phrase
  times for the cue's take, those times are fixed points and the words between them are placed by the same weight
  between the fixed points. A word that starts a set phrase gets that time exactly (est: false); every other word is
  an estimate (est: true).
- Runs: shorts.json lines carry a "scene" (the kind of picture: capture, ui, diagram, number, logo, ...). A new run
  starts where the scene changes: at the start of the line's cue, or inside a line at a phrase of a "switches" entry
  ({"at": "<phrase as in the text>", "scene": "..."}), frame-snapped. Consecutive lines with the same scene are one run.
- END = the narration's length including its end hold (script.json "tail"), rounded up to a frame.

cut.json keeps the shape the rest of the pipeline reads: runs [{i, T0, T1, dur, layout: 'fv', scene, lines, text}],
words [{w, line, s, e, est}], END; plus cues (the narration's cues) and narration (provider, voice, placeholder)."""
import json, math, os, re, subprocess, sys

sys.path.insert(0, 'scripts'); import config as C

FPS = C.FPS
S = json.load(open('shorts.json', encoding='utf-8'))
_WEIGHT_DROP = re.compile(r'[\s.,!?·…"\'“”‘’()\[\]-]')


def weight(s):
    """script-to-motion player.js: s.replace(/[\\s.,!?·…"'“”‘’()\\[\\]-]/g, '').length (UTF-16 units, as JS counts)"""
    return len(_WEIGHT_DROP.sub('', s).encode('utf-16-le')) // 2


def js_data(path, var):
    """the object a generated js file assigns to window.<var>"""
    s = open(path, encoding='utf-8').read()
    m = re.search(r'window\.' + var + r'\s*=\s*', s)
    if not m: raise SystemExit(f'{path}: no window.{var}')
    return json.loads(s[m.end():s.rindex('}') + 1])


def fr(t):
    return round(t * FPS) / FPS


def cue_words(c, sync):
    """the cue's words (whitespace-separated, as in its text) with estimated or fixed start times (seconds, absolute)"""
    text = c.get('text') or ''
    total = max(1, weight(text))
    m = sync.get(c['id'])
    measured = bool(m and c.get('take') and m.get('take') == c['take'] and abs(m.get('d', -1) - c['duration']) < 0.01
                    and isinstance(m.get('phrases'), dict))
    anchors = {}                                   # char index -> seconds from the cue start (player.js when(): first occurrence)
    if measured:
        for p, t in m['phrases'].items():
            i = text.find(p)
            if i >= 0: anchors[i] = t
    pts = [(0, 0.0)] + sorted((weight(text[:i]), t) for i, t in anchors.items()) + [(total, c['duration'])]
    mono = [pts[0]]
    for w, t in pts[1:]:
        if w > mono[-1][0] and t > mono[-1][1]: mono.append((w, t))
        elif w == mono[-1][0] and w == 0: mono[-1] = (0, min(mono[-1][1], t))
    def at(wt):
        for (w0, t0), (w1, t1) in zip(mono, mono[1:]):
            if wt <= w1: return t0 + (t1 - t0) * (wt - w0) / max(1e-9, w1 - w0)
        return mono[-1][1]
    out, pos = [], 0
    for tok in text.split():
        i = text.index(tok, pos); pos = i + len(tok)
        fixed = i in anchors
        s = c['start'] + (anchors[i] if fixed else at(weight(text[:i])))
        out.append(dict(w=tok, line=c['id'], s=round(s, 3), est=not fixed, ci=i))
    for k, w in enumerate(out):
        w['e'] = round(out[k + 1]['s'] if k + 1 < len(out) else c['end'], 3)
    return out


def phrase_time(c, words, phrase):
    """when a phrase of the cue starts: the word it begins with (the same time a scene's when() would use)"""
    text = c.get('text') or ''
    i = text.find(phrase)
    if i < 0: raise SystemExit(f'switch phrase "{phrase}" is not in cue {c["id"]}: "{text}"')
    before = [w for w in words if w['ci'] <= i]
    if before and before[-1]['ci'] == i: return before[-1]['s']
    total = max(1, weight(text))
    return c['start'] + c['duration'] * weight(text[:i]) / total


def build(sk):
    nd = C.ndir(sk)
    cues_js, sync_js = f'{nd}/js/cues.js', f'{nd}/js/sync.js'
    if not os.path.exists(cues_js):
        raise SystemExit(f'{sk}: no {cues_js} — run: python scripts/narration_init.py {sk} && {C.NODE} {C.NARRATION}/tts.mjs {nd}')
    D = js_data(cues_js, 'VIDEO_DATA')
    sync = js_data(sync_js, 'SYNC') if os.path.exists(sync_js) else {}
    cues = {c['id']: c for c in D['cues']}
    lines = S[sk]['lines']
    missing = [L['id'] for L in lines if L['id'] not in cues]
    if missing: raise SystemExit(f'{sk}: lines {missing} have no cue in {cues_js} — run narration_init.py {sk} and tts.mjs again')
    stale = [L['id'] for L in lines if (cues[L['id']].get('text') or '') != L['text']]
    if stale: raise SystemExit(f'{sk}: the text of {stale} differs from {cues_js} — run narration_init.py {sk} and tts.mjs again')
    END = math.ceil(D['duration'] * FPS - 1e-6) / FPS
    words = []
    for L in lines: words += cue_words(cues[L['id']], sync)
    # scene segments: each line from its cue start (the first from 0) to the next line's cue start, split at its switches
    segs = []
    for k, L in enumerate(lines):
        c = cues[L['id']]
        t0 = 0.0 if k == 0 else fr(c['start'])
        t1 = END if k + 1 == len(lines) else fr(cues[lines[k + 1]['id']]['start'])
        scene = L.get('scene') or 'visual'
        lw = [w for w in words if w['line'] == L['id']]
        for sw in L.get('switches', []):
            ts = fr(phrase_time(c, lw, sw['at']))
            if not t0 < ts < t1: raise SystemExit(f'{sk} {L["id"]}: switch at "{sw["at"]}" ({ts:.3f} s) is outside the line ({t0:.3f}-{t1:.3f} s)')
            segs.append(dict(T0=t0, T1=ts, scene=scene, line=L['id'])); t0 = ts; scene = sw['scene']
        segs.append(dict(T0=t0, T1=t1, scene=scene, line=L['id']))
    runs = []
    for s_ in segs:
        if s_['T1'] - s_['T0'] < 1e-6: continue
        if runs and runs[-1]['scene'] == s_['scene']:
            runs[-1]['T1'] = s_['T1']
            if s_['line'] not in runs[-1]['lines']: runs[-1]['lines'].append(s_['line'])
        else:
            runs.append(dict(T0=s_['T0'], T1=s_['T1'], layout='fv', scene=s_['scene'], lines=[s_['line']]))
    for i, r in enumerate(runs):
        r['i'] = i; r['dur'] = round(r['T1'] - r['T0'], 3)
        r['text'] = ' '.join(w['w'] for w in words if r['T0'] - 1e-6 <= w['s'] < r['T1'] - 1e-6)
    for w in words: w.pop('ci', None)
    # the voice: the narration as tts.mjs laid it out (t = 0 is the video's t = 0), 48 kHz stereo, exactly END long
    os.makedirs(sk, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{nd}/audio/narration.wav', '-af', f'apad=whole_dur={END}',
                    '-t', f'{END:.6f}', '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', f'{sk}/voice.wav'], check=True)
    narr = dict(provider=(json.load(open(f'{nd}/script.json', encoding='utf-8')).get('tts') or {}).get('provider', 'google'),
                voice=D.get('voice', ''), model=D.get('model'), narration=D.get('narration', True),
                placeholder=bool(D.get('placeholder')), unreviewed=[c['id'] for c in D['cues'] if c.get('unreviewed')],
                leadIn=D.get('leadIn'), tail=D.get('tail'))
    keep = ('id', 'start', 'end', 'duration', 'take', 'placeholder', 'unreviewed', 'cut', 'text', 'say')
    return dict(runs=runs, words=words, END=END, cues=[{k: c[k] for k in keep if k in c} for c in D['cues']], narration=narr)


res = json.load(open('cut.json', encoding='utf-8')) if os.path.exists('cut.json') else {}
for sk in sys.argv[1:] or list(S):
    r = res[sk] = build(sk)
    n = r['narration']
    state = ('PLACEHOLDERS (silent, estimated timing)' if n['placeholder'] else 'no narration ("narration": false)'
             if not n['narration'] else f'recorded ({n["provider"]} {n["voice"]})') + (f'; NOT READ YET: {n["unreviewed"]}' if n['unreviewed'] else '')
    est = sum(w['est'] for w in r['words'])
    print(f'== {sk} END={r["END"]:.3f}s · narration {state} · {len(r["words"])} words, {len(r["words"]) - est} at set phrase times')
    for x in r['runs']:
        flag = '  > 8 s: split it (a switch or a scene change)' if x['dur'] > 8.0 else ''
        print(f'  RUN{x["i"]:02d} {x["scene"]:10s} {x["T0"]:7.3f}-{x["T1"]:7.3f} ({x["dur"]:.2f}s) {x["text"]}{flag}')
json.dump(res, open('cut.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
