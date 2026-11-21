"""Example graphics module for the sketch theme (references/theme-sketch.md): one run of a transistor-switch short.
Copy to work/scripts/gfx_<tag>.py, set "theme": "sketch" in project.json, then python3 scripts/build_gfx.py <tag>.
The scene is JS (sketch.js helpers on S) with its times filled in from Python. In a real short every time comes from
the words: W(ws, '컨트롤에') for the moment a phrase starts (graphics.md "Timing"); here the times are spread over the
run so the example builds on any project."""
import build_gfx_common as G

SCENE = """
// the circuit, drawn on stroke by stroke on the 20 px grid using returned part pins
S.at({t_title}, {d}, () => S.text(90, 250, 'CONTROL에 3V를 주면?', 92));
S.at({t_title} + {d}, {d} * .5, () => S.line(92, 275, 860, 270, {{ stroke: S.RED, strokeWidth: 6, roughness: 2 }}));

let sup, r1, outP, p, gnd, rb, ctrl;
S.at({t_sup}, {d}, () => {{
  sup = S.port(640, 380, {{ flip: true, fill: '#d9d4c8' }});
  S.text(700, 398, '+3V', 66, {{ font: 'l' }});
}});
S.at({t_sup} + {d} * .5, {d}, () => {{
  r1 = S.res(520, 540, {{ rot: 90, size: 'L' }});
  S.path([sup.tip, [520, 380], r1.pins.A]);
  S.label(r1, 'R', '', {{ side: 'right' }});
}});
S.at({t_sup} + {d} * 1.2, {d}, () => {{
  S.line(r1.pins.B[0], r1.pins.B[1], 520, 740);
  S.dot(520, 740, 13);
  outP = S.port(740, 740);
  S.line(520, 740, outP.pins.A[0], outP.pins.A[1]);
  S.text(700, 690, 'OUT', 60, {{ font: 'l' }});
  S.text(835, 760, '3V', 62, {{ fill: S.BLUE }});
}});
S.at({t_tr}, {d} * 1.5, () => {{
  p = S.npn(500, 920);
  S.path([[520, 740], [p.C[0], 740], p.C]);
}});
S.at({t_tr} + {d}, {d}, () => {{
  gnd = S.gnd(p.E[0], 1160);
  S.line(p.E[0], p.E[1], gnd.pins.A[0], gnd.pins.A[1]);
}});
S.at({t_tr} + {d} * 1.5, {d}, () => {{
  rb = S.res(260, p.B[1]);
  S.line(rb.pins.B[0], rb.pins.B[1], p.B[0], p.B[1]);
  ctrl = S.port(120, p.B[1], {{ flip: true }});
  S.line(ctrl.pins.A[0], ctrl.pins.A[1], rb.pins.A[0], rb.pins.A[1]);
  S.text(60, p.B[1] - 50, 'CONTROL', 54, {{ font: 'l' }});
}});

// "3V를 넣어 주면": the control goes red, a small current into the base
S.at({t_on}, {d} * .5, () => S.port(120, p.B[1], {{ flip: true, fill: S.RED }}), 'fade');
S.at({t_on}, {d}, () => S.text(60, p.B[1] + 95, '1 (3V)', 64, {{ fill: S.RED }}));
const BASE = [ctrl.tip, [p.bar, p.B[1]]];
S.energize({t_on} + {d} * .4, BASE, 'rgba(240,120,40,.35)', 20);
S.stream({t_on} + {d} * .6, BASE, {{ n: 7, color: S.ORANGE, r: 9 }});

// the transistor turns on: the big current flows from +3V through R and the transistor to ground
const MAIN = [sup.tip, [520, 380], r1.pins.A, r1.pins.B, [520, 740], ...p.inside, gnd.pins.A];
S.energize({t_flow}, MAIN);
S.stream({t_flow} + {d} * .4, MAIN, {{ n: 11 }});

// the payoff, under the camera's push: OUT's 3V struck out, 0V written
S.at({t_pay}, {d} * .6, () => S.ellipse(855, 740, 140, 100));
S.at({t_pay} + {d} * .6, {d} * .4, () => S.strike(815, 715, 80, 50));
S.at({t_pay} + {d}, {d} * .8, () => S.text(620, 880, '0V로 뚝!', 84, {{ fill: S.RED, rot: -5 }}));
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
        # a slow, even push onto OUT (sine in-out, >= 1.2 s, <= 1.5x), a hold while it is rewritten, then back
        moves=[dict(t=push, dur=max(1.2, 0.9 * k * 1.3), ease='sine.inOut', kind='push', to=dict(x=700, y=730, s=1.5)),
               dict(t=back, dur=max(1.0, 0.8 * k * 1.3), ease='sine.inOut', kind='pull', to=dict(x=540, y=720, s=1.0))],
        thumb=[[16 * k, dur]]))
