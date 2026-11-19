"""The review server: index.html served over http, with notes the user leaves on the page and live reloads.
usage: python3 scripts/review_server.py [--port 8765]           (run inside work/; stop with Ctrl+C)

Why: from file:// the page cannot talk to anyone, so a review meant S (copy), switch to the terminal, paste, type,
then reload by hand. Served from here, the page itself is the review desk:
  Space    (while playing) pause and write a note for this moment; drag on the picture to mark the spot (optional);
           Enter sends and plays on, Esc cancels and stays paused (Space when paused plays, as before)
  V (hold) say the note (Korean speech recognition in Chrome); release, check the text, Enter sends
  L        the notes list: status, the agent's replies; click a note to loop that moment, confirm or reopen it
Each note is stored in review/notes.json with the time, cue, run, caption on screen, the marked box, and a screenshot
of that frame (review/<id>.png, the box drawn in), and one line is printed to stdout:
  NOTE n003 s1 12.34s [c05 · s1_r6 +1.20s] 칩이 자막을 가려요 | box 120,900,600,300 | shot review/n003.png
so an agent that started this server under a watcher (Claude Code's Monitor) wakes on each note, with no copy-paste.
The agent answers with scripts/review.py (reply, status); the page shows it at once.

Live reload: the page is told when a file changes. A changed gfx/<sk>_r<i>.html swaps only that run's frame (the
position kept); a changed index.html (preview.py after prep.sh or compose.py) reloads the page at the same moment,
without the start screen. So the loop is: note -> the agent fixes and rebuilds -> the picture changes in front of you.

Listens on 127.0.0.1 only. Writes only review/ (notes.json, the screenshots, server.json with the port)."""
import hashlib, http.server, json, os, queue, shutil, socketserver, subprocess, sys, threading, time, glob
from urllib.parse import urlparse, parse_qs

if not os.path.exists('cut.json'): raise SystemExit('run it inside work/ (no cut.json here)')
port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 8765
os.makedirs('review', exist_ok=True)
NOTES = 'review/notes.json'
lock = threading.Lock()
clients = []                                            # one queue per open page (server-sent events)
STATUS = {'open', 'fixing', 'done', 'question', 'recording', 'confirmed', 'wontfix'}


def load():
    try: return json.load(open(NOTES, encoding='utf-8'))
    except (OSError, ValueError): return []


def save(notes):
    tmp = NOTES + '.tmp'; json.dump(notes, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1); os.replace(tmp, NOTES)


def say(*a): print(*a, flush=True)


def push(ev):
    for q in list(clients): q.put(ev)


CHROME = next((p for p in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome') or '',
                           shutil.which('chromium') or '', shutil.which('chrome') or '') if p and os.path.exists(p)), None)


def shoot(n):
    """The frame the user was looking at, with the marked box, as a still of index.html (file://, like render.py)."""
    if not CHROME: return None
    f = os.path.abspath(f'review/{n["id"]}.png')
    q = f'?s={n["sk"]}&t={n["t"]:.3f}&still' + (('&box=' + ','.join(str(round(v)) for v in n['box'])) if n.get('box') else '')
    subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=540,960',
                    '--virtual-time-budget=8000', f'--screenshot={f}', 'file://' + os.path.abspath('index.html') + q],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
    return f'review/{n["id"]}.png' if os.path.exists(f) else None


def line(n):
    b = (' | box ' + ','.join(str(round(v)) for v in n['box'])) if n.get('box') else ''
    return (f'NOTE {n["id"]} {n["sk"]} {n["t"]:.2f}s [{n.get("cue") or "-"} · {n["run"]} +{n["rt"]:.2f}s] '
            f'{n["text"]}{b}' + (f' | shot {n["shot"]}' if n.get('shot') else '') + (' (voice)' if n.get('via') == 'voice' else ''))


def new_note(d):
    with lock:
        notes = load()
        nid = 'n%03d' % (1 + max([int(x['id'][1:]) for x in notes] or [0]))
        n = dict(id=nid, sk=d['sk'], t=float(d['t']), run=d.get('run', ''), rt=float(d.get('rt', 0)), cue=d.get('cue'),
                 line=d.get('line', ''), caption=d.get('caption', ''), text=d['text'].strip(), box=d.get('box'),
                 via=d.get('via', 'text'), status='open', created=time.strftime('%H:%M:%S'), replies=[], shot=None)
        notes.append(n); save(notes)
    push({'type': 'notes'})

    def later():                                        # the screenshot takes a few seconds: print once it is there
        shot = shoot(n)
        with lock:
            notes = load()
            for x in notes:
                if x['id'] == nid: x['shot'] = shot; n.update(x)
            save(notes)
        say(line(n)); push({'type': 'notes'})
    threading.Thread(target=later, daemon=True).start()
    return n


def update(nid, d):
    with lock:
        notes = load(); n = next((x for x in notes if x['id'] == nid), None)
        if not n: return None
        who = d.get('who', 'agent')
        if d.get('status'):
            if d['status'] not in STATUS: raise ValueError('status must be one of ' + ', '.join(sorted(STATUS)))
            n['status'] = d['status']
        if d.get('text'): n['replies'].append(dict(who=who, text=d['text'].strip(), at=time.strftime('%H:%M:%S')))
        save(notes)
    if who == 'user':                                   # the user's answer wakes the agent too
        say(f'USER {nid} {n["status"]}' + (f': {d["text"].strip()}' if d.get('text') else '') + f'  (was: {n["text"]})')
    push({'type': 'notes', 'id': nid, 'who': who})
    return n


def watch():
    """Tell the pages what changed: index.html by content (preview.py rewrites it each time), the runs by mtime."""
    def page_hash():
        try: return hashlib.md5(open('index.html', 'rb').read()).hexdigest()
        except OSError: return None
    h, m = page_hash(), {f: os.path.getmtime(f) for f in glob.glob('gfx/*_r*.html')}
    while True:
        time.sleep(0.5)
        h2 = page_hash()
        if h2 and h2 != h:
            h = h2; m = {f: os.path.getmtime(f) for f in glob.glob('gfx/*_r*.html')}; push({'type': 'page'}); continue
        changed = []
        for f in glob.glob('gfx/*_r*.html'):
            t = os.path.getmtime(f)
            if m.get(f) != t: m[f] = t; changed.append(os.path.basename(f)[:-5])
        if changed:
            time.sleep(0.3)                             # let a build finish writing the batch
            for f in glob.glob('gfx/*_r*.html'): m[f] = os.path.getmtime(f)
            push({'type': 'runs', 'rids': sorted(changed)})


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store'); super().end_headers()

    def js(self, obj, code=200):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

    def body(self):
        return json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == '/api/notes':
            sk = parse_qs(u.query).get('s', [None])[0]
            with lock: notes = load()
            return self.js([n for n in notes if not sk or n['sk'] == sk])
        if u.path == '/api/events':
            self.send_response(200); self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
            q = queue.Queue(); clients.append(q)
            try:
                self.wfile.write(b'data: {"type":"hello"}\n\n'); self.wfile.flush()
                while True:
                    try: ev = q.get(timeout=15)
                    except queue.Empty: self.wfile.write(b': ping\n\n'); self.wfile.flush(); continue
                    self.wfile.write(b'data: ' + json.dumps(ev, ensure_ascii=False).encode() + b'\n\n'); self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError): pass
            finally: clients.remove(q)
            return
        return super().do_GET()

    def do_POST(self):
        u = urlparse(self.path)
        try:
            if u.path == '/api/note': return self.js(new_note(self.body()))
            if u.path.startswith('/api/note/'):
                n = update(u.path.rsplit('/', 1)[1], self.body())
                return self.js(n) if n else self.js({'error': 'no such note'}, 404)
            if u.path == '/api/reload':                 # review.py reload: force it (normally the watcher sees the change)
                d = self.body(); push({'type': 'runs', 'rids': d['rids']} if d.get('rids') else {'type': 'page'})
                return self.js({'ok': True})
        except (ValueError, KeyError) as e:
            return self.js({'error': str(e)}, 400)
        self.js({'error': 'not found'}, 404)


class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True; allow_reuse_address = True


for p in range(port, port + 20):
    try: srv = S(('127.0.0.1', p), H); break
    except OSError: continue
else: raise SystemExit(f'no free port from {port}')
json.dump({'port': p, 'pid': os.getpid()}, open('review/server.json', 'w'))
threading.Thread(target=watch, daemon=True).start()
C = json.load(open('cut.json', encoding='utf-8'))
for sk in C: say(f'REVIEW http://127.0.0.1:{p}/index.html?s={sk}')
o = [n for n in load() if n['status'] in ('open', 'question')]
say(f'notes: review/notes.json ({len(load())}, {len(o)} open)' + ('' if CHROME else ' · no Chrome found: notes get no screenshot'))
try: srv.serve_forever()
except KeyboardInterrupt: pass
