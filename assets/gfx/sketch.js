/* The sketch theme's drawing kit (references/theme-sketch.md): hand-drawn schematics on paper, drawn on by time.
   Loaded by a run page whose theme is 'sketch' (build_gfx_common.page), after rough.js and before engine.js.
   The run's drawing lives in one SVG inside #world (world coordinates = frame pixels at the rest camera, 1080x1920), so
   the engine's camera (cfg.moves) pushes and pulls it like any card. Everything is a pure function of t (seek-safe).

   A run supplies cfg.sketch, the body of function (S) { ... } that builds the scene with the helpers below:
     Timing & current:
       S.at(t0, d, fn, kind)                     pieces drawn inside appear over [t0, t0+d]; kind: 'draw' (default) | 'fade' | 'pop'
       S.out(t, d, items)                        hide what an at() returned from t on (fade over d)
       S.energize(t0, pts, color, w, d)          a translucent thick band drawn along a wire (the current's path)
       S.stream(t0, pts, {n, color, r, speed, until})  charges flowing along a wire, glowing, from t0
       S.curArrow(pts, opts)                     circuit current arrow (filled arrowhead; opts: {color, strokeWidth, head, at, label})
     Primitives (world px; fixed seed via S.o):
       S.line(x1,y1,x2,y2,o)  S.path([[x,y],..],o)  S.dot(x,y,r,col)  S.circle(cx,cy,d,o)  S.ellipse(cx,cy,w,h,o)  S.rect(x,y,w,h,o)
       S.text(x,y,str,size,{font:'k'|'l', fill, anchor, rot})   k = Gaegu (Korean + words), l = Architects Daughter (labels)
     Parts (canonical 120 px unit, 20 px grid, fixed per-part seed, world return {pins, path, paths, box, at(t,state)}):
       S.defPart(name, spec)                     define a canonical part; size 'S'(2/3)|'M'(1)|'L'(4/3)|'XL'(2)|'XXL'(3), rot, flip
       S.res(cx, cy, {rot, size, flip})          pins {A, B}   (legacy 2-pt S.res(x1,y1,x2,y2,{s}) supported)
       S.pot(cx, cy, {rot, size, flip})          pins {A, B, W}
       S.ldr(cx, cy, {rot, size, flip})          pins {A, B}
       S.thermistor(cx, cy, {rot, size, flip})   pins {A, B}
       S.cap(cx, cy, {rot, size, flip, polar})   pins {A, B} or {P, N}   (legacy 2-pt S.cap(x1,y1,x2,y2,{s}) supported)
       S.vcap(cx, cy, {rot, size, flip})         pins {A, B}   (variable capacitor)
       S.ecap(cx, cy, {rot, size, flip})         pins {P, N}   (electrolytic; curved N plate, + red / - blue)
       S.ind(cx, cy, {core, rot, size, flip})    pins {A, B}   (4 humps; core:true adds 2 core lines)
       S.xfmr(cx, cy, {rot, size, flip})         pins {P1, P2, S1, S2}; paths {primary, secondary}
       S.fuse(cx, cy, {rot, size, flip})         pins {A, B}
       S.xtal(cx, cy, {rot, size, flip})         pins {A, B}
       S.diode(cx, cy, {kind, rot, size, flip, on})  kind: 'std'|'led'|'zener'|'photo'|'schottky', pins {A, K}; S.led alias with {on} state
       S.battery(cx, cy, {cells, rot, size, flip})   pins {P, N}   (legacy S.battery(x,y,dir,s) -> {..., L, R} supported)
       S.vdc(cx, cy, {rot, size, flip})          pins {P, N}   (circle with upright + red / - blue)
       S.vac(cx, cy, {rot, size, flip})          pins {A, B}   (circle with sine wave)
       S.isrc(cx, cy, {rot, size, flip})         pins {A, B}   (circle with arrow A->B)
       S.npn(cx, cy, {rot, size, flip, emit})    pins {B, C, E} + top-level B,C,E,bar,r,inside; S.pnp same
       S.nmos(cx, cy, {rot, size, flip})         r=60 circle, pins {G(-120,0), D(20,-120), S(20,120)}; path/paths.DS; S.pmos same
       S.opamp(cx, cy, {power, rot, size, flip}) pins {INP, INN, OUT} (+ {VP, VN} if power:true); paths {INP_OUT, INN_OUT}
       S.gate(type, cx, cy, {rot, size, flip})   type: 'and'|'or'|'not'|'nand'|'nor'|'xor'; pins {A, B, Y} (not: {A, Y})
       S.sw(cx, cy, {kind, closed, pos, rot, size, flip})  kind: 'spst'|'spdt'|'push'; pins {A,B} (spdt: {COM,NO,NC}); .at(t, state)
       S.relay(cx, cy, {closed, rot, size, flip}) pins {C1, C2, COM, NO}; .at(t, {closed})
       S.lamp(cx, cy, {on, rot, size, flip})     pins {A, B}; .at(t, {on})
       S.motor(cx, cy, {rot, size, flip})        pins {A, B}
       S.speaker(cx, cy, {rot, size, flip})      pins {A, B}
       S.buzzer(cx, cy, {rot, size, flip})       pins {A, B}
       S.meter(cx, cy, {label, rot, size, flip}) label: 'A'|'V'|'Ω', pins {A, B}; aliases S.ammeter, S.voltmeter
       S.dial(cx, cy, {value, min, max, label, rot, size, flip})  pins {P, N} (+ red / - blue); .at(t, {value})
       S.scope(cx, cy, {pts, w, h, color, rot, size, flip})       pins {IN, GND}
       S.gnd(cx, cy, {rot, size, flip})          pins {A}   (legacy S.gnd(x,y,s,c) supported)
       S.vcc(cx, cy, {label, rot, size, flip})   pins {A}   (legacy S.vcc(x,y,label,s) supported)
       S.port(cx, cy, {fill, rot, size, flip})   pins {A}   (legacy S.port(x,y,dir,fill) supported)
       S.chip(cx, cy, {w, h, name, left, right, pitch, rot, size, flip})  pitch 60, lead 60; legacy S.chip(x,y,w,h,opts) supported
       S.wire(pts, opts)                         orthogonal wire through pts (returns cleaned pts)
       S.route(pinA, pinB, {via, dir, ...})      orthogonal 20 px grid auto-route (draws & returns pts without duplicates)
       S.hop(cx, cy, {dir, r, rot, size, flip})  semicircle wire jump over unjoined crossing; pins {A, B}
       S.term(cx, cy, {fill, label, rot, size, flip})  open circle terminal; pins {A}
       S.block(x, y, w, h, title, opts)          dashed block enclosure with title; returns {box, pins}
       S.label(part, name, value, {side})        name 48 px, value 44 px; auto-flips if crossing x>960 or y<140
     Real-world parts (hand-drawn physical illustrations, 20 px grid):
       S.cellReal(cx, cy, {kind:'AA'|'9V', rot, size, flip})   pins {P, N} (+ red / - blue)
       S.resReal(cx, cy, {value:'220', tol:'gold', rot, size, flip})  pins {A, B} (4-band colour code from value)
       S.ledReal(cx, cy, {on, color, rot, size, flip})         pins {A, K} (long A, short K, flat rim K); .at(t, {on})
       S.ecapReal(cx, cy, {rot, size, flip})                   pins {P, N} (vent cross, blue - stripe, long P)
       S.to92(cx, cy, {pins:'EBC', label, rot, size, flip})    3 legs at (-20,0,+20, 60); pins in opts.pins order
       S.breadboard(x, y, cols, rows, opts)                    20 px hole grid + rails; returns .hole(c, r) (also (cx,cy,opts))
     Pen marks:
       S.arrow(pts,col,w)  S.strike(x,y,w,h,col)  S.hl(x,y,w,h)  S.marker(x,y,str,size,maxW)  S.note(x,y,w,h,lines)
     Matter:
       S.atom(cx,cy,{label,hands,color,size,rot,flip})  S.electron(cx,cy,opts)  S.hole(cx,cy,opts)  S.ion(cx,cy,{sign,size})
       S.lattice(x0,y0,cols,rows,pitch,{cell})  S.band(x,y,w,h,c)  S.hill(x0,yb,w,h,c)  S.glow(x,y,r)  S.chair(x,y,{s,empty})  S.person(x,y,s,c)
     Motion:
       S.layer(() => {...}, ox, oy) -> layer; S.move(layer, [[t, dx, dy, scale], ...])
     Colours:
       S.INK S.RED S.BLUE S.ORANGE S.GRAY S.HL; S.o({...}) gives rough options with the theme's defaults. */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const INK = '#22201c', RED = '#d4382c', BLUE = '#2a5db0', ORANGE = '#f08a2c', GRAY = '#8a857b', HL = 'rgba(255,208,0,.55)';
  const S = { INK, RED, BLUE, ORANGE, GRAY, HL };
  const SIZE_K = { S: 2 / 3, M: 1, L: 4 / 3, XL: 2, XXL: 3, s: 2 / 3, m: 1, l: 4 / 3, xl: 2, xxl: 3 };   // XL/XXL: a real object as the hero
  let svg, g, rc, seed, ITEMS, CUR, MOVES, STATES, maskSeq, partSeq, built = false;

  function reset() {
    const world = document.getElementById('world');
    if (svg) svg.remove();
    svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('width', 1080); svg.setAttribute('height', 1920); svg.setAttribute('viewBox', '0 0 1080 1920');
    svg.style.cssText = 'position:absolute;left:0;top:0;overflow:visible';
    svg.innerHTML = '<defs></defs><g></g>';
    world.appendChild(svg);
    g = svg.lastChild; rc = rough.svg(svg); seed = 11; ITEMS = []; MOVES = []; STATES = [];
    maskSeq = 0; partSeq = 0; CUR = { t0: 0, d: 0.5, kind: 'draw' };
  }
  const o = S.o = (x = {}) => ({ roughness: 1.1, bowing: 1.2, strokeWidth: 5, stroke: INK, seed: seed++, ...x });
  const add = S.add = (n) => { g.appendChild(n); ITEMS.push({ n, ...CUR }); return n; };

  /* ---- math & seed helpers ---- */
  function hashName(name) {
    let h = 2166136261;
    for (let i = 0; i < name.length; i++) {
      h ^= name.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }
  const partSeedBase = (name) => (hashName(name) >>> 0) % 2147483000 + 1;
  const sizeScale = (sz) => (sz == null ? 1 : typeof sz === 'number' ? (sz > 0 ? sz : 1) : (SIZE_K[sz] || 1));
  const cleanNum = (v) => { const r = Math.round(v * 1e6) / 1e6; return Object.is(r, -0) ? 0 : r; };
  function rotTrig(deg) {
    const d = ((deg % 360) + 360) % 360;
    if (d === 0) return [1, 0];
    if (d === 90) return [0, 1];
    if (d === 180) return [-1, 0];
    if (d === 270) return [0, -1];
    const rad = (deg * Math.PI) / 180;
    return [Math.cos(rad), Math.sin(rad)];
  }
  function makeXform(cx, cy, opts = {}) {
    const k = sizeScale(opts.size);
    const rot = opts.rot || 0;
    const flip = opts.flip;
    const sx = (flip === true || flip === 'x') ? -k : k;
    const sy = flip === 'y' ? -k : k;
    const [c, s] = rotTrig(rot);
    const toWorld = (lx, ly) => {
      const x1 = lx * sx, y1 = ly * sy;
      return [cleanNum(cx + x1 * c - y1 * s), cleanNum(cy + x1 * s + y1 * c)];
    };
    const boxWorld = (x0, y0, x1, y1) => {
      const pts = [toWorld(x0, y0), toWorld(x1, y0), toWorld(x1, y1), toWorld(x0, y1)];
      const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
      const minX = Math.min(...xs), minY = Math.min(...ys), maxX = Math.max(...xs), maxY = Math.max(...ys);
      return { x: cleanNum(minX), y: cleanNum(minY), w: cleanNum(maxX - minX), h: cleanNum(maxY - minY) };
    };
    const attr = sx === sy
      ? `translate(${cx} ${cy}) rotate(${rot}) scale(${k})`
      : `translate(${cx} ${cy}) rotate(${rot}) scale(${sx} ${sy})`;
    return { k, rot, sx, sy, toWorld, boxWorld, attr };
  }
  function dedupPts(pts) {
    const out = [];
    for (const p of pts) {
      if (!p) continue;
      const prev = out[out.length - 1];
      if (!prev || Math.hypot(p[0] - prev[0], p[1] - prev[1]) > 1e-6) out.push([p[0], p[1]]);
    }
    return out;
  }

  /* ---- timing & current ---- */
  S.at = (t0, d, fn, kind = 'draw') => { const prev = CUR, k = ITEMS.length; CUR = { t0, d: Math.max(d, 1e-3), kind }; fn(); CUR = prev; return ITEMS.slice(k); };
  S.out = (t, d, items) => { for (const it of items) { it.outT = t; it.outD = Math.max(d || 0.3, 1e-3); } return items; };
  S.energize = (t0, pts, color = 'rgba(212,56,44,.30)', w = 24, d = 0.5) => S.at(t0, d, () => S.path(pts, { stroke: color, strokeWidth: w, roughness: 0.6 }));
  S.stream = (t0, pts, { n = 10, color = '#ff3b22', r = 12, speed = 300, until } = {}) => {
    const clean = dedupPts(pts), segs = []; let L = 0;
    for (let i = 0; i < clean.length - 1; i++) {
      const l = Math.hypot(clean[i + 1][0] - clean[i][0], clean[i + 1][1] - clean[i][1]);
      if (l > 1e-6) { segs.push([clean[i], clean[i + 1], L, l]); L += l; }
    }
    if (!segs.length || L <= 1e-6) return [];
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
  S.curArrow = (ptsOrX, optsOrY = {}, dirArg, extraOpts) => {
    let pts, opts;
    if (typeof ptsOrX === 'number') {
      const x = ptsOrX, y = optsOrY, len = 30;
      const ang = typeof dirArg === 'number' ? dirArg : ({ r: 0, l: Math.PI, u: -Math.PI / 2, d: Math.PI / 2 }[dirArg] || 0);
      pts = [[x - len * Math.cos(ang), y - len * Math.sin(ang)], [x + len * Math.cos(ang), y + len * Math.sin(ang)]];
      opts = extraOpts || {};
    } else {
      pts = ptsOrX;
      opts = typeof optsOrY === 'string' ? { color: optsOrY } : (optsOrY || {});
    }
    const c = opts.color || RED, w = opts.strokeWidth || 5, head = opts.head || 22;
    S.path(pts, { stroke: c, strokeWidth: w, roughness: 1.1 });
    let a = pts[pts.length - 2], b = pts[pts.length - 1], tip = b;
    if (opts.at === 'mid' && pts.length >= 2) {
      const midIdx = Math.floor((pts.length - 1) / 2);
      a = pts[midIdx]; b = pts[midIdx + 1];
      tip = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    }
    const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
    const tri = [tip, [tip[0] - head * Math.cos(ang - 0.45), tip[1] - head * Math.sin(ang - 0.45)], [tip[0] - head * Math.cos(ang + 0.45), tip[1] - head * Math.sin(ang + 0.45)]];
    add(rc.polygon(tri, o({ fill: c, fillStyle: 'solid', stroke: c, strokeWidth: 2, roughness: 0.4 })));
    if (opts.label) {
      const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
      const font = /[\uac00-\ud7a3]/.test(opts.label) ? 'k' : 'l';
      S.text(mx, my - 20, opts.label, 44, { font, fill: c, anchor: 'middle', rot: 0 });
    }
  };

  /* ---- drawing primitives ---- */
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

  /* ---- defPart core ---- */
  const sineInOut = (p) => 0.5 * (1 - Math.cos(Math.PI * p));
  function evalPartState(st, t) {
    const keys = st.keys.slice().sort((a, b) => a.t - b.t);
    let cur = { ...st.init };
    for (const k of keys) {
      if (t <= k.t) break;
      const dur = Math.max(k.dur || 0.3, 1e-3);
      const p = Math.min(1, Math.max(0, (t - k.t) / dur));
      const e = sineInOut(p);
      if (p < 1) {
        const out = { ...cur };
        for (const key of Object.keys(out)) {
          if (typeof out[key] === 'boolean') out[key] = out[key] ? 1 : 0;
        }
        for (const key of Object.keys(k.state)) {
          const v0 = typeof cur[key] === 'boolean' ? (cur[key] ? 1 : 0) : (cur[key] ?? 0);
          const v1 = typeof k.state[key] === 'boolean' ? (k.state[key] ? 1 : 0) : (k.state[key] ?? 0);
          out[key] = v0 + (v1 - v0) * e;
        }
        return out;
      }
      cur = { ...cur, ...k.state };
    }
    const out = { ...cur };
    for (const key of Object.keys(out)) {
      if (typeof out[key] === 'boolean') out[key] = out[key] ? 1 : 0;
    }
    return out;
  }

  function defPart(name, spec) {
    const base = partSeedBase(name);
    return function partFn(cx, cy, opts = {}) {
      const parentG = g;
      const baseAt = CUR;
      const pid = partSeq++;
      const xf = makeXform(cx, cy, opts);
      const partG = document.createElementNS(NS, 'g');
      partG.setAttribute('class', 'sk-part');
      partG.setAttribute('data-part', name);
      partG.setAttribute('data-part-id', String(pid));
      partG.setAttribute('transform', xf.attr);
      parentG.appendChild(partG);

      let strokeIdx = 0;
      const partItems = [];
      const partTexts = [];
      const stateHandlers = [];
      let normalizeFn = null;
      const stateEntry = { init: { ...(opts.initState || {}) }, keys: [], apply: null };

      const partOpt = (xo = {}) => {
        if (xo.fillStyle === 'dots') throw new Error(`sketch part "${name}": fillStyle 'dots' is forbidden`);
        const merged = { roughness: 1.1, bowing: 1.2, strokeWidth: 5, stroke: INK, ...xo, seed: base + 16 * (strokeIdx++) };
        delete merged.group;
        if (merged.fill === undefined || merged.fill === null || merged.fill === '') delete merged.fill;
        return merged;
      };
      const pushNode = (node, win = [0, 1], targetG = partG) => {
        node.querySelectorAll('path').forEach((p) => {
          const sw = parseFloat(p.getAttribute('stroke-width'));
          if (sw > 0) p.setAttribute('stroke-width', sw / xf.k);
        });
        (targetG || partG).appendChild(node);
        const f0 = win[0], f1 = win[1];
        const it = { n: node, t0: baseAt.t0 + baseAt.d * f0, d: Math.max(baseAt.d * (f1 - f0), 1e-3), kind: baseAt.kind };
        ITEMS.push(it);
        partItems.push(it);
        return it;
      };
      const pushWorldNode = (node, win = [0.7, 1]) => {
        parentG.appendChild(node);
        const f0 = win[0], f1 = win[1];
        const it = { n: node, t0: baseAt.t0 + baseAt.d * f0, d: Math.max(baseAt.d * (f1 - f0), 1e-3), kind: baseAt.kind };
        ITEMS.push(it);
        partItems.push(it);
        return it;
      };
      const ctx = {
        k: xf.k,
        rot: xf.rot,
        toWorld: xf.toWorld,
        boxWorld: xf.boxWorld,
        strokeIdx: () => strokeIdx,
        setStrokeIdx: (v) => { strokeIdx = v; },
        group: (parent = partG) => { const sg = document.createElementNS(NS, 'g'); parent.appendChild(sg); return sg; },
        line: (x1, y1, x2, y2, xo, win) => pushNode(rc.line(x1, y1, x2, y2, partOpt(xo)), win, xo && xo.group),
        path: (pts, xo, win) => pushNode(rc.linearPath(pts, partOpt(xo)), win, xo && xo.group),
        polygon: (pts, xo, win) => pushNode(rc.polygon(pts, partOpt(xo)), win, xo && xo.group),
        rect: (x, y, w, h, xo, win) => pushNode(rc.rectangle(x, y, w, h, partOpt(xo)), win, xo && xo.group),
        circle: (x, y, d, xo, win) => pushNode(rc.circle(x, y, d, partOpt(xo)), win, xo && xo.group),
        ellipse: (x, y, w, h, xo, win) => pushNode(rc.ellipse(x, y, w, h, partOpt(xo)), win, xo && xo.group),
        arc: (x, y, w, h, a0, a1, cl, xo, win) => pushNode(rc.arc(x, y, w, h, a0, a1, cl, partOpt(xo)), win, xo && xo.group),
        curve: (pts, xo, win) => pushNode(rc.curve(pts, partOpt(xo)), win, xo && xo.group),
        sign: (lx, ly, sign = '+', so = {}, win = [0.7, 1]) => {
          const [wx, wy] = xf.toWorld(lx, ly);
          const r = 16 * (so.scale || 1);
          const col = so.stroke || (sign === '+' ? RED : BLUE);
          const sw = so.strokeWidth || 6;
          const rough = so.roughness != null ? so.roughness : 0.6;
          const f0 = win[0], f1 = win[1];
          if (sign === '+') {
            const mid = f0 + (f1 - f0) * 0.2;
            const end = f0 + (f1 - f0) * 0.85;
            pushWorldNode(rc.line(wx - r, wy, wx + r, wy, partOpt({ stroke: col, strokeWidth: sw, roughness: rough })), [f0, end]);
            pushWorldNode(rc.line(wx, wy - r, wx, wy + r, partOpt({ stroke: col, strokeWidth: sw, roughness: rough })), [mid, f1]);
          } else {
            pushWorldNode(rc.line(wx - r, wy, wx + r, wy, partOpt({ stroke: col, strokeWidth: sw, roughness: rough })), win);
          }
        },
        text: (lx, ly, str, fontSize, to = {}, win = [0.7, 1]) => {
          const [wx, wy] = xf.toWorld(lx, ly);
          return ctx.worldText(wx, wy + fontSize * 0.35, str, fontSize, to, win);
        },
        worldText: (wx, wy, str, fontSize, to = {}, win = [0.7, 1]) => {
          const prevCur = CUR;
          CUR = { t0: baseAt.t0 + baseAt.d * win[0], d: Math.max(baseAt.d * (win[1] - win[0]), 1e-3), kind: baseAt.kind };
          let tNode;
          try {
            tNode = S.text(wx, wy, str, fontSize, { font: 'l', anchor: 'middle', ...to, rot: 0 });
          } finally {
            CUR = prevCur;
          }
          tNode.setAttribute('data-part-text', name);
          tNode.setAttribute('data-part-id', String(pid));
          const it = ITEMS[ITEMS.length - 1];
          partItems.push(it);
          partTexts.push(tNode);
          return it;
        },
        normalizeState: (fn) => { normalizeFn = fn; },
        setInitState: (s) => { Object.assign(stateEntry.init, normalizeFn ? normalizeFn(s) : s); },
        onDraw: (fn) => { stateHandlers.push(fn); }
      };

      const res = typeof spec === 'function' ? spec(ctx, opts, { cx, cy, xf }) : spec.build(ctx, opts, { cx, cy, xf });
      const pins = res.pins || {};
      const path = dedupPts(res.path || []);
      const paths = {};
      if (res.paths) {
        for (const k of Object.keys(res.paths)) paths[k] = dedupPts(res.paths[k]);
      }
      const box = res.box || (res.localBox ? xf.boxWorld(...res.localBox) : xf.boxWorld(-60, -30, 60, 30));

      const partObj = {
        pins,
        path,
        paths,
        box,
        _items: partItems,
        _texts: partTexts,
        _g: partG,
        at(t, state, dur = 0.3) {
          let stObj = typeof state === 'string' ? { [state]: true } : (state || {});
          if (normalizeFn) stObj = normalizeFn(stObj);
          stateEntry.keys.push({ t, state: stObj, dur });
          return partObj;
        }
      };
      if (res.extra) Object.assign(partObj, res.extra);

      if (stateHandlers.length) {
        stateEntry.apply = (t, evalSt) => {
          for (const h of stateHandlers) h(t, evalSt);
        };
        STATES.push(stateEntry);
      }
      return partObj;
    };
  }
  S.defPart = defPart;

  /* ---- 2-point backward-compat wrapper ---- */
  function twoPointWrap(partFn, name, x1, y1, x2, y2, opts = {}) {
    const dx = x2 - x1, dy = y2 - y1, span = Math.hypot(dx, dy);
    const cx = (x1 + x2) / 2, cy = (y1 + y2) / 2;
    let rot = (Math.atan2(dy, dx) * 180) / Math.PI;
    for (const a of [0, 90, -90, 180, -180]) {
      if (Math.abs(rot - a) < 1e-6) { rot = a === -180 ? 180 : a; break; }
    }
    let size = opts.size != null ? opts.size : (opts.s != null ? opts.s : 'M');
    let k = sizeScale(size);
    if (span < 120 * k - 1e-4) {
      console.warn(`sketch: ${name} span (${span.toFixed(1)}) shorter than body (${(120 * k).toFixed(1)}); using size S`);
      size = 'S';
      k = 2 / 3;
    }
    const part = partFn(cx, cy, { ...opts, rot, size });
    if (span > 120 * k + 0.5) {
      const pNames = Object.keys(part.pins);
      const p1 = part.pins[pNames[0]], p2 = part.pins[pNames[1]];
      const base = partSeedBase(name);
      const baseAt = CUR;
      const leadWin = { t0: baseAt.t0, d: Math.max(baseAt.d * 0.35, 1e-3), kind: baseAt.kind };
      const addLead = (ax, ay, bx, by, idx) => {
        const node = rc.line(ax, ay, bx, by, {
          roughness: 1.1, bowing: 1.2, strokeWidth: 5, stroke: opts.stroke || INK,
          preserveVertices: true, seed: base + 16 * idx
        });
        g.appendChild(node);
        const it = { n: node, ...leadWin };
        ITEMS.push(it);
        part._items.push(it);
      };
      addLead(x1, y1, p1[0], p1[1], 14);
      addLead(p2[0], p2[1], x2, y2, 15);
      part.pins[pNames[0]] = [x1, y1];
      part.pins[pNames[1]] = [x2, y2];
      part.path = dedupPts([[x1, y1], ...part.path, [x2, y2]]);
    }
    return part;
  }

  /* ---- migrated canonical parts ---- */
  const resPart = defPart('res', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.path([[-60, 0], [-36, 0], [-30, -24], [-18, 24], [-6, -24], [6, 24], [18, -24], [30, 24], [36, 0], [60, 0]],
      { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 1]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -24, 60, 24] };
  });
  S.res = (a, b, c, d, e) => (typeof d === 'number' ? twoPointWrap(resPart, 'res', a, b, c, d, e) : resPart(a, b, c));

  const capPart = defPart('cap', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -12, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
    ctx.line(12, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
    ctx.line(-12, -38, -12, 38, { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.4, 0.9]);
    ctx.line(12, -38, 12, 38, { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.4, 0.9]);
    if (opts.polar) {
      ctx.sign(-24 - 16 / ctx.k, -28 - 24 / ctx.k, '+', { stroke: RED }, [0.7, 1]);
      ctx.sign(24 + 16 / ctx.k, -28 - 24 / ctx.k, '-', { stroke: BLUE }, [0.7, 1]);
    }
    const p1 = ctx.toWorld(-60, 0), p2 = ctx.toWorld(60, 0);
    return {
      pins: opts.polar ? { P: p1, N: p2 } : { A: p1, B: p2 },
      path: [p1, p2],
      paths: { AB: [p1, p2] },
      localBox: [-60, -38, 60, 38]
    };
  });
  S.cap = (a, b, c, d, e) => (typeof d === 'number' ? twoPointWrap(capPart, 'cap', a, b, c, d, e) : capPart(a, b, c));

  const diodePart = defPart('diode', (ctx, opts) => {
    const kind = opts.kind || 'std';
    const c = opts.stroke || INK;
    let glowItem, litTriItem, arrowsOff = [], arrowsOn = [];
    if (kind === 'led') {
      ctx.normalizeState((s) => {
        if (s.on !== undefined) return { on: s.on ? 1 : 0 };
        if (s.off !== undefined) return { on: s.off ? 0 : 1 };
        return s;
      });
      ctx.setInitState({ on: !!opts.on });
      glowItem = ctx.circle(0, 0, 150, { stroke: 'none', fill: HL, fillStyle: 'hachure', hachureGap: 8, fillWeight: 10, roughness: 2 }, [0.55, 1]);
      litTriItem = ctx.polygon([[-26, -28], [-26, 28], [26, 0]], { stroke: 'none', fill: 'rgba(255,208,0,.9)', fillStyle: 'solid' }, [0.55, 1]);
    }
    ctx.line(-60, 0, -26, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
    ctx.line(26, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
    ctx.polygon([[-26, -28], [-26, 28], [26, 0]], { stroke: c, strokeWidth: 5, fill: opts.fill, fillStyle: opts.fill ? 'solid' : undefined }, [0.1, 0.6]);
    if (kind === 'zener') {
      ctx.path([[16, -34], [26, -28], [26, 28], [36, 34]], { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.5, 0.85]);
    } else if (kind === 'schottky') {
      ctx.path([[42, -16], [42, -32], [26, -32], [26, 32], [10, 32], [10, 16]], { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.5, 0.85]);
    } else {
      ctx.line(26, -28, 26, 28, { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.5, 0.85]);
    }
    const drawMiniArrow = (x0, y0, x1, y1, col, arr) => {
      const ang = Math.atan2(y1 - y0, x1 - x0), h = 15;
      arr.push(ctx.line(x0, y0, x1, y1, { stroke: col, strokeWidth: 4 }, [0.65, 1]));
      arr.push(ctx.polygon([[x1, y1], [x1 - h * Math.cos(ang - 0.45), y1 - h * Math.sin(ang - 0.45)], [x1 - h * Math.cos(ang + 0.45), y1 - h * Math.sin(ang + 0.45)]],
        { fill: col, fillStyle: 'solid', stroke: col, strokeWidth: 2, roughness: 0.4 }, [0.7, 1]));
    };
    if (kind === 'led') {
      const savedIdx = ctx.strokeIdx();
      drawMiniArrow(6, -42, 32, -68, GRAY, arrowsOff);
      drawMiniArrow(30, -34, 56, -60, GRAY, arrowsOff);
      ctx.setStrokeIdx(savedIdx);
      drawMiniArrow(6, -42, 32, -68, RED, arrowsOn);
      drawMiniArrow(30, -34, 56, -60, RED, arrowsOn);
      ctx.onDraw((_t, st) => {
        const on = Math.min(1, Math.max(0, st.on || 0));
        const gVis = glowItem._vis != null ? glowItem._vis : 1;
        glowItem.n.style.opacity = gVis * on;
        litTriItem.n.style.opacity = (litTriItem._vis != null ? litTriItem._vis : 1) * on;
        for (const it of arrowsOff) it.n.style.opacity = (it._vis != null ? it._vis : 1) * (1 - on);
        for (const it of arrowsOn) it.n.style.opacity = (it._vis != null ? it._vis : 1) * on;
      });
    } else if (kind === 'photo') {
      const dummy = [];
      drawMiniArrow(36, -72, 10, -44, c, dummy);
      drawMiniArrow(12, -74, -14, -46, c, dummy);
    }
    const A = ctx.toWorld(-60, 0), K = ctx.toWorld(60, 0);
    const localBox = (kind === 'led' || kind === 'photo') ? [-60, -74, 60, 32]
      : kind === 'zener' ? [-60, -34, 60, 34]
      : kind === 'schottky' ? [-60, -32, 60, 32] : [-60, -28, 60, 28];
    return { pins: { A, K }, path: [A, K], paths: { AK: [A, K] }, localBox };
  });
  S.diode = (a, b, c, d, e) => (typeof d === 'number' ? twoPointWrap(diodePart, 'diode', a, b, c, d, e) : diodePart(a, b, c));
  S.led = (a, b, c, d, e) => {
    if (typeof d === 'number') return twoPointWrap(diodePart, 'diode', a, b, c, d, { ...(e || {}), kind: 'led' });
    return diodePart(a, b, { ...(c || {}), kind: 'led' });
  };

  const batteryPart = defPart('battery', (ctx, opts) => {
    const cells = Math.max(1, opts.cells || 1), c = opts.stroke || INK;
    let pairs;
    if (cells === 1) {
      pairs = [[-14, 14]];
    } else {
      const step = Math.min(36, 76 / cells), gap = Math.min(14, step * 0.42), start = -((cells - 1) * step) / 2;
      pairs = [];
      for (let i = 0; i < cells; i++) {
        const cx0 = start + i * step;
        pairs.push([cx0 - gap / 2, cx0 + gap / 2]);
      }
    }
    const firstX = pairs[0][0], lastX = pairs[pairs.length - 1][1];
    ctx.line(-60, 0, firstX, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.4]);
    ctx.line(lastX, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.4]);
    for (const [px, nx] of pairs) {
      ctx.line(px, -50, px, 50, { stroke: c, strokeWidth: 7 }, [0.3, 0.8]);
      ctx.line(nx, -28, nx, 28, { stroke: c, strokeWidth: 9 }, [0.3, 0.8]);
    }
    ctx.sign(firstX - 20 - 14 / ctx.k, -32 - 22 / ctx.k, '+', { stroke: RED }, [0.75, 1]);
    ctx.sign(lastX + 20 + 14 / ctx.k, -32 - 22 / ctx.k, '-', { stroke: BLUE }, [0.75, 1]);
    const P = ctx.toWorld(-60, 0), N = ctx.toWorld(60, 0);
    return { pins: { P, N }, path: [P, N], paths: { PN: [P, N] }, localBox: [-60, -50, 60, 50] };
  });
  S.battery = (x, y, dirOrOpts, s) => {
    if (typeof dirOrOpts === 'number') {
      const dir = dirOrOpts, part = batteryPart(x, y, { flip: dir < 0, size: s != null ? s : 1 });
      part.L = dir >= 0 ? part.pins.P : part.pins.N;
      part.R = dir >= 0 ? part.pins.N : part.pins.P;
      return part;
    }
    const opts = dirOrOpts || {}, part = batteryPart(x, y, opts);
    part.L = opts.flip ? part.pins.N : part.pins.P;
    part.R = opts.flip ? part.pins.P : part.pins.N;
    return part;
  };

  function makeBjt(name, isPnp) {
    const partFn = defPart(name, (ctx, opts) => {
      const r = 60, bx = -18, c = opts.stroke || INK, e = opts.emit || c;
      ctx.circle(0, 0, r * 2, { strokeWidth: 4.5, stroke: c }, [0, 0.35]);
      ctx.line(bx, -32, bx, 32, { strokeWidth: 8, stroke: c }, [0.25, 0.65]);
      ctx.line(-120, 0, bx, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.25, 0.65]);
      ctx.path([[bx, -14], [20, -44], [20, -120]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.3, 0.85]);
      ctx.path([[bx, 14], [20, 44], [20, 120]], { stroke: e, strokeWidth: 5, preserveVertices: true }, [0.3, 0.85]);
      const [x0, y0, x1, y1] = isPnp ? [20, 44, bx, 14] : [bx, 14, 20, 44];
      const an = Math.atan2(y1 - y0, x1 - x0), f = isPnp ? 0.4 : 0.85;
      const tx = x0 + (x1 - x0) * f, ty = y0 + (y1 - y0) * f, ak = 20;
      ctx.polygon([[tx, ty], [tx - ak * Math.cos(an - 0.45), ty - ak * Math.sin(an - 0.45)], [tx - ak * Math.cos(an + 0.45), ty - ak * Math.sin(an + 0.45)]],
        { fill: e, fillStyle: 'solid', stroke: e, strokeWidth: 2, roughness: 0.4 }, [0.75, 1]);
      const B = ctx.toWorld(-120, 0), C = ctx.toWorld(20, -120), E = ctx.toWorld(20, 120);
      const inside = dedupPts([C, ctx.toWorld(20, -44), ctx.toWorld(bx, -14), ctx.toWorld(bx, 14), ctx.toWorld(20, 44), E]);
      const bePath = dedupPts([B, ctx.toWorld(bx, 0), ctx.toWorld(bx, 14), ctx.toWorld(20, 44), E]);
      const bar = ctx.toWorld(bx, 0)[0], wr = cleanNum(r * ctx.k);
      return {
        pins: { B, C, E },
        path: inside,
        paths: { CE: inside, BE: bePath },
        localBox: [-60, -60, 60, 60],
        extra: { B, C, E, bar, r: wr, inside }
      };
    });
    return (cx, cy, sOrOpts, x) => (typeof sOrOpts === 'number'
      ? partFn(cx, cy, { ...(x || {}), size: sOrOpts })
      : partFn(cx, cy, sOrOpts));
  }
  S.npn = makeBjt('npn', false);
  S.pnp = makeBjt('pnp', true);

  const gndPart = defPart('gnd', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(0, -40, 0, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.4]);
    [48, 30, 12].forEach((w, i) => ctx.line(-w, i * 16, w, i * 16, { stroke: c, strokeWidth: 5 }, [0.3 + i * 0.15, 0.7 + i * 0.15]));
    const A = ctx.toWorld(0, -40);
    return { pins: { A }, path: [A], paths: {}, localBox: [-48, -40, 48, 32] };
  });
  S.gnd = (x, y, sOrOpts, c) => (typeof sOrOpts === 'number'
    ? gndPart(x, y, { size: sOrOpts, stroke: c || INK })
    : gndPart(x, y, sOrOpts));

  const vccPart = defPart('vcc', (ctx, opts) => {
    const c = opts.stroke || INK, label = opts.label != null ? opts.label : 'VCC';
    ctx.line(0, 40, 0, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.4]);
    ctx.line(-40, 0, 40, 0, { stroke: c, strokeWidth: 8 }, [0.3, 0.7]);
    const o0 = ctx.toWorld(0, 0), o1 = ctx.toWorld(0, -1);
    const dx = o1[0] - o0[0], dy = o1[1] - o0[1], len = Math.hypot(dx, dy) || 1;
    const ux = dx / len, uy = dy / len;
    if (Math.abs(ux) > Math.abs(uy)) {
      ctx.worldText(o0[0] + ux * 18, o0[1] + 56 * 0.35, label, 56, { font: 'l', anchor: ux > 0 ? 'start' : 'end', fill: c }, [0.65, 1]);
    } else {
      ctx.worldText(o0[0], o0[1] + uy * 36 + 56 * 0.35, label, 56, { font: 'l', anchor: 'middle', fill: c }, [0.65, 1]);
    }
    const A = ctx.toWorld(0, 40);
    return { pins: { A }, path: [A], paths: {}, localBox: [-40, -40, 40, 40] };
  });
  S.vcc = (x, y, lblOrOpts, s) => ((typeof lblOrOpts === 'string' || typeof s === 'number')
    ? vccPart(x, y, { label: lblOrOpts, size: s != null ? s : 1 })
    : vccPart(x, y, lblOrOpts));

  const portPart = defPart('port', (ctx, opts) => {
    const fill = opts.fill !== undefined ? opts.fill : GRAY;
    ctx.polygon([[-40, -20], [18, -20], [40, 0], [18, 20], [-40, 20]],
      { fill, fillStyle: 'hachure', hachureGap: 6, fillWeight: 3, strokeWidth: 4, preserveVertices: true }, [0, 1]);
    const A = ctx.toWorld(-40, 0), tip = ctx.toWorld(40, 0);
    return { pins: { A }, path: [A, tip], paths: {}, localBox: [-40, -20, 40, 20], extra: { tip } };
  });
  S.port = (x, y, dirOrOpts, fill) => {
    if (typeof dirOrOpts === 'number') {
      const dir = dirOrOpts;
      return portPart(x + 40 * dir, y, { flip: dir < 0, fill: fill !== undefined ? fill : GRAY });
    }
    if (typeof dirOrOpts === 'string') return portPart(x, y, { fill: dirOrOpts });
    return portPart(x, y, dirOrOpts);
  };

  const chipPart = defPart('chip', (ctx, opts) => {
    const pitch = opts.pitch || 60, lead = 60;
    const hasCustom = opts.left !== undefined || opts.right !== undefined;
    const left = opts.left !== undefined ? opts.left : (hasCustom ? [] : ['1', '2', '3']);
    const right = opts.right !== undefined ? opts.right : (hasCustom ? [] : ['6', '5', '4']);
    const nRows = Math.max(left.length, right.length, 1);
    const w = opts.w || 160;
    const h = opts.h || Math.max(120, Math.ceil((nRows * pitch + 20) / 20) * 20);
    ctx.rect(-w / 2, -h / 2, w, h, { strokeWidth: 5 }, [0, 0.45]);
    const pins = {};
    left.forEach((p, i) => {
      const ly = (i - (left.length - 1) / 2) * pitch;
      ctx.line(-w / 2 - lead, ly, -w / 2, ly, { preserveVertices: true }, [0.35, 0.8]);
      ctx.text(-w / 2 - 28, ly - 16 - 10 / ctx.k, String(p), 44, { font: 'l', anchor: 'middle' }, [0.7, 1]);
      pins[p] = ctx.toWorld(-w / 2 - lead, ly);
    });
    right.forEach((p, i) => {
      const ly = (i - (right.length - 1) / 2) * pitch;
      ctx.line(w / 2, ly, w / 2 + lead, ly, { preserveVertices: true }, [0.35, 0.8]);
      ctx.text(w / 2 + 28, ly - 16 - 10 / ctx.k, String(p), 44, { font: 'l', anchor: 'middle' }, [0.7, 1]);
      pins[p] = ctx.toWorld(w / 2 + lead, ly);
    });
    if (opts.name) ctx.text(0, 0, opts.name, 56, { font: 'l', anchor: 'middle' }, [0.7, 1]);
    return { pins, path: [], paths: {}, localBox: [-w / 2, -h / 2, w / 2, h / 2] };
  });
  S.chip = (x0, y0, wOrOpts, h, opts) => {
    if (typeof wOrOpts === 'number') {
      const part = chipPart(x0 + wOrOpts / 2, y0 + h / 2, { w: wOrOpts, h, ...(opts || {}) });
      return Object.assign({}, part.pins, part);
    }
    return chipPart(x0, y0, wOrOpts);
  };

  /* ---- phase 1 batch 1 parts (A: passive, B: sources) ---- */
  const ZIGZAG_PTS = [[-60, 0], [-36, 0], [-30, -24], [-18, 24], [-6, -24], [6, 24], [18, -24], [30, 24], [36, 0], [60, 0]];
  function partArrow(ctx, x0, y0, x1, y1, { stroke = INK, strokeWidth = 5, head = 16, winLine = [0.6, 0.9], winHead = [0.7, 1], preserveVertices = false } = {}) {
    const ang = Math.atan2(y1 - y0, x1 - x0);
    const sx1 = x1 - head * 0.45 * Math.cos(ang), sy1 = y1 - head * 0.45 * Math.sin(ang);
    ctx.line(x0, y0, sx1, sy1, { stroke, strokeWidth, preserveVertices }, winLine);
    ctx.polygon(
      [
        [x1, y1],
        [x1 - head * Math.cos(ang - 0.45), y1 - head * Math.sin(ang - 0.45)],
        [x1 - head * Math.cos(ang + 0.45), y1 - head * Math.sin(ang + 0.45)]
      ],
      { fill: stroke, fillStyle: 'solid', stroke, strokeWidth: 2, roughness: 0.4 },
      winHead
    );
  }
  function buildCircleSource(ctx, opts, drawInside, pinNames = ['A', 'B']) {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -40, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(40, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.circle(0, 0, 80, { stroke: c, strokeWidth: 5 }, [0.2, 0.75]);
    drawInside(c);
    const p0 = ctx.toWorld(-60, 0), p1 = ctx.toWorld(60, 0);
    return {
      pins: { [pinNames[0]]: p0, [pinNames[1]]: p1 },
      path: [p0, p1],
      paths: { [pinNames.join('')]: [p0, p1] },
      localBox: [-60, -40, 60, 40]
    };
  }

  S.pot = defPart('pot', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.path(ZIGZAG_PTS, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.7]);
    partArrow(ctx, 0, -60, 0, -16, { stroke: c, strokeWidth: 5, head: 16, winLine: [0.55, 0.9], winHead: [0.7, 1], preserveVertices: true });
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0), W = ctx.toWorld(0, -60), mid = ctx.toWorld(0, 0);
    return { pins: { A, B, W }, path: [A, B], paths: { AB: [A, B], AW: [A, mid, W], WB: [W, mid, B] }, localBox: [-60, -60, 60, 24] };
  });

  S.ldr = defPart('ldr', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.path(ZIGZAG_PTS, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.7]);
    partArrow(ctx, 30, -66, 8, -36, { stroke: c, strokeWidth: 4, head: 15, winLine: [0.65, 0.95], winHead: [0.7, 1] });
    partArrow(ctx, 6, -68, -16, -38, { stroke: c, strokeWidth: 4, head: 15, winLine: [0.65, 0.95], winHead: [0.7, 1] });
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -68, 60, 24] };
  });

  S.thermistor = defPart('thermistor', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.path(ZIGZAG_PTS, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.7]);
    ctx.path([[-34, 32], [-20, 32], [26, -32]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.65, 1]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -32, 60, 32] };
  });

  S.ecap = defPart('ecap', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -12, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
    ctx.line(12, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
    ctx.line(-12, -38, -12, 38, { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.4, 0.9]);
    ctx.curve([[24, -38], [15, -19], [12, 0], [15, 19], [24, 38]], { stroke: c, strokeWidth: 8, roughness: 0.9 }, [0.4, 0.9]);
    ctx.sign(-24 - 16 / ctx.k, -28 - 24 / ctx.k, '+', { stroke: RED }, [0.7, 1]);
    ctx.sign(24 + 16 / ctx.k, -28 - 24 / ctx.k, '-', { stroke: BLUE }, [0.7, 1]);
    const P = ctx.toWorld(-60, 0), N = ctx.toWorld(60, 0);
    return { pins: { P, N }, path: [P, N], paths: { PN: [P, N] }, localBox: [-60, -38, 60, 38] };
  });

  S.ind = defPart('ind', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -40, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(40, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    for (let i = 0; i < 4; i++) {
      ctx.arc(-30 + i * 20, 0, 20, 32, Math.PI, 2 * Math.PI, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.25 + i * 0.12, 0.5 + i * 0.12]);
    }
    if (opts.core) {
      ctx.line(-40, -26, 40, -26, { stroke: c, strokeWidth: 4.5 }, [0.75, 1]);
      ctx.line(-40, -36, 40, -36, { stroke: c, strokeWidth: 4.5 }, [0.75, 1]);
    }
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: opts.core ? [-60, -36, 60, 12] : [-60, -18, 60, 12] };
  });

  S.xfmr = defPart('xfmr', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.path([[-60, -60], [-28, -60], [-28, -40]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.2]);
    ctx.path([[-28, 40], [-28, 60], [-60, 60]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.35, 0.5]);
    for (let i = 0; i < 4; i++) {
      ctx.arc(-28, -30 + i * 20, 28, 20, -Math.PI / 2, Math.PI / 2, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.15 + i * 0.07, 0.3 + i * 0.07]);
    }
    ctx.line(-4.5, -48, -4.5, 48, { stroke: c, strokeWidth: 4.5 }, [0.4, 0.65]);
    ctx.line(4.5, -48, 4.5, 48, { stroke: c, strokeWidth: 4.5 }, [0.4, 0.65]);
    ctx.path([[60, -60], [28, -60], [28, -40]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.55, 0.75]);
    ctx.path([[28, 40], [28, 60], [60, 60]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.85, 1]);
    for (let i = 0; i < 4; i++) {
      ctx.arc(28, -30 + i * 20, 28, 20, Math.PI / 2, 1.5 * Math.PI, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.65 + i * 0.07, 0.8 + i * 0.07]);
    }
    const P1 = ctx.toWorld(-60, -60), P2 = ctx.toWorld(-60, 60), S1 = ctx.toWorld(60, -60), S2 = ctx.toWorld(60, 60);
    const primary = [P1, ctx.toWorld(-28, -60), ctx.toWorld(-28, 60), P2];
    const secondary = [S1, ctx.toWorld(28, -60), ctx.toWorld(28, 60), S2];
    return { pins: { P1, P2, S1, S2 }, path: primary, paths: { primary, secondary }, localBox: [-60, -60, 60, 60] };
  });

  S.fuse = defPart('fuse', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.55]);
    ctx.rect(-32, -14, 64, 28, { stroke: c, strokeWidth: 5 }, [0.35, 1]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -16, 60, 16] };
  });

  S.xtal = defPart('xtal', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -24, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.4]);
    ctx.line(24, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.4]);
    ctx.line(-24, -26, -24, 26, { stroke: c, strokeWidth: 7, preserveVertices: true }, [0.3, 0.7]);
    ctx.line(24, -26, 24, 26, { stroke: c, strokeWidth: 7, preserveVertices: true }, [0.3, 0.7]);
    ctx.rect(-12, -36, 24, 72, { stroke: c, strokeWidth: 5 }, [0.55, 1]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -36, 60, 36] };
  });

  S.vdc = defPart('vdc', (ctx, opts) => buildCircleSource(ctx, opts, () => {
    ctx.sign(-19, 0, '+', { stroke: RED, scale: 0.68 * ctx.k, strokeWidth: 5 }, [0.65, 1]);
    ctx.sign(19, 0, '-', { stroke: BLUE, scale: 0.68 * ctx.k, strokeWidth: 5 }, [0.65, 1]);
  }, ['P', 'N']));

  S.vac = defPart('vac', (ctx, opts) => buildCircleSource(ctx, opts, (c) => {
    const pts = [];
    for (let x = -24; x <= 24; x += 6) pts.push([x, 16 * Math.sin((Math.PI * x) / 24)]);
    ctx.curve(pts, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.6, 1]);
  }));

  S.isrc = defPart('isrc', (ctx, opts) => buildCircleSource(ctx, opts, (c) => {
    partArrow(ctx, -24, 0, 24, 0, { stroke: c, strokeWidth: 5, head: 18, winLine: [0.6, 0.9], winHead: [0.7, 1] });
  }));

  /* ---- phase 2 batch 2 parts (C: semiconductors) ---- */
  function makeMosfet(name, isPmos) {
    return defPart(name, (ctx, opts) => {
      const r = 60, gx = -30, cx = -12, c = opts.stroke || INK;
      ctx.circle(0, 0, r * 2, { strokeWidth: 4.5, stroke: c }, [0, 0.35]);
      ctx.line(-120, 0, gx, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.15, 0.45]);
      ctx.line(gx, -36, gx, 36, { stroke: c, strokeWidth: 7 }, [0.25, 0.55]);
      ctx.line(cx, -44, cx, -20, { stroke: c, strokeWidth: 8 }, [0.35, 0.6]);
      ctx.line(cx, -11, cx, 11, { stroke: c, strokeWidth: 8 }, [0.4, 0.65]);
      ctx.line(cx, 20, cx, 44, { stroke: c, strokeWidth: 8 }, [0.45, 0.7]);
      ctx.path([[cx, -32], [20, -32], [20, -120]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.45, 0.85]);
      ctx.path([[cx, 32], [20, 32], [20, 120]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.45, 0.85]);
      ctx.path([[cx, 0], [20, 0], [20, 32]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.55, 0.9]);
      const tri = isPmos
        ? [[17, 0], [-4, -10], [-4, 10]]
        : [[-8, 0], [13, -10], [13, 10]];
      ctx.polygon(tri, { fill: c, fillStyle: 'solid', stroke: c, strokeWidth: 2, roughness: 0.4 }, [0.75, 1]);
      const G = ctx.toWorld(-120, 0), D = ctx.toWorld(20, -120), pinS = ctx.toWorld(20, 120);
      const ds = dedupPts([D, ctx.toWorld(20, -32), ctx.toWorld(cx, -32), ctx.toWorld(cx, 32), ctx.toWorld(20, 32), pinS]);
      return { pins: { G, D, S: pinS }, path: ds, paths: { DS: ds }, localBox: [-60, -60, 60, 60] };
    });
  }
  S.nmos = makeMosfet('nmos', false);
  S.pmos = makeMosfet('pmos', true);

  /* ---- phase 3 batch 3 parts (D: switches & outputs, E: instruments, F: wiring & layout) ---- */
  function normClosed(s) {
    if (!s) return {};
    if (s.closed !== undefined) return { closed: s.closed ? 1 : 0 };
    if (s.on !== undefined) return { closed: s.on ? 1 : 0 };
    if (s.open !== undefined) return { closed: s.open ? 0 : 1 };
    if (s.pos !== undefined) return { closed: Number(s.pos) ? 1 : 0 };
    return s;
  }
  function normSpdt(s) {
    if (!s) return {};
    if (s.pos !== undefined) return { pos: Number(s.pos) || 0 };
    if (s.to !== undefined) return { pos: String(s.to).toUpperCase() === 'NO' ? 1 : 0 };
    if (s.NO || s.no) return { pos: 1 };
    if (s.NC || s.nc) return { pos: 0 };
    if (s.closed !== undefined) return { pos: s.closed ? 1 : 0 };
    if (s.on !== undefined) return { pos: s.on ? 1 : 0 };
    return s;
  }
  const swSpstPart = defPart('sw_spst', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.normalizeState(normClosed);
    ctx.setInitState({ closed: opts.closed || opts.on ? 1 : 0 });
    const armG = ctx.group();
    ctx.line(0, 0, 48, 0, { stroke: c, strokeWidth: 6, preserveVertices: true, group: armG }, [0.4, 0.9]);
    ctx.line(-60, 0, -28, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(28, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.circle(-24, 0, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.25, 0.65]);
    ctx.circle(24, 0, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.25, 0.65]);
    ctx.onDraw((_t, st) => {
      const cl = Math.min(1, Math.max(0, st.closed || 0));
      const ang = -34 * (1 - cl);
      armG.setAttribute('transform', `translate(-24 0) rotate(${ang})`);
    });
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -34, 60, 14] };
  });
  const swPushPart = defPart('sw_push', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.normalizeState(normClosed);
    ctx.setInitState({ closed: opts.closed || opts.on ? 1 : 0 });
    ctx.line(-60, 0, -28, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(28, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.circle(-24, 0, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.2, 0.6]);
    ctx.circle(24, 0, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.2, 0.6]);
    const plungerG = ctx.group();
    ctx.line(-26, -3, 26, -3, { stroke: c, strokeWidth: 6, preserveVertices: true, group: plungerG }, [0.45, 0.85]);
    ctx.line(0, -3, 0, -26, { stroke: c, strokeWidth: 5, preserveVertices: true, group: plungerG }, [0.55, 0.9]);
    ctx.line(-14, -26, 14, -26, { stroke: c, strokeWidth: 7, group: plungerG }, [0.65, 1]);
    ctx.onDraw((_t, st) => {
      const cl = Math.min(1, Math.max(0, st.closed || 0));
      const dy = -18 * (1 - cl);
      plungerG.setAttribute('transform', `translate(0 ${dy})`);
    });
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -44, 60, 14] };
  });
  const swSpdtPart = defPart('sw_spdt', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.normalizeState(normSpdt);
    ctx.setInitState({ pos: opts.pos != null ? Number(opts.pos) : (opts.closed || opts.on ? 1 : 0) });
    const armG = ctx.group();
    ctx.line(0, 0, 52.15, 0, { stroke: c, strokeWidth: 6, preserveVertices: true, group: armG }, [0.4, 0.9]);
    ctx.line(-60, 0, -32, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.path([[16, -33], [16, -40], [60, -40]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.15, 0.55]);
    ctx.path([[16, 33], [16, 40], [60, 40]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.15, 0.55]);
    ctx.circle(-28, 0, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.25, 0.65]);
    ctx.circle(16, -28, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.25, 0.65]);
    ctx.circle(16, 28, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.25, 0.65]);
    ctx.onDraw((_t, st) => {
      const pos = Math.min(1, Math.max(0, st.pos || 0));
      const ang = -32.47 + pos * 64.94;
      armG.setAttribute('transform', `translate(-28 0) rotate(${ang})`);
    });
    const COM = ctx.toWorld(-60, 0), NC = ctx.toWorld(60, -40), NO = ctx.toWorld(60, 40);
    const piv = ctx.toWorld(-28, 0), ncC = ctx.toWorld(16, -28), noC = ctx.toWorld(16, 28);
    const comNc = dedupPts([COM, piv, ncC, ctx.toWorld(16, -40), NC]);
    const comNo = dedupPts([COM, piv, noC, ctx.toWorld(16, 40), NO]);
    return { pins: { COM, NC, NO }, path: comNc, paths: { COM_NC: comNc, COM_NO: comNo }, localBox: [-60, -46, 60, 46] };
  });
  S.sw = (cxOrKind, cyOrX, optsOrY, extra) => {
    let cx = cxOrKind, cy = cyOrX, opts = optsOrY || {};
    if (typeof cxOrKind === 'string') {
      cx = cyOrX; cy = optsOrY; opts = { ...(extra || {}), kind: cxOrKind };
    }
    const k = (opts.kind || 'spst').toLowerCase();
    if (k === 'spdt') return swSpdtPart(cx, cy, opts);
    if (k === 'push') return swPushPart(cx, cy, opts);
    if (k === 'spst') return swSpstPart(cx, cy, opts);
    throw new Error(`sketch: unknown sw kind "${opts.kind}"`);
  };

  S.relay = defPart('relay', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.normalizeState(normClosed);
    ctx.setInitState({ closed: opts.closed || opts.on ? 1 : 0 });
    ctx.rect(-42, -58, 84, 116, { stroke: GRAY, strokeWidth: 3, strokeLineDash: [8, 6] }, [0, 0.35]);
    ctx.path([[-60, -40], [-22, -40], [-22, -27]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.1, 0.45]);
    ctx.path([[-22, 27], [-22, 40], [-60, 40]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.3, 0.6]);
    for (let i = 0; i < 3; i++) {
      ctx.arc(-22, -18 + i * 18, 18, 18, -Math.PI / 2, Math.PI / 2, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.2 + i * 0.08, 0.4 + i * 0.08]);
    }
    ctx.line(-8, 0, 14, 0, { stroke: GRAY, strokeWidth: 3, strokeLineDash: [5, 4] }, [0.4, 0.7]);
    const armG = ctx.group();
    ctx.line(0, 0, 0, 44, { stroke: c, strokeWidth: 6, preserveVertices: true, group: armG }, [0.5, 0.9]);
    ctx.path([[60, -40], [22, -40], [22, -22]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.3, 0.65]);
    ctx.path([[22, 22], [22, 40], [60, 40]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.3, 0.65]);
    ctx.circle(22, -22, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.35, 0.7]);
    ctx.circle(22, 22, 10, { stroke: c, strokeWidth: 4, fill: '#f3efe6', fillStyle: 'solid' }, [0.35, 0.7]);
    ctx.onDraw((_t, st) => {
      const cl = Math.min(1, Math.max(0, st.closed || 0));
      const ang = -26 * (1 - cl);
      armG.setAttribute('transform', `translate(22 -22) rotate(${ang})`);
    });
    const C1 = ctx.toWorld(-60, -40), C2 = ctx.toWorld(-60, 40), COM = ctx.toWorld(60, -40), NO = ctx.toWorld(60, 40);
    const coil = [C1, ctx.toWorld(-22, -40), ctx.toWorld(-22, 40), C2];
    const contact = [COM, ctx.toWorld(22, -40), ctx.toWorld(22, 40), NO];
    return { pins: { C1, C2, COM, NO }, path: contact, paths: { coil, contact }, localBox: [-60, -58, 60, 58] };
  });

  S.lamp = defPart('lamp', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.normalizeState((s) => {
      if (s.on !== undefined) return { on: s.on ? 1 : 0 };
      if (s.off !== undefined) return { on: s.off ? 0 : 1 };
      return s;
    });
    ctx.setInitState({ on: !!opts.on });
    const glowItem = ctx.circle(0, 0, 150, { stroke: 'none', fill: HL, fillStyle: 'hachure', hachureGap: 8, fillWeight: 10, roughness: 2 }, [0.55, 1]);
    const litCircle = ctx.circle(0, 0, 72, { stroke: 'none', fill: 'rgba(255,208,0,.85)', fillStyle: 'solid' }, [0.55, 1]);
    ctx.line(-60, 0, -36, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(36, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.circle(0, 0, 72, { stroke: c, strokeWidth: 5 }, [0.2, 0.7]);
    ctx.line(-25, -25, 25, 25, { stroke: c, strokeWidth: 5 }, [0.55, 0.9]);
    ctx.line(-25, 25, 25, -25, { stroke: c, strokeWidth: 5 }, [0.65, 1]);
    ctx.onDraw((_t, st) => {
      const on = Math.min(1, Math.max(0, st.on || 0));
      glowItem.n.style.opacity = (glowItem._vis != null ? glowItem._vis : 1) * on;
      litCircle.n.style.opacity = (litCircle._vis != null ? litCircle._vis : 1) * on;
    });
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -36, 60, 36] };
  });

  S.motor = defPart('motor', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -40, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(40, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.circle(0, 0, 80, { stroke: c, strokeWidth: 5 }, [0.2, 0.75]);
    ctx.text(0, 0, 'M', 46, { font: 'l', anchor: 'middle', fill: c }, [0.65, 1]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -40, 60, 40] };
  });

  S.speaker = defPart('speaker', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, -20, -24, -20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(-60, 20, -24, 20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.rect(-24, -24, 24, 48, { stroke: c, strokeWidth: 5 }, [0.25, 0.65]);
    ctx.polygon([[0, -24], [36, -52], [36, 52], [0, 24]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.45, 1]);
    const A = ctx.toWorld(-60, -20), B = ctx.toWorld(-60, 20);
    const ab = dedupPts([A, ctx.toWorld(-24, -20), ctx.toWorld(-24, 20), B]);
    return { pins: { A, B }, path: ab, paths: { AB: ab }, localBox: [-60, -52, 40, 52] };
  });

  S.meter = defPart('meter', (ctx, opts) => {
    const c = opts.stroke || INK;
    const lbl = opts.label != null ? String(opts.label) : 'V';
    ctx.line(-60, 0, -40, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(40, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.circle(0, 0, 80, { stroke: c, strokeWidth: 4.5 }, [0.2, 0.75]);
    ctx.text(0, 0, lbl, 46, { font: /[\uac00-\ud7a3]/.test(lbl) ? 'k' : 'l', anchor: 'middle', fill: c }, [0.65, 1]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -40, 60, 40] };
  });
  S.ammeter = (cx, cy, opts = {}) => S.meter(cx, cy, { ...opts, label: 'A' });
  S.voltmeter = (cx, cy, opts = {}) => S.meter(cx, cy, { ...opts, label: 'V' });

  S.dial = defPart('dial', (ctx, opts) => {
    const c = opts.stroke || INK;
    const min = opts.min != null ? opts.min : 0;
    const max = opts.max != null ? opts.max : 1;
    const initVal = opts.value != null ? opts.value : min;
    ctx.setInitState({ value: initVal });
    ctx.rect(-70, -70, 140, 120, { stroke: c, strokeWidth: 5, fill: 'rgba(255,255,255,.45)', fillStyle: 'solid' }, [0, 0.4]);
    ctx.line(-40, 50, -40, 80, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.2, 0.55]);
    ctx.line(40, 50, 40, 80, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.2, 0.55]);
    ctx.arc(0, 32, 100, 100, (-155 * Math.PI) / 180, (-25 * Math.PI) / 180, false, { stroke: c, strokeWidth: 4, roughness: 0.9 }, [0.35, 0.7]);
    for (let i = 0; i < 5; i++) {
      const a = ((-155 + i * 32.5) * Math.PI) / 180;
      ctx.line(40 * Math.cos(a), 32 + 40 * Math.sin(a), 50 * Math.cos(a), 32 + 50 * Math.sin(a), { stroke: c, strokeWidth: 3.5 }, [0.45, 0.75]);
    }
    const needleG = ctx.group();
    ctx.line(0, 0, 0, -44, { stroke: RED, strokeWidth: 4.5, preserveVertices: true, group: needleG }, [0.55, 0.95]);
    ctx.circle(0, 32, 12, { fill: c, fillStyle: 'solid', stroke: c, strokeWidth: 2 }, [0.5, 0.85]);
    if (opts.label) ctx.text(0, -46, String(opts.label), 44, { font: 'l', anchor: 'middle', fill: c }, [0.65, 1]);
    ctx.sign(-40 - 18 / ctx.k, 66, '+', { stroke: RED, scale: 0.8 }, [0.7, 1]);
    ctx.sign(40 + 18 / ctx.k, 66, '-', { stroke: BLUE, scale: 0.8 }, [0.7, 1]);
    ctx.onDraw((_t, st) => {
      const raw = st.value != null ? st.value : min;
      const frac = Math.min(1, Math.max(0, (raw - min) / (max - min || 1)));
      const ang = (frac - 0.5) * 130;
      needleG.setAttribute('transform', `translate(0 32) rotate(${ang})`);
    });
    const P = ctx.toWorld(-40, 80), N = ctx.toWorld(40, 80);
    return { pins: { P, N }, path: [P, N], paths: { PN: [P, N] }, localBox: [-70, -70, 70, 80] };
  });

  S.scope = defPart('scope', (ctx, opts) => {
    const c = opts.stroke || INK;
    const w = opts.w || 220, h = opts.h || 140;
    const hw = w / 2, hh = h / 2;
    ctx.rect(-hw, -hh, w, h, { stroke: c, strokeWidth: 5, fill: 'rgba(255,255,255,.5)', fillStyle: 'solid' }, [0, 0.4]);
    if (opts.grid !== false) {
      ctx.line(-hw + 10, 0, hw - 10, 0, { stroke: GRAY, strokeWidth: 2, strokeLineDash: [6, 6] }, [0.25, 0.55]);
      ctx.line(0, -hh + 10, 0, hh - 10, { stroke: GRAY, strokeWidth: 2, strokeLineDash: [6, 6] }, [0.25, 0.55]);
    }
    let rawPts = opts.pts;
    if (!rawPts || !rawPts.length) {
      rawPts = [];
      for (let i = 0; i <= 24; i++) {
        const u = i / 24;
        rawPts.push([u, Math.sin(u * Math.PI * 4) * 0.72]);
      }
    }
    const isNorm = rawPts.every((p) => p[0] >= -0.01 && p[0] <= 1.01 && p[1] >= -1.5 && p[1] <= 1.5);
    const padW = w - 28, padH = h - 28;
    const wavePts = isNorm
      ? rawPts.map(([ux, uy]) => [-padW / 2 + ux * padW, -uy * (padH / 2)])
      : rawPts.map(([lx, ly]) => [lx, ly]);
    ctx.path(wavePts, { stroke: opts.color || RED, strokeWidth: 4.5, roughness: 0.7 }, [0.45, 1]);
    const IN = ctx.toWorld(-hw, 0), GND = ctx.toWorld(0, hh);
    return { pins: { IN, GND }, path: [IN, GND], paths: { IN_GND: [IN, GND] }, localBox: [-hw, -hh, hw, hh] };
  });

  function simplifyOrtho(pts) {
    const d = dedupPts(pts);
    if (d.length <= 2) return d;
    const out = [d[0]];
    for (let i = 1; i < d.length - 1; i++) {
      const a = out[out.length - 1], b = d[i], c = d[i + 1];
      const sameX = Math.abs(a[0] - b[0]) < 1e-6 && Math.abs(b[0] - c[0]) < 1e-6;
      const sameY = Math.abs(a[1] - b[1]) < 1e-6 && Math.abs(b[1] - c[1]) < 1e-6;
      if (sameX && (b[1] - a[1]) * (c[1] - b[1]) >= 0) continue;
      if (sameY && (b[0] - a[0]) * (c[0] - b[0]) >= 0) continue;
      out.push(b);
    }
    out.push(d[d.length - 1]);
    return out;
  }
  function orthoStep(a, b, mode = 'hv', grid = 20) {
    const snap = (v) => Math.round(v / grid) * grid;
    if (Math.abs(a[0] - b[0]) < 1e-6 || Math.abs(a[1] - b[1]) < 1e-6) return [a, b];
    if (mode === 'vh') return [a, [a[0], b[1]], b];
    if (mode === 'hvh') { const mx = snap((a[0] + b[0]) / 2); return [a, [mx, a[1]], [mx, b[1]], b]; }
    if (mode === 'vhv') { const my = snap((a[1] + b[1]) / 2); return [a, [a[0], my], [b[0], my], b]; }
    return [a, [b[0], a[1]], b];
  }
  S.wire = (pts, opts = {}) => {
    const mode = opts.dir === 'v' ? 'vh' : 'hv';
    const raw = [];
    for (let i = 0; i < pts.length; i++) {
      if (i === 0) { raw.push(pts[0]); continue; }
      const seg = orthoStep(pts[i - 1], pts[i], mode);
      raw.push(...seg.slice(1));
    }
    const clean = simplifyOrtho(raw);
    if (clean.length >= 2) {
      const node = S.path(clean, { stroke: opts.stroke || INK, strokeWidth: opts.strokeWidth || 5, roughness: opts.roughness != null ? opts.roughness : 1.0, preserveVertices: true, ...(opts.strokeLineDash ? { strokeLineDash: opts.strokeLineDash } : {}) });
      clean.node = node;
    }
    return clean;
  };
  S.route = (pinA, pinB, opts = {}) => {
    const grid = opts.grid || 20;
    const snap = (v) => Math.round(v / grid) * grid;
    const via = opts.via;
    const mode = typeof via === 'string' ? via : (opts.dir || 'hv');
    let raw = [];
    if (via && typeof via === 'object' && !Array.isArray(via)) {
      if (via.x != null) { const vx = snap(via.x); raw = [pinA, [vx, pinA[1]], [vx, pinB[1]], pinB]; }
      else if (via.y != null) { const vy = snap(via.y); raw = [pinA, [pinA[0], vy], [pinB[0], vy], pinB]; }
      else raw = orthoStep(pinA, pinB, mode, grid);
    } else if (Array.isArray(via)) {
      const wps = typeof via[0] === 'number' ? [[snap(via[0]), snap(via[1])]] : via.map((p) => [snap(p[0]), snap(p[1])]);
      const seq = [pinA, ...wps, pinB];
      raw = [seq[0]];
      for (let i = 1; i < seq.length; i++) raw.push(...orthoStep(seq[i - 1], seq[i], opts.dir || 'hv', grid).slice(1));
    } else {
      raw = orthoStep(pinA, pinB, mode, grid);
    }
    const clean = simplifyOrtho(raw);
    if (clean.length >= 2) {
      const node = S.path(clean, { stroke: opts.stroke || INK, strokeWidth: opts.strokeWidth || 5, roughness: opts.roughness != null ? opts.roughness : 1.0, preserveVertices: true, ...(opts.strokeLineDash ? { strokeLineDash: opts.strokeLineDash } : {}) });
      clean.node = node;
    }
    return clean;
  };

  const hopPart = defPart('hop', (ctx, opts) => {
    const c = opts.stroke || INK, r = 14;
    if (opts.gap !== false) {
      ctx.line(-r + 2, 0, r - 2, 0, { stroke: '#f3efe6', strokeWidth: 10, roughness: 0.2 }, [0, 0.2]);
    }
    ctx.arc(0, 0, r * 2, r * 2, Math.PI, 2 * Math.PI, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.1, 1]);
    const A = ctx.toWorld(-r, 0), B = ctx.toWorld(r, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-r, -r, r, 4] };
  });
  S.hop = (cx, cy, optsOrDir = {}) => {
    if (typeof optsOrDir === 'string') return hopPart(cx, cy, { rot: optsOrDir === 'v' ? 90 : 0 });
    const o2 = { ...optsOrDir };
    if (o2.dir === 'v' && o2.rot == null) o2.rot = 90;
    if (o2.r != null && o2.size == null) o2.size = o2.r / 14;
    return hopPart(cx, cy, o2);
  };

  const termPart = defPart('term', (ctx, opts) => {
    const c = opts.stroke || INK;
    const fill = opts.fill !== undefined ? opts.fill : '#f3efe6';
    ctx.circle(0, 0, 24, { stroke: c, strokeWidth: 4.5, fill, fillStyle: 'solid' }, [0, 1]);
    if (opts.label) ctx.text(0, -34, String(opts.label), 44, { font: /[\uac00-\ud7a3]/.test(opts.label) ? 'k' : 'l', anchor: 'middle', fill: c }, [0.65, 1]);
    const A = ctx.toWorld(0, 0);
    return { pins: { A }, path: [A], paths: {}, localBox: [-12, -12, 12, 12] };
  });
  S.term = (cx, cy, rOrOpts, stroke) => {
    if (typeof rOrOpts === 'number') return termPart(cx, cy, { size: rOrOpts / 12, stroke: stroke || INK });
    return termPart(cx, cy, rOrOpts);
  };

  S.block = (x, y, w, h, title, opts = {}) => {
    const c = opts.stroke || GRAY;
    S.rect(x, y, w, h, { stroke: c, strokeWidth: opts.strokeWidth || 3.5, strokeLineDash: opts.dash || [12, 9], ...(opts.fill ? { fill: opts.fill, fillStyle: opts.fillStyle || 'solid' } : {}) });
    if (title) {
      const fs = Math.max(44, opts.fontSize || 44);
      const font = /[\uac00-\ud7a3]/.test(title) ? 'k' : 'l';
      const ty = opts.titlePos === 'top' ? y - 16 : y + fs + 10;
      const tx = opts.titlePos === 'top' ? x + 12 : x + 20;
      S.text(tx, ty, title, fs, { font, fill: opts.titleColor || c, anchor: 'start', rot: 0 });
    }
    return {
      box: { x, y, w, h },
      pins: { N: [x + w / 2, y], S: [x + w / 2, y + h], W: [x, y + h / 2], E: [x + w, y + h / 2] }
    };
  };

  S.opamp = defPart('opamp', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, -20, -40, -20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(-60, 20, -40, 20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(40, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    if (opts.power) {
      ctx.line(0, -60, 0, -26, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
      ctx.line(0, 26, 0, 60, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    }
    ctx.polygon(
      [[-40, -52], [-40, 52], [40, 0]],
      { stroke: c, strokeWidth: 5, preserveVertices: true, fill: opts.fill, fillStyle: opts.fill ? 'solid' : undefined },
      [0.2, 0.75]
    );
    ctx.sign(-24, -20, '+', { stroke: RED, scale: 0.6 * ctx.k, strokeWidth: 4.5 }, [0.65, 1]);
    ctx.sign(-24, 20, '-', { stroke: BLUE, scale: 0.6 * ctx.k, strokeWidth: 4.5 }, [0.65, 1]);
    const INP = ctx.toWorld(-60, -20), INN = ctx.toWorld(-60, 20), OUT = ctx.toWorld(60, 0);
    const pins = { INP, INN, OUT };
    if (opts.power) {
      pins.VP = ctx.toWorld(0, -60);
      pins.VN = ctx.toWorld(0, 60);
    }
    return {
      pins,
      path: [INP, OUT],
      paths: { INP_OUT: [INP, OUT], INN_OUT: [INN, OUT] },
      localBox: opts.power ? [-60, -60, 60, 60] : [-60, -52, 60, 52]
    };
  });

  function makeGate(type) {
    return defPart('gate_' + type, (ctx, opts) => {
      const c = opts.stroke || INK;
      const hasBubble = type === 'not' || type === 'nand' || type === 'nor';
      if (type === 'not') {
        ctx.line(-60, 0, -36, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
        ctx.polygon(
          [[-36, -34], [-36, 34], [24, 0]],
          { stroke: c, strokeWidth: 5, preserveVertices: true, fill: opts.fill, fillStyle: opts.fill ? 'solid' : undefined },
          [0.2, 0.7]
        );
        ctx.circle(32, 0, 16, { stroke: c, strokeWidth: 4.5, roughness: 0.8 }, [0.6, 0.9]);
        ctx.line(40, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.7, 1]);
        const A = ctx.toWorld(-60, 0), Y = ctx.toWorld(60, 0);
        return { pins: { A, Y }, path: [A, Y], paths: { AY: [A, Y] }, localBox: [-60, -34, 60, 34] };
      }
      if (type === 'and' || type === 'nand') {
        ctx.line(-60, -20, -40, -20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
        ctx.line(-60, 20, -40, 20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
        ctx.path([[-8, -36], [-40, -36], [-40, 36], [-8, 36]], { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.15, 0.55]);
        ctx.arc(-8, 0, 72, 72, -Math.PI / 2, Math.PI / 2, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.45, 0.8]);
      } else {
        const backX = (y) => -38 + 12 * (1 - (y / 36) ** 2);
        const inX = type === 'xor' ? backX(20) - 10 : backX(20);
        ctx.line(-60, -20, inX, -20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
        ctx.line(-60, 20, inX, 20, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
        const backPts = [], xorPts = [], topPts = [], botPts = [];
        for (let i = 0; i <= 8; i++) {
          const y = -36 + 9 * i;
          backPts.push([backX(y), y]);
          if (type === 'xor') xorPts.push([backX(y) - 10, y]);
        }
        const bez = (p0, p1, p2, p3, u) => {
          const m = 1 - u;
          return [
            m ** 3 * p0[0] + 3 * m ** 2 * u * p1[0] + 3 * m * u ** 2 * p2[0] + u ** 3 * p3[0],
            m ** 3 * p0[1] + 3 * m ** 2 * u * p1[1] + 3 * m * u ** 2 * p2[1] + u ** 3 * p3[1]
          ];
        };
        for (let i = 0; i <= 4; i++) {
          const u = i / 4;
          topPts.push(bez([-38, -36], [-2, -36], [16, -18], [28, 0], u));
          botPts.push(bez([-38, 36], [-2, 36], [16, 18], [28, 0], u));
        }
        if (type === 'xor') ctx.curve(xorPts, { stroke: c, strokeWidth: 5, roughness: 0.8 }, [0.1, 0.45]);
        ctx.curve(backPts, { stroke: c, strokeWidth: 5, roughness: 0.8 }, [0.2, 0.55]);
        ctx.curve(topPts, { stroke: c, strokeWidth: 5, roughness: 0.8 }, [0.4, 0.8]);
        ctx.curve(botPts, { stroke: c, strokeWidth: 5, roughness: 0.8 }, [0.4, 0.8]);
      }
      if (hasBubble) {
        ctx.circle(36, 0, 16, { stroke: c, strokeWidth: 4.5, roughness: 0.8 }, [0.65, 0.9]);
        ctx.line(44, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.75, 1]);
      } else {
        ctx.line(28, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.7, 1]);
      }
      const A = ctx.toWorld(-60, -20), B = ctx.toWorld(-60, 20), mid = ctx.toWorld(0, 0), Y = ctx.toWorld(60, 0);
      return { pins: { A, B, Y }, path: [A, mid, Y], paths: { AY: [A, mid, Y], BY: [B, mid, Y] }, localBox: [-60, -36, 60, 36] };
    });
  }
  const GATE_PARTS = {};
  for (const t of ['and', 'or', 'not', 'nand', 'nor', 'xor']) GATE_PARTS[t] = makeGate(t);
  S.gate = (type, cx, cy, opts) => {
    const t = String(type || '').toLowerCase();
    const fn = GATE_PARTS[t];
    if (!fn) throw new Error(`sketch: unknown gate type "${type}"`);
    return fn(cx, cy, opts);
  };

  /* ---- phase 2 deferred symbols & real-world parts ---- */
  S.vcap = defPart('vcap', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-60, 0, -12, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.45]);
    ctx.line(12, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.45]);
    ctx.line(-12, -38, -12, 38, { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.35, 0.75]);
    ctx.line(12, -38, 12, 38, { stroke: c, strokeWidth: 8, preserveVertices: true }, [0.35, 0.75]);
    partArrow(ctx, -34, 34, 34, -34, { stroke: c, strokeWidth: 4.5, head: 16, winLine: [0.6, 0.9], winHead: [0.7, 1] });
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -38, 60, 38] };
  });

  S.buzzer = defPart('buzzer', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.line(-20, 4, -20, 60, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(20, 4, 20, 60, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(-48, 4, 48, 4, { stroke: c, strokeWidth: 6, preserveVertices: true }, [0.25, 0.6]);
    ctx.arc(0, 4, 80, 80, Math.PI, 2 * Math.PI, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.4, 0.85]);
    ctx.arc(0, 4, 106, 106, -Math.PI * 0.67, -Math.PI * 0.33, false, { stroke: c, strokeWidth: 3.5, roughness: 0.8 }, [0.7, 0.95]);
    ctx.arc(0, 4, 124, 124, -Math.PI * 0.63, -Math.PI * 0.37, false, { stroke: c, strokeWidth: 3.5, roughness: 0.8 }, [0.75, 1]);
    const A = ctx.toWorld(-20, 60), B = ctx.toWorld(20, 60);
    const ab = dedupPts([A, ctx.toWorld(-20, 4), ctx.toWorld(20, 4), B]);
    return { pins: { A, B }, path: ab, paths: { AB: ab }, localBox: [-48, -58, 48, 60] };
  });

  function withAlpha(col, alpha) {
    if (!col) return `rgba(212,56,44,${alpha})`;
    const s = String(col).trim().toLowerCase();
    const named = { red: '#d4382c', blue: '#2a5db0', green: '#2e8b57', yellow: '#ffd000', orange: '#f08a2c', white: '#ffffff' };
    const hex = named[s] || s;
    const m6 = hex.match(/^#([0-9a-f]{6})$/);
    if (m6) {
      const n = parseInt(m6[1], 16);
      return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`;
    }
    const m3 = hex.match(/^#([0-9a-f]{3})$/);
    if (m3) {
      const r = parseInt(m3[1][0] + m3[1][0], 16), g0 = parseInt(m3[1][1] + m3[1][1], 16), b = parseInt(m3[1][2] + m3[1][2], 16);
      return `rgba(${r},${g0},${b},${alpha})`;
    }
    const mRgb = hex.match(/^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/);
    if (mRgb) return `rgba(${mRgb[1]},${mRgb[2]},${mRgb[3]},${alpha})`;
    return col;
  }

  const RES_DIGIT_COLS = ['#1e1d1a', '#7b4a26', '#d4382c', '#f08a2c', '#e6c229', '#2e8b57', '#2a5db0', '#7a49a5', '#7b7770', '#f5f2ea'];
  const RES_MULT_EXTRA = { '-2': '#b8bcc2', '-1': '#d4a638' };
  const RES_TOL_COLS = {
    gold: '#d4a638', '5%': '#d4a638',
    silver: '#b8bcc2', '10%': '#b8bcc2',
    brown: '#7b4a26', '1%': '#7b4a26',
    red: '#d4382c', '2%': '#d4382c',
    green: '#2e8b57', '0.5%': '#2e8b57',
    blue: '#2a5db0', '0.25%': '#2a5db0',
    violet: '#7a49a5', '0.1%': '#7a49a5',
    none: null, '20%': null
  };
  function parseResOhms(val) {
    if (typeof val === 'number') return val;
    const raw = String(val == null ? '220' : val).replace(/[Ωω,\s]/g, '').replace(/ohms?$/i, '');
    let m = raw.match(/^(\d*)[Rr](\d+)$/);
    if (m) return parseFloat((m[1] || '0') + '.' + m[2]);
    m = raw.match(/^(\d+)[kK](\d+)$/);
    if (m) return parseFloat(m[1] + '.' + m[2]) * 1e3;
    m = raw.match(/^(\d+)[mM](\d+)$/);
    if (m) return parseFloat(m[1] + '.' + m[2]) * 1e6;
    m = raw.match(/^([\d.]+)([kKmMgG]?)$/);
    if (m) {
      const mul = { '': 1, k: 1e3, K: 1e3, M: 1e6, G: 1e9, m: 1e-3 }[m[2]] || 1;
      return parseFloat(m[1]) * mul;
    }
    return 220;
  }
  function resColorBands(val, tol, override) {
    if (Array.isArray(override) && override.length >= 3) return override.slice(0, 4);
    const ohms = parseResOhms(val);
    let b1 = RES_DIGIT_COLS[0], b2 = RES_DIGIT_COLS[0], b3 = RES_DIGIT_COLS[0];
    if (ohms > 0 && Number.isFinite(ohms)) {
      let exp = Math.floor(Math.log10(ohms)) - 1;
      let sig = Math.round(ohms / Math.pow(10, exp));
      if (sig >= 100) { sig = Math.round(sig / 10); exp += 1; }
      if (sig < 10) { sig *= 10; exp -= 1; }
      exp = Math.max(-2, Math.min(9, exp));
      b1 = RES_DIGIT_COLS[Math.floor(sig / 10) % 10];
      b2 = RES_DIGIT_COLS[sig % 10];
      b3 = exp < 0 ? RES_MULT_EXTRA[String(exp)] : RES_DIGIT_COLS[exp];
    }
    const tolKey = tol == null ? 'gold' : String(tol).trim().toLowerCase();
    const b4 = Object.prototype.hasOwnProperty.call(RES_TOL_COLS, tolKey) ? RES_TOL_COLS[tolKey] : tol;
    return b4 ? [b1, b2, b3, b4] : [b1, b2, b3];
  }

  S.cellReal = defPart('cellReal', (ctx, opts) => {
    const c = opts.stroke || INK;
    const kind = String(opts.kind || 'AA').toUpperCase() === '9V' ? '9V' : 'AA';
    if (kind === '9V') {
      ctx.polygon([[-40, -32], [-28, -46], [50, -46], [38, -32]],
        { stroke: c, strokeWidth: 4.5, fill: 'rgba(138,133,123,.15)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 2.5, preserveVertices: true }, [0.1, 0.55]);
      ctx.polygon([[38, -32], [50, -46], [50, 46], [38, 60]],
        { stroke: c, strokeWidth: 4.5, fill: 'rgba(138,133,123,.26)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 2.5, preserveVertices: true }, [0.15, 0.6]);
      ctx.rect(-40, -32, 78, 28,
        { stroke: 'none', fill: 'rgba(212,56,44,.22)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 3, hachureAngle: 55 }, [0.2, 0.65]);
      ctx.rect(-40, -32, 78, 92, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.5]);
      ctx.line(-40, -4, 38, -4, { stroke: c, strokeWidth: 4.5 }, [0.35, 0.7]);
      ctx.rect(-26, -60, 12, 20,
        { stroke: c, strokeWidth: 4.5, fill: 'rgba(212,56,44,.22)', fillStyle: 'hachure', hachureGap: 4, fillWeight: 2, preserveVertices: true }, [0.5, 0.85]);
      ctx.polygon([[10, -60], [30, -60], [27, -40], [13, -40]],
        { stroke: c, strokeWidth: 4.5, fill: 'rgba(42,93,176,.22)', fillStyle: 'hachure', hachureGap: 4, fillWeight: 2, preserveVertices: true }, [0.5, 0.85]);
      ctx.sign(-38 - 16 / ctx.k, -50, '+', { stroke: RED, scale: 0.85 }, [0.7, 1]);
      ctx.sign(46 + 16 / ctx.k, -50, '-', { stroke: BLUE, scale: 0.85 }, [0.7, 1]);
      const P = ctx.toWorld(-20, -60), N = ctx.toWorld(20, -60);
      return { pins: { P, N }, path: [P, N], paths: { PN: [P, N] }, localBox: [-40, -60, 50, 60] };
    }
    ctx.polygon([[-46, -28], [53, -28], [53, 28], [-46, 28]],
      { stroke: 'none', fill: 'rgba(138,133,123,.14)', fillStyle: 'hachure', hachureGap: 8, fillWeight: 2.5, hachureAngle: -30 }, [0.1, 0.55]);
    ctx.rect(-46, -28, 30, 56,
      { stroke: 'none', fill: 'rgba(212,56,44,.22)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 3, hachureAngle: 55 }, [0.2, 0.65]);
    ctx.arc(-16, 0, 14, 56, -Math.PI / 2, Math.PI / 2, false, { stroke: c, strokeWidth: 4.5, roughness: 0.9 }, [0.35, 0.75]);
    ctx.line(-46, -28, 53, -28, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.1, 0.55]);
    ctx.line(-46, 28, 53, 28, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.1, 0.55]);
    ctx.ellipse(-46, 0, 14, 56, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.2, 0.65]);
    ctx.arc(53, 0, 14, 56, -Math.PI / 2, Math.PI / 2, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.25, 0.7]);
    ctx.rect(-60, -11, 14, 22,
      { stroke: c, strokeWidth: 5, fill: 'rgba(212,56,44,.25)', fillStyle: 'hachure', hachureGap: 4, fillWeight: 2.5, preserveVertices: true }, [0.45, 0.85]);
    ctx.sign(-36 - 14 / ctx.k, -32 - 22 / ctx.k, '+', { stroke: RED }, [0.7, 1]);
    ctx.sign(36 + 14 / ctx.k, -32 - 22 / ctx.k, '-', { stroke: BLUE }, [0.7, 1]);
    const P = ctx.toWorld(-60, 0), N = ctx.toWorld(60, 0);
    return { pins: { P, N }, path: [P, N], paths: { PN: [P, N] }, localBox: [-60, -28, 60, 28] };
  });

  S.resReal = defPart('resReal', (ctx, opts) => {
    const c = opts.stroke || INK;
    const bands = resColorBands(opts.value, opts.tol, opts.bands);
    ctx.line(-60, 0, -38, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    ctx.line(38, 0, 60, 0, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.35]);
    const bodyPts = [
      [-38, 0], [-36, -18], [-24, -20], [-14, -15], [14, -15], [24, -20], [36, -18],
      [38, 0], [36, 18], [24, 20], [14, 15], [-14, 15], [-24, 20], [-36, 18]
    ];
    ctx.polygon(bodyPts,
      { stroke: 'none', fill: '#e6d3ad', fillStyle: 'hachure', hachureGap: 7, fillWeight: 3, hachureAngle: -35 }, [0.15, 0.6]);
    const bandSpecs = [[-29, 34], [-14, 28], [1, 28], [20, 34]];
    bands.forEach((bCol, i) => {
      const [bx, bh] = bandSpecs[i];
      ctx.rect(bx, -bh / 2, 7, bh,
        { stroke: bCol, strokeWidth: 1.5, fill: bCol, fillStyle: 'hachure', hachureGap: 3.2, fillWeight: 3.2, hachureAngle: 70, roughness: 0.6 },
        [0.45 + i * 0.08, 0.85 + i * 0.04]);
    });
    ctx.polygon(bodyPts, { stroke: c, strokeWidth: 5, roughness: 1.0 }, [0.2, 0.8]);
    const A = ctx.toWorld(-60, 0), B = ctx.toWorld(60, 0);
    return { pins: { A, B }, path: [A, B], paths: { AB: [A, B] }, localBox: [-60, -20, 60, 20] };
  });

  S.ledReal = defPart('ledReal', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.normalizeState((s) => {
      if (s.on !== undefined) return { on: s.on ? 1 : 0 };
      if (s.off !== undefined) return { on: s.off ? 0 : 1 };
      return s;
    });
    ctx.setInitState({ on: !!opts.on });
    const baseCol = opts.color;
    const offTint = withAlpha(baseCol || RED, 0.16);
    const innerLit = baseCol ? withAlpha(baseCol, 0.88) : 'rgba(255,208,0,.9)';
    const outerGlow = (!baseCol || String(baseCol).toLowerCase() === 'yellow') ? HL : withAlpha(baseCol, 0.48);
    const domePts = [[-26, -8], [-26, -34], [-22, -46], [-12, -55], [0, -58], [12, -55], [22, -46], [26, -34], [26, -8]];
    const glowItem = ctx.circle(0, -32, 136,
      { stroke: 'none', fill: outerGlow, fillStyle: 'hachure', hachureGap: 8, fillWeight: 10, roughness: 2 }, [0.55, 1]);
    const litItem = ctx.polygon(domePts, { stroke: 'none', fill: innerLit, fillStyle: 'solid' }, [0.55, 1]);
    ctx.polygon(domePts,
      { stroke: 'none', fill: offTint, fillStyle: 'hachure', hachureGap: 7, fillWeight: 3, hachureAngle: -40 }, [0.1, 0.55]);
    ctx.path([[-16, -8], [-16, -26], [-8, -32]], { stroke: GRAY, strokeWidth: 3 }, [0.3, 0.65]);
    ctx.polygon([[4, -30], [16, -30], [16, -8], [8, -8], [8, -22]], { stroke: GRAY, strokeWidth: 3 }, [0.3, 0.65]);
    ctx.path(domePts, { stroke: c, strokeWidth: 5, roughness: 1.0 }, [0.15, 0.7]);
    ctx.polygon([[-26, -8], [-35, -6], [-35, 3], [26, 3], [26, -8]],
      { stroke: c, strokeWidth: 5, fill: offTint, fillStyle: 'hachure', hachureGap: 6, fillWeight: 2.5, preserveVertices: true }, [0.25, 0.75]);
    ctx.line(21, -8, 21, 3, { stroke: c, strokeWidth: 3.5 }, [0.4, 0.75]);
    ctx.line(-20, 3, -20, 60, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.45, 0.95]);
    ctx.line(20, 3, 20, 40, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.45, 0.95]);
    ctx.onDraw((_t, st) => {
      const on = Math.min(1, Math.max(0, st.on || 0));
      glowItem.n.style.opacity = (glowItem._vis != null ? glowItem._vis : 1) * on;
      litItem.n.style.opacity = (litItem._vis != null ? litItem._vis : 1) * on;
    });
    const A = ctx.toWorld(-20, 60), K = ctx.toWorld(20, 40);
    return { pins: { A, K }, path: [A, K], paths: { AK: [A, K] }, localBox: [-35, -58, 26, 60] };
  });

  S.ecapReal = defPart('ecapReal', (ctx, opts) => {
    const c = opts.stroke || INK;
    ctx.rect(-34, -48, 68, 56,
      { stroke: 'none', fill: 'rgba(34,32,28,.12)', fillStyle: 'hachure', hachureGap: 7, fillWeight: 2.5, hachureAngle: -35 }, [0.1, 0.5]);
    ctx.rect(14, -46, 18, 54,
      { stroke: BLUE, strokeWidth: 2, fill: 'rgba(42,93,176,.32)', fillStyle: 'hachure', hachureGap: 4.5, fillWeight: 3, hachureAngle: 50 }, [0.35, 0.8]);
    ctx.line(-34, -48, -34, 8, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.45]);
    ctx.line(34, -48, 34, 8, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0, 0.45]);
    ctx.arc(0, 8, 68, 20, 0, Math.PI, false, { stroke: c, strokeWidth: 5, roughness: 0.9 }, [0.25, 0.65]);
    ctx.ellipse(0, -48, 68, 22, { stroke: c, strokeWidth: 5, fill: 'rgba(255,255,255,.5)', fillStyle: 'solid', roughness: 0.9 }, [0.2, 0.65]);
    ctx.line(-18, -53, 18, -43, { stroke: GRAY, strokeWidth: 3.5 }, [0.55, 0.9]);
    ctx.line(-18, -43, 18, -53, { stroke: GRAY, strokeWidth: 3.5 }, [0.55, 0.9]);
    ctx.line(-20, 16, -20, 60, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.5, 0.95]);
    ctx.line(20, 16, 20, 40, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.5, 0.95]);
    ctx.sign(23, -18, '-', { stroke: BLUE, scale: 0.65 * ctx.k, strokeWidth: 4.5 }, [0.7, 1]);
    const P = ctx.toWorld(-20, 60), N = ctx.toWorld(20, 40);
    return { pins: { P, N }, path: [P, N], paths: { PN: [P, N] }, localBox: [-34, -59, 34, 60] };
  });

  S.to92 = defPart('to92', (ctx, opts) => {
    const c = opts.stroke || INK;
    const rawPins = opts.pins != null ? opts.pins : 'EBC';
    const names = (Array.isArray(rawPins) ? rawPins.map(String) : String(rawPins).split('')).slice(0, 3);
    while (names.length < 3) names.push(['E', 'B', 'C'][names.length]);
    ctx.arc(0, -34, 72, 24, Math.PI, 2 * Math.PI, false,
      { stroke: c, strokeWidth: 5, fill: 'rgba(34,32,28,.12)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 2.5, roughness: 0.9 }, [0.1, 0.55]);
    ctx.rect(-36, -34, 72, 46,
      { stroke: c, strokeWidth: 5, fill: 'rgba(34,32,28,.20)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 3, hachureAngle: -40 }, [0.15, 0.65]);
    [-20, 0, 20].forEach((lx, i) => {
      ctx.line(lx, 12, lx, 60, { stroke: c, strokeWidth: 5, preserveVertices: true }, [0.45 + i * 0.08, 0.95]);
    });
    if (opts.label) ctx.text(0, -11, String(opts.label), 44, { font: 'l', anchor: 'middle', fill: c }, [0.7, 1]);
    const pts = [ctx.toWorld(-20, 60), ctx.toWorld(0, 60), ctx.toWorld(20, 60)];
    const pins = {};
    names.forEach((pn, i) => { pins[pn] = pts[i]; });
    const mid = ctx.toWorld(0, 0);
    const paths = {};
    if (pins.C && pins.E) paths.CE = dedupPts([pins.C, mid, pins.E]);
    if (pins.B && pins.E) paths.BE = dedupPts([pins.B, mid, pins.E]);
    if (pins.D && pins.S) paths.DS = dedupPts([pins.D, mid, pins.S]);
    const mainPath = paths.CE || paths.DS || [pts[0], pts[2]];
    return { pins, path: mainPath, paths, localBox: [-36, -46, 36, 60] };
  });

  const breadboardPart = defPart('breadboard', (ctx, opts) => {
    const cols = Math.max(2, opts.cols || 15);
    const rows = Math.max(2, opts.rows || 10);
    const rails = opts.rails !== false;
    const topRows = Math.ceil(rows / 2);
    const c = opts.stroke || INK;
    const W = (cols + 3) * 20;
    const H = (rows + (rails ? 8 : 2)) * 20;
    const hw = W / 2, hh = H / 2;
    const colX = (col) => -hw + 40 + col * 20;
    const rowY = (row) => {
      if (typeof row === 'string') {
        const s = row.toLowerCase();
        if (s === 'top+' || s === '+') return -hh + 20;
        if (s === 'top-' || s === '-') return -hh + 40;
        if (s === 'bot+') return hh - 40;
        if (s === 'bot-') return hh - 20;
      }
      if (rails) {
        if (row === -2) return -hh + 20;
        if (row === -1) return -hh + 40;
        if (row === rows) return hh - 40;
        if (row === rows + 1) return hh - 20;
      }
      const baseY = -hh + (rails ? 80 : 20);
      return baseY + (row >= topRows ? row + 1 : row) * 20;
    };
    ctx.rect(-hw, -hh, W, H, { stroke: c, strokeWidth: 5, fill: '#faf6ed', fillStyle: 'solid' }, [0, 0.3]);
    if (rails) {
      ctx.line(-hw + 30, -hh + 10, hw - 16, -hh + 10, { stroke: RED, strokeWidth: 3 }, [0.15, 0.5]);
      ctx.line(-hw + 30, -hh + 50, hw - 16, -hh + 50, { stroke: BLUE, strokeWidth: 3 }, [0.15, 0.5]);
      ctx.line(-hw + 8, -hh + 60, hw - 8, -hh + 60, { stroke: GRAY, strokeWidth: 2.5 }, [0.2, 0.55]);
      ctx.line(-hw + 8, hh - 60, hw - 8, hh - 60, { stroke: GRAY, strokeWidth: 2.5 }, [0.2, 0.55]);
      ctx.line(-hw + 30, hh - 50, hw - 16, hh - 50, { stroke: RED, strokeWidth: 3 }, [0.15, 0.5]);
      ctx.line(-hw + 30, hh - 10, hw - 16, hh - 10, { stroke: BLUE, strokeWidth: 3 }, [0.15, 0.5]);
      ctx.sign(-hw + 18, -hh + 20, '+', { stroke: RED, scale: 0.45 * ctx.k, strokeWidth: 4 }, [0.65, 1]);
      ctx.sign(-hw + 18, -hh + 40, '-', { stroke: BLUE, scale: 0.45 * ctx.k, strokeWidth: 4 }, [0.65, 1]);
      ctx.sign(-hw + 18, hh - 40, '+', { stroke: RED, scale: 0.45 * ctx.k, strokeWidth: 4 }, [0.65, 1]);
      ctx.sign(-hw + 18, hh - 20, '-', { stroke: BLUE, scale: 0.45 * ctx.k, strokeWidth: 4 }, [0.65, 1]);
    }
    const trenchY = -hh + (rails ? 80 : 20) + topRows * 20;
    ctx.rect(-hw + 10, trenchY - 8, W - 20, 16,
      { stroke: GRAY, strokeWidth: 3, fill: 'rgba(138,133,123,.22)', fillStyle: 'hachure', hachureGap: 6, fillWeight: 2 }, [0.2, 0.6]);
    const drawHole = (hx, hy) => {
      ctx.rect(hx - 4, hy - 4, 8, 8, { stroke: c, strokeWidth: 2, fill: '#3b3730', fillStyle: 'solid', roughness: 0.4 }, [0.25, 0.95]);
    };
    if (rails) {
      for (const ry of [-hh + 20, -hh + 40, hh - 40, hh - 20]) {
        for (let col = 0; col < cols; col++) drawHole(colX(col), ry);
      }
    }
    for (let r = 0; r < rows; r++) {
      const hy = rowY(r);
      for (let col = 0; col < cols; col++) drawHole(colX(col), hy);
    }
    const hole = (col, row) => ctx.toWorld(colX(col), rowY(row));
    return { pins: {}, path: [], paths: {}, localBox: [-hw, -hh, hw, hh], extra: { hole, cols, rows } };
  });
  S.breadboard = (xOrCx, yOrCy, colsOrOpts, rowsArg, extraOpts) => {
    if (typeof colsOrOpts === 'number') {
      const cols = Math.max(2, colsOrOpts);
      const rows = typeof rowsArg === 'number' ? Math.max(2, rowsArg) : 10;
      const opts = (typeof rowsArg === 'object' && rowsArg !== null) ? rowsArg : (extraOpts || {});
      const rails = opts.rails !== false;
      const k = sizeScale(opts.size);
      const W = (cols + 3) * 20 * k;
      const H = (rows + (rails ? 8 : 2)) * 20 * k;
      return breadboardPart(xOrCx + W / 2, yOrCy + H / 2, { ...opts, cols, rows });
    }
    return breadboardPart(xOrCx, yOrCy, colsOrOpts);
  };

  /* ---- labels ---- */
  S.label = (part, name, value, opts = {}) => {
    const b = part.box || { x: 0, y: 0, w: 0, h: 0 };
    const cx = b.x + b.w / 2, cy = b.y + b.h / 2;
    let side = opts.side || (b.w >= b.h ? 'top' : 'right');
    const gap = 16, lineH = 48;
    const hasName = name != null && name !== '', hasVal = value != null && value !== '';
    if (!hasName && !hasVal) return [];
    const fontOf = (str) => (/[\uac00-\ud7a3]/.test(str) ? 'k' : 'l');
    const estW = (str, fs) => String(str).length * fs * 0.62;
    const maxW = Math.max(hasName ? estW(name, 48) : 0, hasVal ? estW(value, 44) : 0);
    const totalH = (hasName ? 48 : 0) + (hasVal ? (hasName ? lineH : 44) : 0);

    if (side === 'top' && (b.y - gap - totalH < 140)) side = 'bottom';
    else if (side === 'bottom' && (b.y + b.h + gap + totalH > 1395) && (b.y - gap - totalH >= 140)) side = 'top';
    else if (side === 'right' && (b.x + b.w + gap + maxW > 960)) side = 'left';

    const out = [];
    const placeLine = (x, y, str, fs, anchor, fill) => out.push(S.text(x, y, str, fs, { font: fontOf(str), fill, anchor, rot: 0 }));
    if (side === 'top' || side === 'bottom') {
      const anchor = 'middle';
      if (side === 'top') {
        if (hasName && hasVal) {
          placeLine(cx, b.y - gap - lineH, name, 48, anchor, opts.fill || INK);
          placeLine(cx, b.y - gap, value, 44, anchor, opts.valueFill || GRAY);
        } else if (hasName) {
          placeLine(cx, b.y - gap, name, 48, anchor, opts.fill || INK);
        } else {
          placeLine(cx, b.y - gap, value, 44, anchor, opts.valueFill || GRAY);
        }
      } else {
        if (hasName && hasVal) {
          placeLine(cx, b.y + b.h + gap + 42, name, 48, anchor, opts.fill || INK);
          placeLine(cx, b.y + b.h + gap + 42 + lineH, value, 44, anchor, opts.valueFill || GRAY);
        } else if (hasName) {
          placeLine(cx, b.y + b.h + gap + 42, name, 48, anchor, opts.fill || INK);
        } else {
          placeLine(cx, b.y + b.h + gap + 40, value, 44, anchor, opts.valueFill || GRAY);
        }
      }
    } else {
      const anchor = side === 'right' ? 'start' : 'end';
      const tx = side === 'right' ? b.x + b.w + gap : b.x - gap;
      if (hasName && hasVal) {
        placeLine(tx, cy - 6, name, 48, anchor, opts.fill || INK);
        placeLine(tx, cy - 6 + lineH, value, 44, anchor, opts.valueFill || GRAY);
      } else if (hasName) {
        placeLine(tx, cy + 16, name, 48, anchor, opts.fill || INK);
      } else {
        placeLine(tx, cy + 15, value, 44, anchor, opts.valueFill || GRAY);
      }
    }
    return out;
  };

  /* ---- pen marks ---- */
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

  /* ---- layers that move: S.layer(() => {...}) groups what is drawn inside; S.move(layer, [[t, dx, dy, s], ...])
     slides (and scales about its origin) the whole group through the keyframes, eased in and out between them ---- */
  S.layer = (fn, ox = 0, oy = 0) => {
    const lg = document.createElementNS(NS, 'g'), parent = g; parent.appendChild(lg); g = lg;
    try { fn(); } finally { g = parent; }
    return { g: lg, ox, oy };
  };
  S.move = (layer, keys) => { MOVES.push({ layer, keys: keys.map((k) => [k[0], k[1] || 0, k[2] || 0, k[3] == null ? 1 : k[3]]) }); return layer; };
  function moveAt(m, t) {
    const K = m.keys; let k = K[0];
    if (t <= K[0][0]) k = K[0]; else if (t >= K[K.length - 1][0]) k = K[K.length - 1];
    else { const i = K.findIndex((q) => q[0] > t), a = K[i - 1], b = K[i], p = (t - a[0]) / (b[0] - a[0]), e = p < 0.5 ? 4 * p ** 3 : 1 - (-2 * p + 2) ** 3 / 2;
      k = [t, a[1] + (b[1] - a[1]) * e, a[2] + (b[2] - a[2]) * e, a[3] + (b[3] - a[3]) * e]; }
    const { ox, oy } = m.layer;
    m.layer.g.setAttribute('transform', `translate(${k[1] + ox} ${k[2] + oy}) scale(${k[3]}) translate(${-ox} ${-oy})`);
  }

  /* ---- matter: atoms, bonds, carriers, ions, junction ---- */
  const electronPart = defPart('electron', (ctx, opts) => {
    ctx.circle(0, 0, 24, { fill: opts.fill || BLUE, fillStyle: 'solid', stroke: opts.stroke || '#173a78', strokeWidth: 2, roughness: 0.6 }, [0, 1]);
    const C = ctx.toWorld(0, 0);
    return { pins: { C }, path: [], paths: {}, localBox: [-12, -12, 12, 12] };
  });
  S.electron = (x, y, rOrOpts) => electronPart(x, y, typeof rOrOpts === 'number' ? { size: rOrOpts / 12 } : rOrOpts);

  const holePart = defPart('hole', (ctx, opts) => {
    ctx.circle(0, 0, 30, { stroke: opts.stroke || RED, strokeWidth: 4, strokeLineDash: [7, 6], roughness: 0.8 }, [0, 1]);
    const C = ctx.toWorld(0, 0);
    return { pins: { C }, path: [], paths: {}, localBox: [-15, -15, 15, 15] };
  });
  S.hole = (x, y, rOrOpts) => holePart(x, y, typeof rOrOpts === 'number' ? { size: rOrOpts / 15 } : rOrOpts);

  const ionPart = defPart('ion', (ctx, opts) => {
    const sign = opts.sign || '+', c = opts.stroke || (sign === '+' ? RED : BLUE);
    ctx.circle(0, 0, 60, { stroke: c, strokeWidth: 4 }, [0, 0.55]);
    ctx.sign(0, 0, sign === '+' ? '+' : '-', { stroke: c, scale: ctx.k }, [0.45, 1]);
    const C = ctx.toWorld(0, 0);
    return { pins: { C }, path: [], paths: {}, localBox: [-30, -30, 30, 30] };
  });
  S.ion = (x, y, signOrOpts = '+', r) => {
    if (typeof signOrOpts === 'string') {
      return ionPart(x, y, { sign: signOrOpts, ...(typeof r === 'number' ? { size: r / 30 } : (r || {})) });
    }
    return ionPart(x, y, signOrOpts);
  };

  const atomPart = defPart('atom', (ctx, opts) => {
    const color = opts.color || opts.stroke || INK;
    const label = opts.label != null ? opts.label : 'Si';
    const hands = opts.hands != null ? opts.hands : 4;
    const fontSize = typeof opts.fontSize === 'number' ? Math.max(44, opts.fontSize) : 48;
    ctx.circle(0, 0, 120, { stroke: color, strokeWidth: 5, fill: 'rgba(255,255,255,.55)', fillStyle: 'solid' }, [0, 0.65]);
    ctx.text(0, 0, label, fontSize, { font: 'l', anchor: 'middle', fill: color }, [0.6, 1]);
    const dirs = [['N', 0, -1], ['E', 1, 0], ['S', 0, 1], ['W', -1, 0], ['NE', 0.7, -0.7]].slice(0, hands);
    const pins = {}, handPts = [];
    for (const [k, dx, dy] of dirs) { const pt = ctx.toWorld(dx * 60, dy * 60); pins[k] = pt; handPts.push(pt); }
    return { pins, path: [], paths: {}, localBox: [-60, -60, 60, 60], extra: { hands: handPts } };
  });
  S.atom = (cx, cy, labelOrOpts = 'Si', opts) => {
    if (typeof labelOrOpts === 'string') {
      const o2 = opts || {};
      const scale = o2.r != null ? o2.r / 60 : (typeof o2.size === 'string' ? o2.size : (o2.scale || 1));
      const fontSize = typeof o2.size === 'number' ? o2.size : o2.fontSize;
      return atomPart(cx, cy, { ...o2, label: labelOrOpts, size: scale, fontSize });
    }
    const o2 = labelOrOpts || {};
    const scale = o2.r != null ? o2.r / 60 : (o2.size != null ? o2.size : 1);
    return atomPart(cx, cy, { ...o2, size: scale });
  };

  // a lattice of atoms joined by bonds; each bond holds two electrons (the shared pair). cell(i, j) may return
  // {label, color, skipBond: ['r'|'d'], extra: true} to make a dopant; returns {at(i,j), bond(i,j,dir)} positions
  S.lattice = (x0, y0, cols, rows, pitch, { cell = () => ({}), r = 46, size = 44, electrons = true } = {}) => {
    const P = (i, j) => [x0 + i * pitch, y0 + j * pitch], out = { at: P, bonds: {} };
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      const c = cell(i, j) || {}, [x, y] = P(i, j);
      for (const [dir, di, dj] of [['r', 1, 0], ['d', 0, 1]]) {
        if (i + di >= cols || j + dj >= rows) continue;
        const [x2, y2] = P(i + di, j + dj), miss = (c.skipBond || []).includes(dir) || ((cell(i + di, j + dj) || {}).skipFrom || []).includes(dir);
        S.line(x + di * r, y + dj * r, x2 - di * r, y2 - dj * r, { strokeWidth: 4 });
        const mx = (x + x2) / 2, my = (y + y2) / 2; out.bonds[`${i},${j},${dir}`] = [mx, my];
        if (electrons) {
          const ox = dj * 13, oy = di * 13;
          S.electron(mx - ox, my - oy, 9);
          if (miss) S.hole(mx + ox, my + oy, 11); else S.electron(mx + ox, my + oy, 9);
        }
      }
    }
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) { const c = cell(i, j) || {}, [x, y] = P(i, j); S.atom(x, y, c.label || 'Si', { r, size, color: c.color || INK }); }
    return out;
  };
  S.band = (x, y, w, h, c = 'rgba(120,112,98,.55)') => add(rc.rectangle(x, y, w, h, o({ stroke: GRAY, strokeWidth: 3, strokeLineDash: [10, 8], fill: c, fillStyle: 'hachure', hachureGap: 14, fillWeight: 2.5, hachureAngle: 60 })));
  S.hill = (x0, yb, w, h, c = RED) => {   // the potential barrier drawn as a hill
    const pts = []; for (let k = 0; k <= 24; k++) { const u = k / 24; pts.push([x0 + w * u, yb - h * Math.exp(-Math.pow((u - 0.5) / 0.2, 2))]); }
    return add(rc.curve(pts, o({ stroke: c, strokeWidth: 6, roughness: 0.8 })));
  };
  S.glow = (x, y, r = 90) => add(rc.circle(x, y, r * 2, o({ stroke: 'none', fill: 'rgba(255,208,0,.55)', fillStyle: 'hachure', hachureGap: 8, fillWeight: 10, roughness: 2 })));
  S.chair = (x, y, { s = 1, empty = false } = {}) => {   // a theatre seat seen from the front; empty: red dashed
    const st = empty ? { stroke: RED, strokeLineDash: [8, 7] } : {};
    S.rect(x - 46 * s, y - 70 * s, 92 * s, 80 * s, { strokeWidth: 4.5, ...st }); S.rect(x - 56 * s, y + 10 * s, 112 * s, 30 * s, { strokeWidth: 4.5, ...st });
    S.line(x - 46 * s, y + 40 * s, x - 46 * s, y + 80 * s, { strokeWidth: 4, ...st }); S.line(x + 46 * s, y + 40 * s, x + 46 * s, y + 80 * s, { strokeWidth: 4, ...st });
  };
  S.person = (x, y, s = 1, c = INK) => {   // a seated stick figure whose seat is at (x, y)
    S.circle(x, y - 118 * s, 44 * s, { stroke: c, strokeWidth: 4.5 }); S.line(x, y - 96 * s, x, y - 10 * s, { stroke: c });
    S.path([[x - 32 * s, y - 70 * s], [x, y - 56 * s], [x + 32 * s, y - 70 * s]], { stroke: c, strokeWidth: 4.5 });
  };

  /* ---- build and draw ---- */
  function prep() {
    const defs = svg.firstChild;
    ITEMS.forEach((it, k) => {
      if (it.kind === 'stream') return;
      if (it.n.tagName === 'text') {
        // a line that runs off the page is shrunk to fit x 40-1000 (a safety net; size the copy so it never triggers)
        let b0 = it.n.getBBox();
        if (b0.width > 0 && (b0.x < 40 || b0.x + b0.width > 1000)) {
          const fs = +it.n.getAttribute('font-size'), sc = Math.min(1, 960 / b0.width);
          it.n.setAttribute('font-size', Math.floor(fs * sc)); b0 = it.n.getBBox();
          const dx = b0.x < 40 ? 40 - b0.x : b0.x + b0.width > 1000 ? 1000 - b0.x - b0.width : 0;
          if (dx) { it.n.setAttribute('x', +it.n.getAttribute('x') + dx); it.n.setAttribute('transform', (it.n.getAttribute('transform') || '').replace(/rotate\(([-\d.]+) ([-\d.]+) /, (m, r, x) => `rotate(${r} ${+x + dx} `)); }
          console.warn('sketch: text shrunk to fit the page:', it.n.textContent);
        }
        const b = it.n.getBBox(), cp = document.createElementNS(NS, 'clipPath'), r = document.createElementNS(NS, 'rect');
        cp.id = 'skc' + k; r.setAttribute('x', b.x - 10); r.setAttribute('y', b.y - 20); r.setAttribute('height', b.height + 40);
        cp.appendChild(r); defs.appendChild(cp); it.n.setAttribute('clip-path', `url(#skc${k})`); it.clip = r; it.w = b.width + 20;
      } else {
        for (const e of [...it.n.querySelectorAll('path')]) {
          const solid = (e.getAttribute('fill') || 'none') !== 'none';
          if (solid) continue;
          const d = (e.getAttribute('d') || '').trim();
          if (!d || /m/.test(d)) continue;
          const parts = d.split(/(?=M)/).map((s) => s.trim()).filter(Boolean);
          if (parts.length <= 1 || !parts.every((s) => s.startsWith('M'))) continue;
          const parent = e.parentNode;
          for (const subD of parts) {
            const clone = e.cloneNode(false);
            clone.setAttribute('d', subD);
            parent.insertBefore(clone, e);
          }
          parent.removeChild(e);
        }
        it.paths = [...it.n.querySelectorAll('path')].map((e) => {
          const solid = (e.getAttribute('fill') || 'none') !== 'none';
          if (solid) return { e, L: 0, solid: true, maskPath: null };
          const L = e.getTotalLength();
          const hasDash = !!(e.getAttribute('stroke-dasharray') || e.style.strokeDasharray);
          if (hasDash) {
            const mid = 'skm' + (maskSeq++), m = document.createElementNS(NS, 'mask');
            m.setAttribute('id', mid); m.setAttribute('maskUnits', 'userSpaceOnUse');
            m.setAttribute('x', '-2000'); m.setAttribute('y', '-2000'); m.setAttribute('width', '5000'); m.setAttribute('height', '5000');
            const mp = document.createElementNS(NS, 'path');
            mp.setAttribute('d', e.getAttribute('d') || '');
            mp.setAttribute('fill', 'none'); mp.setAttribute('stroke', '#fff');
            const sw = parseFloat(e.getAttribute('stroke-width')) || 5;
            mp.setAttribute('stroke-width', sw + 4); mp.setAttribute('stroke-linecap', 'round');
            mp.style.strokeDasharray = `${L} ${L}`; mp.style.strokeDashoffset = L;
            m.appendChild(mp); defs.appendChild(m); e.setAttribute('mask', `url(#${mid})`);
            return { e, L, solid: false, maskPath: mp };
          }
          e.style.strokeDasharray = `${L} ${L}`;
          return { e, L, solid: false, maskPath: null };
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
    for (const m of MOVES) moveAt(m, t);
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
      if (it.kind === 'fade') { it._vis = e * vis; it.n.style.opacity = it._vis; continue; }
      it._vis = p > 0 ? vis : 0;
      it.n.style.opacity = it._vis;
      if (it.kind === 'pop') continue;
      for (const q of it.paths) {
        if (q.solid) q.e.style.opacity = e;
        else if (q.maskPath) q.maskPath.style.strokeDashoffset = q.L * (1 - e);
        else q.e.style.strokeDashoffset = q.L * (1 - e);
      }
    }
    for (const st of STATES) {
      if (st.apply) st.apply(t, evalPartState(st, t));
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
