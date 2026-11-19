import sys, json, os, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_gfx_common as G
# usage: build_gfx.py [tag ...]   (tag = the suffix of scripts/gfx_<tag>.py: a short like s1, or a graphics subagent's
# own module like s1a / s1b). With no tag every scripts/gfx_*.py is built.
which = sys.argv[1:] or sorted(os.path.basename(f)[4:-3] for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gfx_*.py')))
for w in which:
    mod = __import__('gfx_' + w)
    try:
        mod.build()
    except LookupError as e:                     # a builder that calls words() on a run retired in gfx/runmap.json
        print(f'gfx_{w}: {e}')
# several graphics subagents build at once: serialise the read-modify-write of the shared thumbs file with a lock dir
lock = 'gfx/.thumbs.lock'
for _ in range(600):
    try: os.mkdir(lock); break
    except FileExistsError: time.sleep(0.05)
try:
    for f, new in (('gfx/thumbs.json', G.THUMBS),):
        old = json.load(open(f, encoding='utf-8')) if os.path.exists(f) else {}
        old.update(new)
        json.dump(old, open(f, 'w'), indent=1)
finally:
    try: os.rmdir(lock)
    except OSError: pass
print('built', list(G.THUMBS))
