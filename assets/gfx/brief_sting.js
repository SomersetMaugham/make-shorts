/* Minimal Ink & Rule Sting for the `brief` theme (references/theme-brief.md).
   Pure seek-safe function of sting-local time s: BRIEF_STING.draw(canvas, s, opts).
   Outro (2.8 s): crimson cursor -> double editorial ink rules sweep outward -> Hahmlet 700 wordmark rises from
   baseline mask + crimson square period -> registration bar glides along bottom rule -> clean convergence close.
   Intro (1.4 s): subtle crimson registration sweep along the cover masthead hairline (never delays the hook). */
(function () {
  var ST = window.BRIEF_STING = window.BRIEF_STING || {};
  ST.DUR = { outro: 2.8, intro: 1.4 };

  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function easeOut(p) { p = clamp(p, 0, 1); return 1 - Math.pow(1 - p, 3); }
  function easeInOut(p) { p = clamp(p, 0, 1); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; }
  function prog(t, t0, dur, fn) { return (fn || easeOut)(clamp((t - t0) / (dur || 0.4), 0, 1)); }

  function rgba(hex, a) {
    var h = (hex || '#161618').replace('#', '');
    if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
    var n = parseInt(h, 16);
    return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + clamp(a, 0, 1).toFixed(3) + ')';
  }

  ST.draw = function (canvas, s, opts) {
    var ctx = canvas.getContext('2d');
    var W = canvas.width, H = canvas.height;
    ctx.clearRect(0, 0, W, H);
    opts = opts || {};
    var mode = opts.mode || 'outro';
    var dur = ST.DUR[mode] || 2.8;
    if (s < 0 || s > dur + 0.05) return;

    var accent = opts.accent || '#B42323';
    var ink = opts.ink || '#161618';

    if (mode === 'intro') {
      // Subtle editorial crimson registration glint sweeping left-to-right across the cover masthead bottom hairline
      var p = prog(s, 0.08, 0.95, easeInOut);
      var a = prog(s, 0.08, 0.16) * (1 - prog(s, 0.95, 0.28));
      if (a <= 0.01) return;
      var x0 = opts.x0 != null ? opts.x0 : 60;
      var span = opts.width != null ? opts.width : 960;
      var y = opts.y != null ? opts.y : 141;
      var barW = 136;
      var bx = x0 + (span - barW) * p;
      ctx.fillStyle = rgba(accent, a);
      ctx.fillRect(bx, y - 2, barW, 4);
      return;
    }

    // Outro: centered Minimal Ink & Rule Masthead Lockup
    var brand = opts.brand != null ? opts.brand : 'BRIEF';
    var tagline = opts.tagline != null ? opts.tagline : 'RESEARCH  ·  ANALYSIS  ·  INSIGHT';
    var cx = opts.x != null ? opts.x : W / 2;
    var cy = opts.y != null ? opts.y : 890;
    var boxW = opts.width != null ? opts.width : 680;
    var boxH = 216;
    var topY = cy - boxH / 2;
    var botY = cy + boxH / 2;

    var inRule = prog(s, 0.10, 0.55, easeOut);
    var outRule = prog(s, 2.20, 0.48, easeInOut);
    var ruleSpan = boxW * inRule * (1 - outRule);

    // 1) Registration corner ticks
    var tickA = prog(s, 0.40, 0.35) * (1 - prog(s, 2.05, 0.30));
    if (tickA > 0.01) {
      ctx.save();
      ctx.strokeStyle = rgba(ink, 0.28 * tickA);
      ctx.lineWidth = 2;
      var ox = boxW / 2 + 28, oy = boxH / 2 + 28, L = 18;
      var corners = [[-1, -1], [1, -1], [-1, 1], [1, 1]];
      for (var c = 0; c < corners.length; c++) {
        var sx = corners[c][0], sy = corners[c][1];
        var tx = cx + sx * ox, ty = cy + sy * oy;
        ctx.beginPath();
        ctx.moveTo(tx - sx * L, ty);
        ctx.lineTo(tx, ty);
        ctx.lineTo(tx, ty - sy * L);
        ctx.stroke();
      }
      ctx.restore();
    }

    // 2) Initial crimson vertical cursor
    var curIn = prog(s, 0.0, 0.14), curOut = prog(s, 0.32, 0.20);
    var curA = curIn * (1 - curOut);
    if (curA > 0.01) {
      ctx.fillStyle = rgba(accent, curA);
      ctx.fillRect(cx - 2, cy - 42 * curIn, 4, 84 * curIn);
    }

    // 3) Double editorial top rule + bottom rule
    if (ruleSpan > 1) {
      ctx.fillStyle = ink;
      ctx.fillRect(cx - ruleSpan / 2, topY, ruleSpan, 4);
      ctx.fillStyle = rgba(ink, 0.35);
      ctx.fillRect(cx - (ruleSpan * 0.92) / 2, topY + 10, ruleSpan * 0.92, 1.5);
      ctx.fillStyle = ink;
      ctx.fillRect(cx - ruleSpan / 2, botY, ruleSpan, 2);
    }

    // 4) Crimson registration slider along bottom rule during hold
    var scanP = prog(s, 1.05, 1.05, easeInOut);
    var scanA = prog(s, 1.05, 0.18) * (1 - prog(s, 1.98, 0.18));
    if (scanA > 0.01 && ruleSpan > 120) {
      var sw = 100;
      var rx = (cx - boxW / 2) + (boxW - sw) * scanP;
      ctx.fillStyle = rgba(accent, scanA);
      ctx.fillRect(rx, botY - 1.5, sw, 5);
    }

    // 5) Masked Hahmlet 700 wordmark + signature crimson square period
    var wIn = prog(s, 0.45, 0.50, easeOut);
    var wOut = prog(s, 2.02, 0.38, easeInOut);
    var wVis = wIn * (1 - wOut);
    if (wVis > 0.005) {
      ctx.save();
      ctx.beginPath();
      ctx.rect(cx - boxW / 2, topY + 24, boxW, boxH - 44);
      ctx.clip();
      var yOff = (1 - wIn) * 116 + wOut * 116;
      var fontSize = brand.length > 7 ? 96 : 124;
      ctx.font = '700 ' + fontSize + 'px Hahmlet, serif';
      ctx.fillStyle = rgba(ink, Math.min(1, wVis * 1.4));
      ctx.textAlign = 'left';
      ctx.textBaseline = 'middle';
      // Custom letter spacing for clean editorial tracking
      var track = fontSize * 0.07;
      var chars = Array.from(brand);
      var totalW = 0;
      for (var i = 0; i < chars.length; i++) {
        totalW += ctx.measureText(chars[i]).width + (i < chars.length - 1 ? track : 0);
      }
      var dotGap = 14, dotBase = 22;
      var startX = cx - (totalW + dotGap + dotBase) / 2;
      var curX = startX;
      for (var j = 0; j < chars.length; j++) {
        ctx.fillText(chars[j], curX, cy + 4 + yOff);
        curX += ctx.measureText(chars[j]).width + track;
      }
      var dIn = prog(s, 0.78, 0.24, easeOut);
      var dSz = dotBase * dIn * (1 - wOut);
      if (dSz > 0.5) {
        var dotCx = startX + totalW + dotGap + dotBase / 2;
        var dotCy = cy + fontSize * 0.27 + yOff;
        ctx.fillStyle = accent;
        ctx.fillRect(dotCx - dSz / 2, dotCy - dSz / 2, dSz, dSz);
      }
      ctx.restore();
    }

    // 6) Closing crimson square dot convergence
    var endDotA = prog(s, 2.38, 0.16) * (1 - prog(s, 2.62, 0.22));
    if (endDotA > 0.01) {
      ctx.fillStyle = rgba(accent, endDotA);
      ctx.fillRect(cx - 9, cy - 9, 18, 18);
    }

    // 7) Mono tagline beneath
    var sA = prog(s, 0.90, 0.35) * (1 - prog(s, 1.98, 0.25));
    if (sA > 0.01 && tagline) {
      ctx.font = '500 25px "Geist Mono", Pretendard, monospace';
      ctx.fillStyle = rgba('#666670', sA);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillText(tagline, cx, botY + 34);
    }
  };
})();
