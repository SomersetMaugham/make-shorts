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
    'lookdev': 'This round is POINT 1: the hero frames of each section, before the rest of the short is built. Please '
               'check every image against the floor (elevate.md §3) and the consistency rules (§4).',
    'whole': 'This round is POINT 3: the whole short before it goes to the user for review (whole-short and section sheets '
             'and key frames). Please check every image against the floor (elevate.md §3) and the consistency rules (§4), '
             'including three runs in a row with the same layout and, when previous-round images are listed, a changed '
             'stretch that still looks the same at phone size (judge it scaled to 360 px wide).',
    'motion': 'This round is POINT 2: frame-by-frame sheets (consecutive tiles are 1–6 frames apart at 60 fps). Please '
              'check every run boundary and camera move for one-frame jumps, jerks (a camera move completed within 10 frames), '
              'flashes of a wrong state, muddy overlaps, a hero missing at a run\'s first frame, a run that ends while '
              'zoomed, and a visual that lands after its words (elevate.md §3)? Please name each finding by its image number and tile label. '
              'If exactly one tile shows a different state in the middle of a run (not at a run boundary) and its '
              'neighbours agree with each other, list it under "Suspect", not "Must-fix": it can be a capture glitch.',
}[point]
THEME = json.load(open('project.json')).get('theme', 'stage') if os.path.exists('project.json') else 'stage'
_LOOKS = {'sketch': 'hand-drawn on paper in the sketch theme',
          'reel': 'in the code-reel theme (dark navy, a fixed header, a diagram card on top, a divider and a code card below whose '
                  'white box highlights the line being discussed; one diagram may continue across several runs by design)',
          'sungkim': 'in the Sungkim theme (warm paper, a header with a one-line title, a visual box, a source line and info cards '
                     'that stack in; header, boxes and earlier cards stay in place across runs by design)',
          'brief': 'in the Brief editorial magazine theme (newsprint paper #F5F4F0, top segmented progress bar, Hahmlet 700 '
                   'section-coloured title over a double ink rule, framed upper visual, archive source chip and editorial lower '
                   'cards; header, visual frame and earlier cards stay in place across runs by design)'}
LOOK = (_LOOKS.get(THEME, 'on a graphite stage with glass cards') + ' (read '
        + os.path.join(SKILL, 'references', {'sketch': 'theme-sketch.md', 'reel': 'theme-reel.md', 'sungkim': 'theme-sungkim.md', 'brief': 'theme-brief.md'}.get(THEME, 'theme.md')) + ')')
prompt = f"""Hi, and thank you for taking this on. I'd like to ask you to act as the defect checker described in {RUBRIC}.
Please read that file in full and answer in exactly the format of its §5. You didn't build this work, which is exactly
why your fresh eyes are valuable. Please look at the images listed below and read the files named here. Please do not edit or
create any file and do not run any command: your written answer is the report, and this script saves it.

Please report only defects you can point to in an image: for each, the image number and label, the rule from §3 or §4
it breaks, and where in the frame (for example "top-left, y 150-210"). Please leave out scores, grades, ranked upgrades,
ideas for new shots, requests for more camera moves or effects, and opinions on taste or beauty: the user decides those.
If an image breaks no rule, list its number under "Clean". If a rule is unclear to you, or two rules conflict, please
say so in the report instead of guessing.

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
if r.returncode or '## Must-fix' not in text:   # judged by the §5 format, not length: a clean report is short
    raise SystemExit(f'agy failed (exit {r.returncode}): {(r.stderr or text)[-600:]}')
open(out, 'w', encoding='utf-8').write(f'<!-- {point} round {rnd} · {model} · {len(imgs)} images · {time.time() - t0:.0f} s -->\n' + text + '\n')
m = re.search(r'## Must-fix[^\n]*\n(.*?)(?=\n## |\Z)', text, re.S)
print(f'{out} ({len(imgs)} images, {time.time() - t0:.0f} s)')
print((m.group(1) if m else text[:600]).strip())
