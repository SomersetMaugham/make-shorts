"""The YouTube description's chapters and source links (editing-spec 8b), from the short as rendered.

  python3 scripts/chapters.py s1                 print the block for a short
  python3 scripts/chapters.py s1 --publish 01    also write it into edit/PUBLISH.md, Short 01's YouTube description

Where the chapters come from: a line in shorts.json that opens a chapter carries `"chapter": "<title>"`; its time is
that line's start in cut.json (the recorded timeline), floored to the second. The first chapter is always 0:00.
YouTube shows chapters only when the first is 0:00, there are three or more, and each is 10 s or longer, so a chapter
that starts less than 10 s after the one before is merged into it (its title dropped, with a warning), and so is a
last chapter under 10 s; fewer than three is an error. Shorts may not show chapters in the Shorts player; the
description and the watch page do.

Where the links come from: shorts.json `"sources": [{"name": "…", "url": "https://…"}]` per short, the pages the
narration names or the screen shows (captured articles, data and weather providers), in the order they appear.
Links in a Shorts description are not clickable in the Shorts player; they are still the record of where every figure
came from.

--publish puts the block after the description's first paragraph (the summary) and before the rest (the disclaimer and
the hashtag line), replacing an earlier chapters/sources block. check_publish.py checks the chapter rules again.
"""
import json, os, re, sys

a = sys.argv[1:]
if not a: sys.exit(__doc__)
sk = a[0]
publish = a[a.index('--publish') + 1] if '--publish' in a else None
S = json.load(open('shorts.json', encoding='utf-8'))[sk]
C = json.load(open('cut.json', encoding='utf-8'))[sk]
start = {q['id']: q['start'] for q in C['cues']}
END = C['END']
MIN_LEN = 10

fmt = lambda t: f'{int(t) // 60}:{int(t) % 60:02d}'
marks = []
for L in S['lines']:
    if L.get('chapter'):
        t = 0 if not marks else int(start.get(L['id'], 0))
        marks.append([t, L['chapter']])
if not marks: sys.exit(f'chapters: no line of {sk} carries "chapter" in shorts.json')
marks[0][0] = 0
out, warn = [marks[0]], []
for t, title in marks[1:]:                       # a chapter starting under 10 s after the last kept one joins it
    if t - out[-1][0] < MIN_LEN:
        warn.append(f'"{title}" ({fmt(t)}) starts {t - out[-1][0]} s after "{out[-1][1]}": merged into it'); continue
    out.append([t, title])
while len(out) > 1 and END - out[-1][0] < MIN_LEN:   # a last chapter under 10 s joins the one before
    t, title = out.pop(); warn.append(f'"{title}" ({fmt(t)}) is the last {END - t:.0f} s: merged into "{out[-1][1]}"')
if len(out) < 3: sys.exit(f'chapters: only {len(out)} chapter(s) of 10 s or more; YouTube needs 3 (add "chapter" to more lines)')

block = '\n'.join(f'{fmt(t)} {title}' for t, title in out)
src = S.get('sources', [])
if src:
    block += '\n\n자료\n' + '\n'.join(f'· {s["name"]}: {s["url"]}' for s in src)
else:
    warn.append('no "sources" in shorts.json: the description lists no links')
print(block)
for w in warn: print('⚠ ' + w, file=sys.stderr)

if publish:
    p = os.path.join('..', 'edit', 'PUBLISH.md'); s = open(p, encoding='utf-8').read()
    head = f'## Short {publish}:'
    i = s.index(head); j = s.find('\n## Short ', i + 1); j = len(s) if j < 0 else j
    sec = s[i:j]
    yi = sec.index('### YouTube Shorts')
    m = re.search(r'\*\*Description\*\*\n```\n(.*?)\n```', sec[yi:], re.S)
    if not m: sys.exit('chapters: no YouTube Description block in ' + head)
    paras = m.group(1).split('\n\n')
    keep = [x for x in paras[1:] if not re.match(r'^\d+:\d\d ', x) and not x.startswith('자료\n')]
    desc = '\n\n'.join([paras[0], block] + keep)
    a0, a1 = yi + m.start(1), yi + m.end(1)
    s = s[:i] + sec[:a0] + desc + sec[a1:] + s[j:]
    open(p, 'w', encoding='utf-8').write(s)
    print(f'chapters: written into {p} ({head} YouTube description)', file=sys.stderr)
