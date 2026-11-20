/* The sketch theme's drawing kit (references/theme-sketch.md): hand-drawn schematics on paper, drawn on by time.
   Loaded by a run page whose theme is 'sketch' (build_gfx_common.page), after rough.js and before engine.js.
   The run's drawing lives in one SVG inside #world (world coordinates = frame pixels at the rest camera, 1080x1920), so
   the engine's camera (cfg.moves) pushes and pulls it like any card. Everything is a pure function of t (seek-safe).

   A run supplies cfg.sketch, the body of function (S) { ... } that builds the scene with the helpers below:
     S.at(t0, d, () => { ...draw... }, kind)   pieces drawn inside appear over [t0, t0+d]:
         'draw' (default) strokes are drawn on like a pen, text is written left to right; 'fade'; 'pop' (appears at t0)
     S.out(t, d, items)                        hide what an at() returned from t on (fade over d)
     S.energize(t0, pts, color)                a translucent thick band drawn along a wire (the current's path)
     S.stream(t0, pts, {n, color, r, speed})   charges flowing along a wire, glowing, forever from t0
   Drawing (world px; every piece hand-drawn by rough.js with a fixed seed, so frames never shimmer):
     S.line(x1,y1,x2,y2,o) S.path([[x,y],..],o) S.dot(x,y,r,col) S.circle(cx,cy,d,o) S.ellipse(cx,cy,w,h,o) S.rect(x,y,w,h,o)
     S.text(x,y,str,size,{font:'k'|'l', fill, anchor, rot})   k = Gaegu (Korean + words), l = Architects Daughter (labels)
     S.res(x1,y1,x2,y2,{s})  S.cap(x1,y1,x2,y2)  S.gnd(x,y,s)  S.vcc(x,y,label)  S.port(x,y,dir,fill)  S.diode(x1,y1,x2,y2)
     S.npn(cx,cy,s,{emit}) -> {B,C,E,bar}   S.pnp(cx,cy,s) -> {B,C,E}   S.chip(x,y,w,h,{name,left:[...],right:[...]}) -> pins
     S.arrow(pts,col,w)  S.strike(x,y,w,h)  S.marker(x,y,str,size,maxW)  S.note(x,y,w,h,lines)
   Colours: S.INK S.RED S.BLUE S.ORANGE S.GRAY S.HL; S.o({...}) gives rough options with the theme's defaults. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const INK = '#22201c', RED = '#d4382c', BLUE = '#2a5db0', ORANGE = '#f08a2c', GRAY = '#8a857b', HL = 'rgba(255,208,0,.55)';
  const S = { INK, RED, BLUE, ORANGE, GRAY, HL };
  let svg, g, rc, seed, ITEMS, CUR, built = false;

  function reset() {
    const world = document.getElementById('world');
    if (svg) svg.remove();
    svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', 1080); svg.setAttribute('height', 1920); svg.setAttribute('viewBox', '0 0 1080 1920');
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    svg.innerHTML = '<defs></defs><g></g>';
    world.appendChild(svg);
    g = svg.lastChild; rc = rough.svg(svg); seed = 11; ITEMS = []; CUR = { t0: 0, d: 0.5, kind: 'draw' };
  }
  const o = S.o = (x = {}) => ({ roughness: 1.1, bowing: 1.2, strokeWidth: 5, stroke: INK, seed: seed++, ...x });
  const add = S.add = (n) => { g.appendChild(n); ITEMS.push({ n, ...CUR }); return n; };

  /* ---- timing ---- */
  S.at = (t0, d, fn, kind = 'draw') => { const prev = CUR, k = ITEMS.length; CUR = { t0, d: Math.max(d, 1e-3), kind }; fn(); CUR = prev; return ITEMS.slice(k); };
  S.out = (t, d, items) => { for (const it of items) { it.outT = t; it.outD = Math.max(d || 0.3, 1e-3); } return items; };
  S.energize = (t0, pts, color = 'rgba(212,56,44,.30)', w = 24, d = 0.5) => S.at(t0, d, () => S.path(pts, { stroke: color, strokeWidth: w, roughness: 0.6 }));
  S.stream = (t0, pts, { n = 10, color = '#ff3b22', r = 12, speed = 300, until } = {}) => {
    const segs = []; let L = 0;
    for (let i = 0; i < pts.length - 1; i++) { const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); segs.push([pts[i], pts[i + 1], L, l]); L += l; }
    const out = [];
    for (let k = 0; k < n; k++) {
      const q = document.createElementNS(NS, 'g'), h = document.createElementNS(NS, 'circle'), c = document.createElementNS(NS, 'circle');
      h.setAttribute('r', r * 2.4); h.setAttribute('fill', color); h.setAttribute('opacity', 0.22);
      c.setAttribute('r', r); c.setAttribute('fill', color); c.setAttribute('stroke', '#7a1a10'); c.setAttribute('stroke-width', 2.5);
      q.append(h, c); g.appendChild(q);
      const it = { n: q, kind: 'stream', t0, d: 0.3, segs, L, off: k / n, speed, outT: until, outD: 0.3 }; ITEMS.push(it); out.push(it);
    }
    return out;
  };

  /* ---- drawing ---- */
  S.line = (a, b, c, d, x) => add(rc.line(a, b, c, d, o(x)));
  S.path = (pts, x) => add(rc.linearPath(pts, o(x)));
  S.circle = (cx, cy, d, x) => add(rc.circle(cx, cy, d, o(x)));
  S.ellipse = (cx, cy, w, h, x) => add(rc.ellipse(cx, cy, w, h, o({ stroke: RED, strokeWidth: 6, roughness: 2, ...x })));
  S.rect = (x0, y0, w, h, x) => add(rc.rectangle(x0, y0, w, h, o(x)));
  S.dot = (x, y, r = 12, c = INK) => add(rc.circle(x, y, r * 2, o({ fill: c, fillStyle: 'solid', stroke: c, strokeWidth: 2 })));
  S.text = (x, y, s, size, { font = 'k', fill = INK, anchor = 'start', rot = -1.2 } = {}) => {
    const t = document.createElementNS(NS, 'text');
    t.setAttribute('x', x); t.setAttribute('y', y); t.setAttribute('font-size', size); t.setAttribute('fill', fill);
    t.setAttribute('class', font === 'l' ? 'sk-l' : 'sk-k'); t.setAttribute('text-anchor', anchor);
    t.setAttribute('transform', `rotate(${rot} ${x} ${y})`); t.textContent = s; return add(t);
  };
  S.res = (x1, y1, x2, y2, x = {}) => {     // zigzag between two points on one axis
    const v = x1 === x2, L = v ? y2 - y1 : x2 - x1, n = 6, z = L * 0.62, s0 = (L - z) / 2, amp = 26 * (x.s || 1);
    const P = (a, b) => (v ? [x1 + b, y1 + a] : [x1 + a, y1 + b]), pts = [[x1, y1], P(s0, 0)];
    for (let i = 0; i < n; i++) pts.push(P(s0 + (z * (i + 0.5)) / n, i % 2 ? -amp : amp));
    pts.push(P(s0 + z, 0), [x2, y2]); return S.path(pts, x);
  };
  S.cap = (x1, y1, x2, y2, x = {}) => {     // two plates across the middle of the segment
    const v = x1 === x2, mx = (x1 + x2) / 2, my = (y1 + y2) / 2, gap = 14 * (x.s || 1), w = 46 * (x.s || 1);
    if (v) { S.line(x1, y1, x1, my - gap); S.line(x1, my + gap, x1, y2); S.line(x1 - w, my - gap, x1 + w, my - gap, { strokeWidth: 7 }); S.line(x1 - w, my + gap, x1 + w, my + gap, { strokeWidth: 7 }); }
    else { S.line(x1, y1, mx - gap, y1); S.line(mx + gap, y1, x2, y2); S.line(mx - gap, y1 - w, mx - gap, y1 + w, { strokeWidth: 7 }); S.line(mx + gap, y1 - w, mx + gap, y1 + w, { strokeWidth: 7 }); }
  };
  S.diode = (x1, y1, x2, y2, x = {}) => {   // triangle pointing from 1 to 2, bar at 2
    const ang = Math.atan2(y2 - y1, x2 - x1), mx = (x1 + x2) / 2, my = (y1 + y2) / 2, k = 34 * (x.s || 1);
    const P = (a, b) => [mx + a * Math.cos(ang) - b * Math.sin(ang), my + a * Math.sin(ang) + b * Math.cos(ang)];
    S.line(x1, y1, ...P(-k, 0)); S.line(...P(k, 0), x2, y2);
    add(rc.polygon([P(-k, -k), P(-k, k), P(k, 0)], o({ fill: x.fill || 'none', fillStyle: 'solid' }))); S.line(...P(k, -k), ...P(k, k), { strokeWidth: 7 });
  };
  S.gnd = (x, y, s = 1, c = INK) => { S.line(x, y - 40 * s, x, y, { stroke: c }); [56, 36, 16].forEach((w, i) => S.line(x - w * s, y + i * 15 * s, x + w * s, y + i * 15 * s, { stroke: c })); };
  S.vcc = (x, y, label = 'VCC', s = 1) => { S.line(x - 40 * s, y, x + 40 * s, y, { strokeWidth: 7 }); S.line(x, y, x, y + 40 * s); S.text(x, y - 22 * s, label, 56 * s, { font: 'l', anchor: 'middle' }); };
  S.port = (x, y, dir = 1, fill = GRAY) => {   // the schematic's pentagon flag, hachure-filled
    const w = 74, h = 40, p = dir > 0 ? [[x, y - h / 2], [x + w - 22, y - h / 2], [x + w, y], [x + w - 22, y + h / 2], [x, y + h / 2]]
      : [[x, y - h / 2], [x - w + 22, y - h / 2], [x - w, y], [x - w + 22, y + h / 2], [x, y + h / 2]];
    return add(rc.polygon(p, o({ fill, fillStyle: 'hachure', hachureGap: 6, fillWeight: 3, strokeWidth: 4 })));
  };
  function bjt(cx, cy, s, x, pnp) {
    const r = 78 * s, bx = cx - 22 * s, c = x.stroke || INK, e = x.emit || c;
    S.circle(cx, cy, r * 2, { strokeWidth: 4.5, stroke: c });
    S.line(bx, cy - 42 * s, bx, cy + 42 * s, { strokeWidth: 8, stroke: c });
    S.line(cx - r - 40 * s, cy, bx, cy, { stroke: c });
    S.path([[bx, cy - 20 * s], [cx + 28 * s, cy - 56 * s], [cx + 28 * s, cy - r - 30 * s]], { stroke: c });
    S.path([[bx, cy + 20 * s], [cx + 28 * s, cy + 56 * s], [cx + 28 * s, cy + r + 30 * s]], { stroke: e });
    const [x0, y0, x1, y1] = pnp ? [cx + 28 * s, cy + 56 * s, bx, cy + 20 * s] : [bx, cy + 20 * s, cx + 28 * s, cy + 56 * s];
    const an = Math.atan2(y1 - y0, x1 - x0), f = pnp ? 0.4 : 0.85, tx = x0 + (x1 - x0) * f, ty = y0 + (y1 - y0) * f, k = 26 * s;
    add(rc.polygon([[tx, ty], [tx - k * Math.cos(an - 0.45), ty - k * Math.sin(an - 0.45)], [tx - k * Math.cos(an + 0.45), ty - k * Math.sin(an + 0.45)]],
      o({ fill: e, fillStyle: 'solid', stroke: e, strokeWidth: 2, roughness: 0.4 })));
    return { B: [cx - r - 40 * s, cy], C: [cx + 28 * s, cy - r - 30 * s], E: [cx + 28 * s, cy + r + 30 * s], bar: bx, r,
      inside: [[cx + 28 * s, cy - r - 30 * s], [cx + 28 * s, cy - 56 * s], [bx, cy - 20 * s], [bx, cy + 20 * s], [cx + 28 * s, cy + 56 * s], [cx + 28 * s, cy + r + 30 * s]] };
  }
  S.npn = (cx, cy, s = 1, x = {}) => bjt(cx, cy, s, x, false);
  S.pnp = (cx, cy, s = 1, x = {}) => bjt(cx, cy, s, x, true);
  S.chip = (x0, y0, w, h, { name = '', left = [], right = [], pitch = 74 } = {}) => {   // IC box; pins listed top-down as numbers or labels
    S.rect(x0, y0, w, h, { strokeWidth: 5 });
    if (name) S.text(x0 + w / 2, y0 + h / 2 + 22, name, 64, { font: 'l', anchor: 'middle' });
    const pins = {}, y1 = y0 + (h - pitch * (Math.max(left.length, right.length) - 1)) / 2;
    left.forEach((p, i) => { const y = y1 + i * pitch; S.line(x0 - 70, y, x0, y); S.text(x0 - 30, y - 12, String(p), 40, { font: 'l', anchor: 'middle' }); pins[p] = [x0 - 70, y]; });
    right.forEach((p, i) => { const y = y1 + i * pitch; S.line(x0 + w, y, x0 + w + 70, y); S.text(x0 + w + 30, y - 12, String(p), 40, { font: 'l', anchor: 'middle' }); pins[p] = [x0 + w + 70, y]; });
    return pins;
  };
  S.arrow = (pts, c = RED, w = 5) => {
    S.path(pts, { stroke: c, strokeWidth: w, roughness: 1.4 });
    const [a, b] = [pts[pts.length - 2], pts[pts.length - 1]], ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    [0.5, -0.5].forEach((d) => S.line(b[0], b[1], b[0] - 30 * Math.cos(ang + d), b[1] - 30 * Math.sin(ang + d), { stroke: c, strokeWidth: w }));
  };
  S.strike = (x, y, w, h, c = RED) => { S.line(x, y + h, x + w, y, { stroke: c, strokeWidth: 8 }); S.line(x + 2, y, x + w - 2, y + h, { stroke: c, strokeWidth: 8 }); };
  S.hl = (x, y, w, h) => add(rc.rectangle(x, y, w, h, o({ stroke: 'none', fill: HL, fillStyle: 'hachure', hachureGap: 7, fillWeight: 16, hachureAngle: -12, roughness: 2.2 })));
  S.marker = (x, y, s, size = 64, maxW = 820) => {   // a key line on a highlighter stroke (keep x + width < 940: the button column)
    const t = S.text(x + 20, y, s, size); let w = t.getComputedTextLength();
    if (w > maxW) { t.setAttribute('font-size', Math.floor((size * maxW) / w)); w = maxW; }
    const it = ITEMS.pop(); g.removeChild(t); S.hl(x, y - size * 0.95, w + 40, size * 1.3); g.appendChild(t); ITEMS.push(it);
  };
  S.note = (x, y, w, h, lines) => {   // a sticky note; lines: [[text, size, fill]]
    S.rect(x, y, w, h, { stroke: '#c9a227', fill: 'rgba(255,226,120,.8)', fillStyle: 'solid', strokeWidth: 3, roughness: 1.6 });
    lines.forEach(([s, size = 54, fill = INK], i) => S.text(x + 30, y + 70 + i * (size + 16), s, size, { fill, rot: -2 }));
  };

  /* ---- build and draw ---- */
  function prep() {
    const defs = svg.firstChild;
    ITEMS.forEach((it, k) => {
      if (it.kind === 'stream') return;
      if (it.n.tagName === 'text') {
        const b = it.n.getBBox(), cp = document.createElementNS(NS, 'clipPath'), r = document.createElementNS(NS, 'rect');
        cp.id = 'skc' + k; r.setAttribute('x', b.x - 10); r.setAttribute('y', b.y - 20); r.setAttribute('height', b.height + 40);
        cp.appendChild(r); defs.appendChild(cp); it.n.setAttribute('clip-path', `url(#skc${k})`); it.clip = r; it.w = b.width + 20;
      } else {
        it.paths = [...it.n.querySelectorAll('path')].map((e) => {
          const solid = (e.getAttribute('fill') || 'none') !== 'none', L = solid ? 0 : e.getTotalLength();
          if (!solid) e.style.strokeDasharray = `${L} ${L}`; return { e, L, solid };
        });
      }
    });
  }
  function build() {
    reset();
    try { (new Function('S', window.CFG.sketch || ''))(S); } catch (e) { console.error('sketch:', e); }
    prep(); built = true;
  }
  const ease = (p) => 1 - Math.pow(1 - p, 3);
  function draw(t) {
    if (!built) build();
    for (const it of ITEMS) {
      const p = Math.min(1, Math.max(0, (t - it.t0) / it.d)), e = ease(p);
      const gone = it.outT != null ? Math.min(1, Math.max(0, (t - it.outT) / it.outD)) : 0, vis = 1 - gone;
      if (it.kind === 'stream') {
        const v = ((((t - it.t0) * it.speed) / it.L + it.off) % 1 + 1) % 1, D = v * it.L;
        const sg = it.segs.find((q) => D >= q[2] && D <= q[2] + q[3]) || it.segs[it.segs.length - 1], f = (D - sg[2]) / sg[3];
        it.n.setAttribute('transform', `translate(${sg[0][0] + (sg[1][0] - sg[0][0]) * f} ${sg[0][1] + (sg[1][1] - sg[0][1]) * f})`);
        it.n.style.opacity = t < it.t0 ? 0 : vis * Math.min(1, p * 3) * Math.min(1, v * 12, (1 - v) * 12); continue;
      }
      if (it.clip) { it.clip.setAttribute('width', it.w * e); it.n.style.opacity = p > 0 ? vis : 0; continue; }
      if (it.kind === 'fade') { it.n.style.opacity = e * vis; continue; }
      it.n.style.opacity = p > 0 ? vis : 0;
      if (it.kind === 'pop') continue;
      for (const q of it.paths) q.solid ? (q.e.style.opacity = e) : (q.e.style.strokeDashoffset = q.L * (1 - e));
    }
  }
  let lastT = 0;
  const prevRender = window.CFG_RENDER;
  window.CFG_RENDER = function (t, cam) { lastT = t; draw(t); if (prevRender) prevRender(t, cam); };
  // text is measured (clips, markers): build again once the handwriting fonts are in, and redraw the current frame
  Promise.all(['700 40px Gaegu', '40px "Architects Daughter"'].map((f) => document.fonts.load(f, '가A'))).then(() => {
    built = false; if (document.getElementById('world')) draw(lastT);
  });
  window.SK = S;
})();
