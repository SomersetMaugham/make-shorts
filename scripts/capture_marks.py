"""Capture a real page and find where its cited sentences are (the Sungkim theme's upper-card captures, 2026-11-23).

The user's review of the first Sungkim short: captures were unreadable, a stray comment box was left in, and the
sentence the cards talk about was not marked. This tool makes the capture and gives the exact boxes of the phrases,
so a graphics module can crop to them and underline them (sungkim_kit.capture_html(..., marks=...)).

  python3 scripts/capture_marks.py <url> <out.png> --phrase "I further propose common limits" [--phrase ...]
         [--remove "form,textarea"] [--width 1280] [--height 6000]

It saves the page's HTML locally (with <base href> so its styles and images still load), drops the elements matched
by --remove (CSS selectors), and renders it in headless Chrome at the given width: the screenshot goes to out.png and
the phrase boxes (x0, y0, x1, y1 in the screenshot's pixels, one box per line the phrase wraps onto) to out.json,
with the body text height (`text_px`) measured from the page. A phrase that is not found is reported, not guessed.
Pages that build their text with scripts may render differently from the live site: LOOK at the PNG.
"""
import argparse, html, json, os, re, subprocess, sys, tempfile

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36'

ap = argparse.ArgumentParser()
ap.add_argument('url'); ap.add_argument('out')
ap.add_argument('--phrase', action='append', default=[])
ap.add_argument('--remove', default='')
ap.add_argument('--live', action='store_true', help='drive Chrome on the live page over the DevTools protocol (for pages that render with scripts); needs websocket-client')
ap.add_argument('--width', type=int, default=1280); ap.add_argument('--height', type=int, default=6000)
a = ap.parse_args()

raw = subprocess.run(['curl', '-sL', '--max-time', '30', '-A', UA, a.url], capture_output=True).stdout.decode('utf-8', 'ignore')
if len(raw) < 500: sys.exit(f'capture_marks: the page returned {len(raw)} bytes - blocked or empty; capture it by hand')
raw = re.sub(r'(?i)<head([^>]*)>', lambda m: f'<head{m.group(1)}><base href="{html.escape(a.url)}">', raw, count=1)
probe = r"""<script>
setTimeout(function () {
  var rm = %s; if (rm) document.querySelectorAll(rm).forEach(function (e) { e.remove(); });
  var out = {phrases: {}, missing: []};
  %s.forEach(function (ph) {
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT), n, boxes = null;
    // the phrase may span several text nodes (links, emphasis): join the text with runs of whitespace collapsed,
    // remembering for every joined character which node and offset it came from
    var map = [], text = '', prevSpace = true;
    while ((n = w.nextNode())) {
      var v = n.nodeValue, pe = n.parentElement;
      if (pe && /^(SCRIPT|STYLE|NOSCRIPT)$/.test(pe.tagName)) continue;
      for (var c = 0; c < v.length; c++) {
        var sp = /\s/.test(v[c]);
        if (sp && prevSpace) continue;
        text += sp ? ' ' : v[c]; map.push([n, c]); prevSpace = sp;
      }
    }
    // every occurrence; keep the visible one set in the largest type (a page title also sits in hidden menus)
    var best = null, from = 0, i;
    while ((i = text.indexOf(ph, from)) >= 0) {
      from = i + 1;
      var r = document.createRange(), e = map[i + ph.length - 1];
      r.setStart(map[i][0], map[i][1]); r.setEnd(e[0], e[1] + 1);
      var bx = Array.from(r.getClientRects()).filter(function (b) { return b.width > 2 && b.left >= 0 && b.right <= innerWidth; })
        .map(function (b) { return [Math.round(b.left + scrollX), Math.round(b.top + scrollY), Math.round(b.right + scrollX), Math.round(b.bottom + scrollY)]; });
      if (!bx.length) continue;
      var h = Math.max.apply(null, bx.map(function (b) { return b[3] - b[1]; }));
      if (!best || h > best.h) best = {h: h, boxes: bx};
    }
    if (!best) { out.missing.push(ph); return; }
    boxes = best.boxes;
    out.phrases[ph] = boxes;
  });
  var p = document.querySelector('article p, main p, p');
  out.text_px = p ? parseFloat(getComputedStyle(p).fontSize) : 16;
  var pre = document.createElement('pre'); pre.id = 'CAPTURE_MARKS'; pre.style.display = 'none';
  pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
}, 2500);
</script>""" % (json.dumps(a.remove), json.dumps(a.phrase))
raw = re.sub(r'(?i)</body>', lambda m: probe + '</body>', raw, count=1) if re.search(r'(?i)</body>', raw) else raw + probe

if a.live:
    import base64, socket, time, urllib.request
    import websocket                                                       # pip install websocket-client
    sock = socket.socket(); sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]; sock.close()
    prof = tempfile.mkdtemp()
    ch = subprocess.Popen([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--remote-debugging-port={port}',
                           f'--user-data-dir={prof}', f'--window-size={a.width},{a.height}', f'--user-agent={UA}', 'about:blank'],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try: tabs = json.load(urllib.request.urlopen(f'http://127.0.0.1:{port}/json')); break
            except Exception: time.sleep(0.2)
        ws = websocket.create_connection([t for t in tabs if t['type'] == 'page'][0]['webSocketDebuggerUrl'], timeout=60)
        seq = [0]
        def cdp(method, **params):
            seq[0] += 1; ws.send(json.dumps(dict(id=seq[0], method=method, params=params)))
            while True:
                msg = json.loads(ws.recv())
                if msg.get('id') == seq[0]: return msg.get('result', {})
        cdp('Emulation.setDeviceMetricsOverride', width=a.width, height=a.height, deviceScaleFactor=1, mobile=False)
        cdp('Page.navigate', url=a.url); time.sleep(8)
        js = probe.split('setTimeout(function () {', 1)[1].rsplit('}, 2500);', 1)[0]
        cdp('Runtime.evaluate', expression='(function(){' + js + '})()')
        got = cdp('Runtime.evaluate', expression="document.getElementById('CAPTURE_MARKS').textContent", returnByValue=True)
        shot = cdp('Page.captureScreenshot', format='png', captureBeyondViewport=False)
        open(a.out, 'wb').write(base64.b64decode(shot['data']))
        dom = '<pre id="CAPTURE_MARKS">' + html.escape(got['result']['value']) + '</pre>'
    finally:
        ch.kill()
else:
  tmp = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8'); tmp.write(raw); tmp.close()
  flags = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
         f'--window-size={a.width},{a.height}', '--virtual-time-budget=6000', f'--user-agent={UA}']
  dom = subprocess.run(flags + ['--dump-dom', 'file://' + tmp.name], capture_output=True, timeout=120).stdout.decode('utf-8', 'ignore')
  subprocess.run(flags + [f'--screenshot={os.path.abspath(a.out)}', 'file://' + tmp.name], capture_output=True, timeout=120)
  os.unlink(tmp.name)
m = re.search(r'<pre id="CAPTURE_MARKS"[^>]*>(.*?)</pre>', dom, re.S)
if not m: sys.exit('capture_marks: the probe did not run (the page may replace the document); LOOK at the PNG')
res = json.loads(html.unescape(m.group(1)))
res.update(url=a.url, width=a.width, height=a.height)
json.dump(res, open(os.path.splitext(a.out)[0] + '.json', 'w'), ensure_ascii=False, indent=1)
for ph, b in res['phrases'].items(): print(f'{ph!r}: {b}')
for ph in res['missing']: print(f'NOT FOUND: {ph!r}')
print(f'body text {res["text_px"]} px -> capture_html needs zoom >= {26 / res["text_px"] / (968 / a.width):.2f} for 26 px on screen')
