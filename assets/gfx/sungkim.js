/* The Sungkim theme (references/theme-sungkim.md): runtime for pages written by scripts/sungkim_kit.py.
   Everything is a pure function of the run time t (engine.js calls window.CFG_RENDER(t)):
   [data-t]     lands at t: fades in and rises 16 px over 0.4 s (0 = in place on frame 0)
   [data-fill]  a bar fills to its value from data-t over data-dur s
   [data-u]     a unit square takes its colour data-c at t
   [data-sweep] a red underline under a cited sentence sweeps in from the left at t over 0.5 s */
(function () {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  const prog = (t, t0, d, e) => (e || ease)(clamp((t - t0) / (d || 0.4), 0, 1));
  window.REEL = { clamp, lerp, ease, easeOut, prog };

  // the title stays on one line: from 112 px down by 2 px until it fits (at least 72 px); measured once
  let fitted = false;
  function fitTitle() {
    const el = document.getElementById('skTitle');
    if (!el) return;
    let size = 112;
    el.style.fontSize = size + 'px';
    while (el.scrollWidth > el.clientWidth && size > 72) { size -= 2; el.style.fontSize = size + 'px'; }
    fitted = true;
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitTitle);

  window.CFG_RENDER = function (t) {
    if (!fitted) fitTitle();
    document.querySelectorAll('[data-t]').forEach((el) => {
      const t0 = parseFloat(el.dataset.t);
      const p = t0 <= 0.02 ? 1 : prog(t, t0, 0.4, easeOut);
      el.style.opacity = p;
      if (!el.dataset.fill) el.style.transform = `translateY(${((1 - p) * 16).toFixed(2)}px)`;
    });
    document.querySelectorAll('[data-fill]').forEach((el) => {
      const p = prog(t, parseFloat(el.dataset.t), parseFloat(el.dataset.dur || 1.2), easeOut);
      el.style.opacity = 1;
      el.style.width = (parseFloat(el.dataset.fill) * 100 * p).toFixed(2) + '%';
    });
    document.querySelectorAll('[data-u]').forEach((el) => {
      el.style.background = t >= parseFloat(el.dataset.u) ? el.dataset.c : '';
    });
    document.querySelectorAll('[data-sweep]').forEach((el) => {      // a red underline under a cited sentence
      el.style.transform = `scaleX(${prog(t, parseFloat(el.dataset.sweep), 0.5, easeOut).toFixed(3)})`;
    });
    if (window.TOP_RENDER) window.TOP_RENDER(t);
  };
})();
