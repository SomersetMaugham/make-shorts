"""The narration gate before a short is assembled (finish.sh runs it): the role script-to-motion's check.mjs plays for
the narration. It reads state and compares files; it never listens and never decides where silence or a word is.
usage: python scripts/check_narration.py s1 [--draft]

Errors (exit 1):
- js/cues.js is missing or was built from another script.json (tts.mjs was not re-run after an edit)
- a cue is still a silent placeholder (allowed with --draft: the review copy before the user decides to record)
- a recorded take has no cut yet (unreviewed: true): read it with wave.mjs and set its "cut" ("ranges": [] when nothing goes)
- js/sync.js does not say what script.json "at" sets (sync.mjs was not re-run), or an "at" belongs to an older take
- cut.json[sk] was built from other cue timings (timeline.py was not re-run)
- Google voice: a recorded cue whose pauses were not checked on its current take and cut, or whose last check found a
  comma, tag or sentence end with no pause (narration/<sk>/phrasing.json, written by phrasing-check.mjs). The user
  heard it and accepted it: "phrasingOk": true on the cue in script.json.
Warnings: a keyword chip (shorts.json "highlights") whose first word sits in a recorded cue at an estimated time — chips
land on the word, so set the phrase's time in "at" (wave.mjs --cue <id> --step 0.01) and run sync.mjs + timeline.py."""
import json, os, re, subprocess, sys

sys.path.insert(0, 'scripts'); import config as C

sk = sys.argv[1]; DRAFT = '--draft' in sys.argv
nd = C.ndir(sk); errs, warns = [], []


def js_data(path, var):
    s = open(path, encoding='utf-8').read(); m = re.search(r'window\.' + var + r'\s*=\s*', s)
    return json.loads(s[m.end():s.rindex('}') + 1])


if not os.path.exists(f'{nd}/js/cues.js'):
    print(f'✖ {sk}: no {nd}/js/cues.js — run narration_init.py {sk} and tts.mjs'); sys.exit(1)
D = js_data(f'{nd}/js/cues.js', 'VIDEO_DATA')
script = json.load(open(f'{nd}/script.json', encoding='utf-8'))

# what tts.mjs and sync.mjs would write now, from their own code (lib/scriptsig.mjs, lib/phrases.mjs)
helper = r"""
import fs from 'node:fs'; import path from 'node:path'; import { pathToFileURL } from 'node:url';
const [lib, dir] = process.argv.slice(1);
const { scriptSignature } = await import(pathToFileURL(path.join(lib, 'scriptsig.mjs')));
const { phraseTimes } = await import(pathToFileURL(path.join(lib, 'phrases.mjs')));
const script = JSON.parse(fs.readFileSync(path.join(dir, 'script.json'), 'utf8'));
const box = {}; new Function('window', fs.readFileSync(path.join(dir, 'js/cues.js'), 'utf8'))(box);
const cues = new Map(box.VIDEO_DATA.cues.map((c) => [c.id, c]));
const phrases = {}, problems = [];
for (const sc of script.cues) {
  const cue = cues.get(sc.id); if (!cue) continue;
  const r = phraseTimes(sc, cue, null);
  if (r.problems) problems.push(`${sc.id}: ${r.problems.join('; ')}`);
  if (r.stale) problems.push(`${sc.id}: "at" not used — ${r.stale}`);
  if (r.phrases && Object.keys(r.phrases).length) phrases[sc.id] = r.phrases;
}
console.log(JSON.stringify({ sig: scriptSignature(script), phrases, problems }));
"""
r = subprocess.run([C.NODE, '--input-type=module', '-e', helper, os.path.abspath(f'{C.NARRATION}/lib'), os.path.abspath(nd)],
                   capture_output=True, text=True, encoding='utf-8')
if r.returncode != 0:
    print(f'✖ {sk}: could not read the narration state: {r.stderr.strip()[-400:]}'); sys.exit(1)
now = json.loads(r.stdout)
if D.get('scriptSig') != now['sig']:
    errs.append(f'js/cues.js was built from another script.json — run: {C.NODE} {C.NARRATION}/tts.mjs {nd}')
ph = [c['id'] for c in D['cues'] if c.get('placeholder')]
if ph and not DRAFT:
    errs.append(f'{len(ph)} cue(s) not recorded yet ({", ".join(ph)}). Recording waits for the user: hand over the review copy '
                f'and script.txt and ask; on their word: tts.mjs {nd} --approved')
un = [c['id'] for c in D['cues'] if c.get('unreviewed')]
if un:
    errs.append(f'take(s) not read yet: {", ".join(un)} — node {C.NARRATION}/wave.mjs {nd} --unreviewed, set each "cut" '
                f'("ranges": [] when nothing goes), tts.mjs again')
errs += [f'"at": {p}' for p in now['problems']]
sync = js_data(f'{nd}/js/sync.js', 'SYNC') if os.path.exists(f'{nd}/js/sync.js') else {}
have = {i: v.get('phrases', {}) for i, v in sync.items()}
if have != now['phrases']:
    errs.append(f'js/sync.js does not say what script.json "at" sets — run: {C.NODE} {C.NARRATION}/sync.mjs {nd}')

# pauses: phrasing-check.mjs's verdict on each recorded cue's current take and cut (Chirp skips most commas)
if script.get('tts', {}).get('provider', 'google') == 'google':
    pj = f'{nd}/phrasing.json'
    PJ = json.load(open(pj, encoding='utf-8')) if os.path.exists(pj) else {}
    sc = {c['id']: c for c in script['cues']}
    stale, missing = [], []
    for c in D['cues']:
        s_ = sc.get(c['id'], {})
        if not c.get('take') or s_.get('phrasingOk'): continue
        v = PJ.get(c['id'])
        if not v or v.get('take') != c['take'] or v.get('cut') != s_.get('cut') or v.get('say') != s_.get('say'):
            stale.append(c['id'])
        elif v.get('missing') or v.get('unknown'):
            missing.append(f"{c['id']} " + (v['unknown'] or ', '.join(f'"{m["word"]}"' for m in v['missing'])))
    if stale:
        errs.append(f'pauses not checked on the current take/cut: {", ".join(stale)} — run: {C.NODE} '
                    f'{C.NARRATION}/phrasing-check.mjs {nd} {" ".join(stale)}')
    if missing:
        errs.append('missing pause (phrasing-check): ' + '; '.join(missing) + ' — tag it in say ([pause short]), re-take '
                    '--only, recut; or "phrasingOk": true on the cue if the user heard it and accepted it')

cut = json.load(open('cut.json', encoding='utf-8')).get(sk) if os.path.exists('cut.json') else None
if not cut:
    errs.append(f'no cut.json entry — run: python scripts/timeline.py {sk}')
else:
    a = [(c['id'], c['start'], c['end'], c.get('take')) for c in cut.get('cues', [])]
    b = [(c['id'], c['start'], c['end'], c.get('take')) for c in D['cues']]
    if a != b: errs.append(f'cut.json was built from other cue timings — run: python scripts/timeline.py {sk}')
    else:
        recorded = {c['id'] for c in D['cues'] if c.get('take')}
        # the chips compose.py actually draws (captions.json, written by prep.sh): each starts on a word of the timeline
        caps = json.load(open(f'{sk}/captions.json', encoding='utf-8')) if os.path.exists(f'{sk}/captions.json') else []
        for ch in (c for c in caps if c.get('hl')):
            w = min(cut['words'], key=lambda w: abs(w['s'] - ch['t0']), default=None)
            if w and abs(w['s'] - ch['t0']) < 0.05 and w['line'] in recorded and w['est']:
                warns.append(f'keyword chip "{ch["text"]}" ({w["line"]}) lands at an estimated time — set its "at" '
                             f'(wave.mjs {nd} --cue {w["line"]} --step 0.01), then sync.mjs and timeline.py')

for w in warns: print(f'⚠ {sk}: {w}')
for e in errs: print(f'✖ {sk}: {e}')
if errs: sys.exit(1)
print(f'{sk}: narration ok' + (' (draft: placeholders allowed)' if DRAFT and ph else ''))
