"""The art director and the motion reviewer of the elevation (references/elevate.md): Gemini Neon through agy, read-only.
usage (inside work/):
  python3 scripts/art_director.py lookdev 1 chk/lookdev-1/at_s1/*.png             hero frames before the whole build: B + world check
  python3 scripts/art_director.py whole 1 chk/elevate-1 [--before chk/elevate-0]  whole short + sections + key frames: A, B, floor, upgrades
  python3 scripts/art_director.py motion 1 chk/motion-1                           frame-by-frame sheets of run boundaries and key moments: C, sync, floor
  options: --sk s1 · --note "one line to the director (e.g. why an upgrade was declined)" · --model gemini-4-neon-medium
Images are PNG files or folders of them (render.py --screenshot ... --out <folder>). Each is described to the director
with its time, cue and the line spoken there. The report goes to review/art-<point>-<round>.md; the stdout is short.
Runs a few minutes: start it in the background. agy gets read access to the images, the project and the skill's
references, no write grant and no shell (the report is its answer, saved by this script)."""
import glob, json, os, re, subprocess, sys, time

if not os.path.exists('cut.json'): raise SystemExit('run it inside work/')
a = sys.argv[1:]
def opt(name, default=None):
    if name in a:
        i = a.index(name); v = a[i + 1]; del a[i:i + 2]; return v
    return default
sk = opt('--sk', 's1'); note = opt('--note', ''); before = opt('--before'); model = opt('--model', 'gemini-4-neon-medium')
if len(a) < 3 or a[0] not in ('lookdev', 'whole', 'motion'): raise SystemExit(__doc__)
point, rnd, paths = a[0], a[1], a[2:]
SKILL = json.load(open('project.json')).get('skill_dir') if os.path.exists('project.json') else None
SKILL = SKILL or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUBRIC = os.path.join(SKILL, 'references', 'elevate.md')
AGY = os.path.expanduser('~/.local/bin/agy')                 # never the zsh alias (it adds --dangerously-skip-permissions)
C = json.load(open('cut.json', encoding='utf-8'))[sk]


def pngs(ps):
    out = []
    for p in ps:
        out += sorted(glob.glob(os.path.join(p, '**', '*.png'), recursive=True)) if os.path.isdir(p) else [p]
    # a sheet's own tiles (render.py keeps them in a shot_* folder next to it) are not sent twice
    return [os.path.abspath(p) for p in out if p.endswith('.png') and not os.path.basename(os.path.dirname(p)).startswith('shot_')]


def describe(f):
    """'<file>: 0:43.90 [c07] the line' for a frame; 'a sheet a-b s' for a contact sheet."""
    b = os.path.basename(f)
    m = re.search(r'shot_\w+?_([\d.]+)-([\d.]+)\.png$', b)
    if m: return f'{f}: contact sheet {m.group(1)}–{m.group(2)} s (tiles labelled m:ss.ss [cue])'
    m = re.search(r'_([\d.]+)_(c\w+|-)\.png$', b)
    if not m: return f
    t = float(m.group(1)); q = next((c for c in C['cues'] if c['id'] == m.group(2)), None)
    r = next((r for r in C['runs'] if r['T0'] <= t < r['T1']), None)
    mm, ss = divmod(t, 60)
    return (f'{f}: {int(mm)}:{ss:05.2f} [{m.group(2)}]' + (f' {sk}_r{r["i"]} ({r.get("scene", "")})' if r else '')
            + (f' — spoken: "{q["text"]}"' if q else ''))


imgs = pngs(paths); prev = pngs([before]) if before else []
if not imgs: raise SystemExit('no PNG images in ' + ' '.join(paths))
brief = os.path.abspath('GFX_BRIEF.md') if os.path.exists('GFX_BRIEF.md') else None
script = os.path.abspath(f'narration/{sk}/script.txt')
runs = '\n'.join(f'- {sk}_r{r["i"]} {r["T0"]:.2f}–{r["T1"]:.2f} s {r.get("scene", "")}: '
                 + ' '.join(q['text'] for q in C['cues'] if q['id'] in r.get('lines', []))[:90] for r in C['runs'])
TASK = {
    'lookdev': 'POINT 1 — look development, before the whole build. Score only B 그래픽 디자인 per hero frame and do the '
               'world check (elevate.md §4 B, §5). The rest of the short is built only when these frames reach 4.',
    'whole': 'POINT 3 — elevate, the whole short before it goes to the user for review. Group the runs into the short\'s '
             '3–5 story sections (hook, problem, mechanism, example, payoff — from the script) and score every section on '
             'A 연출 and B 그래픽 디자인 (elevate.md §4), list the floor violations (§4 D) and rank 6–10 upgrades (§5).',
    'motion': 'POINT 2 — the motion and sync pass on frame-by-frame sheets (consecutive tiles are 1–6 frames apart at 60 '
              'fps). Score C 모션 per section, check every run boundary and camera move for one-frame jumps, flashes of a '
              'wrong state, muddy overlaps and a hero missing at a run\'s first frame, and check that each visual lands '
              'with or before its words (elevate.md §4 C and D). Name every finding by sheet and tile label. A single tile '
              'that shows a different state in the MIDDLE of a run may be a capture glitch: report it as "suspect flash", separately '
              'from the must-fix list.',
}[point]
THEME = json.load(open('project.json')).get('theme', 'stage') if os.path.exists('project.json') else 'stage'
LOOK = ('hand-drawn on paper in the sketch theme (pen schematics, red/blue pens, highlighter, handwriting; read '
        + os.path.join(SKILL, 'references', 'theme-sketch.md') + ' and score it by the sketch-theme paragraph of the rubric)'
        if THEME == 'sketch' else 'on a graphite stage with glass cards')
prompt = f"""You are the ART DIRECTOR of the elevation described in {RUBRIC} (read it all; use its §4 rubric and answer in
exactly the format of its §5). You have no stake in this work: you did not build it and you do not defend it. You only
look at the images listed below, read the files named here, and judge. Do not edit or create any file, do not run
anything; your answer is your report.

The work: a Korean vertical short (1080x1920, YouTube Shorts / Reels), narration with burned-in captions and keyword
chips, every run a full-frame HyperFrames graphic {LOOK}. Audience: Korean viewers
scrolling shorts, curious about AI but not specialists. The scale is ABSOLUTE (3 = competent explainer graphics,
4 = a crafted world a viewer finds beautiful on its own, 5 = reel-worthy); never grade on effort or against a previous
round. A card or page holding a title and a line of text is a slide (B at most 2).
On the phone the platform draws its like/comment/share buttons over x > 960, y 1000–1700 and its title below y 1560:
text or a key element there is a floor violation.

{TASK}

Read also: the script (what is said, cue by cue) {script}""" + (f"\nand the graphics brief {brief}" if brief else '') + f"""

Runs of the short (id, time, scene kind, words):
{runs}

Images, in order (open every one as an image):
""" + '\n'.join(f'{i + 1}. {describe(f)}' for i, f in enumerate(imgs)) + (
    '\n\nThe previous round, for comparison (a changed stretch that looks the same at phone size is a floor violation):\n'
    + '\n'.join(f'- {describe(f)}' for f in prev) if prev else '') + (f'\n\nA note from the builder: {note}' if note else '') + """

Answer in Korean, in the format of elevate.md §5, naming images by their number and label."""

os.makedirs('review', exist_ok=True)
out = f'review/art-{point}-{rnd}.md'
dirs = sorted({os.path.dirname(f) for f in imgs + prev} | {os.path.abspath('.'), os.path.join(SKILL, 'references')})
cmd = [AGY, '-p', prompt, '--model', model, '--settings', '{"allowNonWorkspaceAccess": false}']
for d in dirs: cmd += ['--add-dir', d]
t0 = time.time()
r = subprocess.run(cmd, capture_output=True, text=True)
text = (r.stdout or '').strip()
if r.returncode or len(text) < 200:
    raise SystemExit(f'agy failed (exit {r.returncode}): {(r.stderr or text)[-600:]}')
open(out, 'w', encoding='utf-8').write(f'<!-- {point} round {rnd} · {model} · {len(imgs)} images · {time.time() - t0:.0f} s -->\n' + text + '\n')
m = re.search(r'\|[^\n]*A[^\n]*\n((?:\|[^\n]*\n)+)', text)
print(f'{out} ({len(imgs)} images, {time.time() - t0:.0f} s)')
print((m.group(1) if m else text[:600]).strip())
