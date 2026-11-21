"""Warn when a sketch graphics module draws circuit parts by hand instead of with the kit (references/theme-sketch.md
"Parts", docs/plans/2026-11-21-parts-library.md §6). The same part must look the same everywhere, so every part comes
from assets/gfx/sketch.js; a part the kit lacks is added to the kit and the catalogue first.

usage: python3 scripts/check_parts.py [scripts/gfx_s1.py ...]     (no arguments: every scripts/gfx_*.py)
build_gfx.py calls it for the modules it builds. It only warns (exit 0): a warning is a question, not a failure.

What it flags, in the JS of the module:
- a home-made part: a function or const named like a part (drawBattery, makeResistor, meter = (...) => ...);
- a cluster of raw strokes: 12 or more S.line / S.path / S.rect / S.circle / S.polygon calls within 8 lines (a part
  being assembled by hand). Waveforms, matter drawings and other intended free drawing are fine: put `// parts-ok`
  on the line (or the line above the block) to say so."""
import glob, os, re, sys

PARTS = ('battery|cell|res(istor)?|cap(acitor)?|ecap|diode|led|zener|ind(uctor)?|coil|xfmr|transformer|fuse|xtal|crystal|'
         'pot|ldr|thermistor|vdc|vac|isrc|source|gnd|ground|vcc|npn|pnp|bjt|transistor|nmos|pmos|mosfet|fet|opamp|gate|'
         'switch|sw|relay|lamp|bulb|motor|speaker|meter|ammeter|voltmeter|ohmmeter|dial|gauge|scope')
HOME_MADE = re.compile(r'(?:function\s+|(?:const|let|var)\s+)((?:draw|make|build|my|hand)?_?(?:' + PARTS + r')\w*)\s*(?:=\s*(?:\([^)]*\)|\w+)\s*=>|\()',
                       re.I)
RAW = re.compile(r'\bS\.(line|path|rect|circle|polygon)\(')
# words in a comment that name a part unambiguously ("crystal", "cell", "source", "gate" also mean lattice and logic)
COMMENT_PARTS = PARTS.replace('cell|', '').replace('|crystal', '').replace('source|', '').replace('|gate', '')
KIT_CALL = re.compile(r'\bS\.(' + PARTS + r')\(', re.I)          # the kit itself in use: raw lines nearby are wiring


def js_of(src):
    """The module's JS: every triple-quoted string (SCENE = r\"\"\" ... \"\"\" and the like)."""
    return '\n'.join(m.group(2) for m in re.finditer(r'(\"\"\"|\'\'\')(.*?)\1', src, re.S))


def check(path):
    src = open(path, encoding='utf-8').read()
    lines = js_of(src).split('\n')
    out = []
    ok = lambda i: '// parts-ok' in lines[i] or (i > 0 and '// parts-ok' in lines[i - 1])
    for i, ln in enumerate(lines):
        m = HOME_MADE.search(ln)
        if m and not ok(i) and not ln.lstrip().startswith('//'):
            name = m.group(1)
            if name.lower() in ('gate', 'sw', 'source'):     # too generic on their own: only flag drawX / makeX forms
                continue
            out.append(f'home-made part "{name}": use the kit (S.{name.lower().replace("draw", "").lstrip("_") or "…"}) '
                       f'or add it to sketch.js and the catalogue first   | {ln.strip()[:90]}')
    # a comment that names a part, followed by raw strokes: "// Ammeter shell" + S.circle / S.line ... (PN part 3)
    for i, ln in enumerate(lines):
        c = ln.split('//', 1)[1] if '//' in ln else ''
        m = c and not ok(i) and re.search(r'\b(' + COMMENT_PARTS + r')\b', c, re.I)
        if m and not any(KIT_CALL.search(lines[q]) for q in range(i + 1, min(i + 7, len(lines)))):
            n = sum(len(RAW.findall(lines[q])) for q in range(i + 1, min(i + 7, len(lines))) if not ok(q))
            if n >= 3:
                out.append(f'"{m.group(1)}" drawn with {n} raw strokes after line {i + 1} of the scene JS: use the kit '
                           f'part (or add it to sketch.js and the catalogue first)   | {ln.strip()[:90]}')
    raw = [i for i, ln in enumerate(lines) if RAW.search(ln) and not ok(i)]
    j = 0
    while j < len(raw):
        k = j
        while k + 1 < len(raw) and raw[k + 1] - raw[j] <= 8: k += 1
        n = sum(len(RAW.findall(lines[i])) for i in raw[j:k + 1])
        if n >= 12:
            out.append(f'{n} raw strokes within lines {raw[j] + 1}-{raw[k] + 1} of the scene JS: a part drawn by hand? '
                       f'(mark intended free drawing with // parts-ok)')
            j = k + 1
        else:
            j += 1
    return out


def main(paths):
    here = os.path.dirname(os.path.abspath(__file__))
    paths = paths or sorted(glob.glob(os.path.join(here, 'gfx_*.py')))
    total = 0
    for p in paths:
        for w in check(p):
            print(f'check_parts: {os.path.basename(p)}: {w}'); total += 1
    if total:
        print(f'check_parts: {total} warning(s) — parts come from the kit (theme-sketch.md "Parts")')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
