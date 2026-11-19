"""The "Compositions" section of GFX_BRIEF.md, straight from the timeline: every run (all are full visuals) with its
scene, duration and words at run-relative start times, and the cover-safe note on each r0. Paste it under
"## Compositions", then add one "Idea:" line per composition (what it shows, the real source, what lands on which word).
A word marked ~ sits at an estimated time (character position in its cue, references/narration.md); one without ~ starts a
phrase whose time the agent set from the take. Anchor graphics on phrases with W(ws, '<phrase>'), never on these numbers:
they move when the narration is recorded, and build_gfx re-reads them (graphics.md "Timing").
usage: $PY scripts/brief_runs.py [s1 s2 ...]        (all shorts in shorts.json if none given)"""
import json, sys

S = json.load(open('shorts.json', encoding='utf-8')); C = json.load(open('cut.json', encoding='utf-8'))
for sk in sys.argv[1:] or [k for k in S if k in C]:
    s, c = S[sk], C[sk]
    cover = ' / '.join(s.get('cover', []))
    state = 'PLACEHOLDER timing (not recorded yet)' if c['narration']['placeholder'] else 'recorded timing'
    print(f'\n### Short {sk} "{s.get("title", "")}"' + (f' (cover "{cover}")' if cover else '') + f' · {state} · END {c["END"]:.2f} s')
    for r in c['runs']:
        ws = [w for w in c['words'] if r['T0'] - 1e-6 <= w['s'] < r['T1'] - 1e-6]
        words = ' '.join(f"{w['w']}@{'~' if w['est'] else ''}{max(w['s'] - r['T0'], 0):.2f}" for w in ws)
        note = ' - cover-safe frame 0 (keep everything below y 620 at t 0)' if r['i'] == 0 else ''
        print(f"- `{sk}_r{r['i']}` {r['scene']} {r['dur']:.2f} s{note}: {words}")
        print('  Idea: <what it shows, the real source, what lands on which phrase>')
