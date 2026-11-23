/* Outro / intro stings (the user chose the pixel lightbulb, 2026-11-24; designed by agy Neon high).
   A sting is a pure function of its own time s (0..3): it returns cells [x, y, colour, alpha] on a 24x24 grid.
   STING.draw(canvas, name, s, colours) paints it; a page calls it from its render hook with s = t - t0.
   The lightbulb: the ink outline draws bottom-up (0-0.6 s), the filament and the glow light (0.5-1.0 s), rays
   twinkle (0.9-2.0 s), the pixels lift away like embers (2.0-2.95 s). */
(function(){
  var STING = window.STING = window.STING || {};
  var O = {N: 24, C: {teal: '#0F786C', gold: '#F0B429', red: '#D9483B', ink: '#16181D'},
    rnd: function(i){ var x = Math.sin(i * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); },
    ease: function(p){ p = Math.max(0, Math.min(1, p)); return p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; },
    clamp: function(v, a, b){ return Math.max(a, Math.min(b, v)); }};
  var N = O.N, C = O.C;
  STING.DUR = {bulb: 3.0};
  function clean(cells) {
    var map = {}, order = [], out = [];
    for (var i = 0; i < cells.length; i++) {
      var p = cells[i];
      var x = Math.round(p[0]), y = Math.round(p[1]);
      var a = O.clamp(p[3] == null ? 1 : p[3], 0, 1);
      if (x < 0 || x >= N || y < 0 || y >= N || a <= 0.01) continue;
      var k = x + y * N;
      if (!(k in map)) order.push(k);
      map[k] = [x, y, p[2], a];
    }
    for (var j = 0; j < order.length; j++) out.push(map[order[j]]);
    return out;
  }

  // Smooth ease-out helper for snappy yet organic motion
  function easeOut(p) {
    p = O.clamp(p, 0, 1);
    return 1 - Math.pow(1 - p, 3);
  }

  // ---------------------------------------------------------------------------
  // 1. 픽셀 전구 (Pixel Lightbulb)
  // Ink contour draws bottom-up, red filament & gold glow ignite, rays twinkle,
  // then pixels lift away upward like warm embers.
  // ---------------------------------------------------------------------------
  var BULB_BASE_CONTOUR = (function(){
    var left = [
      [11,20],[10,20],[9,19],[10,19],[11,19],
      [8,18],[8,17],[8,16],[9,16],[10,16],[11,16],
      [8,15],[8,14],[7,13],[6,12],[5,11],[5,10],[5,9],[5,8],[5,7],[6,6],[7,5],[8,5],[9,4],[10,4],[11,4]
    ];
    var list = [];
    for (var i = 0; i < left.length; i++) {
      var p = left[i], frac = i / (left.length - 1);
      list.push({x: p[0], y: p[1], f: frac});
      list.push({x: 23 - p[0], y: p[1], f: frac});
    }
    return list;
  })();

  var BULB_FILL = (function(){
    var spans = {
      5:[9,14], 6:[7,16], 7:[6,17], 8:[6,17], 9:[6,17],
      10:[6,17], 11:[6,17], 12:[7,16], 13:[8,15], 14:[9,14], 15:[9,14]
    };
    var filament = {
      '10,9':1,'13,9':1,'10,10':1,'13,10':1,
      '11,11':1,'12,11':1,'11,12':1,'12,12':1,'11,13':1,'12,13':1,'11,14':1,'12,14':1
    };
    var highlight = {'8,6':1,'7,7':1};
    var list = [];
    for (var y = 5; y <= 15; y++) {
      var r = spans[y];
      for (var x = r[0]; x <= r[1]; x++) {
        var key = x + ',' + y;
        if (highlight[key]) continue;
        var isFil = !!filament[key];
        var dx = x - 11.5, dy = y - 10.5;
        list.push({
          x: x, y: y,
          col: isFil ? C.red : C.gold,
          fil: isFil,
          dist: Math.sqrt(dx * dx + dy * dy)
        });
      }
    }
    return list;
  })();

  var BULB_RAYS = [
    [11,2,0,-1,C.gold,0],[12,2,0,-1,C.gold,0],[11,1,0,-1,C.gold,0],[12,1,0,-1,C.gold,0],
    [4,4,-1,-1,C.red,1],[3,3,-1,-1,C.red,1],[19,4,1,-1,C.red,1],[20,3,1,-1,C.red,1],
    [3,9,-1,0,C.teal,0],[2,9,-1,0,C.teal,0],[1,9,-1,0,C.teal,0],
    [20,9,1,0,C.teal,0],[21,9,1,0,C.teal,0],[22,9,1,0,C.teal,0],
    [4,13,-1,1,C.gold,1],[3,14,-1,1,C.gold,1],[19,13,1,1,C.gold,1],[20,14,1,1,C.gold,1]
  ];

  STING.bulb = function(t) {
      if (t <= 0.02 || t >= 2.95) return [];
      var cells = [];

      // Rising ember exit helper (top pixels lift first, drifting upward & dispersing)
      function emit(x, y, col, a, seed) {
        if (a <= 0.01) return;
        if (t > 2.04) {
          var start = 2.04 + ((y / 22) * 0.34) + O.rnd(seed) * 0.14;
          var q = O.clamp((t - start) / 0.42, 0, 1);
          if (q > 0) {
            var qe = q * q;
            var driftX = Math.round((O.rnd(seed + 19) - 0.5) * 7 * q);
            var driftY = -Math.round(qe * 8 + q * 2);
            cells.push([x + driftX, y + driftY, col, a * (1 - q)]);
            return;
          }
        }
        cells.push([x, y, col, a]);
      }

      // 1) Ink outline draws symmetrically bottom-to-top (0.03..0.60s)
      var drawP = easeOut((t - 0.03) / 0.57);
      for (var i = 0; i < BULB_BASE_CONTOUR.length; i++) {
        var b = BULB_BASE_CONTOUR[i];
        var a = O.clamp((drawP - b.f * 0.86) / 0.14, 0, 1);
        emit(b.x, b.y, C.ink, a, b.x * 17 + b.y * 31);
      }

      // 2) Teal collar bands snap in (0.16..0.48s)
      var collarP = O.ease((t - 0.16) / 0.32);
      for (var cy = 17; cy <= 18; cy++) {
        for (var cx = 9; cx <= 14; cx++) {
          var distMid = Math.abs(cx - 11.5) / 3;
          var ca = O.clamp((collarP - distMid * 0.45) / 0.55, 0, 1);
          emit(cx, cy, C.teal, ca, cx * 23 + cy * 41);
        }
      }

      // 3) Red filament ignites (0.52..0.76s), then gold glow blooms radially (0.72..1.00s)
      var filP = O.ease((t - 0.52) / 0.24);
      var glowP = O.ease((t - 0.72) / 0.28);
      for (var j = 0; j < BULB_FILL.length; j++) {
        var f = BULB_FILL[j];
        var fa;
        if (f.fil) {
          var rowFrac = (14 - f.y) / 6;
          fa = O.clamp((filP - rowFrac * 0.55) / 0.45, 0, 1);
        } else {
          var radFrac = f.dist / 7.2;
          fa = O.clamp((glowP - radFrac * 0.72) / 0.28, 0, 1);
        }
        emit(f.x, f.y, f.col, fa, f.x * 37 + f.y * 13);
      }

      // Subtle filament spark accent during held state (1.32..1.68s)
      if (t >= 1.32 && t <= 1.68) {
        var sp = Math.sin(O.clamp((t - 1.32) / 0.36, 0, 1) * Math.PI);
        if (sp > 0.35) {
          emit(11, 9, C.red, sp, 701);
          emit(12, 9, C.red, sp, 702);
        }
      }

      // 4) Outer pixel rays shoot out (0.86..1.04s), twinkle gently during hold, pop off (2.00..2.26s)
      if (t > 0.86 && t < 2.30) {
        var rayIn = O.ease((t - 0.86) / 0.18);
        var rayOut = t > 2.00 ? O.clamp((t - 2.00) / 0.26, 0, 1) : 0;
        var beat0 = (t > 1.18 && t < 1.50) ? 1 : 0;
        var beat1 = (t > 1.52 && t < 1.84) ? 1 : 0;
        for (var r = 0; r < BULB_RAYS.length; r++) {
          var ry = BULB_RAYS[r];
          var shift = (ry[5] === 0 ? beat0 : beat1);
          var inOff = Math.round((1 - rayIn) * -1);
          var outOff = Math.round(rayOut * 2);
          var rx = ry[0] + ry[2] * (inOff + shift + outOff);
          var ryy = ry[1] + ry[3] * (inOff + shift + outOff);
          var ra = rayIn * (1 - rayOut);
          cells.push([rx, ryy, ry[4], ra]);
        }
      }

      return clean(cells);
  };

  STING.draw = function (canvas, name, s, colours) {
    var g = canvas.getContext('2d'), cell = canvas.width / N;
    g.clearRect(0, 0, canvas.width, canvas.height);
    if (s < 0 || s > (STING.DUR[name] || 3)) return;
    if (colours) { for (var k in colours) C[k] = colours[k]; }
    (STING[name](s) || []).forEach(function (p) {
      g.globalAlpha = p[3] == null ? 1 : p[3]; g.fillStyle = p[2];
      g.fillRect(Math.round(p[0] * cell), Math.round(p[1] * cell), Math.ceil(cell * 0.9), Math.ceil(cell * 0.9));
    });
    g.globalAlpha = 1;
  };
})();
