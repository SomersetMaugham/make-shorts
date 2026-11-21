#!/usr/bin/env python3
"""Render the sketch theme parts catalog and identity verification sheets (stdlib only).

Usage:
    python3 scripts/parts_sheet.py --out DIR [--sheet catalog|identity|circuits|all]
"""
import argparse
import builtins
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_sketch_css():
    """Import CSS and SKETCH_CSS from scripts/build_gfx_common.py without duplicating them."""
    orig_cwd = os.getcwd()
    orig_open = builtins.open
    sys.path.insert(0, HERE)
    has_cut = os.path.exists(os.path.join(ROOT, 'cut.json'))

    def safe_open(file, mode='r', *args, **kwargs):
        if not has_cut and file == 'cut.json' and 'r' in mode:
            return io.StringIO('{}')
        return orig_open(file, mode, *args, **kwargs)

    try:
        if not has_cut:
            builtins.open = safe_open
        import build_gfx_common
        return build_gfx_common.CSS, build_gfx_common.SKETCH_CSS
    finally:
        builtins.open = orig_open
        os.chdir(orig_cwd)


def find_chrome():
    return next(
        (p for p in (
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            shutil.which('google-chrome') or '',
            shutil.which('chromium') or '',
            shutil.which('chrome') or '',
        ) if p and os.path.exists(p)),
        None,
    )


def copy_assets(out_dir):
    assets_dir = os.path.join(out_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)
    shutil.copy2(os.path.join(ROOT, 'assets', 'gfx', 'rough.js'), os.path.join(out_dir, 'rough.js'))
    shutil.copy2(os.path.join(ROOT, 'assets', 'gfx', 'sketch.js'), os.path.join(out_dir, 'sketch.js'))
    shutil.copy2(os.path.join(ROOT, 'assets', 'fonts', 'Gaegu-Bold.ttf'), os.path.join(assets_dir, 'Gaegu-Bold.ttf'))
    shutil.copy2(os.path.join(ROOT, 'assets', 'fonts', 'ArchitectsDaughter-Regular.ttf'), os.path.join(assets_dir, 'ArchitectsDaughter-Regular.ttf'))


def make_html(title, css, sketch_css, sketch_body, t_end, after_render_js=''):
    cfg_json = json.dumps({'theme': 'sketch', 'sketch': sketch_body})
    return f"""<!doctype html>
<html lang="ko" data-resolution="portrait"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<title>{html.escape(title)}</title>
<style>{css}{sketch_css}</style></head>
<body>
<div id="root" class="sketch" data-width="1080" data-height="1920">
<div id="ground"></div><div class="beam" id="beam-a"></div><div class="beam" id="beam-b"></div><div id="vignette"></div><div id="grain"></div>
<div id="viewport"><div id="world" style="width:1080px;height:1920px"></div></div>
</div>
<pre id="result" style="position:absolute;left:-9999px;top:-9999px"></pre>
<script>window.CFG={cfg_json};</script>
<script src="rough.js"></script><script src="sketch.js"></script>
<script>
Promise.all(['700 40px Gaegu', '40px "Architects Daughter"'].map((f) => document.fonts.load(f, '가A')))
  .then(() => document.fonts.ready)
  .then(() => {{
    window.CFG_RENDER({t_end});
    {after_render_js}
  }});
</script>
</body></html>"""


CATALOG_PAGE_1 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (1/7) — 수동·전원·반도체', 62, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: '저항', fn: 'S.res', draw: (x, y) => S.res(x, y) },
  { ko: '커패시터', fn: 'S.cap', draw: (x, y) => S.cap(x, y) },
  { ko: '전해 커패시터', fn: 'S.cap({polar})', draw: (x, y) => S.cap(x, y, { polar: true }) },
  { ko: '다이오드', fn: 'S.diode', draw: (x, y) => S.diode(x, y) },
  { ko: '제너 다이오드', fn: "S.diode({kind:'zener'})", draw: (x, y) => S.diode(x, y, { kind: 'zener' }) },
  { ko: '포토 다이오드', fn: "S.diode({kind:'photo'})", draw: (x, y) => S.diode(x, y, { kind: 'photo' }) },
  { ko: 'LED (꺼짐)', fn: 'S.led({on:false})', draw: (x, y) => S.led(x, y, { on: false }) },
  { ko: 'LED (켜짐 .at)', fn: 'S.led().at(0.6,{on:true})', draw: (x, y) => S.led(x, y, { on: false }).at(0.6, { on: true }) },
  { ko: '건전지 (1셀)', fn: 'S.battery', draw: (x, y) => S.battery(x, y) },
  { ko: '건전지 (2셀)', fn: 'S.battery({cells:2})', draw: (x, y) => S.battery(x, y, { cells: 2 }) },
  { ko: '접지', fn: 'S.gnd', draw: (x, y) => S.gnd(x, y) },
  { ko: '전원 기준', fn: 'S.vcc', draw: (x, y) => S.vcc(x, y + 10) },
  { ko: '포트', fn: 'S.port', draw: (x, y) => S.port(x, y) },
  { ko: 'NPN 트랜지스터', fn: 'S.npn', draw: (x, y) => S.npn(x, y), tall: true },
  { ko: 'PNP 트랜지스터', fn: 'S.pnp', draw: (x, y) => S.pnp(x, y), tall: true },
];

const cols = 3, colX = [190, 540, 890];
const rowY = [330, 620, 910, 1200, 1600];
const pinOffsets = (p, cx, cy) => {
  const [px, py] = p, dx = px - cx, dy = py - cy;
  if (Math.abs(dy) >= Math.abs(dx)) {
    return dy < 0 ? [px, py - 14, 'middle'] : [px, py + 30, 'middle'];
  }
  return dx < 0 ? [px - 14, py + 9, 'end'] : [px + 14, py + 9, 'start'];
};

items.forEach((it, idx) => {
  const r = Math.floor(idx / cols), c = idx % cols;
  const cx = colX[c], cy = rowY[r];
  const labelY = it.tall ? cy - 220 : cy - 135;
  S.at(0.05, 0.35, () => {
    S.text(cx, labelY, it.ko, 36, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(cx, labelY + 34, it.fn, 24, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(cx, cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const [lx, ly, anchor] = pinOffsets(pt, cx, cy);
        S.text(lx, ly, pn, 26, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
});
"""

CATALOG_PAGE_2 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (2/7) — IC 칩 · 물질 · 전류', 62, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: 'IC 칩 (pitch 60, lead 60)', fn: 'S.chip', cx: 280, cy: 370, labelOff: 165, draw: (x, y) => S.chip(x, y, { name: 'IC', left: ['1', '2', '3'], right: ['6', '5', '4'] }) },
  { ko: '전류 화살표', fn: 'S.curArrow', cx: 760, cy: 370, labelOff: 165, draw: (x, y) => { S.curArrow([[x - 90, y], [x + 90, y]], { color: S.RED, label: 'I' }); return null; } },
  { ko: '원자', fn: 'S.atom', cx: 200, cy: 730, labelOff: 155, draw: (x, y) => S.atom(x, y) },
  { ko: '전자', fn: 'S.electron', cx: 540, cy: 730, labelOff: 155, draw: (x, y) => S.electron(x, y, { size: 'L' }) },
  { ko: '정공 (점선)', fn: 'S.hole', cx: 880, cy: 730, labelOff: 155, draw: (x, y) => S.hole(x, y, { size: 'L' }) },
  { ko: '양이온', fn: "S.ion('+')", cx: 280, cy: 1040, labelOff: 145, draw: (x, y) => S.ion(x, y, '+') },
  { ko: '음이온', fn: "S.ion('-')", cx: 760, cy: 1040, labelOff: 145, draw: (x, y) => S.ion(x, y, '-') },
  { ko: '결정 격자', fn: 'S.lattice', cx: 540, cy: 1480, labelOff: 220, draw: (x, y) => { S.lattice(x - 160, y - 80, 3, 2, 160, { cell: (i, j) => (i === 1 && j === 0 ? { label: 'B', color: S.RED, skipBond: ['r'] } : {}) }); return null; } },
];

for (const it of items) {
  S.at(0.05, 0.35, () => {
    const labelY = it.cy - it.labelOff;
    S.text(it.cx, labelY, it.ko, 36, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(it.cx, labelY + 34, it.fn, 24, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(it.cx, it.cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const dx = pt[0] - it.cx, dy = pt[1] - it.cy;
        let lx, ly, anchor = 'middle';
        if (Math.hypot(dx, dy) < 1) {
          const b = part.box || { y: it.cy - 20, h: 40 };
          lx = pt[0];
          ly = b.y + b.h + 28;
        } else if (Math.abs(dy) >= Math.abs(dx)) {
          lx = pt[0];
          ly = dy < 0 ? pt[1] - 14 : pt[1] + 28;
        } else {
          lx = pt[0] + (dx < 0 ? -14 : 14);
          ly = pt[1] + 8;
          anchor = dx < 0 ? 'end' : 'start';
        }
    S.text(lx, ly, pn, 24, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
}
"""


CATALOG_PAGE_3 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (3/7) — 수동 소자(확장) · 전원', 60, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: '가변저항', fn: 'S.pot', draw: (x, y) => S.pot(x, y) },
  { ko: '광저항 (CdS)', fn: 'S.ldr', draw: (x, y) => S.ldr(x, y) },
  { ko: '서미스터', fn: 'S.thermistor', draw: (x, y) => S.thermistor(x, y) },
  { ko: '전해 커패시터', fn: 'S.ecap', draw: (x, y) => S.ecap(x, y) },
  { ko: '인덕터', fn: 'S.ind', draw: (x, y) => S.ind(x, y) },
  { ko: '철심 인덕터', fn: 'S.ind({core:true})', draw: (x, y) => S.ind(x, y, { core: true }) },
  { ko: '변압기', fn: 'S.xfmr', draw: (x, y) => S.xfmr(x, y) },
  { ko: '퓨즈', fn: 'S.fuse', draw: (x, y) => S.fuse(x, y) },
  { ko: '크리스탈', fn: 'S.xtal', draw: (x, y) => S.xtal(x, y) },
  { ko: '직류 전원', fn: 'S.vdc', draw: (x, y) => S.vdc(x, y) },
  { ko: '교류 전원', fn: 'S.vac', draw: (x, y) => S.vac(x, y) },
  { ko: '전류원', fn: 'S.isrc', draw: (x, y) => S.isrc(x, y) },
];

const cols = 3, colX = [190, 540, 890];
const rowY = [355, 740, 1125, 1510];
const pinOffsets = (p, cx, cy) => {
  const [px, py] = p, dx = px - cx, dy = py - cy;
  if (Math.abs(dy) > Math.abs(dx)) {
    return dy < 0 ? [px, py - 14, 'middle'] : [px, py + 30, 'middle'];
  }
  return dx < 0 ? [px - 14, py + 9, 'end'] : [px + 14, py + 9, 'start'];
};

items.forEach((it, idx) => {
  const r = Math.floor(idx / cols), c = idx % cols;
  const cx = colX[c], cy = rowY[r];
  const labelY = cy - 160;
  S.at(0.05, 0.35, () => {
    S.text(cx, labelY, it.ko, 36, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(cx, labelY + 34, it.fn, 24, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(cx, cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const [lx, ly, anchor] = pinOffsets(pt, cx, cy);
        S.text(lx, ly, pn, 26, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
});
"""


CATALOG_PAGE_4 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (4/7) — 반도체 (MOSFET · OPAMP · 게이트)', 50, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: 'N채널 MOSFET', fn: 'S.nmos', cx: 230, cy: 390, tall: true, draw: (x, y) => S.nmos(x, y) },
  { ko: 'P채널 MOSFET', fn: 'S.pmos', cx: 560, cy: 390, tall: true, draw: (x, y) => S.pmos(x, y) },
  { ko: '연산증폭기', fn: 'S.opamp', cx: 865, cy: 390, draw: (x, y) => S.opamp(x, y) },
  { ko: '연산증폭기 (전원)', fn: 'S.opamp({power:true})', cx: 195, cy: 770, draw: (x, y) => S.opamp(x, y, { power: true }) },
  { ko: 'AND 게이트', fn: "S.gate('and')", cx: 535, cy: 770, draw: (x, y) => S.gate('and', x, y) },
  { ko: 'OR 게이트', fn: "S.gate('or')", cx: 865, cy: 770, draw: (x, y) => S.gate('or', x, y) },
  { ko: 'NOT 게이트', fn: "S.gate('not')", cx: 195, cy: 1130, draw: (x, y) => S.gate('not', x, y) },
  { ko: 'NAND 게이트', fn: "S.gate('nand')", cx: 535, cy: 1130, draw: (x, y) => S.gate('nand', x, y) },
  { ko: 'NOR 게이트', fn: "S.gate('nor')", cx: 865, cy: 1130, draw: (x, y) => S.gate('nor', x, y) },
  { ko: 'XOR 게이트', fn: "S.gate('xor')", cx: 195, cy: 1490, draw: (x, y) => S.gate('xor', x, y) },
];

const pinOffsets = (p, cx, cy) => {
  const [px, py] = p, dx = px - cx, dy = py - cy;
  if (Math.abs(dy) > Math.abs(dx)) {
    return dy < 0 ? [px, py - 14, 'middle'] : [px, py + 30, 'middle'];
  }
  return dx < 0 ? [px - 14, py + 9, 'end'] : [px + 14, py + 9, 'start'];
};

items.forEach((it) => {
  const cx = it.cx, cy = it.cy;
  const labelY = it.tall ? cy - 215 : cy - 165;
  S.at(0.05, 0.35, () => {
    S.text(cx, labelY, it.ko, 36, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(cx, labelY + 34, it.fn, 24, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(cx, cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const [lx, ly, anchor] = pinOffsets(pt, cx, cy);
        S.text(lx, ly, pn, 24, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
});
"""


CATALOG_PAGE_5 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (5/7) — 스위치 · 출력', 58, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: '토글 스위치 (열림)', fn: 'S.sw', draw: (x, y) => S.sw(x, y) },
  { ko: '토글 스위치 (닫힘)', fn: 'S.sw().at({closed})', draw: (x, y) => S.sw(x, y).at(0.6, { closed: true }) },
  { ko: '푸시 버튼 (열림)', fn: "S.sw({kind:'push'})", draw: (x, y) => S.sw(x, y, { kind: 'push' }) },
  { ko: '푸시 버튼 (눌림)', fn: "S.sw({kind:'push'}).at", draw: (x, y) => S.sw(x, y, { kind: 'push' }).at(0.6, { closed: true }) },
  { ko: 'SPDT 스위치 (NC)', fn: "S.sw({kind:'spdt'})", draw: (x, y) => S.sw(x, y, { kind: 'spdt' }) },
  { ko: 'SPDT 스위치 (NO)', fn: "S.sw({kind:'spdt'}).at", draw: (x, y) => S.sw(x, y, { kind: 'spdt' }).at(0.6, { pos: 1 }) },
  { ko: '릴레이 (열림)', fn: 'S.relay', draw: (x, y) => S.relay(x, y) },
  { ko: '릴레이 (닫힘)', fn: 'S.relay().at({closed})', draw: (x, y) => S.relay(x, y).at(0.6, { closed: true }) },
  { ko: '전구 (꺼짐)', fn: 'S.lamp', draw: (x, y) => S.lamp(x, y) },
  { ko: '전구 (켜짐)', fn: 'S.lamp().at({on:true})', draw: (x, y) => S.lamp(x, y).at(0.6, { on: true }) },
  { ko: '모터', fn: 'S.motor', draw: (x, y) => S.motor(x, y) },
  { ko: '스피커', fn: 'S.speaker', draw: (x, y) => S.speaker(x, y) },
];

const cols = 3, colX = [195, 535, 865];
const rowY = [355, 740, 1125, 1510];
const pinOffsets = (p, cx, cy) => {
  const [px, py] = p, dx = px - cx, dy = py - cy;
  if (Math.abs(dy) > Math.abs(dx)) {
    return dy < 0 ? [px, py - 14, 'middle'] : [px, py + 30, 'middle'];
  }
  return dx < 0 ? [px - 14, py + 9, 'end'] : [px + 14, py + 9, 'start'];
};

items.forEach((it, idx) => {
  const r = Math.floor(idx / cols), c = idx % cols;
  const cx = colX[c], cy = rowY[r];
  const labelY = cy - 160;
  S.at(0.05, 0.35, () => {
    S.text(cx, labelY, it.ko, 34, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(cx, labelY + 34, it.fn, 22, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(cx, cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const [lx, ly, anchor] = pinOffsets(pt, cx, cy);
        S.text(lx, ly, pn, 24, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
});
"""


CATALOG_PAGE_6 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (6/7) — 계측기 · 배선 · 구획', 56, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: '전류계', fn: 'S.ammeter', cx: 195, cy: 345, draw: (x, y) => S.ammeter(x, y) },
  { ko: '전압계', fn: 'S.voltmeter', cx: 535, cy: 345, draw: (x, y) => S.voltmeter(x, y) },
  { ko: '저항계', fn: "S.meter({label:'Ω'})", cx: 865, cy: 345, draw: (x, y) => S.meter(x, y, { label: 'Ω' }) },
  { ko: '아날로그 계기 (0.2)', fn: 'S.dial().at(0.2)', cx: 195, cy: 730, draw: (x, y) => S.dial(x, y).at(0.6, { value: 0.2 }) },
  { ko: '아날로그 계기 (0.85)', fn: 'S.dial().at(0.85)', cx: 535, cy: 730, draw: (x, y) => S.dial(x, y).at(0.6, { value: 0.85 }) },
  { ko: '오실로스코프', fn: 'S.scope', cx: 865, cy: 730, draw: (x, y) => S.scope(x, y) },
  { ko: '직각 전선', fn: 'S.wire(pts)', cx: 195, cy: 1120, draw: (x, y) => { S.wire([[x - 70, y + 30], [x, y + 30], [x, y - 30], [x + 70, y - 30]]); return null; } },
  { ko: '자동 격자 연결', fn: 'S.route(A,B,{via})', cx: 535, cy: 1120, draw: (x, y) => { const a = S.term(x - 60, y + 30), b = S.term(x + 60, y - 30); S.route(a.pins.A, b.pins.A, { via: 'hvh' }); return null; } },
  { ko: '교차 점프 · 접점', fn: 'S.hop / S.dot', cx: 865, cy: 1120, draw: (x, y) => { S.wire([[x - 80, y], [x + 80, y]]); S.wire([[x - 30, y - 45], [x - 30, y + 45]]); S.wire([[x + 30, y - 45], [x + 30, y + 45]]); S.hop(x - 30, y); S.dot(x + 30, y, 9); return null; } },
  { ko: '단자', fn: 'S.term', cx: 230, cy: 1500, draw: (x, y) => S.term(x, y) },
  { ko: '점선 구획', fn: 'S.block(x,y,w,h,title)', cx: 700, cy: 1500, draw: (x, y) => { S.block(x - 160, y - 80, 320, 160, '입력단'); S.res(x, y + 20); return null; } },
];

const pinOffsets = (p, cx, cy) => {
  const [px, py] = p, dx = px - cx, dy = py - cy;
  if (Math.hypot(dx, dy) < 1) return [px, py + 34, 'middle'];
  if (Math.abs(dy) > Math.abs(dx)) {
    return dy < 0 ? [px, py - 14, 'middle'] : [px, py + 30, 'middle'];
  }
  return dx < 0 ? [px - 14, py + 9, 'end'] : [px + 14, py + 9, 'start'];
};

items.forEach((it) => {
  const cx = it.cx, cy = it.cy;
  const labelY = cy - 160;
  S.at(0.05, 0.35, () => {
    S.text(cx, labelY, it.ko, 34, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(cx, labelY + 34, it.fn, 22, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(cx, cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const [lx, ly, anchor] = pinOffsets(pt, cx, cy);
        S.text(lx, ly, pn, 24, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
});
"""


CATALOG_PAGE_7 = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '부품 도감 (7/7) — 2단계 기호 · 실물 그림', 56, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

const items = [
  { ko: '가변 커패시터', fn: 'S.vcap', cx: 190, cy: 340, labelOff: 155, draw: (x, y) => S.vcap(x, y) },
  { ko: '쇼트키 다이오드', fn: "S.diode({kind:'schottky'})", cx: 540, cy: 340, labelOff: 155, draw: (x, y) => S.diode(x, y, { kind: 'schottky' }) },
  { ko: '버저', fn: 'S.buzzer', cx: 890, cy: 340, labelOff: 155, draw: (x, y) => S.buzzer(x, y) },
  { ko: '건전지 실물 (AA)', fn: "S.cellReal({kind:'AA'})", cx: 190, cy: 675, labelOff: 155, draw: (x, y) => S.cellReal(x, y, { kind: 'AA' }) },
  { ko: '건전지 실물 (9V)', fn: "S.cellReal({kind:'9V'})", cx: 540, cy: 675, labelOff: 155, draw: (x, y) => S.cellReal(x, y, { kind: '9V' }) },
  { ko: '색띠 저항 (220Ω)', fn: "S.resReal({value:'220'})", cx: 890, cy: 675, labelOff: 155, draw: (x, y) => S.resReal(x, y, { value: '220', tol: 'gold' }) },
  { ko: 'LED 실물 (꺼짐)', fn: 'S.ledReal({on:false})', cx: 190, cy: 1015, labelOff: 155, draw: (x, y) => S.ledReal(x, y, { on: false }) },
  { ko: 'LED 실물 (켜짐)', fn: 'S.ledReal().at({on:true})', cx: 540, cy: 1015, labelOff: 155, draw: (x, y) => S.ledReal(x, y, { on: false }).at(0.6, { on: true }) },
  { ko: '전해 콘덴서 캔', fn: 'S.ecapReal', cx: 890, cy: 1015, labelOff: 155, draw: (x, y) => S.ecapReal(x, y) },
  { ko: 'TO-92 트랜지스터', fn: "S.to92({pins:'EBC'})", cx: 230, cy: 1410, labelOff: 180, draw: (x, y) => S.to92(x, y, { pins: 'EBC' }) },
  { ko: '브레드보드 조각', fn: 'S.breadboard(x,y,12,8)', cx: 700, cy: 1450, labelOff: 220, draw: (x, y) => S.breadboard(x - 150, y - 160, 12, 8) },
];

const pinOffsets = (p, cx, cy) => {
  const [px, py] = p, dx = px - cx, dy = py - cy;
  if (Math.abs(dy) >= Math.abs(dx)) {
    return dy < 0 ? [px, py - 14, 'middle'] : [px, py + 30, 'middle'];
  }
  return dx < 0 ? [px - 14, py + 9, 'end'] : [px + 14, py + 9, 'start'];
};

items.forEach((it) => {
  const cx = it.cx, cy = it.cy;
  const labelY = cy - it.labelOff;
  S.at(0.05, 0.35, () => {
    S.text(cx, labelY, it.ko, 34, { font: 'k', anchor: 'middle', rot: 0 });
    S.text(cx, labelY + 34, it.fn, 22, { font: 'l', fill: S.GRAY, anchor: 'middle', rot: 0 });
    const part = it.draw(cx, cy);
    if (part && part.pins) {
      for (const [pn, pt] of Object.entries(part.pins)) {
        S.dot(pt[0], pt[1], 5, S.RED);
        const [lx, ly, anchor] = pinOffsets(pt, cx, cy);
        S.text(lx, ly, pn, 22, { font: 'l', fill: S.BLUE, anchor, rot: 0 });
      }
    }
  });
});
"""


CATALOG_REAL_SYMBOL = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '실물 ↔ 회로 기호', 62, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
  S.text(135, 178, '부품', 34, { font: 'k', fill: S.BLUE, anchor: 'middle', rot: 0 });
  S.text(430, 178, '실물 그림', 34, { font: 'k', fill: S.BLUE, anchor: 'middle', rot: 0 });
  S.text(840, 178, '회로 기호', 34, { font: 'k', fill: S.BLUE, anchor: 'middle', rot: 0 });
});

const pairs = [
  { ko: 'AA 건전지', sub: 'cellReal ↔ battery', y: 305, real: (x, y) => S.cellReal(x, y, { kind: 'AA' }), sym: (x, y) => S.battery(x, y) },
  { ko: '9V 건전지', sub: 'cellReal(9V) ↔ battery', y: 535, real: (x, y) => S.cellReal(x, y, { kind: '9V' }), sym: (x, y) => S.battery(x, y, { cells: 2 }) },
  { ko: '색띠 저항', sub: 'resReal(220) ↔ res', y: 765, real: (x, y) => S.resReal(x, y, { value: '220', tol: 'gold' }), sym: (x, y) => S.res(x, y) },
  { ko: 'LED', sub: 'ledReal ↔ led', y: 995, real: (x, y) => S.ledReal(x, y, { on: false }).at(0.7, { on: true }), sym: (x, y) => S.led(x, y, { on: false }).at(0.7, { on: true }) },
  { ko: '전해 커패시터', sub: 'ecapReal ↔ ecap', y: 1225, real: (x, y) => S.ecapReal(x, y), sym: (x, y) => S.ecap(x, y) },
  { ko: '트랜지스터', sub: 'to92 ↔ npn', y: 1485, real: (x, y) => S.to92(x, y, { pins: 'EBC' }), sym: (x, y) => S.npn(x, y, { size: 'S' }) },
];

pairs.forEach((p, idx) => {
  S.at(0.05, 0.35, () => {
    if (idx > 0) S.line(60, p.y - 115, 1020, p.y - 115, { stroke: S.GRAY, strokeWidth: 2, strokeLineDash: [8, 8] });
    S.text(60, p.y - 6, p.ko, 36, { font: 'k', anchor: 'start', rot: 0 });
    S.text(60, p.y + 30, p.sub, 22, { font: 'l', fill: S.GRAY, anchor: 'start', rot: 0 });
    p.real(430, p.y);
    S.text(635, p.y + 12, '↔', 44, { font: 'k', fill: S.RED, anchor: 'middle', rot: 0 });
    p.sym(840, p.y);
  });
});
"""


DRAW_PART_FN = r"""
const drawPart = (kind, cx, cy, opts) => {
  if (kind === 'res') return S.res(cx, cy, opts);
  if (kind === 'pot') return S.pot(cx, cy, opts);
  if (kind === 'ldr') return S.ldr(cx, cy, opts);
  if (kind === 'thermistor') return S.thermistor(cx, cy, opts);
  if (kind === 'cap') return S.cap(cx, cy, opts);
  if (kind === 'vcap') return S.vcap(cx, cy, opts);
  if (kind === 'ecap') return S.ecap(cx, cy, opts);
  if (kind === 'ind') return S.ind(cx, cy, opts);
  if (kind === 'ind_core') return S.ind(cx, cy, { ...opts, core: true });
  if (kind === 'xfmr') return S.xfmr(cx, cy, opts);
  if (kind === 'fuse') return S.fuse(cx, cy, opts);
  if (kind === 'xtal') return S.xtal(cx, cy, opts);
  if (kind === 'diode') return S.diode(cx, cy, opts);
  if (kind === 'zener') return S.diode(cx, cy, { ...opts, kind: 'zener' });
  if (kind === 'photo') return S.diode(cx, cy, { ...opts, kind: 'photo' });
  if (kind === 'schottky') return S.diode(cx, cy, { ...opts, kind: 'schottky' });
  if (kind === 'led') return S.led(cx, cy, opts);
  if (kind === 'battery') return S.battery(cx, cy, opts);
  if (kind === 'vdc') return S.vdc(cx, cy, opts);
  if (kind === 'vac') return S.vac(cx, cy, opts);
  if (kind === 'isrc') return S.isrc(cx, cy, opts);
  if (kind === 'gnd') return S.gnd(cx, cy, opts);
  if (kind === 'vcc') return S.vcc(cx, cy, opts);
  if (kind === 'port') return S.port(cx, cy, opts);
  if (kind === 'npn') return S.npn(cx, cy, opts);
  if (kind === 'pnp') return S.pnp(cx, cy, opts);
  if (kind === 'nmos') return S.nmos(cx, cy, opts);
  if (kind === 'pmos') return S.pmos(cx, cy, opts);
  if (kind === 'opamp') return S.opamp(cx, cy, opts);
  if (kind === 'opamp_p') return S.opamp(cx, cy, { ...opts, power: true });
  if (kind === 'and' || kind === 'or' || kind === 'not' || kind === 'nand' || kind === 'nor' || kind === 'xor') {
    return S.gate(kind, cx, cy, opts);
  }
  if (kind === 'sw') return S.sw(cx, cy, opts);
  if (kind === 'sw_push') return S.sw(cx, cy, { ...opts, kind: 'push' });
  if (kind === 'sw_spdt') return S.sw(cx, cy, { ...opts, kind: 'spdt' });
  if (kind === 'relay') return S.relay(cx, cy, opts);
  if (kind === 'lamp') return S.lamp(cx, cy, opts);
  if (kind === 'motor') return S.motor(cx, cy, opts);
  if (kind === 'speaker') return S.speaker(cx, cy, opts);
  if (kind === 'buzzer') return S.buzzer(cx, cy, opts);
  if (kind === 'ammeter') return S.ammeter(cx, cy, opts);
  if (kind === 'voltmeter') return S.voltmeter(cx, cy, opts);
  if (kind === 'ohmmeter') return S.meter(cx, cy, { ...opts, label: 'Ω' });
  if (kind === 'dial') return S.dial(cx, cy, opts);
  if (kind === 'scope') return S.scope(cx, cy, opts);
  if (kind === 'hop') return S.hop(cx, cy, opts);
  if (kind === 'term') return S.term(cx, cy, opts);
  if (kind === 'chip') return S.chip(cx, cy, { ...opts, w: 120, h: 120, name: 'IC', left: ['1', '2'], right: ['4', '3'] });
  if (kind === 'atom') return S.atom(cx, cy, opts);
  if (kind === 'electron') return S.electron(cx, cy, opts);
  if (kind === 'hole') return S.hole(cx, cy, opts);
  if (kind === 'ion') return S.ion(cx, cy, { ...opts, sign: '+' });
  if (kind === 'cell_aa') return S.cellReal(cx, cy, { ...opts, kind: 'AA' });
  if (kind === 'cell_9v') return S.cellReal(cx, cy, { ...opts, kind: '9V' });
  if (kind === 'res_real') return S.resReal(cx, cy, { ...opts, value: '220', tol: 'gold' });
  if (kind === 'led_real') return S.ledReal(cx, cy, opts);
  if (kind === 'ecap_real') return S.ecapReal(cx, cy, opts);
  if (kind === 'to92') return S.to92(cx, cy, { ...opts, pins: 'EBC' });
  if (kind === 'breadboard') return S.breadboard(cx, cy, { ...opts, cols: 5, rows: 2 });
  throw new Error('Unknown part: ' + kind);
};
"""


def make_identity_compact_sketch(page_idx, total_pages, kinds):
    kinds_json = json.dumps(kinds)
    return f"""
window.__ID_CASES = [];
const kinds = {kinds_json};
{DRAW_PART_FN}

const xs = [175, 295, 415, 535, 655, 785, 915];
S.at(0, 0.25, () => {{
  S.text(40, 95, '동일성 검사 ({page_idx + 1}/{total_pages}) — 회전 · 크기(S/M/L) · 순서', 50, {{ rot: 0 }});
  S.line(40, 112, 1040, 112, {{ stroke: S.RED, strokeWidth: 5 }});
  ['0°', '90°', '180°', '270°', 'S', 'L', '역순'].forEach((lbl, i) =>
    S.text(xs[i], 155, lbl, 28, {{ font: 'k', anchor: 'middle', fill: S.BLUE, rot: 0 }}));
}});

const rowStep = kinds.length <= 6 ? 260 : 200;
const rowY = (i) => 270 + i * rowStep;

S.at(0.1, 0.4, () => {{
  kinds.forEach((kind, ri) => {{
    const cy = rowY(ri);
    S.text(40, cy + 10, kind, 28, {{ font: 'l', anchor: 'start', rot: 0 }});
    const vars = [
      ['rot0', {{ rot: 0, size: 'M' }}],
      ['rot90', {{ rot: 90, size: 'M' }}],
      ['rot180', {{ rot: 180, size: 'M' }}],
      ['rot270', {{ rot: 270, size: 'M' }}],
      ['sizeS', {{ rot: 0, size: 'S' }}],
      ['sizeL', {{ rot: 0, size: 'L' }}],
    ];
    vars.forEach(([vname, opts], ci) => {{
      const part = drawPart(kind, xs[ci], cy, opts);
      window.__ID_CASES.push({{ kind, variant: vname, part }});
    }});
  }});
}});

S.at(0.2, 0.4, () => {{
  for (let ri = kinds.length - 1; ri >= 0; ri--) {{
    const kind = kinds[ri];
    const cy = rowY(ri);
    S.line(865, cy + 75, 965, cy + 75, {{ stroke: S.GRAY, strokeWidth: 2 }});
    const part = drawPart(kind, xs[6], cy, {{ rot: 0, size: 'M' }});
    window.__ID_CASES.push({{ kind, variant: 'revOrder', part }});
  }}
}});
"""


def make_identity_large_sketch(page_idx, total_pages, kinds):
    kinds_json = json.dumps(kinds)
    return f"""
window.__ID_CASES = [];
const kinds = {kinds_json};
{DRAW_PART_FN}

S.at(0, 0.25, () => {{
  S.text(40, 95, '동일성 검사 ({page_idx + 1}/{total_pages}) — 다단자 · 큰 부품 (S/M/L)', 48, {{ rot: 0 }});
  S.line(40, 112, 1040, 112, {{ stroke: S.RED, strokeWidth: 5 }});
}});

const rowAX = [200, 420, 650, 865];
const rowBX = [210, 520, 860];
const blockY = (i) => 275 + i * 540;

S.at(0.1, 0.4, () => {{
  kinds.forEach((kind, i) => {{
    const y0 = blockY(i), y1 = y0 + 270;
    S.text(40, y0 - 110, kind + ' (0/90/180/270 · S / L / 역순)', 28, {{ font: 'l', anchor: 'start', fill: S.BLUE, rot: 0 }});
    [0, 90, 180, 270].forEach((rot, ci) => {{
      const part = drawPart(kind, rowAX[ci], y0, {{ rot, size: 'M' }});
      window.__ID_CASES.push({{ kind, variant: 'rot' + rot, part }});
    }});
    [['sizeS', 'S', rowBX[0]], ['sizeL', 'L', rowBX[1]]].forEach(([vname, sz, cx]) => {{
      const part = drawPart(kind, cx, y1, {{ rot: 0, size: sz }});
      window.__ID_CASES.push({{ kind, variant: vname, part }});
    }});
  }});
}});

S.at(0.2, 0.4, () => {{
  for (let i = kinds.length - 1; i >= 0; i--) {{
    const kind = kinds[i], y1 = blockY(i) + 270;
    S.line(780, y1 + 130, 940, y1 + 130, {{ stroke: S.GRAY, strokeWidth: 2 }});
    const part = drawPart(kind, rowBX[2], y1, {{ rot: 0, size: 'M' }});
    window.__ID_CASES.push({{ kind, variant: 'revOrder', part }});
  }}
}});
"""


def make_identity_flip_sketch(page_idx, total_pages, kinds):
    kinds_json = json.dumps(kinds)
    return f"""
window.__ID_CASES = [];
const kinds = {kinds_json};
{DRAW_PART_FN}

const xs = [255, 415, 565, 705, 890];
S.at(0, 0.25, () => {{
  S.text(40, 95, '동일성 검사 ({page_idx + 1}/{total_pages}) — 좌우 반전 (flip · 회전 · S/L)', 48, {{ rot: 0 }});
  S.line(40, 112, 1040, 112, {{ stroke: S.RED, strokeWidth: 5 }});
  ['0°', 'flip', 'flip+90°', 'flip+S', 'flip+L'].forEach((lbl, i) =>
    S.text(xs[i], 155, lbl, 28, {{ font: 'k', anchor: 'middle', fill: S.BLUE, rot: 0 }}));
}});

const rowStep = 260;
const rowY = (i) => 270 + i * rowStep;

S.at(0.1, 0.4, () => {{
  kinds.forEach((kind, ri) => {{
    const cy = rowY(ri);
    S.text(40, cy + 10, kind, 26, {{ font: 'l', anchor: 'start', rot: 0 }});
    const vars = [
      ['rot0', {{ rot: 0, size: 'M' }}],
      ['flip', {{ rot: 0, size: 'M', flip: true }}],
      ['flipRot90', {{ rot: 90, size: 'M', flip: true }}],
      ['flipS', {{ rot: 0, size: 'S', flip: true }}],
      ['flipL', {{ rot: 0, size: 'L', flip: true }}],
    ];
    vars.forEach(([vname, opts], ci) => {{
      const part = drawPart(kind, xs[ci], cy, opts);
      window.__ID_CASES.push({{ kind, variant: vname, part }});
    }});
  }});
}});
"""


def make_identity_large_flip_sketch(page_idx, total_pages, kinds):
    kinds_json = json.dumps(kinds)
    return f"""
window.__ID_CASES = [];
const kinds = {kinds_json};
{DRAW_PART_FN}

S.at(0, 0.25, () => {{
  S.text(40, 95, '동일성 검사 ({page_idx + 1}/{total_pages}) — 큰 부품 좌우 반전 (flip · S/L)', 46, {{ rot: 0 }});
  S.line(40, 112, 1040, 112, {{ stroke: S.RED, strokeWidth: 5 }});
}});

const rowAX = [210, 520, 820];
const rowBX = [280, 740];
const blockY = (i) => 290 + i * 620;

S.at(0.1, 0.4, () => {{
  kinds.forEach((kind, i) => {{
    const y0 = blockY(i), y1 = y0 + 290;
    S.text(40, y0 - 125, kind + ' (0° · flip · flip+90° / flip+S · flip+L)', 28, {{ font: 'l', anchor: 'start', fill: S.BLUE, rot: 0 }});
    [['rot0', {{ rot: 0, size: 'M' }}, rowAX[0]], ['flip', {{ rot: 0, size: 'M', flip: true }}, rowAX[1]], ['flipRot90', {{ rot: 90, size: 'M', flip: true }}, rowAX[2]]].forEach(([vname, opts, cx]) => {{
      const part = drawPart(kind, cx, y0, opts);
      window.__ID_CASES.push({{ kind, variant: vname, part }});
    }});
    [['flipS', 'S', rowBX[0]], ['flipL', 'L', rowBX[1]]].forEach(([vname, sz, cx]) => {{
      const part = drawPart(kind, cx, y1, {{ rot: 0, size: sz, flip: true }});
      window.__ID_CASES.push({{ kind, variant: vname, part }});
    }});
  }});
}});
"""


CIRCUIT_1_LED = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '시트 3 (1/3) — 건전지 · 스위치 · 저항 · LED', 54, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

let bat, sw, r1, led, w1, w2, w3, w4;
S.at(0.1, 0.5, () => {
  bat = S.battery(260, 720, { rot: 90, cells: 2 });
  S.label(bat, 'V1', '3V', { side: 'left' });

  sw = S.sw(380, 540, { kind: 'spst' }).at(1.0, { closed: true });
  S.label(sw, 'S1', '', { side: 'top' });

  r1 = S.res(620, 720, { rot: 90 });
  S.label(r1, 'R1', '220Ω', { side: 'left' });

  led = S.led(440, 900, { rot: 180 }).at(1.15, { on: true });
  S.label(led, 'D1', 'LED', { side: 'bottom' });

  w1 = S.route(bat.pins.P, sw.pins.A, { via: 'vh' });
  w2 = S.route(sw.pins.B, r1.pins.A);
  w3 = S.route(r1.pins.B, led.pins.A, { via: 'vh' });
  w4 = S.route(led.pins.K, bat.pins.N);
});

const LOOP = [...w1, ...sw.path, ...w2, ...r1.path, ...w3, ...led.path, ...w4];
S.energize(1.2, LOOP);
S.stream(1.25, LOOP, { n: 12 });
"""


CIRCUIT_2_NPN = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '시트 3 (2/3) — NPN 트랜지스터 스위치', 54, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

let vcc, rc, led, q1, gnd, vctrl, sw, rb;
let wc1, wc2, wc3, wc4, wb1, wb2, wb3;
S.at(0.1, 0.55, () => {
  vcc = S.vcc(560, 260, '5V');
  rc = S.res(560, 440, { rot: 90 });
  S.label(rc, 'Rc', '1kΩ', { side: 'right' });

  led = S.led(560, 640, { rot: 90 }).at(1.15, { on: true });
  S.label(led, 'D1', 'LED', { side: 'right' });

  q1 = S.npn(540, 920);
  S.label(q1, 'Q1', 'NPN', { side: 'right' });

  gnd = S.gnd(560, 1180);

  vctrl = S.vcc(160, 680, '3.3V');
  sw = S.sw(160, 820, { kind: 'push', rot: 90 }).at(1.0, { closed: true });
  S.label(sw, 'S1', '', { side: 'left' });

  rb = S.res(300, 920);
  S.label(rb, 'Rb', '10kΩ', { side: 'top' });

  wc1 = S.route(vcc.pins.A, rc.pins.A);
  wc2 = S.route(rc.pins.B, led.pins.A);
  wc3 = S.route(led.pins.K, q1.pins.C);
  wc4 = S.route(q1.pins.E, gnd.pins.A);

  wb1 = S.route(vctrl.pins.A, sw.pins.A);
  wb2 = S.route(sw.pins.B, rb.pins.A, { via: 'vh' });
  wb3 = S.route(rb.pins.B, q1.pins.B);
});

const BASE = [...wb1, ...sw.path, ...wb2, ...rb.path, ...wb3, ...q1.paths.BE, ...wc4];
const MAIN = [...wc1, ...rc.path, ...wc2, ...led.path, ...wc3, ...q1.paths.CE, ...wc4];
S.energize(1.1, BASE, 'rgba(240,120,40,.35)', 18);
S.stream(1.15, BASE, { n: 8, color: S.ORANGE, r: 9 });
S.energize(1.25, MAIN);
S.stream(1.3, MAIN, { n: 12 });
"""


CIRCUIT_3_RC = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '시트 3 (3/3) — RC 충·방전 (SPDT 전환)', 52, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

let bat, gnd1, sw, gnd2, r1, c1, gnd3, vm;
let w_bat_nc, w_no_g, w_com_r, w_r_c, w_c_g;
S.at(0.1, 0.4, () => {
  bat = S.battery(200, 740, { rot: 90, cells: 2 });
  S.label(bat, 'V1', '5V', { side: 'left' });
  gnd1 = S.gnd(200, 960);

  sw = S.sw(380, 560, { kind: 'spdt', flip: true }).at(1.4, { pos: 1 });
  S.label(sw, 'S1', 'SPDT', { side: 'top' });
  gnd2 = S.gnd(300, 960);

  r1 = S.res(560, 560);
  S.label(r1, 'R1', '10kΩ', { side: 'top' });

  c1 = S.ecap(700, 740, { rot: 90 });
  S.label(c1, 'C1', '100μF', { side: 'left' });
  gnd3 = S.gnd(700, 960);

  vm = S.voltmeter(840, 740, { rot: 90 });
  S.label(vm, 'Vc', '', { side: 'right' });

  S.route(bat.pins.N, gnd1.pins.A);
  w_bat_nc = S.route(bat.pins.P, sw.pins.NC, { via: 'vh' });
  w_no_g = S.route(sw.pins.NO, gnd2.pins.A, { via: 'hv' });
  w_com_r = S.route(sw.pins.COM, r1.pins.A);
  w_r_c = S.route(r1.pins.B, c1.pins.P, { via: 'hv' });
  w_c_g = S.route(c1.pins.N, gnd3.pins.A);

  S.dot(700, 560);
  S.dot(700, 880);
  S.route([700, 560], vm.pins.A);
  S.route(vm.pins.B, [700, 880], { via: 'vh' });
});

const CHARGE = [...w_bat_nc, ...sw.paths.COM_NC.slice().reverse(), ...w_com_r, ...r1.path, ...w_r_c, ...c1.path, ...w_c_g];
const DISCHARGE = [...w_r_c.slice().reverse(), ...r1.path.slice().reverse(), ...w_com_r.slice().reverse(), ...sw.paths.COM_NO, ...w_no_g];

const chgE = S.energize(0.5, CHARGE, 'rgba(212,56,44,.30)', 22);
S.out(1.4, 0.2, chgE);
S.stream(0.55, CHARGE, { n: 10, until: 1.4 });

S.energize(1.55, DISCHARGE, 'rgba(212,56,44,.30)', 22);   // the current flowing now is red (theme-sketch.md pens), discharge too
S.stream(1.6, DISCHARGE, { n: 9 });
"""


CIRCUIT_4_BREADBOARD = r"""
S.at(0, 0.3, () => {
  S.text(60, 105, '시트 3 (4/4) — 브레드보드 실물 회로 (9V · 220Ω · LED)', 46, { rot: 0 });
  S.line(60, 122, 1020, 122, { stroke: S.RED, strokeWidth: 5 });
});

let bb, bat, r1, led, wp, wn, j1, j2, j3;
S.at(0.1, 0.45, () => {
  bb = S.breadboard(260, 700, 25, 10);
  bat = S.cellReal(160, 880, { kind: '9V' });
  S.label(bat, 'V1', '9V', { side: 'bottom' });

  r1 = S.resReal(440, 820, { value: '220', tol: 'gold' });
  led = S.ledReal(620, 780, { on: false }).at(1.15, { on: true });

  wp = S.route(bat.pins.P, bb.hole(1, 'top+'), { via: 'vh', stroke: S.RED });
  wn = S.route(bb.hole(2, 'top-'), bat.pins.N, { via: 'hv', stroke: S.BLUE });
  j1 = S.route(bb.hole(4, 'top+'), bb.hole(4, 0), { stroke: S.RED });
  j2 = S.route(bb.hole(10, 4), bb.hole(15, 4), { stroke: S.INK });
  j3 = S.route(bb.hole(17, 4), bb.hole(19, 'top-'), { via: [[680, 860]], stroke: S.BLUE });
});

S.at(0.65, 0.4, () => {
  S.text(360, 550, '220Ω (빨·빨·갈·금)', 44, { font: 'k', anchor: 'middle', rot: 0 });
  S.arrow([[380, 570], [435, 795]], S.INK, 4);
  S.text(720, 620, '긴 다리(+) / 평평한 쪽(−)', 44, { font: 'k', anchor: 'middle', fill: S.RED, rot: 0 });
  S.arrow([[690, 640], [635, 725]], S.RED, 4);
  S.text(540, 1140, 'hole(c, r) 구멍 간격 20 px 격자 정렬', 44, { font: 'k', anchor: 'middle', fill: S.BLUE, rot: 0 });
});

const LOOP = [
  ...wp,
  bb.hole(4, 'top+'),
  ...j1,
  ...r1.path,
  ...j2,
  ...led.path,
  ...j3,
  bb.hole(2, 'top-'),
  ...wn,
];
S.energize(1.2, LOOP);
S.stream(1.25, LOOP, { n: 12 });
"""


PUSH15_JS = r"""
(() => {
  const w = document.getElementById('world');
  w.style.transformOrigin = '0 0';
  w.style.transform = 'translate(540px, 720px) scale(1.5) translate(-440px, -730px)';
})();
"""


IDENTITY_CHECK_JS = r"""
(() => {
  const failures = [];
  const cases = window.__ID_CASES || [];
  const svg = document.querySelector('#world svg');
  const rootCtm = svg ? svg.getScreenCTM() : null;
  const byKind = {};
  for (const c of cases) (byKind[c.kind] = byKind[c.kind] || []).push(c);
  const parseScale = (tr) => {
    const m = (tr || '').match(/scale\(([^)\s]+)(?:[,\s]+([^)\s]+))?\)/);
    return m ? Math.abs(parseFloat(m[1])) : 1;
  };
  for (const [kind, list] of Object.entries(byKind)) {
    const ref = list[0];
    const refG = ref.part._g;
    const refK = parseScale(refG.getAttribute('transform'));
    const refPaths = [...refG.querySelectorAll('path')];
    const refDs = refPaths.map((p) => p.getAttribute('d') || '');
    const refSws = refPaths.map((p) => {
      const st = p.getAttribute('stroke') || 'none';
      return st === 'none' ? 0 : parseFloat(p.getAttribute('stroke-width') || '0') * refK;
    });
    for (const c of list) {
      const g = c.part._g;
      const k = parseScale(g.getAttribute('transform'));
      const paths = [...g.querySelectorAll('path')];
      if (paths.length !== refPaths.length) {
        failures.push(`${kind}:${c.variant}: path count ${paths.length} != ${refPaths.length}`);
        continue;
      }
      paths.forEach((p, idx) => {
        const d = p.getAttribute('d') || '';
        if (d !== refDs[idx]) failures.push(`${kind}:${c.variant}: path[${idx}] d mismatch`);
        const st = p.getAttribute('stroke') || 'none';
        if (st !== 'none') {
          const sw = parseFloat(p.getAttribute('stroke-width') || '0') * k;
          if (Math.abs(sw - refSws[idx]) > 1e-3) {
            failures.push(`${kind}:${c.variant}: path[${idx}] on-screen stroke-width ${sw.toFixed(4)} != ${refSws[idx].toFixed(4)}`);
          }
        }
      });
      if (c.part._texts && c.part._texts.length) {
        if (!rootCtm) {
          failures.push(`${kind}:${c.variant}: missing svg.getScreenCTM()`);
        } else {
          for (const t of c.part._texts) {
            const m = t.getScreenCTM();
            const rel = rootCtm.inverse().multiply(m);
            if (Math.abs(rel.b) > 1e-5 || Math.abs(rel.c) > 1e-5 || rel.a <= 0 || rel.d <= 0) {
              failures.push(`${kind}:${c.variant}: text "${t.textContent}" world rotation != 0`);
            }
          }
        }
      }
    }
  }
  const out = { ok: failures.length === 0, checked: cases.length, failures };
  document.getElementById('result').textContent = JSON.stringify(out);
})();
"""


def shoot_png(chrome, html_path, png_path):
    url = 'file://' + os.path.abspath(html_path)
    subprocess.run(
        [
            chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
            '--window-size=1080,1920', '--virtual-time-budget=8000',
            f'--screenshot={os.path.abspath(png_path)}', url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def dump_result(chrome, html_path):
    url = 'file://' + os.path.abspath(html_path)
    proc = subprocess.run(
        [
            chrome, '--headless=new', '--disable-gpu',
            '--virtual-time-budget=8000', '--dump-dom', url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    m = re.search(r'<pre id="result"[^>]*>([\s\S]*?)</pre>', proc.stdout)
    if not m:
        return {'ok': False, 'failures': [f'{os.path.basename(html_path)}: missing <pre id="result">']}
    raw = html.unescape(m.group(1)).strip()
    if not raw:
        return {'ok': False, 'failures': [f'{os.path.basename(html_path)}: empty <pre id="result">']}
    return json.loads(raw)


def main():
    ap = argparse.ArgumentParser(description='Render sketch parts catalog and identity verification sheets.')
    ap.add_argument('--out', required=True, help='Output directory for HTML and PNG sheets')
    ap.add_argument('--sheet', choices=['catalog', 'identity', 'circuits', 'all'], default='all')
    args = ap.parse_args()

    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    css, sketch_css = load_sketch_css()
    copy_assets(out_dir)

    chrome = find_chrome()
    if not chrome:
        raise SystemExit('no Chrome found (needed for headless screenshot and --dump-dom)')

    if args.sheet in ('catalog', 'all'):
        pages = [
            ('catalog', CATALOG_PAGE_1),
            ('catalog_p2', CATALOG_PAGE_2),
            ('catalog_p3', CATALOG_PAGE_3),
            ('catalog_p4', CATALOG_PAGE_4),
            ('catalog_p5', CATALOG_PAGE_5),
            ('catalog_p6', CATALOG_PAGE_6),
            ('catalog_p7', CATALOG_PAGE_7),
            ('real_vs_symbol', CATALOG_REAL_SYMBOL),
        ]
        for stem, body in pages:
            html_path = os.path.join(out_dir, f'{stem}.html')
            png_path = os.path.join(out_dir, f'{stem}.png')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(make_html(stem, css, sketch_css, body, 2.0))
            shoot_png(chrome, html_path, png_path)
            print(os.path.abspath(png_path))

    if args.sheet in ('circuits', 'all'):
        circuit_shots = [
            ('circuit_1_led_before', CIRCUIT_1_LED, 0.8, ''),
            ('circuit_1_led_after', CIRCUIT_1_LED, 2.0, ''),
            ('circuit_1_led_push15', CIRCUIT_1_LED, 2.0, PUSH15_JS),
            ('circuit_2_npn_before', CIRCUIT_2_NPN, 0.8, ''),
            ('circuit_2_npn_after', CIRCUIT_2_NPN, 2.0, ''),
            ('circuit_3_rc_charge', CIRCUIT_3_RC, 1.0, ''),
            ('circuit_3_rc_discharge', CIRCUIT_3_RC, 2.2, ''),
            ('circuit_4_breadboard', CIRCUIT_4_BREADBOARD, 2.0, ''),
        ]
        for stem, body, t_snap, after_js in circuit_shots:
            html_path = os.path.join(out_dir, f'{stem}.html')
            png_path = os.path.join(out_dir, f'{stem}.png')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(make_html(stem, css, sketch_css, body, t_snap, after_js))
            shoot_png(chrome, html_path, png_path)
            print(os.path.abspath(png_path))

    if args.sheet in ('identity', 'all'):
        total_id = 26
        pages = [
            ('identity', make_identity_compact_sketch(0, total_id, ['res', 'cap', 'diode', 'zener', 'photo', 'led'])),
            ('identity_p2', make_identity_compact_sketch(1, total_id, ['battery', 'gnd', 'vcc', 'port', 'atom', 'electron', 'hole', 'ion'])),
            ('identity_p3', make_identity_large_sketch(2, total_id, ['npn', 'pnp', 'chip'])),
            ('identity_p4', make_identity_compact_sketch(3, total_id, ['pot', 'ldr', 'thermistor', 'ecap', 'ind', 'ind_core'])),
            ('identity_p5', make_identity_compact_sketch(4, total_id, ['fuse', 'xtal', 'vdc', 'vac', 'isrc'])),
            ('identity_p6', make_identity_large_sketch(5, total_id, ['xfmr'])),
            ('identity_p7', make_identity_flip_sketch(6, total_id, ['pot', 'ldr', 'thermistor', 'ecap', 'ind', 'ind_core'])),
            ('identity_p8', make_identity_flip_sketch(7, total_id, ['xfmr', 'fuse', 'xtal', 'vdc', 'vac', 'isrc'])),
            ('identity_p9', make_identity_compact_sketch(8, total_id, ['opamp', 'opamp_p', 'not', 'and', 'or'])),
            ('identity_p10', make_identity_compact_sketch(9, total_id, ['nand', 'nor', 'xor'])),
            ('identity_p11', make_identity_large_sketch(10, total_id, ['nmos', 'pmos'])),
            ('identity_p12', make_identity_flip_sketch(11, total_id, ['opamp', 'opamp_p', 'not', 'and', 'or'])),
            ('identity_p13', make_identity_flip_sketch(12, total_id, ['nand', 'nor', 'xor'])),
            ('identity_p14', make_identity_large_flip_sketch(13, total_id, ['nmos', 'pmos'])),
            ('identity_p15', make_identity_compact_sketch(14, total_id, ['sw', 'sw_push', 'sw_spdt', 'relay', 'lamp', 'motor'])),
            ('identity_p16', make_identity_compact_sketch(15, total_id, ['speaker', 'ammeter', 'voltmeter', 'ohmmeter', 'hop', 'term'])),
            ('identity_p17', make_identity_large_sketch(16, total_id, ['dial', 'scope'])),
            ('identity_p18', make_identity_flip_sketch(17, total_id, ['sw', 'sw_push', 'sw_spdt', 'relay', 'lamp', 'motor'])),
            ('identity_p19', make_identity_flip_sketch(18, total_id, ['speaker', 'ammeter', 'voltmeter', 'ohmmeter', 'hop', 'term'])),
            ('identity_p20', make_identity_large_flip_sketch(19, total_id, ['dial', 'scope'])),
            ('identity_p21', make_identity_compact_sketch(20, total_id, ['vcap', 'schottky', 'buzzer', 'cell_aa', 'cell_9v'])),
            ('identity_p22', make_identity_compact_sketch(21, total_id, ['res_real', 'led_real', 'ecap_real', 'to92'])),
            ('identity_p23', make_identity_flip_sketch(22, total_id, ['vcap', 'schottky', 'buzzer', 'cell_aa', 'cell_9v'])),
            ('identity_p24', make_identity_flip_sketch(23, total_id, ['res_real', 'led_real', 'ecap_real', 'to92'])),
            ('identity_p25', make_identity_large_sketch(24, total_id, ['breadboard'])),
            ('identity_p26', make_identity_large_flip_sketch(25, total_id, ['breadboard'])),
        ]
        all_ok = True
        merged = {'ok': True, 'pages': []}
        for stem, body in pages:
            html_path = os.path.join(out_dir, f'{stem}.html')
            png_path = os.path.join(out_dir, f'{stem}.png')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(make_html(stem, css, sketch_css, body, 1.0, IDENTITY_CHECK_JS))
            shoot_png(chrome, html_path, png_path)
            res = dump_result(chrome, html_path)
            res['page'] = stem
            merged['pages'].append(res)
            if not res.get('ok'):
                all_ok = False
        merged['ok'] = all_ok
        print(json.dumps(merged, ensure_ascii=False))
        if not all_ok:
            sys.exit(1)


if __name__ == '__main__':
    main()
