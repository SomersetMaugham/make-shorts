"""The agent's side of the review: read the notes the user left on the page and answer them there.
usage (inside work/, with review_server.py running):
  python3 scripts/review.py list [--all]                      the open notes (--all: every note), one line each
  python3 scripts/review.py show n003                         one note in full (time, cue, run, caption, box, screenshot, replies)
  python3 scripts/review.py reply n003 [--status S] "text"    answer on the page; S = fixing | done | question | recording | wontfix
  python3 scripts/review.py status n003 fixing                only the status
  python3 scripts/review.py reload [s1_r6 ...]                tell the page to reload those runs (or the page); normally automatic
Statuses: open (new) -> fixing -> done (rebuilt; the page offers the user 확인 / 다시) -> confirmed by the user.
question: the agent needs the user's answer (the reply is the question). recording: the fix changes a spoken line,
so it waits for the user's word to record (tts.mjs --approved is never run on a note alone)."""
import json, os, sys, urllib.request

if not os.path.exists('review/server.json'): raise SystemExit('no review/server.json: start python3 scripts/review_server.py first')
BASE = f'http://127.0.0.1:{json.load(open("review/server.json"))["port"]}'


def call(path, data=None):
    req = urllib.request.Request(BASE + path, data=None if data is None else json.dumps(data).encode(),
                                 headers={'Content-Type': 'application/json'})
    try: return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except urllib.error.HTTPError as e: raise SystemExit(json.loads(e.read()).get('error', str(e)))
    except OSError as e: raise SystemExit(f'review server not answering at {BASE} ({e}): start scripts/review_server.py')


a = sys.argv[1:]
cmd = a.pop(0) if a else 'list'
st = None
if '--status' in a: i = a.index('--status'); st = a[i + 1]; del a[i:i + 2]
if cmd == 'list':
    for n in call('/api/notes'):
        if '--all' in a or n['status'] in ('open', 'fixing', 'question'):
            print(f'{n["id"]} [{n["status"]}] {n["sk"]} {n["t"]:.2f}s {n["cue"] or "-"} {n["run"]} +{n["rt"]:.2f}s: {n["text"]}'
                  + (f'  (last reply {n["replies"][-1]["who"]}: {n["replies"][-1]["text"]})' if n['replies'] else ''))
elif cmd == 'show':
    n = next((x for x in call('/api/notes') if x['id'] == a[0]), None)
    print(json.dumps(n, ensure_ascii=False, indent=1) if n else f'no note {a[0]}')
elif cmd == 'reply':
    n = call(f'/api/note/{a[0]}', dict(text=' '.join(a[1:]), status=st, who='agent')); print(f'{n["id"]} [{n["status"]}] replied')
elif cmd == 'status':
    n = call(f'/api/note/{a[0]}', dict(status=a[1], who='agent')); print(f'{n["id"]} [{n["status"]}]')
elif cmd == 'reload':
    call('/api/reload', dict(rids=a)); print('reload sent')
else: raise SystemExit(__doc__)
