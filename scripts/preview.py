"""The browser preview: work/index.html plays every short as it will look, before any MP4 is rendered.
usage: python scripts/preview.py [s1 s2 ...]          (every short in cut.json when none is given; run inside work/)

What it is: one page that stacks each run's HyperFrames composition (gfx/<sk>_r<i>.html) as an iframe and drives it
by the narration's clock, with the captions, keyword chips and cover drawn on top where compose.py puts them (same font,
sizes, positions and chip animation; drawn by the browser instead of PIL, so a pixel can differ). The sound is the
narration as tts.mjs laid it out (narration/<sk>/audio/narration.mp3, what voice.wav is made from); before recording it
is silent and the timeline is the placeholders' estimate. The compositions are the live pages, so a graphics fix shows
after build_gfx.py and a reload, with no render at all. What it does not show: motion blur (that comes from the render).

The player is script-to-motion's (assets/template/js/player.js + css/player.css), carried over with its keys and look:
  Space play/pause (Space or Enter on the start screen) · ←/→ 0.5 s, Shift 5 s · . / , one frame (paused; 1/60 s here)
  0 or Home the start · R from the top at 1× · Shift+> / Shift+< speed 0.25×–3× · F fullscreen · C captions on/off
  S copy "time / length [cue · run +time-in-run] line" (for review notes) · A copy the screenshot command for ±1 s
  (paste after `python3 render.py ` in work/) · D the debug bar (time, cue marks, the line; click to seek; with Shift held,
  move the mouse to scrub: fine at the bottom of the screen, coarse at the top). The position and the captions setting are
  remembered. Letter keys work by their physical position, so they also work with the Korean input on.
Opens from file:// by double-click (the page talks to the compositions by postMessage). Served by
scripts/review_server.py (http://127.0.0.1:8765/index.html) it is also the review desk: N writes a note for the moment
(drag on the picture to mark the spot), V held says it, L lists the notes with the agent's replies (확인 / 다시); the
agent is told of each note with a screenshot, and every rebuilt run or page shows here by itself (see review_server.py).
&box=x,y,w,h draws a marked box (the notes' screenshots use it). ?s=s2 opens another short,
?t=12.5 seeks there, &still hides the start screen (for screenshots: render.py --screenshot uses it).

The MP4 is the user's to render, with render.py (the graphics with motion blur, the master, the composite)."""
import json, os, re, sys

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
                 capY=sum(Cfg.LAYOUT['caption_top' if any(l in top for l in r['lines']) else 'caption']) / 2,
                 ok=os.path.exists(f'gfx/{sk}_r{r["i"]}.html')) for r in c['runs']]
    cues = [dict(id=q['id'], start=q['start'], end=q['end'], text=q.get('text', '')) for q in c.get('cues', [])]
    audio = f'narration/{sk}/audio/narration.mp3'
    data[sk] = dict(title=sh.get('title', ''), cover=sh.get('cover', [sh.get('title', '')]), accent=sh.get('accent', 'azure'),
                    END=c['END'], fps=Cfg.FPS, runs=runs, caps=caps, cues=cues, audio=audio if os.path.exists(audio) else None,
                    placeholder=bool(c.get('narration', {}).get('placeholder')))
missing = [f'{sk}_r{r["i"]}' for sk, d in data.items() for r in d['runs'] if not r['ok']]

HTML = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>Shorts preview</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
@font-face{font-family:Pretendard;src:url(fonts/PretendardVariable.ttf);font-weight:45 920;font-display:block}
/* the player: script-to-motion's css/player.css (start screen, debug bar, speed toast), carried over */
html,body{margin:0;height:100%;background:#000;overflow:hidden}
body{font-family:Pretendard,sans-serif;-webkit-font-smoothing:antialiased}
body.vp-playing:not(.vp-cursor){cursor:none}
#stage{position:absolute;left:50%;top:50%;width:1080px;height:1920px;transform-origin:50% 50%;overflow:hidden;background:#111214}
#stage iframe{position:absolute;left:0;top:0;width:1080px;height:1920px;border:0;visibility:hidden;pointer-events:none}
#stage iframe.on{visibility:visible}
.vp-start{position:fixed;inset:0;z-index:100;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;
  background:#000;color:#fff;opacity:1;visibility:visible;transition:opacity .45s ease,visibility 0s linear 0s}
.vp-start.vp-hidden{opacity:0;visibility:hidden;pointer-events:none;transition:opacity .45s ease,visibility 0s linear .45s}
.vp-load{width:min(360px,42vw);height:3px;border-radius:2px;background:rgba(255,255,255,.14);overflow:hidden}
.vp-load-fill{width:100%;height:100%;background:#fff;transform:scaleX(0);transform-origin:0 50%}
.vp-go{display:none;position:relative;width:88px;height:88px;padding:0;border-radius:50%;border:2px solid rgba(255,255,255,.7);background:transparent;cursor:pointer}
.vp-go::after{content:'';position:absolute;left:34px;top:26px;border-style:solid;border-width:17px 0 17px 28px;border-color:transparent transparent transparent #fff}
.vp-start.vp-blocked{cursor:pointer}.vp-start.vp-blocked .vp-load{display:none}.vp-start.vp-blocked .vp-go{display:block}
.vp-debug{position:fixed;left:0;right:0;bottom:0;z-index:90;padding:5px 10px;background:rgba(0,0,0,.78);color:#e8e8e8;
  font:13px/1.4 Pretendard,monospace;display:none;align-items:center;gap:10px}
.vp-debug.vp-on{display:flex}
.vp-debug-time{flex:none;white-space:nowrap;font-variant-numeric:tabular-nums}
.vp-debug-bar{position:relative;flex:1;min-width:0;height:22px;background:#2a2d34;border-radius:4px;cursor:pointer;overflow:hidden}
.vp-debug-info{position:absolute;left:6px;top:3px;bottom:3px;z-index:2;box-sizing:border-box;padding:0 7px;border-radius:3px;
  background:rgba(12,13,16,.78);line-height:16px;white-space:nowrap;overflow:hidden;max-width:62%;text-overflow:ellipsis;pointer-events:none;font-size:12px;color:#fff}
.vp-debug-info:empty{display:none}
.vp-debug-fill{position:absolute;left:0;top:0;bottom:0;background:#E3262E;box-shadow:inset 0 0 0 1px rgba(255,255,255,.15);pointer-events:none;z-index:1}
.vp-debug-mark{position:absolute;top:3px;bottom:3px;background:rgba(255,255,255,.22);border-left:2px solid #7cc4ff;pointer-events:none}
.vp-debug select{flex:none;background:#2a2d34;color:#e8e8e8;border:0;border-radius:4px;height:22px;font:12px Pretendard}
.vp-rate{position:fixed;left:50%;top:12%;transform:translateX(-50%);z-index:200;pointer-events:none;padding:10px 20px;border-radius:999px;
  background:rgba(0,0,0,.62);color:#fff;font:600 20px/1.2 Pretendard,sans-serif;opacity:0;transition:opacity .2s ease;white-space:nowrap}
.vp-rate.vp-on{opacity:1}
/* the short's own captions, chips and cover: compose.py's look */
#caps{position:absolute;inset:0;pointer-events:none}
.cap{position:absolute;left:0;right:0;text-align:center;font:700 74px/88px Pretendard;color:#fff;
  -webkit-text-stroke:20px #0B0C0E;paint-order:stroke fill;word-spacing:16px;white-space:nowrap}
.chip{position:absolute;left:50%;padding:26px 40px 26px;border-radius:28px;background:rgba(24,25,28,.88);
  border:2px solid var(--acc-line);box-shadow:0 50px 120px -40px rgba(0,0,0,.8),0 0 60px -10px var(--acc-glow),inset 0 1.5px 0 rgba(255,255,255,.09);
  font:600 70px/1 Pretendard;letter-spacing:-.025em;color:#fff;white-space:nowrap}
.chip .ln{display:block;height:5px;margin-top:22px;border-radius:3px;background:var(--acc);box-shadow:0 0 14px var(--acc);transform-origin:0 50%}
#cover{position:absolute;left:50%;top:432px;transform:translate(-50%,-50%);padding:44px 56px;border-radius:36px;background:rgba(24,25,28,.94);
  border:2px solid var(--acc-line);box-shadow:0 50px 120px -40px rgba(0,0,0,.82),0 0 70px -10px var(--acc-glow);text-align:center;
  font:600 104px/1.08 Pretendard;letter-spacing:-.03em;color:#fff;white-space:nowrap;display:none}
#cover .ln{height:6px;margin-top:26px;border-radius:3px;background:var(--acc);box-shadow:0 0 16px var(--acc)}
/* review desk (served by review_server.py): the marked box, notes, the list, the pins */
#box{position:absolute;display:none;z-index:6;border:6px solid #FFD23F;border-radius:10px;box-shadow:0 0 0 3000px rgba(0,0,0,.18),0 0 30px rgba(255,210,63,.6);pointer-events:none}
#draw{position:absolute;inset:0;z-index:7;display:none;cursor:crosshair}
.rv-panel{position:fixed;right:16px;bottom:44px;z-index:150;width:min(440px,calc(100vw - 32px));box-sizing:border-box;padding:14px;border-radius:14px;
  background:rgba(20,21,24,.97);border:1px solid rgba(255,255,255,.14);color:#eee;font:14px/1.45 Pretendard,sans-serif;display:none;box-shadow:0 20px 60px rgba(0,0,0,.6)}
.rv-panel.vp-on,.rv-list.vp-on{display:block}
.rv-head{font-size:12px;color:#aab;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rv-panel textarea,.rv-card input{width:100%;box-sizing:border-box;background:#0e0f12;color:#fff;border:1px solid #3a3d45;border-radius:8px;padding:8px;font:15px/1.4 Pretendard,sans-serif;resize:vertical}
.rv-row{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:8px;font-size:12px;color:#aab}
.rv-btn{background:#2F95FF;color:#fff;border:0;border-radius:7px;padding:6px 12px;font:600 13px Pretendard,sans-serif;cursor:pointer}
.rv-btn.ghost{background:#2a2d34}
.rv-list{position:fixed;right:16px;top:16px;z-index:140;width:min(460px,calc(100vw - 32px));max-height:calc(100vh - 80px);overflow:auto;box-sizing:border-box;padding:12px;
  border-radius:14px;background:rgba(20,21,24,.97);border:1px solid rgba(255,255,255,.14);color:#eee;font:14px/1.45 Pretendard,sans-serif;display:none}
.rv-card{padding:10px;border-radius:10px;background:#1b1d22;margin-top:8px;border-left:4px solid var(--c)}
.rv-card .hd{display:flex;justify-content:space-between;gap:8px;font-size:12px;color:#aab;cursor:pointer}
.rv-card .st{color:var(--c);font-weight:700}
.rv-card .rp{margin-top:6px;padding:6px 8px;border-radius:7px;background:#25282f;font-size:13px}
.rv-card .rp.user{background:#202a36}
.rv-card .act{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;align-items:center}
.rv-card .act input{flex:1;min-width:140px;padding:5px 8px;font-size:13px}
.rv-pin{position:absolute;top:0;bottom:0;width:4px;margin-left:-2px;z-index:3;background:var(--c);pointer-events:none}
.rv-badge{position:fixed;left:16px;top:14px;z-index:80;padding:5px 10px;border-radius:999px;background:rgba(0,0,0,.6);color:#ddd;font:12px Pretendard,sans-serif;pointer-events:none}
body.vp-playing .rv-badge{opacity:0}
</style></head><body>
<div id="stage"><div id="caps"></div><div id="cover"></div><div id="box"></div><div id="draw"></div></div>
<div class="vp-start" id="start"><div class="vp-load"><div class="vp-load-fill" id="loadFill"></div></div><button class="vp-go" aria-label="재생"></button></div>
<div class="vp-debug" id="debug"><select id="pick"></select><div class="vp-debug-time" id="dbgTime"></div>
  <div class="vp-debug-bar" id="bar"><div class="vp-debug-fill" id="fill"></div><div class="vp-debug-info" id="dbgInfo"></div></div></div>
<div class="vp-rate" id="toast"></div>
<div class="rv-panel" id="rvPanel"><div class="rv-head" id="rvHead"></div>
  <textarea id="rvText" rows="3" placeholder="무엇을 고칠까요? 화면을 끌면 위치가 표시돼요"></textarea>
  <div class="rv-row"><span id="rvHint">Enter 보내기 · Shift+Enter 줄바꿈 · Esc 취소</span><button class="rv-btn" id="rvSend">보내기</button></div></div>
<div class="rv-list" id="rvList"></div>
<div class="rv-badge" id="rvBadge" style="display:none"></div>
<audio id="aud" preload="auto"></audio>
<script>
const DATA = __DATA__, MISSING = __MISSING__;
const TXT = { normal: '보통', copied: '복사됨', copyFailed: '복사하지 못했어요', shotCopied: '스크린샷 명령 복사됨' };
const ACC = { azure: [47,149,255], ember: [255,138,91], mint: [79,214,160], iris: [156,124,255] };
const params = new URLSearchParams(location.search);
const sk = DATA[params.get('s')] ? params.get('s') : Object.keys(DATA)[0];
const D = DATA[sk], duration = D.END;
const $ = (id) => document.getElementById(id);
const stage = $('stage'), caps = $('caps'), aud = $('aud'), start = $('start');
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };
const POS_KEY = 'vp-pos:' + location.pathname + ':' + sk, CAP_KEY = 'vp-captions:' + location.pathname;
const a = ACC[D.accent] || ACC.azure;
stage.style.setProperty('--acc', `rgb(${a})`); stage.style.setProperty('--acc-line', `rgba(${a},.33)`); stage.style.setProperty('--acc-glow', `rgba(${a},.55)`);
document.title = `${sk} · ${D.title}`;
for (const k of Object.keys(DATA)) { const o = document.createElement('option'); o.value = k; o.textContent = k; if (k === sk) o.selected = true; $('pick').appendChild(o); }
$('pick').onchange = () => { location.search = '?s=' + $('pick').value; };

// one iframe per run, all loaded up front; the visible one gets its run-relative time every frame
let loaded = 0;
const frames = D.runs.map((r) => {
  const f = document.createElement('iframe');
  f.onload = () => { loaded++; $('loadFill').style.transform = `scaleX(${loaded / D.runs.length})`; };
  if (r.ok) f.src = r.src; else loaded++;
  stage.insertBefore(f, caps); return f;
});
const chunkEls = D.caps.map((c) => {
  const el = document.createElement('div');
  if (c.hl) { el.className = 'chip'; el.innerHTML = '<span class="tx"></span><span class="ln"></span>'; el.querySelector('.tx').textContent = c.text; }
  else { el.className = 'cap'; el.textContent = c.text; }
  el.style.display = 'none'; caps.appendChild(el); return el;
});
const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
$('cover').innerHTML = D.cover.map((l) => `<div>${esc(l)}</div>`).join('') + '<div class="ln"></div>';
for (const c of D.cues) {
  const m = document.createElement('div'); m.className = 'vp-debug-mark';
  m.style.left = (c.start / duration) * 100 + '%'; m.style.width = ((c.end - c.start) / duration) * 100 + '%'; m.title = `${c.id}: ${c.text}`;
  $('bar').appendChild(m);
}
if (D.audio) aud.src = D.audio;

function fit() { const s = Math.min(innerWidth / 1080, innerHeight / 1920); stage.style.transform = `translate(-50%, -50%) scale(${s})`; }
addEventListener('resize', fit); document.addEventListener('fullscreenchange', fit); fit();

// ---------- the clock ----------
let t = 0, playing = false, rate = 1, anchorT = 0, anchorPerf = 0, showDebug = false;
let showCaptions = store.get(CAP_KEY) !== '0';
const now = () => performance.now() / 1000;
function play() {
  if (t >= duration - 1e-3) t = 0;
  playing = true; anchorT = t; anchorPerf = now(); document.body.classList.add('vp-playing');
  if (D.audio) { aud.currentTime = t; aud.playbackRate = rate; aud.play().catch(() => { pause(); start.classList.add('vp-blocked'); start.classList.remove('vp-hidden'); }); }
}
function pause() { playing = false; document.body.classList.remove('vp-playing'); if (D.audio) aud.pause(); store.set(POS_KEY, t.toFixed(2)); }
function seek(x) { t = clamp(x, 0, duration); anchorT = t; anchorPerf = now(); if (D.audio) aud.currentTime = t; render(); store.set(POS_KEY, t.toFixed(2)); }
function tick() {
  if (playing) {
    t = D.audio && !aud.paused ? aud.currentTime : anchorT + (now() - anchorPerf) * rate;
    if (loopB != null && t >= loopB) seek(loopA);       // a note's moment, looped from the notes list (Esc ends it)
    else if (t >= duration) { t = duration; pause(); }
  }
  // every frame, playing or not: a composition that finished loading late (or a headless screenshot) still gets the
  // current time, so a paused frame is never stale
  if (loaded >= D.runs.length) render();
  requestAnimationFrame(tick);
}
const runAt = (x) => { for (let k = 0; k < D.runs.length; k++) if (x < D.runs[k].T1 - 1e-6) return k; return D.runs.length - 1; };
const cueAt = (x) => D.cues.find((c) => x >= c.start && x < c.end) || [...D.cues].reverse().find((c) => c.start <= x);
const pw3 = (p) => 1 - Math.pow(1 - clamp(p, 0, 1), 3);
const fmt = (s) => { const m = Math.floor(s / 60); return `${m}:${(s - m * 60).toFixed(2).padStart(5, '0')}`; };
function render() {
  const k = runAt(t), r = D.runs[k];
  frames.forEach((f, j) => f.classList.toggle('on', j === k));
  try { frames[k].contentWindow.postMessage({ hfT: Math.max(0, t - r.T0) }, '*'); } catch (e) {}
  D.caps.forEach((c, j) => {
    const el = chunkEls[j], on = showCaptions && t > 0 && c.t0 <= t + 1e-6 && t < c.t1;
    el.style.display = on ? 'block' : 'none';
    if (!on) return;
    if (c.hl) {
      const tr = t - c.t0, pin = Math.min(1, tr / 0.18), e = pw3(pin);
      el.style.top = r.capY + 'px';
      el.style.transform = `translate(-50%, calc(-50% + ${12 * (1 - e)}px)) scale(${0.96 + 0.04 * e})`;
      el.style.opacity = Math.min(1, pin * 1.6);
      el.querySelector('.ln').style.transform = `scaleX(${pw3((tr - 0.08) / 0.32)})`;
    } else el.style.top = (r.capY - 44) + 'px';
  });
  $('cover').style.display = showCaptions && t < 0.05 ? 'block' : 'none';
  if (showDebug) {
    const c = cueAt(t);
    $('dbgTime').textContent = `${t.toFixed(2)} / ${duration.toFixed(2)}초`;
    $('dbgInfo').textContent = `${c ? '[' + c.id + '] ' : ''}${sk}_r${r.i} +${(t - r.T0).toFixed(2)}s · ${c ? c.text : ''}`;
    $('fill').style.width = (t / duration) * 100 + '%';
  }
}

// ---------- the debug bar: click to seek; Shift held + mouse move scrubs (script-to-motion's gain: fine at the bottom) ----------
$('bar').addEventListener('pointerdown', (e) => { const b = $('bar').getBoundingClientRect(); seek(((e.clientX - b.left) / b.width) * duration); });
const GAIN_MIN = 1 / 3000, gainMax = () => duration * 0.02;
const gainAt = (y) => { const u = clamp(1 - y / Math.max(1, innerHeight), 0, 1); return GAIN_MIN * Math.pow(gainMax() / GAIN_MIN, u); };
let lastX = null, target = null, scrubRaf = 0, cursorTimer = 0;
const flush = () => { scrubRaf = 0; if (target != null) seek(target); };
document.addEventListener('pointermove', (e) => {
  if (!showDebug || !start.classList.contains('vp-hidden') || !e.shiftKey) { lastX = null; return; }
  if (lastX == null) { lastX = e.clientX; return; }
  const dx = e.clientX - lastX; lastX = e.clientX; if (!dx) return;
  target = clamp((target != null ? target : t) + dx * gainAt(e.clientY), 0, duration);
  if (!scrubRaf) scrubRaf = requestAnimationFrame(flush);
});
document.addEventListener('pointerleave', () => { lastX = null; }); addEventListener('blur', () => { lastX = null; });
const syncTarget = (e) => { if (e && e.key === 'Shift') return; target = null; };
document.addEventListener('keydown', syncTarget, true); document.addEventListener('pointerdown', syncTarget, true);
document.addEventListener('mousemove', () => { document.body.classList.add('vp-cursor'); clearTimeout(cursorTimer); cursorTimer = setTimeout(() => document.body.classList.remove('vp-cursor'), 1500); });

// ---------- speed, toast, copy (script-to-motion's player.js) ----------
const RATES = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3];
let toastTimer = 0;
function toast(text, ms = 900) { $('toast').textContent = text; $('toast').classList.add('vp-on'); clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').classList.remove('vp-on'), ms); }
function setRate(r) { if (playing) { anchorT = t; anchorPerf = now(); } rate = r; aud.defaultPlaybackRate = r; aud.playbackRate = r; toast(r === 1 ? `1x (${TXT.normal})` : r + 'x'); }
function stepRate(dir) { const i = RATES.indexOf(rate); setRate(RATES[clamp(i + dir, 0, RATES.length - 1)]); }
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; } catch (_) {}
  const ta = document.createElement('textarea'); ta.value = text; ta.style.cssText = 'position:fixed;left:-9999px;top:0;opacity:0';
  document.body.appendChild(ta); ta.select(); let ok = false; try { ok = document.execCommand('copy'); } catch (_) {} ta.remove(); return ok;
}
function fullscreen() { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen().catch(() => {}); }
function cueLine() {
  const c = cueAt(t), r = D.runs[runAt(t)];
  return `${fmt(t)} / ${fmt(duration)} ${c ? `[${c.id} · ${sk}_r${r.i} +${(t - r.T0).toFixed(2)}s] ${c.text}` : `[${sk}_r${r.i} +${(t - r.T0).toFixed(2)}s]`}`.trimEnd() + '\n\n';
}
function startNow() { start.classList.remove('vp-blocked'); start.classList.add('vp-hidden'); play(); }
start.addEventListener('click', () => { if (start.classList.contains('vp-blocked') || loaded >= D.runs.length) startNow(); });

document.addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.target && /^(SELECT|TEXTAREA|INPUT)$/.test(e.target.tagName)) return;
  const k = e.key;
  if (REVIEW && reviewKey(e)) return;
  // letter keys by their physical position (e.code), so they also work with the Korean input on
  const is = (code, ...keys) => e.code === code || keys.includes(k);
  if (!start.classList.contains('vp-hidden')) {
    if (k === ' ' || k === 'Enter') { e.preventDefault(); startNow(); }
    else if (is('KeyF', 'f', 'F')) fullscreen();
    return;
  }
  const step = e.shiftKey ? 5 : 0.5, frame = 1 / (D.fps || 60);
  if (e.shiftKey && (k === '>' || e.code === 'Period')) { e.preventDefault(); stepRate(+1); }
  else if (e.shiftKey && (k === '<' || e.code === 'Comma')) { e.preventDefault(); stepRate(-1); }
  else if (k === ' ') { e.preventDefault(); playing ? pause() : play(); }
  else if (k === 'ArrowRight') seek(t + step);
  else if (k === 'ArrowLeft') seek(t - step);
  else if (!e.shiftKey && is('Period', '.')) { if (!playing) seek(t + frame); }
  else if (!e.shiftKey && is('Comma', ',')) { if (!playing) seek(t - frame); }
  else if (k === 'Home' || is('Digit0', '0')) seek(0);
  else if (is('KeyR', 'r', 'R')) { if (rate !== 1) setRate(1); seek(0); play(); }
  else if (is('KeyF', 'f', 'F')) fullscreen();
  else if (is('KeyC', 'c', 'C')) { showCaptions = !showCaptions; store.set(CAP_KEY, showCaptions ? '1' : '0'); render(); }
  else if (is('KeyS', 's', 'S')) { const line = cueLine(); copyText(line).then((ok) => toast(ok ? TXT.copied + ' · ' + line.split(' / ')[0] : TXT.copyFailed, 1200)); }
  else if (is('KeyA', 'a', 'A')) {
    // A: the render.py contact-sheet command for this moment — 1 s either side, every 10th frame; pasted after
    // `python3 render.py ` in work/ (it shoots this page with headless Chrome: no render needed)
    const from = Math.max(0, t - 1), to = Math.min(duration, t + 1);
    const cmd = `--screenshot --short ${sk} --from ${from.toFixed(2)} --to ${to.toFixed(2)} --gapframe 10 --fast --jobs 1 (check it with render.py from the create-video-shorts skill)`;
    copyText(cmd).then((ok) => toast(ok ? TXT.shotCopied + ' · ' + fmt(from) + '–' + fmt(to) : TXT.copyFailed, 1400));
  }
  else if (is('KeyD', 'd', 'D')) { showDebug = !showDebug; $('debug').classList.toggle('vp-on', showDebug); render(); }
});

// ---------- the review desk: only when served by review_server.py (http://127.0.0.1) ----------
// N: a note for this moment (drag on the picture to mark the spot) · V held: say it · L: the notes list.
// The server stores each note with a screenshot and prints it for the agent; its replies and every rebuilt run come
// back here by server-sent events, so nothing is copied, pasted or reloaded by hand.
const REVIEW = location.protocol.startsWith('http');
const boxEl = $('box'), drawEl = $('draw');
const showBox = (b) => { if (!b) { boxEl.style.display = 'none'; return; }
  Object.assign(boxEl.style, { display: 'block', left: b[0] + 'px', top: b[1] + 'px', width: b[2] + 'px', height: b[3] + 'px' }); };
if (params.get('box')) showBox(params.get('box').split(',').map(Number));
const ST = { open: ['새 메모', '#FFD23F'], fixing: ['수정 중', '#2F95FF'], question: ['질문', '#FF8A5B'], recording: ['녹음 대기', '#9C7CFF'],
  done: ['반영됨', '#4FD6A0'], confirmed: ['확인됨', '#6b7280'], wontfix: ['보류', '#6b7280'] };
let notesList = [], panelOpen = false, noteBox = null, noteT = 0, noteVia = 'text', loopA = null, loopB = null, rec = null, recBase = '';
const capsAt = (x) => D.caps.filter((c) => c.t0 <= x + 1e-6 && x < c.t1).map((c) => c.text).join(' / ');
function stagePt(e) { const b = stage.getBoundingClientRect(), k = 1080 / b.width; return [clamp((e.clientX - b.left) * k, 0, 1080), clamp((e.clientY - b.top) * k, 0, 1920)]; }
let drag0 = null;
drawEl.addEventListener('pointerdown', (e) => { drag0 = stagePt(e); drawEl.setPointerCapture(e.pointerId); });
drawEl.addEventListener('pointermove', (e) => {
  if (!drag0) return; const p = stagePt(e);
  noteBox = [Math.min(drag0[0], p[0]), Math.min(drag0[1], p[1]), Math.abs(p[0] - drag0[0]), Math.abs(p[1] - drag0[1])]; showBox(noteBox);
});
drawEl.addEventListener('pointerup', () => { drag0 = null; if (noteBox && (noteBox[2] < 24 || noteBox[3] < 24)) { noteBox = null; showBox(null); } $('rvText').focus(); });
function openPanel(via) {
  if (playing) pause();
  loopA = loopB = null; panelOpen = true; noteT = t; noteVia = via; noteBox = null; showBox(null);
  const c = cueAt(t), r = D.runs[runAt(t)];
  $('rvHead').textContent = `${fmt(t)} · ${c ? c.id + ' · ' : ''}${sk}_r${r.i} +${(t - r.T0).toFixed(2)}s · ${capsAt(t) || (c ? c.text : '')}`;
  $('rvText').value = ''; $('rvPanel').classList.add('vp-on'); drawEl.style.display = 'block';
  if (via !== 'voice') setTimeout(() => $('rvText').focus(), 0);
}
function closePanel() { panelOpen = false; $('rvPanel').classList.remove('vp-on'); drawEl.style.display = 'none'; showBox(null); if (rec) { rec.abort(); rec = null; } $('rvText').blur(); }
async function sendNote() {
  const text = $('rvText').value.trim(); if (!text) { toast('메모가 비어 있어요', 1200); return; }
  const c = cueAt(noteT), r = D.runs[runAt(noteT)];
  const body = { sk, t: noteT, run: `${sk}_r${r.i}`, rt: noteT - r.T0, cue: c ? c.id : null, line: c ? c.text : '', caption: capsAt(noteT),
    text, box: noteBox && noteBox.map(Math.round), via: noteVia };
  closePanel();
  try { const n = await (await fetch('/api/note', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })).json();
    toast(`${n.id} 보냄 · 에이전트에게 전달돼요`, 1800); } catch (e) { toast('보내지 못했어요: 검수 서버가 꺼져 있어요', 2500); }
  loadNotes();
}
$('rvSend').onclick = sendNote;
$('rvText').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendNote(); }
  else if (e.key === 'Escape') { e.preventDefault(); closePanel(); }
});
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
function voiceStart() {
  if (!SR) { toast('이 브라우저에는 음성 인식이 없어요', 1500); return; }
  if (!panelOpen) openPanel('voice'); noteVia = 'voice'; recBase = $('rvText').value.trim();
  rec = new SR(); rec.lang = 'ko-KR'; rec.interimResults = true; rec.continuous = true;
  rec.onresult = (e) => { let s = ''; for (let i = 0; i < e.results.length; i++) s += e.results[i][0].transcript;
    $('rvText').value = (recBase ? recBase + ' ' : '') + s.trim(); };
  rec.onerror = (e) => { if (e.error !== 'aborted') toast('음성 인식 오류: ' + e.error, 1800); };
  try { rec.start(); $('rvHint').textContent = '듣는 중… V를 떼면 끝나요'; } catch (e) {}
}
function voiceStop() { if (!rec) return; const r = rec; rec = null; setTimeout(() => r.stop(), 300);
  $('rvHint').textContent = '확인하고 Enter로 보내요 · Esc 취소'; $('rvText').focus(); }
document.addEventListener('keyup', (e) => { if (REVIEW && e.code === 'KeyV') voiceStop(); });
function reviewKey(e) {
  // keys of the review desk; true when the key was used here
  if (panelOpen) {
    if (e.key === 'Escape') closePanel(); else if (e.key === 'Enter') sendNote();
    else if (e.code === 'KeyV' && !e.repeat && !rec) voiceStart();
    return true;
  }
  if (!start.classList.contains('vp-hidden')) return false;
  if (e.code === 'KeyN') { e.preventDefault(); openPanel('text'); return true; }
  if (e.code === 'KeyV') { e.preventDefault(); if (!e.repeat) voiceStart(); return true; }
  if (e.code === 'KeyL') { $('rvList').classList.toggle('vp-on'); return true; }
  if (e.key === 'Escape') { if (loopB != null) { loopA = loopB = null; showBox(null); toast('반복 끝', 800); } else $('rvList').classList.remove('vp-on'); return true; }
  return false;
}
async function answer(id, status, text) {
  await fetch('/api/note/' + id, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ who: 'user', status, text }) });
  loadNotes();
}
function loopNote(n) {
  loopA = Math.max(0, n.t - 1); loopB = Math.min(duration, n.t + 2); showBox(n.box); seek(loopA); play();
  toast(`${n.id} 구간 반복 · Esc로 끝`, 1500);
}
function drawList() {
  const L = $('rvList'); L.innerHTML = '';
  const head = document.createElement('div'); head.className = 'rv-row'; head.style.marginTop = '0';
  head.innerHTML = `<b style="color:#fff">검수 메모 ${notesList.length}</b><span>N 메모 · V 말하기 · L 닫기</span>`; L.appendChild(head);
  for (const n of [...notesList].reverse()) {
    const [label, col] = ST[n.status] || [n.status, '#aaa'];
    const el = document.createElement('div'); el.className = 'rv-card'; el.style.setProperty('--c', col);
    el.innerHTML = `<div class="hd"><span>${n.id} · ${fmt(n.t)} · ${esc(n.cue || '')} ${esc(n.run)}</span><span class="st">${label}</span></div>
      <div style="margin-top:4px">${esc(n.text)}</div>` + n.replies.map((r) => `<div class="rp ${r.who}">${r.who === 'user' ? '나' : '에이전트'}: ${esc(r.text)}</div>`).join('');
    el.querySelector('.hd').onclick = () => loopNote(n);
    if (['done', 'question', 'recording'].includes(n.status)) {
      const act = document.createElement('div'); act.className = 'act';
      act.innerHTML = `<input placeholder="${n.status === 'done' ? '다시 고칠 점 (선택)' : '답하기'}">` +
        (n.status === 'done' ? '<button class="rv-btn" data-a="ok">확인</button><button class="rv-btn ghost" data-a="again">다시</button>'
                             : '<button class="rv-btn" data-a="reply">보내기</button>');
      const inp = act.querySelector('input');
      inp.addEventListener('keydown', (e) => { if (e.key === 'Enter' && !e.isComposing) act.querySelector('.rv-btn' + (n.status === 'done' ? '.ghost' : '')).click(); });
      act.querySelectorAll('button').forEach((b) => b.onclick = () => {
        const v = inp.value.trim();
        if (b.dataset.a === 'ok') answer(n.id, 'confirmed', v);
        else if (!v) { toast('무엇을 고칠지 적어 주세요', 1200); inp.focus(); }
        else answer(n.id, 'open', v);
      });
      el.appendChild(act);
    }
    L.appendChild(el);
  }
}
function drawPins() {
  $('bar').querySelectorAll('.rv-pin').forEach((p) => p.remove());
  for (const n of notesList) { const p = document.createElement('div'); p.className = 'rv-pin';
    p.style.left = (n.t / duration) * 100 + '%'; p.style.setProperty('--c', (ST[n.status] || ['', '#aaa'])[1]); p.title = `${n.id}: ${n.text}`; $('bar').appendChild(p); }
}
function badge() {
  const open = notesList.filter((n) => !['confirmed', 'wontfix'].includes(n.status)).length;
  const wait = notesList.filter((n) => ['done', 'question', 'recording'].includes(n.status)).length;
  $('rvBadge').style.display = 'block';
  $('rvBadge').textContent = `검수 연결됨 · 진행 중 메모 ${open}` + (wait ? ` · 내 차례 ${wait}` : '') + ' · N 메모 · V 말하기 · L 목록';
}
async function loadNotes() {
  try { notesList = await (await fetch('/api/notes?s=' + sk)).json(); } catch (e) { return; }
  drawPins(); drawList(); badge();
}
function swapRuns(rids) {
  const mine = rids.filter((rid) => rid.startsWith(sk + '_r'));
  for (const rid of mine) {
    const k = D.runs.findIndex((r) => `${sk}_r${r.i}` === rid); if (k < 0) continue;
    D.runs[k].ok = true; frames[k].src = D.runs[k].src + '?v=' + Date.now();
  }
  if (mine.length) toast(`${mine.join(', ')} 반영됨`, 1800);
}
if (REVIEW) {
  loadNotes();
  const es = new EventSource('/api/events');
  es.onmessage = (m) => {
    const ev = JSON.parse(m.data);
    if (ev.type === 'notes') loadNotes().then(() => {
      const n = ev.who === 'agent' && notesList.find((x) => x.id === ev.id);
      if (n) toast(`${n.id} ${ST[n.status] ? ST[n.status][0] : n.status}` + (n.replies.length ? ' · ' + n.replies[n.replies.length - 1].text : ''), 3500);
    });
    else if (ev.type === 'runs') swapRuns(ev.rids);
    else if (ev.type === 'page') { store.set(POS_KEY, t.toFixed(2)); try { sessionStorage.setItem('vp-hot', '1'); } catch (e) {} location.reload(); }
  };
  es.onerror = () => { $('rvBadge').textContent = '검수 서버 연결 끊김 · 다시 연결 중…'; };
}

// ---------- boot: the start screen until every composition is loaded, then wait for Space / a click ----------
const saved = params.has('t') ? parseFloat(params.get('t')) : parseFloat(store.get(POS_KEY));
if (Number.isFinite(saved)) t = clamp(saved, 0, duration);
let hot = false; try { hot = sessionStorage.getItem('vp-hot') === '1'; sessionStorage.removeItem('vp-hot'); } catch (e) {}
if (params.has('still') || hot) { start.classList.add('vp-hidden'); }   // hot: reloaded by the review server, stay at the moment
const notes = [];
if (D.placeholder) notes.push('녹음 전: 무음, 길이는 추정치');
if (!D.audio) notes.push('내레이션 오디오 없음: prep.sh 먼저');
const miss = MISSING.filter((m) => m.startsWith(sk + '_'));
if (miss.length) notes.push('그래픽 없음: ' + miss.join(', '));
(function waitLoad() {
  if (loaded < D.runs.length) return requestAnimationFrame(waitLoad);
  render();
  if (hot) toast('페이지 갱신됨 · Space로 재생', 1800);
  else if (!params.has('still')) { start.classList.add('vp-blocked'); if (notes.length) toast(notes.join(' · '), 3500); }
})();
requestAnimationFrame(tick);
setInterval(() => { if (playing) store.set(POS_KEY, t.toFixed(2)); }, 1000);
</script></body></html>
"""
out = HTML.replace('__DATA__', json.dumps(data, ensure_ascii=False)).replace('__MISSING__', json.dumps(missing))
open('index.html', 'w', encoding='utf-8').write(out)
for sk, d in data.items():
    print(f'{sk}: {len(d["runs"])} runs, {sum(c["hl"] for c in d["caps"])} chips, {d["END"]:.2f} s'
          + (' · narration not recorded yet (silent)' if d['placeholder'] else '') + f'  ->  open index.html?s={sk}')
if missing: print('compositions not built yet (blank in the preview):', ', '.join(missing))
print(f'index.html written: open {os.path.abspath("index.html")} in Chrome (D: debug bar, S: copy the moment, A: screenshot command)'
      + '\n  review desk (notes on the page, live reload): python3 scripts/review_server.py, then open the REVIEW link it prints')
