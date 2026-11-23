/* The Sungkim theme (references/theme-sungkim.md): a warm paper page with a header (kicker + one-line title), a visual
   box, a source line and up to three info cards that stack in as the narration names them. scripts/sungkim_kit.py
   writes the page; everything here is a pure function of the run time t (engine.js calls window.CFG_RENDER(t)). */
(function () {
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, p) => a + (b - a) * p;
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const easeOut = (p) => 1 - Math.pow(1 - p, 3);
  const prog = (t, t0, d, e) => (e || ease)(clamp((t - t0) / (d || 0.4), 0, 1));
  window.REEL = { clamp, lerp, ease, easeOut, prog };

  // the title stays on one line: from 78 px down by 2 px until it fits (at least 48 px); measured once per page
  let fitted = false;
  function fitTitle() {
    const el = document.getElementById('skTitle');
    if (!el) return;
    let size = 78;
    el.style.fontSize = size + 'px';
    while (el.scrollWidth > el.clientWidth && size > 48) { size -= 2; el.style.fontSize = size + 'px'; }
    fitted = true;
  }
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitTitle);

  window.CFG_RENDER = function (t) {
    const S = (window.CFG || {}).sungkim || {};
    if (!fitted) fitTitle();
    // run 0: frame 0 is the cover, so the header and the visual box appear from the second frame
    if (S.coverSafe) {
      const show = t > 0.012 ? 1 : 0;
      ['skHdr', 'skVis', 'skSrc'].forEach((id) => { const el = document.getElementById(id); if (el) el.style.opacity = show; });
    }
    // info cards: a card with t0 <= 0 is in place on frame 0; a later one rises 24 px and fades in over 0.24 s
    (S.cards || []).forEach((c, i) => {
      const el = document.getElementById('skCard' + i);
      if (!el) return;
      const p = c.t0 <= 0.02 ? 1 : prog(t, c.t0, 0.24, easeOut);
      el.style.opacity = p;
      el.style.transform = `translateY(${(1 - p) * 24}px)`;
    });
    if (window.TOP_RENDER) window.TOP_RENDER(t);
  };
})();
