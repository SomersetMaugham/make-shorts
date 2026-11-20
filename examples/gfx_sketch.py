"""Example graphics module for the sketch theme (references/theme-sketch.md): one run of a transistor-switch short.
Copy to work/scripts/gfx_<tag>.py, set "theme": "sketch" in project.json, then python3 scripts/build_gfx.py <tag>.
The scene is JS (sketch.js helpers on S) with its times filled in from Python. In a real short every time comes from
the words: W(ws, '컨트롤에') for the moment a phrase starts (graphics.md "Timing"); here the times are spread over the
run so the example builds on any project."""
import build_gfx_common as G

SCENE = """
const X = 600, sc = 1.5, cy = 730 + 30 * sc + 78 * sc + 60;
// the circuit, drawn on stroke by stroke
S.at({t_title}, {d}, () => S.text(90, 250, 'CONTROL에 3V를 주면?', 92));
S.at({t_title} + {d}, {d} * .5, () => S.line(92, 275, 860, 270, {{ stroke: S.RED, strokeWidth: 6, roughness: 2 }}));
S.at({t_sup}, {d}, () => {{ S.port(X + 70, 380, -1, '#d9d4c8'); S.text(X + 100, 398, '+3V', 66, {{ font: 'l' }}); }});
S.at({t_sup} + {d} * .5, {d}, () => {{ S.path([[X - 4, 380], [X - 80, 380], [X - 80, 430]]); S.res(X - 80, 430, X - 80, 640, {{ s: 1.2 }}); S.text(X - 10, 560, 'R', 70, {{ font: 'l' }}); }});
S.at({t_sup} + {d} * 1.2, {d}, () => {{ S.line(X - 80, 640, X - 80, 730); S.dot(X - 80, 730, 13); S.line(X - 80, 730, X + 110, 730); S.port(X + 110, 730, 1);
  S.text(X + 105, 680, 'OUT', 60, {{ font: 'l' }}); S.text(X + 245, 752, '3V', 62, {{ fill: S.BLUE }}); }});
let p; S.at({t_tr}, {d} * 1.5, () => {{ p = S.npn(X - 80 - 28 * sc, cy, sc); S.line(X - 80, 730, p.C[0], p.C[1]); }});
S.at({t_tr} + {d}, {d}, () => {{ S.line(p.E[0], p.E[1], p.E[0], 1150); S.gnd(p.E[0], 1190, 1.1); }});
S.at({t_tr} + {d} * 1.5, {d}, () => {{ S.res(220, p.B[1], p.B[0], p.B[1]); S.line(150, p.B[1], 220, p.B[1]); S.port(150, p.B[1], -1); S.text(50, p.B[1] - 60, 'CONTROL', 54, {{ font: 'l' }}); }});
// "3V를 넣어 주면": the control goes red, a small current into the base
S.at({t_on}, {d} * .5, () => S.port(150, p.B[1], -1, S.RED), 'fade');
S.at({t_on}, {d}, () => S.text(70, p.B[1] + 100, '1 (3V)', 64, {{ fill: S.RED }}));
const BASE = [[80, p.B[1]], [p.bar, p.B[1]]];
S.energize({t_on} + {d} * .4, BASE, 'rgba(240,120,40,.35)', 20);
S.stream({t_on} + {d} * .6, BASE, {{ n: 7, color: S.ORANGE, r: 9 }});
// the transistor turns on: the big current flows from +3V through R and the transistor to ground
const MAIN = [[X + 30, 380], [X - 80, 380], [X - 80, 730], ...p.inside, [p.E[0], 1150]];
S.energize({t_flow}, MAIN);
S.stream({t_flow} + {d} * .4, MAIN, {{ n: 11 }});
// the payoff, under the camera's push: OUT's 3V struck out, 0V written
S.at({t_pay}, {d} * .6, () => S.ellipse(X + 150, 732, 180, 104));
S.at({t_pay} + {d} * .6, {d} * .4, () => S.strike(X + 238, 712, 80, 50));
S.at({t_pay} + {d}, {d} * .8, () => S.text(X + 20, 880, '0V로 뚝!', 84, {{ fill: S.RED, rot: -5 }}));
S.at({t_end}, {d}, () => S.marker(80, 1345, '스위치 ON → OUT은 거의 0V'));
"""


def build():
    r, ws = G.words('s1', 3)
    dur = round(r['T1'] - r['T0'], 3)
    k = dur / 20                                         # the preview's 20 s choreography, fitted to this run
    t = dict(t_title=0.1 * k, t_sup=1.6 * k, t_tr=4.6 * k, t_on=8.0 * k, t_flow=9.6 * k, t_pay=11.4 * k, t_end=15.6 * k, d=round(0.7 * k, 3))
    push, back = 11.0 * k, 14.6 * k
    G.page('s1_r3', dict(
        dur=dur, theme='sketch',
        sketch=SCENE.format(**{a: round(b, 3) for a, b in t.items()}),
        # a decisive push onto OUT (expo in-out), a hold while it is rewritten, then back to the whole circuit
        moves=[dict(t=push, dur=0.9 * k * 1.3, ease='expo.inOut', kind='push', to=dict(x=730, y=700, s=2.0)),
               dict(t=back, dur=0.8 * k * 1.3, ease='power3.inOut', kind='pull', to=dict(x=540, y=720, s=1.0))],
        thumb=[[16 * k, dur]]))
