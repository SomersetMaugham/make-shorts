// Where a cue's `say` asks for a pause, and whether the take has one there (local to create-video-shorts, not upstream).
// phrasing-check.mjs gives the heard pieces (Speech-to-Text of the take cut at its silences) and the silences' lengths;
// this lines the heard text up with `say` character by character and reports every expected break with no silence
// near it. It judges only where pauses fall, never words or delivery (SKILL.md: the one allowed STT use).
//
// An expected break: a comma, a `[pause short]` / `[pause]` / `[pause long]` tag, or a sentence end inside the line.
// A cue with "noPause": true expects breaks only at its tags and sentence ends (its commas are the user's call).

const MIN = { comma: 0.15, short: 0.15, pause: 0.4, long: 0.7, stop: 0.25 };
const KEEP = /[가-힣a-z0-9]/;

// say -> { chars: normalised spoken characters, breaks: [{at, kind, word}] }  (at = chars before the break)
export function expectedBreaks(say, { noPause = false } = {}) {
  const s = say.toLowerCase(); let chars = ''; const breaks = [];
  const add = (kind) => {
    if (!chars.length) return;
    const last = breaks[breaks.length - 1];
    const word = (say.slice(0, i).replace(/\[[^\]]*\]/g, '').trim().split(/\s+/).pop() || '');
    if (last && last.at === chars.length) { if (MIN[kind] > MIN[last.kind]) last.kind = kind; return; }
    breaks.push({ at: chars.length, kind, word });
  };
  let i = 0;
  while (i < s.length) {
    const c = s[i];
    if (c === '[') {
      const j = s.indexOf(']', i); const tag = s.slice(i + 1, j < 0 ? s.length : j).trim();
      i = j < 0 ? s.length : j + 1;
      if (tag === 'pause short') add('short'); else if (tag === 'pause') add('pause'); else if (tag === 'pause long') add('long');
      continue;
    }
    i++;
    if (c === ',' && !(/\d/.test(s[i - 2] || '') && /\d/.test(s[i] || ''))) { if (!noPause) add('comma'); }
    else if (/[.?!]/.test(c) && !(/\d/.test(s[i - 2] || '') && /\d/.test(s[i] || ''))) add('stop');
    else if (KEEP.test(c)) chars += c;
  }
  return { chars, breaks: breaks.filter((b) => b.at < chars.length) };
}

// Levenshtein alignment: for every position 0..a.length of a, the matching position in b.
function align(a, b) {
  const n = a.length, m = b.length, D = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
  for (let x = 0; x <= n; x++) D[x][0] = x;
  for (let y = 0; y <= m; y++) D[0][y] = y;
  for (let x = 1; x <= n; x++) for (let y = 1; y <= m; y++)
    D[x][y] = Math.min(D[x - 1][y] + 1, D[x][y - 1] + 1, D[x - 1][y - 1] + (a[x - 1] === b[y - 1] ? 0 : 1));
  const map = new Array(n + 1); let x = n, y = m; map[n] = m;
  while (x > 0 || y > 0) {
    if (x > 0 && y > 0 && D[x][y] === D[x - 1][y - 1] + (a[x - 1] === b[y - 1] ? 0 : 1)) { x--; y--; }
    else if (x > 0 && D[x][y] === D[x - 1][y] + 1) x--;
    else y--;
    if (map[x] === undefined) map[x] = y;
  }
  return map;
}

// pieces: heard text between silences; gaps: the silences' lengths (pieces.length - 1 of them).
// -> { missing: [{word, kind, need, got}], unknown: reason | null }
export function judgeBreaks(say, pieces, gaps, opts = {}) {
  if (pieces.some((p) => /^ERR/.test(p))) return { missing: [], unknown: 'speech-to-text failed on a piece' };
  const exp = expectedBreaks(say, opts);
  let heard = ''; const at = [];                       // heard-character position of each silence
  pieces.forEach((p, k) => {
    heard += [...p.toLowerCase()].filter((c) => KEEP.test(c)).join('');
    if (k < gaps.length) at.push(heard.length);
  });
  if (!heard.length) return { missing: [], unknown: 'nothing heard' };
  const map = align(exp.chars, heard);
  const missing = [];
  for (const b of exp.breaks) {
    const pos = map[b.at], tol = 1;                     // STT respells a word: one character of slack
    let got = 0;
    at.forEach((p, k) => { if (Math.abs(p - pos) <= tol) got = Math.max(got, gaps[k]); });
    if (got < MIN[b.kind]) missing.push({ word: b.word, kind: b.kind, need: MIN[b.kind], got: +got.toFixed(2) });
  }
  return { missing, unknown: null };
}
