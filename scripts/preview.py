"""The browser preview: work/index.html plays every short as it will look, before any MP4 is rendered.
usage: python scripts/preview.py [s1 s2 ...]          (every short in cut.json when none is given; run inside work/)

What it is: one page that stacks each run's HyperFrames composition (gfx/<sk>_r<i>.html) as an iframe and drives it
by the narration's clock, with the captions, keyword chips and cover drawn on top exactly where compose.py puts them
(same font, sizes, positions and chip animation; drawn by the browser instead of PIL, so a pixel can differ). The sound is
the narration timeline (narration/<sk>/audio/narration.mp3, the file voice.wav is made from); before recording it is silent and the timeline is the
placeholders' estimate. The compositions are the live pages, so a graphics fix shows after build_gfx.py and a reload,
with no render at all. What the preview does not show: motion blur (it comes from the 240 fps render).

Open it in Chrome by double-click (file:// works: the page talks to the compositions by postMessage). Keys: space
play/pause, left/right 1 s, shift+left/right 5 s, [ / ] previous / next run, 0 the start. ?s=s2 opens another short and
?t=12.5 seeks there (handy for screenshots: headless Chrome with ?t= and &still). The corner shows the run id and the
time inside the run, so a change request can name "s1_r12 at 3.2 s".

The MP4 is the user's to render, with render.py (240 fps graphics with motion blur, the master, the composite)."""
import json, os, sys

sys.path.insert(0, 'scripts'); import config as Cfg

C = json.load(open('cut.json', encoding='utf-8')); S = json.load(open('shorts.json', encoding='utf-8'))
want = sys.argv[1:] or [k for k in S if k in C]
data = {}
for sk in want:
    c, sh = C[sk], S[sk]
    capf = f'{sk}/captions.json'
    if not os.path.exists(capf):
        raise SystemExit(f'{sk}: no {capf} - run prep.sh {sk} first')
    caps = json.load(open(capf, encoding='utf-8'))
    top = {L['id'] for L in sh['lines'] if L.get('caption') == 'top'}
    runs = [dict(i=r['i'], T0=r['T0'], T1=r['T1'], scene=r.get('scene', ''), src=f'gfx/{sk}_r{r["i"]}.html',
                 capY=(365 + 634) / 2 if any(l in top for l in r['lines']) else (1290 + 1560) / 2,
                 ok=os.path.exists(f'gfx/{sk}_r{r["i"]}.html')) for r in c['runs']]
    audio = f'narration/{sk}/audio/narration.mp3'      # tts.mjs lays it out with t = 0 = the video's t = 0 (what voice.wav is made from)
    data[sk] = dict(title=sh.get('title', ''), cover=sh.get('cover', [sh.get('title', '')]), accent=sh.get('accent', 'azure'),
                    END=c['END'], runs=runs, caps=caps, audio=audio if os.path.exists(audio) else None,
                    placeholder=bool(c.get('narration', {}).get('placeholder')))
missing = [f'{sk}_r{r["i"]}' for sk, d in data.items() for r in d['runs'] if not r['ok']]

HTML = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>Shorts preview</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{font-family:Pretendard;src:url(fonts/PretendardVariable.ttf);font-weight:45 920}
:root{--bg:#0B0C0E;--panel:#18191C;--line:rgba(255,255,255,.12);--text:#fff;--muted:#A3A6AD;--azure:#2F95FF;--ember:#FF8A5B;--mint:#4FD6A0;--iris:#9C7CFF}
html,body{margin:0;height:100%;background:var(--bg);color:var(--text);font-family:Pretendard,system-ui,sans-serif;overflow:hidden}
#wrap{position:absolute;inset:0 0 64px 0;display:flex;align-items:center;justify-content:center}
#stage{position:relative;flex:none;width:1080px;height:1920px;transform-origin:center center;background:#111214;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.6)}
#stage iframe{position:absolute;left:0;top:0;width:1080px;height:1920px;border:0;visibility:hidden;pointer-events:none}
#stage iframe.on{visibility:visible}
#caps{position:absolute;inset:0;pointer-events:none}
.cap{position:absolute;left:0;right:0;text-align:center;font:700 74px/88px Pretendard;color:#fff;
  -webkit-text-stroke:20px #0B0C0E;paint-order:stroke fill;word-spacing:16px;white-space:nowrap}
.chip{position:absolute;left:50%;padding:26px 40px 26px;border-radius:28px;background:rgba(24,25,28,.88);
  border:2px solid var(--acc-line);box-shadow:0 50px 120px -40px rgba(0,0,0,.8),0 0 60px -10px var(--acc-glow),inset 0 1.5px 0 rgba(255,255,255,.09);
  font:600 70px/1 Pretendard;letter-spacing:-.025em;color:#fff;white-space:nowrap}
.chip .ln{display:block;height:5px;margin-top:22px;border-radius:3px;background:var(--acc);box-shadow:0 0 14px var(--acc);transform-origin:0 50%}
#cover{position:absolute;left:50%;top:432px;transform:translate(-50%,-50%);padding:44px 56px;border-radius:36px;background:rgba(24,25,28,.94);
  border:2px solid var(--acc-line);box-shadow:0 50px 120px -40px rgba(0,0,0,.82),0 0 70px -10px var(--acc-glow);text-align:center;
  font:600 104px/1.08 Pretendard;letter-spacing:-.03em;white-space:nowrap;display:none}
#cover .ln{height:6px;margin-top:26px;border-radius:3px;background:var(--acc);box-shadow:0 0 16px var(--acc)}
#hud{position:absolute;left:12px;top:10px;font:500 13px/1.4 ui-monospace,Menlo,monospace;color:var(--muted);background:rgba(0,0,0,.45);padding:6px 9px;border-radius:8px;z-index:5}
#bar{position:absolute;left:0;right:0;bottom:0;height:64px;display:flex;align-items:center;gap:12px;padding:0 16px;background:var(--panel);border-top:1px solid var(--line);box-sizing:border-box}
#bar button,#bar select{background:#212226;color:#fff;border:1px solid var(--line);border-radius:8px;height:36px;padding:0 12px;font:500 14px Pretendard;cursor:pointer}
#seek{flex:1;accent-color:var(--azure)}
#time{font:500 13px ui-monospace,Menlo,monospace;color:var(--muted);min-width:118px;text-align:right}
#warn{position:absolute;right:12px;top:10px;font:500 13px Pretendard;color:#111;background:#FFD27A;padding:6px 10px;border-radius:8px;z-index:5;display:none}
</style></head><body>
<div id="wrap"><div id="stage"><div id="caps"></div><div id="cover"></div></div></div>
<div id="hud"></div><div id="warn"></div>
<div id="bar"><button id="play">재생</button><select id="pick"></select><input id="seek" type="range" min="0" max="1000" value="0"><span id="time"></span></div>
<audio id="aud" preload="auto"></audio>
<script>
const DATA = __DATA__, MISSING = __MISSING__;
const ACC = {azure:[47,149,255], ember:[255,138,91], mint:[79,214,160], iris:[156,124,255]};
const q = new URLSearchParams(location.search);
const sk = DATA[q.get('s')] ? q.get('s') : Object.keys(DATA)[0];
const D = DATA[sk], stage = document.getElementById('stage'), caps = document.getElementById('caps');
const aud = document.getElementById('aud'), seek = document.getElementById('seek'), hud = document.getElementById('hud');
const a = ACC[D.accent] || ACC.azure;
stage.style.setProperty('--acc', `rgb(${a})`); stage.style.setProperty('--acc-line', `rgba(${a},.33)`); stage.style.setProperty('--acc-glow', `rgba(${a},.55)`);
document.title = `${sk} · ${D.title}`;
const pick = document.getElementById('pick');
for (const k of Object.keys(DATA)) { const o = document.createElement('option'); o.value = k; o.textContent = `${k} · ${DATA[k].title}`; if (k === sk) o.selected = true; pick.appendChild(o); }
pick.onchange = () => { location.search = '?s=' + pick.value; };
const warn = document.getElementById('warn');
const notes = [];
if (D.placeholder) notes.push('내레이션 녹음 전: 무음, 길이는 추정치');
if (!D.audio) notes.push('내레이션 오디오 없음: prep.sh를 먼저 실행');
const miss = MISSING.filter((m) => m.startsWith(sk + '_'));
if (miss.length) notes.push('그래픽 없음: ' + miss.join(', '));
if (notes.length) { warn.textContent = notes.join(' · '); warn.style.display = 'block'; }

// one iframe per run, all loaded up front; the visible one gets the run-relative time every frame
const frames = D.runs.map((r) => { const f = document.createElement('iframe'); if (r.ok) f.src = r.src; stage.insertBefore(f, caps); return f; });
// captions and chips, as compose.py draws them
const chunkEls = D.caps.map((c) => {
  const el = document.createElement('div');
  if (c.hl) { el.className = 'chip'; el.innerHTML = `<span class="tx"></span><span class="ln"></span>`; el.querySelector('.tx').textContent = c.text; }
  else { el.className = 'cap'; el.textContent = c.text; }
  el.style.display = 'none'; caps.appendChild(el); return el;
});
const cover = document.getElementById('cover');
cover.innerHTML = D.cover.map((l) => `<div>${l.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</div>`).join('') + '<div class="ln"></div>';
if (D.audio) aud.src = D.audio;

function fit() { const w = innerWidth, h = innerHeight - 64; const s = Math.min(w / 1080, h / 1920) * 0.96; stage.style.transform = `scale(${s})`; }
addEventListener('resize', fit); fit();

let clock = 0, playing = false, last = null;
const runAt = (t) => { for (let k = 0; k < D.runs.length; k++) if (t < D.runs[k].T1 - 1e-6) return k; return D.runs.length - 1; };
const pw3 = (p) => 1 - Math.pow(1 - Math.min(1, Math.max(0, p)), 3);
function draw(t) {
  const k = runAt(t), r = D.runs[k];
  frames.forEach((f, j) => f.classList.toggle('on', j === k));
  try { frames[k].contentWindow.postMessage({ hfT: Math.max(0, t - r.T0) }, '*'); } catch (e) {}
  D.caps.forEach((c, j) => {
    const el = chunkEls[j], on = t > 0 && c.t0 <= t + 1e-6 && t < c.t1;
    el.style.display = on ? 'block' : 'none';
    if (!on) return;
    const y = r.capY;
    if (c.hl) {
      const tr = t - c.t0, pin = Math.min(1, tr / 0.18), e = pw3(pin);
      el.style.top = y + 'px';
      el.style.transform = `translate(-50%, calc(-50% + ${12 * (1 - e)}px)) scale(${0.96 + 0.04 * e})`;
      el.style.opacity = Math.min(1, pin * 1.6);
      el.querySelector('.ln').style.transform = `scaleX(${pw3((tr - 0.08) / 0.32)})`;
    } else { el.style.top = (y - 44) + 'px'; }
  });
  cover.style.display = t < 0.05 ? 'block' : 'none';
  hud.textContent = `${sk}_r${r.i} · ${r.scene} · ${(t - r.T0).toFixed(2)} s in run · ${t.toFixed(2)} / ${D.END.toFixed(2)} s`;
  seek.value = Math.round(t / D.END * 1000);
  document.getElementById('time').textContent = `${fmt(t)} / ${fmt(D.END)}`;
}
const fmt = (t) => `${Math.floor(t / 60)}:${(t % 60).toFixed(1).padStart(4, '0')}`;
function tick(now) {
  if (playing) {
    if (D.audio && !aud.paused) clock = aud.currentTime;
    else if (last != null) clock += (now - last) / 1000;
    if (clock >= D.END) { clock = D.END; setPlay(false); }
  }
  last = now; draw(clock); requestAnimationFrame(tick);
}
function setPlay(on) {
  playing = on; document.getElementById('play').textContent = on ? '정지' : '재생';
  if (D.audio) { if (on) { aud.currentTime = clock; aud.play().catch(() => {}); } else aud.pause(); }
}
function go(t) { clock = Math.max(0, Math.min(D.END, t)); if (D.audio) aud.currentTime = clock; }
document.getElementById('play').onclick = () => setPlay(!playing);
seek.oninput = () => go(seek.value / 1000 * D.END);
addEventListener('keydown', (e) => {
  if (e.target.tagName === 'SELECT') return;
  if (e.code === 'Space') { e.preventDefault(); setPlay(!playing); }
  else if (e.key === 'ArrowLeft') go(clock - (e.shiftKey ? 5 : 1));
  else if (e.key === 'ArrowRight') go(clock + (e.shiftKey ? 5 : 1));
  else if (e.key === '[') go(D.runs[Math.max(0, runAt(clock) - 1)].T0);
  else if (e.key === ']') go(D.runs[Math.min(D.runs.length - 1, runAt(clock) + 1)].T0);
  else if (e.key === '0') go(0);
});
if (q.has('t')) clock = parseFloat(q.get('t')) || 0;
if (q.has('still')) document.getElementById('bar').style.display = document.getElementById('hud').style.display = 'none';
requestAnimationFrame(tick);
</script></body></html>
"""
out = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False)).replace('__MISSING__', json.dumps(missing))
open('index.html', 'w', encoding='utf-8').write(out)
for sk, d in data.items():
    print(f'{sk}: {len(d["runs"])} runs, {sum(c["hl"] for c in d["caps"])} chips, {d["END"]:.2f} s'
          + (' · narration not recorded yet (silent)' if d['placeholder'] else '') + f'  ->  open index.html?s={sk}')
if missing: print('compositions not built yet (blank in the preview):', ', '.join(missing))
print(f'index.html written: open {os.path.abspath("index.html")} in Chrome')
