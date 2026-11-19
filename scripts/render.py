#!/usr/bin/env python3
"""Render a short to MP4 — the user runs this by hand, after checking index.html in Chrome.
A copy sits in work/ (setup.sh puts it there); run it from anywhere:

    python3 render.py s1 01 my-slug        every graphic at 240 fps with motion blur, then the composite -> ../edit/short-01_my-slug/
    python3 render.py s1                   the same, without copying into edit/ (the MP4 is work/s1/final_video.mp4)
    python3 render.py s1 --skip-graphics   only the composite (the graphics are already rendered and unchanged)
    python3 render.py --list               the shorts and whether each is ready (recorded, gates)

Steps: render_full.sh for every run of the short (240 fps -> 60 fps with motion blur; renders that are newer than their
composition are skipped), then finish.sh (text and narration gates, the -14 LUFS master, the segments, the concat, the
final check and the thumbnail candidates). It stops at the first failure and says which step. Needs nothing beyond
what setup.sh installed."""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
W = next((d for d in (HERE, os.path.dirname(HERE), os.path.join(HERE, 'work')) if os.path.exists(os.path.join(d, 'cut.json'))), None)
if W is None: raise SystemExit('no cut.json next to render.py: run it from the work folder (or its parent) after prep.sh')
os.chdir(W)
args = [a for a in sys.argv[1:] if not a.startswith('--')]
flags = {a for a in sys.argv[1:] if a.startswith('--')}
C = json.load(open('cut.json', encoding='utf-8'))

if '--list' in flags or not args:
    for sk, c in C.items():
        n = c.get('narration', {})
        state = 'placeholders (not recorded)' if n.get('placeholder') else ('takes not read: ' + ','.join(n['unreviewed'])) if n.get('unreviewed') else 'ready'
        print(f'{sk}: {len(c["runs"])} runs, {c["END"]:.1f} s, narration {state}')
    if not args: print('\nusage: python3 render.py <short> [NN slug] [--skip-graphics]')
    sys.exit(0)

sk = args[0]; rest = args[1:3]
if sk not in C: raise SystemExit(f'no short {sk} in cut.json (have: {", ".join(C)})')
t0 = time.time()
def step(name, cmd):
    print(f'\n== {name}', flush=True)
    r = subprocess.run(cmd)
    if r.returncode: raise SystemExit(f'{name} failed (exit {r.returncode}); nothing after it ran')

ids = [f'{sk}_r{r["i"]}' for r in C[sk]['runs']]
if '--skip-graphics' not in flags:
    stale = [i for i in ids if not os.path.exists(f'gfx/out60/{i}.mp4')
             or os.path.getmtime(f'gfx/out60/{i}.mp4') < os.path.getmtime(f'gfx/{i}.html')]
    if stale:
        step(f'graphics: {len(stale)} of {len(ids)} compositions at 240 fps (motion blur)', ['bash', 'scripts/render_full.sh', *stale])
    else:
        print('\n== graphics: every render is newer than its composition, nothing to do')
step('composite (gates, master, segments, concat, check, thumbnails)', ['bash', 'scripts/finish.sh', sk, *rest])
print(f'\ndone in {(time.time() - t0) / 60:.1f} min: {os.path.join(W, sk, "final_video.mp4")}'
      + (f'  (and ../edit/short-{rest[0]}_{rest[1]}/final.mp4)' if len(rest) == 2 else ''))
