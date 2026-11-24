/* The Brief theme (references/theme-brief.md): runtime for pages written by scripts/brief_kit.py.
   Everything is a pure seek-safe function of the run time t (engine.js calls window.CFG_RENDER(t)):
   [data-t]      card lands at t: fades in and rises 14 px over 0.38 s (<= 0.02 = in place on frame 0)
   [data-rule]   editorial accent rule draws in cleanly (scaleX for top rule, scaleY for left bar)
   [data-count]  number_card rolls smoothly from data-from to data-to over data-dur s
   [data-fill]   comparison bar fills to its value from data-t over data-dur s
   [data-u]      unit square takes its colour data-c at t
   [data-sweep]  capture highlight wash / underline sweeps in from left at t over 0.48 s */
(function () {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  const prog = (t, t0, d, e) => (e || ease)(clamp((t - t0) / (d || 0.38), 0, 1));
  window.REEL = { clamp, lerp, ease, easeOut, prog };

  // Section title stays on one line: from 84 px down by 2 px until it fits (min 56 px); measured once after fonts load
  let fitted = false;
  function fitTitle() {
    const el = document.getElementById('brTitle');
    if (!el) return;
    let size = 84;
    el.style.fontSize = size + 'px';
    while (el.scrollWidth > el.clientWidth && size > 56) { size -= 2; el.style.fontSize = size + 'px'; }
    fitted = true;
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitTitle);

  function fmtNum(val, dec, comma) {
    const fixed = dec > 0 ? val.toFixed(dec) : String(Math.round(val));
    if (!comma) return fixed;
    const parts = fixed.split('.');
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return parts.join('.');
  }

  window.CFG_RENDER = function (t) {
    if (!fitted) fitTitle();
    document.querySelectorAll('[data-t]').forEach((el) => {
      if (el.dataset.fill || el.dataset.count) return;
      const t0 = parseFloat(el.dataset.t);
      const p = t0 <= 0.02 ? 1 : prog(t, t0, 0.38, easeOut);
      el.style.opacity = p;
      el.style.transform = `translateY(${((1 - p) * 14).toFixed(2)}px)`;
    });
    document.querySelectorAll('[data-rule]').forEach((el) => {
      const t0 = parseFloat(el.dataset.rule);
      const p = t0 <= 0.02 ? 1 : prog(t, t0, 0.42, easeOut);
      const axis = el.dataset.axis || 'x';
      el.style.transform = axis === 'y' ? `scaleY(${p.toFixed(3)})` : `scaleX(${p.toFixed(3)})`;
    });
    document.querySelectorAll('[data-count]').forEach((el) => {
      const t0 = parseFloat(el.dataset.t || 0);
      const dur = parseFloat(el.dataset.dur || 0.9);
      const p = t0 <= 0.02 && dur <= 0.02 ? 1 : prog(t, t0, dur, easeOut);
      const v0 = parseFloat(el.dataset.from);
      const v1 = parseFloat(el.dataset.to);
      const dec = parseInt(el.dataset.dec || '0', 10);
      const comma = el.dataset.comma === '1';
      el.textContent = (el.dataset.prefix || '') + fmtNum(lerp(v0, v1, p), dec, comma) + (el.dataset.suffix || '');
    });
    document.querySelectorAll('[data-fill]').forEach((el) => {
      const p = prog(t, parseFloat(el.dataset.t), parseFloat(el.dataset.dur || 1.15), easeOut);
      el.style.opacity = 1;
      el.style.width = (parseFloat(el.dataset.fill) * 100 * p).toFixed(2) + '%';
    });
    document.querySelectorAll('[data-u]').forEach((el) => {
      el.style.background = t >= parseFloat(el.dataset.u) ? el.dataset.c : '';
    });
    document.querySelectorAll('[data-sweep]').forEach((el) => {
      el.style.transform = `scaleX(${prog(t, parseFloat(el.dataset.sweep), 0.48, easeOut).toFixed(3)})`;
    });
    (((window.CFG || {}).brief || {}).stings || []).forEach((st, i) => {
      const cv = document.getElementById('brSting' + i);
      const cov = document.getElementById('brStingCover' + i);
      if (cov) cov.style.opacity = prog(t, st.t0 - 0.35, 0.35, easeOut);
      if (cv && window.BRIEF_STING) window.BRIEF_STING.draw(cv, t - st.t0, st);
    });
    if (window.TOP_RENDER) window.TOP_RENDER(t);
  };
})();
