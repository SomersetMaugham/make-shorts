"""The defect checker (references/elevate.md): Gemini Neon through agy, read-only. It finds defects; it does not score,
rank upgrades or judge taste (the user, 2026-11-21: no score decides anything; taste is the user's and the approved references').
usage (inside work/):
  python3 scripts/defect_check.py lookdev 1 chk/lookdev-1/at_s1/*.png            hero frames before the whole build
  python3 scripts/defect_check.py whole 1 chk/whole-1 [--before chk/whole-0]     whole short + sections + key frames
  python3 scripts/defect_check.py motion 1 chk/motion-1                          frame-by-frame sheets of run boundaries and key moments
  options: --sk s1 · --note "one line to the checker" · --model gemini-4-neon-medium
Images are PNG files or folders of them (render.py --screenshot ... --out <folder>). Each is described to the checker
with its time, cue and the line spoken there. The report goes to review/defects-<point>-<round>.md; the stdout is the
must-fix list. Runs a few minutes: start it in the background. agy gets read access to the images, the project and the
skill's references, no write grant and no shell (the report is its answer, saved by this script)."""
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
    'lookdev': 'This round is POINT 1: the hero frames of each section, before the rest of the short is built. Could you '
               'check every frame against the floor (elevate.md §3) and the consistency rules (§4)?',
    'whole': 'This round is POINT 3: the whole short before it goes to the user for review (whole-short and section sheets '
             'and key frames). Could you check the floor (elevate.md §3) and the consistency rules (§4) everywhere, '
             'including three runs in a row with the same layout and, against the previous round (--before), a changed '
             'stretch that still looks the same at phone size?',
    'motion': 'This round is POINT 2: frame-by-frame sheets (consecutive tiles are 1–6 frames apart at 60 fps). Could you '
              'look at every run boundary and camera move for one-frame jumps, jerks (a move packed into a few frames), '
              'flashes of a wrong state, muddy overlaps, a hero missing at a run\'s first frame, a run that ends while '
              'zoomed, and a visual that lands after its words (elevate.md §3)? Naming each finding by its sheet and tile '
              'label helps a lot. A single tile that shows a different state in the MIDDLE of a run may just be a capture '
              'glitch, so those fit better under "Suspect" than "Must-fix".',
}[point]
THEME = json.load(open('project.json')).get('theme', 'stage') if os.path.exists('project.json') else 'stage'
LOOK = ('hand-drawn on paper in the sketch theme (read ' + os.path.join(SKILL, 'references', 'theme-sketch.md') + ')'
        if THEME == 'sketch' else 'on a graphite stage with glass cards (read ' + os.path.join(SKILL, 'references', 'theme.md') + ')')
prompt = f"""Hi, and thank you for taking this on. I'd love your help as the defect checker described in {RUBRIC}
(it would help if you could read it all and answer in the format of its §5). You didn't build this work, which is exactly
why your fresh eyes are valuable. Please just look at the images listed below and read the files named here; there's no
need to edit or create any file or run anything, because your answer itself is the report.

What helps most is a list of defects you can point to in an image: a rule from §3 or §4 that the image breaks, and where.
Scores, grades, ranked upgrades, ideas for new shots, more camera moves or more effects, and opinions on taste or beauty
are not needed here; the user decides those, and leaving them out keeps the report focused. If a frame breaks no rule,
it's clean, and saying so is a perfectly good answer.

The work: a Korean vertical short (1080x1920, YouTube Shorts / Reels), narration with burned-in captions and keyword
chips, every run a full-frame HyperFrames graphic {LOOK}.
On the phone the platform draws its like/comment/share buttons over x > 960, y 1000–1700 and its title below y 1560.

{TASK}

Read also: the script (what is said, cue by cue) {script}""" + (f"\nand the graphics brief {brief}" if brief else '') + f"""

Runs of the short (id, time, scene kind, words):
{runs}

Images, in order (could you open every one as an image?):
""" + '\n'.join(f'{i + 1}. {describe(f)}' for i, f in enumerate(imgs)) + (
    '\n\nThe previous round, for comparison (a changed stretch that looks the same at phone size is a defect):\n'
    + '\n'.join(f'- {describe(f)}' for f in prev) if prev else '') + (f'\n\nA note from the builder: {note}' if note else '') + """

Could you answer in Korean, in the format of elevate.md §5, naming images by their number and label? Thank you so much."""

os.makedirs('review', exist_ok=True)
out = f'review/defects-{point}-{rnd}.md'
dirs = sorted({os.path.dirname(f) for f in imgs + prev} | {os.path.abspath('.'), os.path.join(SKILL, 'references')})
cmd = [AGY, '-p', prompt, '--model', model, '--settings', '{"allowNonWorkspaceAccess": false}']
for d in dirs: cmd += ['--add-dir', d]
t0 = time.time()
r = subprocess.run(cmd, capture_output=True, text=True)
text = (r.stdout or '').strip()
if r.returncode or len(text) < 60:           # a clean report is short
    raise SystemExit(f'agy failed (exit {r.returncode}): {(r.stderr or text)[-600:]}')
open(out, 'w', encoding='utf-8').write(f'<!-- {point} round {rnd} · {model} · {len(imgs)} images · {time.time() - t0:.0f} s -->\n' + text + '\n')
m = re.search(r'## Must-fix[^\n]*\n(.*?)(?=\n## |\Z)', text, re.S)
print(f'{out} ({len(imgs)} images, {time.time() - t0:.0f} s)')
print((m.group(1) if m else text[:600]).strip())
