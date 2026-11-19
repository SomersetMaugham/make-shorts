#!/usr/bin/env python3
"""Render a short to MP4 — the user runs this by hand, after checking index.html in Chrome.
A copy sits in work/ (setup.sh puts it there); run it from work/ or the project folder:

    python3 render.py s1 01 my-slug        every graphic with motion blur, then the composite -> ../edit/short-01_my-slug/
    python3 render.py s1                   the same, without copying into edit/ (the MP4 is work/s1/final_video.mp4)
    python3 render.py s1 --fps 60          capture rate of the graphics: 240 (default, or project.json "render_fps"; 4 captures per frame, 3 blended),
                                           120 (2, both blended) or 60 (no blend; engine.js's own viewport blur only)
    python3 render.py s1 --skip-graphics   only the composite (the graphics are already rendered and unchanged)
    python3 render.py --list               the shorts and whether each is ready (recorded, gates)
    python3 render.py --screenshot --short s1 --from 12.0 --to 14.0 [--gapframe 10] [--fast] [--jobs 1]
    python3 render.py --screenshot --run s1_r3 [--gapframe 10]   the same over one whole run (a graphic's own check)
                                           a contact sheet of the preview (index.html) from..to, every gapframe-th frame at
                                           60 fps, shot with headless Chrome -> chk/shot_<short>_<from>-<to>.png. No render
                                           needed. The A key in index.html copies this command for the moment on screen.

Steps of a render: render_full.sh for every run whose render is missing, older than its composition or made at another
--fps, then finish.sh (text and narration gates, the -14 LUFS master, the segments, the concat, the final check and
the thumbnail candidates). It stops at the first failure and says which step."""
import json, os, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
W = next((d for d in (HERE, os.path.dirname(HERE), os.path.join(HERE, 'work')) if os.path.exists(os.path.join(d, 'cut.json'))), None)
if W is None: raise SystemExit('no cut.json next to render.py: run it from the work folder (or its parent) after prep.sh')
os.chdir(W)
argv = sys.argv[1:]
def opt(name, default=None):
    if name in argv:
        i = argv.index(name); v = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]; return v
    return default
flags_all = set(a for a in argv if a.startswith('--'))
C = json.load(open('cut.json', encoding='utf-8'))
PY = next((p for p in ('../.venv/bin/python', '../.venv/Scripts/python.exe') if os.path.exists(p)), sys.executable)

# ---------- --screenshot: the preview page, shot with headless Chrome ----------
if '--screenshot' in flags_all:
    sk = opt('--short') or next(iter(C)); run = opt('--run')
    if run:                                            # --run s1_r3: the whole of that run
        sk, ri = run.split('_r'); r = C[sk]['runs'][int(ri)]
        a, b = float(opt('--from', r['T0'])), float(opt('--to', r['T1'] - 1 / 60))
    else:
        a = float(opt('--from', '0')); b = float(opt('--to', str(C[sk]['END'])))
    gap = int(opt('--gapframe', '10')); jobs = int(opt('--jobs', '1')); fast = '--fast' in argv
    chrome = next((p for p in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                               shutil.which('google-chrome') or '', shutil.which('chromium') or '', shutil.which('chrome') or '')
                   if p and os.path.exists(p)), None)
    if not chrome: raise SystemExit('no Chrome found (needed for --screenshot)')
    if not os.path.exists('index.html'): subprocess.run([PY, 'scripts/preview.py'], check=True)
    ts, t = [], a
    while t <= b + 1e-9: ts.append(round(t, 3)); t += gap / 60
    w, h = (540, 960) if fast else (720, 1280)        # Chrome keeps a window at least ~500 px wide: smaller would crop
    out_dir = os.path.join('chk', f'shot_{sk}_{a:.2f}-{b:.2f}'); os.makedirs(out_dir, exist_ok=True)
    url = 'file://' + os.path.abspath('index.html')
    def shoot(t):
        f = os.path.abspath(os.path.join(out_dir, f'{t:08.3f}.png'))
        subprocess.run([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={w},{h}',
                        '--virtual-time-budget=8000', f'--screenshot={f}', f'{url}?s={sk}&t={t}&still'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f
    with ThreadPoolExecutor(max(1, jobs)) as ex: files = list(ex.map(shoot, ts))
    sheet = os.path.join('chk', f'shot_{sk}_{a:.2f}-{b:.2f}.png')
    subprocess.run([PY, 'scripts/sheet.py', os.path.join(out_dir, '*.png'), sheet, str(min(6, len(files)))], check=True)
    print(f'{len(files)} frames ({a:.2f}-{b:.2f} s, every {gap} frames) -> {os.path.abspath(sheet)}')
    sys.exit(0)

PROJ = json.load(open('project.json', encoding='utf-8')) if os.path.exists('project.json') else {}
fps = str(opt('--fps', os.environ.get('RENDER_FPS', PROJ.get('render_fps', 240))))   # project.json "render_fps" sets a project's default
if fps not in ('240', '120', '60'): raise SystemExit('--fps must be 240, 120 or 60')
args = [x for x in argv if not x.startswith('--')]
flags = {x for x in argv if x.startswith('--')}

if '--list' in flags or not args:
    for sk, c in C.items():
        n = c.get('narration', {})
        state = 'placeholders (not recorded)' if n.get('placeholder') else ('takes not read: ' + ','.join(n['unreviewed'])) if n.get('unreviewed') else 'ready'
        print(f'{sk}: {len(c["runs"])} runs, {c["END"]:.1f} s, narration {state}')
    if not args: print('\nusage: python3 render.py <short> [NN slug] [--fps 240|120|60] [--skip-graphics]   ·   --screenshot (see the docstring)')
    sys.exit(0)

sk = args[0]; rest = args[1:3]
if sk not in C: raise SystemExit(f'no short {sk} in cut.json (have: {", ".join(C)})')
t0 = time.time()
def step(name, cmd, env=None):
    print(f'\n== {name}', flush=True)
    r = subprocess.run(cmd, env=dict(env or os.environ, CVS_RENDER='1'))   # the MP4 steps run only from here
    if r.returncode: raise SystemExit(f'{name} failed (exit {r.returncode}); nothing after it ran')

ids = [f'{sk}_r{r["i"]}' for r in C[sk]['runs']]
if '--skip-graphics' not in flags:
    def stale(i):
        out, mark = f'gfx/out60/{i}.mp4', f'gfx/out60/{i}.fps'
        return (not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(f'gfx/{i}.html')
                or (open(mark).read().strip() if os.path.exists(mark) else '240') != fps)
    todo = [i for i in ids if stale(i)]
    if todo:
        step(f'graphics: {len(todo)} of {len(ids)} compositions at {fps} fps', ['bash', 'scripts/render_full.sh', *todo],
             env=dict(os.environ, RENDER_FPS=fps))
        for i in todo: open(f'gfx/out60/{i}.fps', 'w').write(fps)
    else:
        print(f'\n== graphics: every render is newer than its composition and made at {fps} fps, nothing to do')
step('composite (gates, master, segments, concat, check, thumbnails)', ['bash', 'scripts/finish.sh', sk, *rest])
print(f'\ndone in {(time.time() - t0) / 60:.1f} min: {os.path.join(W, sk, "final_video.mp4")}'
      + (f'  (and ../edit/short-{rest[0]}_{rest[1]}/final.mp4)' if len(rest) == 2 else ''))
