/* The code-reel theme (references/theme-reel.md): a fixed header, a diagram card on top (#top), a divider and a code
   card below (#code) whose white highlight box follows the narration. scripts/reel_kit.py writes the page.
   Everything is a pure function of the run time t: engine.js calls window.CFG_RENDER(t) every frame.
   A run's own diagram code defines window.TOP_RENDER(t) (and may read window.REEL helpers). */
(function () {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);          // cubic in-out
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  // progress 0..1 of a tween that starts at t0 and lasts d seconds
  const prog = (t, t0, d, e) => (e || ease)(clamp((t - t0) / (d || 0.4), 0, 1));
  window.REEL = { clamp, lerp, ease, easeOut, prog };

  function codeRender(t) {
    const R = (window.CFG || {}).reel || {};
    const LH = R.lh || 54, TOP0 = R.top0 || 70;   // code line height and first-line offset inside #code (px), from reel_kit.py
    const hl = R.hl || [];
    const lines = document.querySelectorAll('#code .ln');
    const box = document.getElementById('hlbox');
    if (!box) return;
    // the active highlight: the last entry whose time has come; a move to it lasts 0.35 s
    let i = -1;
    for (let k = 0; k < hl.length; k++) if (t >= hl[k].t) i = k;
    const span = (e) => (e && e.lines && e.lines.length ? [Math.min(...e.lines), Math.max(...e.lines)] : null);
    const cur = i >= 0 ? span(hl[i]) : null, prev = i > 0 ? span(hl[i - 1]) : null;
    // an entry at the run's start is already in place on frame 0 (the landing state), never fading in
    const p = i >= 0 ? (i === 0 && hl[0].t < 0.05 ? 1 : prog(t, hl[i].t, 0.35)) : 1;
    let a, b, op;
    if (cur && prev) { a = lerp(prev[0], cur[0], p); b = lerp(prev[1], cur[1], p); op = 1; }
    else if (cur) { a = cur[0]; b = cur[1]; op = p; }
    else if (prev) { a = prev[0]; b = prev[1]; op = 1 - p; }
    else { a = 1; b = 1; op = 0; }
    box.style.top = (TOP0 + (a - 1) * LH - 6) + 'px';
    box.style.height = ((b - a + 1) * LH + 12) + 'px';
    box.style.opacity = op;
    // lines outside the box dim to 0.32 while a box is up
    lines.forEach((el, k) => {
      const n = k + 1, inside = cur && n >= cur[0] && n <= cur[1], wasIn = prev && n >= prev[0] && n <= prev[1];
      const on = cur ? (inside ? 1 : 0.32) : 1, was = prev ? (wasIn ? 1 : 0.32) : (cur ? 1 : 1);
      el.style.opacity = i >= 0 ? lerp(i > 0 ? was : 1, on, p) : 1;
    });
  }

  window.CFG_RENDER = function (t) {
    const R = (window.CFG || {}).reel || {};
    // r0 only: frame 0 is the cover, so the header and the top card stay out of the first frame
    if (R.coverSafe) {
      const show = t > 0.012 ? 1 : 0;
      ['hdr', 'top'].forEach((id) => { const el = document.getElementById(id); if (el) el.style.opacity = show; });
    }
    codeRender(t);
    if (window.TOP_RENDER) window.TOP_RENDER(t);
  };
})();
