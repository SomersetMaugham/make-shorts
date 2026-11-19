"""Check edit/PUBLISH.md against the publishing rules (editing-spec 8b) before handing it over.
usage: $PY scripts/check_publish.py [../edit/PUBLISH.md]      exit 1 on a broken rule; warnings don't fail
Errors: a YouTube title wider than 54 columns (Hangul and other wide characters count 2: the feed cuts by width), emoji or
# in it, or a duplicate; not exactly three hashtags (or filler tags) on the description's last line; a TikTok hook of 100+
or an Instagram hook of 125+ characters; URLs in the TikTok / Instagram captions; 3-5 hashtags broken (Instagram max 5);
a missing thumbnail file; a line sending viewers to a "full video" (there is none: these shorts stand alone).
Warnings: no power word in the title, a long description or TikTok caption."""
import os, re, sys, unicodedata

PATH = sys.argv[1] if len(sys.argv) > 1 else '../edit/PUBLISH.md'
POWER = ('비밀', '숨겨진', '진실', '드디어', '절대', '멈추', '당장', '무료', '검증', '미친', '충격', '실수', '이겼', '이긴', '끝났',
         '폭로', '아무도', '틀렸', '최악', '최고', '유일', '진짜', '놀라', '함정', '몰랐', '반전', '경고', '왜',
         'secret', 'hidden', 'truth', 'finally', 'never', 'stop', 'free', 'proven', 'insane', 'mistake', 'beats', 'shocking')
FILLER = {'#shorts', '#short', '#viral', '#fyp', '#foryou', '#foryoupage', '#trending', '#쇼츠', '#추천', '#인기', '#알고리즘'}
TAG = re.compile(r'^#[0-9A-Za-z가-힣_]+$')
EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿]')
FULL_VIDEO = re.compile(r'full video|전체 영상|풀영상|풀 영상|본편|link in bio|프로필 링크', re.I)

text = open(PATH, encoding='utf-8').read()
base = os.path.dirname(os.path.abspath(PATH))
errs, warns, titles = [], [], {}


def width(s):
    return sum(2 if unicodedata.east_asian_width(ch) in 'WF' else 1 for ch in s)


def tags(line, lo, hi, where):
    t = line.split()
    if not lo <= len(t) <= hi: errs.append(f'{where}: {len(t)} hashtags on the last line (want {lo}-{hi})')
    for x in t:
        if not TAG.match(x): errs.append(f'{where}: "{x}" is not a hashtag (letters, digits, Hangul; no spaces or punctuation)')
        if x.lower() in FILLER: errs.append(f'{where}: filler hashtag {x}')


def block_after(sec, marker, start=0):
    i = sec.find(marker, start)
    if i < 0: return None, -1
    m = re.search(r'```\n(.*?)\n```', sec[i:], re.S)
    return (m.group(1), i + m.end()) if m else (None, -1)


for sec in re.split(r'\n(?=## Short )', text)[1:]:
    name = sec.splitlines()[0][3:].split('  ')[0]
    m = re.search(r'!\[[^\]]*\]\(([^)]+)\)', sec)
    if not m or not os.path.exists(os.path.join(base, m.group(1))): errs.append(f'{name}: thumbnail file missing ({m.group(1) if m else "no image"})')
    yt = sec.find('### YouTube Shorts'); tt = sec.find('### TikTok'); ig = sec.find('### Instagram Reels')
    if min(yt, tt, ig) < 0: errs.append(f'{name}: needs the YouTube Shorts, TikTok and Instagram Reels subsections'); continue
    title, _ = block_after(sec, '**Title**', yt)
    desc, _ = block_after(sec, '**Description**', yt)
    ttc, _ = block_after(sec, '**Caption**', tt)
    igc, _ = block_after(sec, '**Caption**', ig)
    if title is None or desc is None or ttc is None or igc is None: errs.append(f'{name}: a copy block is missing'); continue
    title = title.strip()
    if width(title) > 54: errs.append(f'{name}: YouTube title is {width(title)} columns wide (54 at most; Hangul counts 2): {title}')
    if '#' in title or EMOJI.search(title): errs.append(f'{name}: no emoji or hashtags in the title')
    if not any(p in title.lower() for p in POWER): warns.append(f'{name}: no power word in the title: {title}')
    if title.lower() in titles: errs.append(f'{name}: same title as {titles[title.lower()]}')
    titles[title.lower()] = name
    paras = desc.split('\n\n')
    if len(paras[0]) > 150: warns.append(f'{name}: description opener is {len(paras[0])} characters (about 150 at most in Korean)')
    tags(desc.strip().splitlines()[-1], 3, 3, f'{name} YouTube')
    for cap, where, hook_max, hi in ((ttc, 'TikTok', 100, 5), (igc, 'Instagram', 125, 5)):
        lines = cap.strip().splitlines()
        if len(lines[0]) >= hook_max: errs.append(f'{name} {where}: hook is {len(lines[0])} characters (under {hook_max})')
        if re.search(r'https?://|www\.', cap): errs.append(f'{name} {where}: URLs are not clickable in captions; remove them')
        tags(lines[-1], 3, hi, f'{name} {where}')
    for where, block in (('YouTube description', desc), ('TikTok', ttc), ('Instagram', igc)):
        if FULL_VIDEO.search(block): errs.append(f'{name} {where}: sends viewers to a full video; these shorts stand alone')
    if len(ttc) > 300: warns.append(f'{name} TikTok: caption is {len(ttc)} characters (about 200 is the target in Korean)')
    print(f'{name}: title {width(title)} cols, TikTok hook {len(ttc.splitlines()[0])}, Instagram hook {len(igc.splitlines()[0])}')

for w in warns: print('warning:', w)
for e in errs: print('ERROR:', e)
print('PUBLISH.md OK' if not errs else f'{len(errs)} error(s)')
sys.exit(1 if errs else 0)
