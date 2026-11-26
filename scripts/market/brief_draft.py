"""Draft lines for the morning market briefing (references/market-brief.md, step 3).

  python3 scripts/market/brief_draft.py [market_data.json] [research.json] [--sk s1] [--out brief_draft.json]

Reads the numbers (fetch_market.py) and the research step's facts (research.json, schema in market-brief.md) and
writes brief_draft.json: the briefing's beats in order, each a draft line with `id`, `scene`, `text`, `say` (numbers
already in spoken Korean: 쩜 for the point, sino-Korean digits, 원·전 for the won) and `src` (the data it came from).
Beats with no data are left out; beats that need words only the research has (the news, after hours) come as
`"todo": true` lines that Claude writes.

This is a draft, never the script: Claude rewrites every line by script-writing.md's first-time-listener gates and
market-brief.md's briefing spine, then copies the lines into shorts.json. Nothing here goes to tts.mjs directly.
"""
import argparse, datetime as dt, json, math, os, sys

DIG = '영일이삼사오육칠팔구'


def sino(n):
    """Sino-Korean reading of a non-negative integer: 1343 -> 천삼백사십삼, 10000 -> 만, 20500 -> 이만 오백."""
    n = int(n)
    if n == 0: return '영'
    groups, out = [], []
    while n: groups.append(n % 10000); n //= 10000
    for gi in range(len(groups) - 1, -1, -1):
        g = groups[gi]
        if not g: continue
        s = ''
        for unit, v in (('천', g // 1000), ('백', g // 100 % 10), ('십', g // 10 % 10)):
            if v: s += ('' if v == 1 else DIG[v]) + unit
        if g % 10: s += DIG[g % 10]
        big = ['', '만', '억', '조'][gi]
        if big == '만' and g == 1: s = ''
        out.append(s + big)
    return ' '.join(out)


def decimal(x, places):
    """3.91 -> 삼쩜 구일, 0.85 -> 영쩜 팔오, 3.0 -> 삼 (references/narration.md §3: the point is 쩜, joined)."""
    s = f'{abs(x):.{places}f}'
    whole, _, frac = s.partition('.')
    frac = frac.rstrip('0')
    return sino(int(whole)) + ('쩜 ' + ''.join(DIG[int(c)] for c in frac) if frac else '')


def josa(word, pair):
    """The particle that fits the word's last sound: josa('마이크론', '이/가') -> '마이크론이'. Latin endings
    (AMD, RTX, TSMC) are read as letters, which end in a vowel, so they take the second form."""
    a, b = pair.split('/')
    ch = word.rstrip()[-1]
    final = (ord(ch) - 0xAC00) % 28 if '가' <= ch <= '힣' else 0
    if a == '으로': return word + ('로' if final in (0, 8) else '으로')   # ㄹ batchim takes 로
    return word + (a if final else b)


def pct_text(p): return ('▲ +' if p > 0 else '▼ −' if p < 0 else '') + f'{abs(p):.2f}%'
def pct_plain(p): return f'{abs(p):.2f}%'
def pct_say(p): return decimal(round(abs(p), 2), 2) + ' 퍼센트'
def verb(p, up='올랐', down='내렸', flat='보합이었'): return up if p > 0 else down if p < 0 else flat


def won(x):
    """1343.54 -> ('1,343.5원', '천삼백사십삼 원 오십 전'): the won to one decimal, the decimal read as 전."""
    x = round(x, 1); w = int(x); jeon = round((x - w) * 100)
    return f'{x:,.1f}원', sino(w) + ' 원' + (f' {sino(jeon)} 전' if jeon else '')


def temp(t):
    t = math.floor(t + 0.5)   # half up: 14.5 -> 15 (Python's round() gives 14)
    return f'{"영하 " if t < 0 else ""}{abs(t)}도', f'{"영하 " if t < 0 else ""}{sino(abs(t))} 도'


def us_dst(d):   # US daylight time: second Sunday of March to first Sunday of November
    m2 = dt.date(d.year, 3, 8); m2 += dt.timedelta((6 - m2.weekday()) % 7)
    n1 = dt.date(d.year, 11, 1); n1 += dt.timedelta((6 - n1.weekday()) % 7)
    return m2 <= d < n1


# US mover group -> the Korean sector to watch (market-brief.md "US -> Korea map"; a watch point, never a pick)
KR_MAP = {
    'semis': ('미국 반도체주', '국내 반도체 대형주'), 'semi_equip': ('미국 반도체 장비주', '국내 반도체 소부장'),
    'apple': ('애플', '국내 애플 부품주'), 'bigtech': ('미국 빅테크', '국내 인터넷·플랫폼주'),
    'ev': ('테슬라', '국내 2차전지주'), 'power': ('미국 전력주', '국내 전력기기·원전주'),
    'obesity': ('비만치료제 기업', '국내 바이오주'), 'defense': ('미국 방산주', '국내 방산주'), 'oil': ('정유주', '국내 정유주'),
}
TERM_LINES = {   # a suggestion for the day of a term; Claude rewrites it in the narrator's voice
    '동지': ('오늘은 밤이 가장 긴 동지입니다. 점심에는 가까운 분들과 팥죽 한 그릇 어떠세요?', None),
    '입춘': ('오늘은 봄의 문턱, 입춘입니다. 아직 바람은 차니 옷차림은 따뜻하게 챙기세요.', None),
    '하지': ('오늘은 낮이 가장 긴 하지입니다. 퇴근길까지 해가 길게 남아 있겠습니다.', None),
    '입동': ('오늘은 겨울이 시작된다는 입동입니다. 이제 아침 기온이 부쩍 낮아집니다.', None),
    '소설': ('오늘은 첫눈이 온다는 소설입니다. 출근길 옷차림 한 겹 더 챙기세요.', None),
    '대설': ('오늘은 눈이 많이 온다는 대설입니다. 빙판길 출근 조심하세요.', None),
    '소한': ('오늘은 한 해 가운데 가장 춥다는 소한입니다. 출근길 단단히 챙겨 입으세요.', None),
    '대한': ('오늘은 큰 추위라는 대한입니다. 따뜻하게 입고 나오세요.', None),
    '처서': ('오늘은 더위가 물러간다는 처서입니다. 아침저녁으로 바람이 한결 선선해집니다.', None),
    '경칩': ('오늘은 개구리가 깨어난다는 경칩입니다. 봄기운이 한 걸음 더 다가왔습니다.', None),
}
SIGNOFF = dict(before_weather='오늘 날씨 알려드리면서 브리핑을 마치겠습니다.', end='감사합니다.')   # the user, 2026-11-26


def sgn(x, flat=0.0):
    return 0 if x is None or abs(x) <= flat else (1 if x > 0 else -1)


def signals(m, r):
    """The night's signals for the Korean open, each as a number (sign = the direction it points). outlook_log.py
    records them every day so their hit rates can be compared (market-brief.md "The outlook record")."""
    ix = m.get('indices', {}); g = lambda k: (ix.get(k) or {}).get('change_pct')
    nf = (r.get('night_futures') or {}).get('change_pct')
    ndf = r.get('ndf') or {}
    return dict(night_futures=nf, sox=g('sox'), nasdaq=g('nasdaq'), sp500=g('sp500'),
                ndf_change=ndf.get('change'),                     # won per dollar: up = a weaker won = against stocks
                vix_change=g('vix'), kospi_prev=(r.get('kospi_prev') or {}).get('change_pct', g('kospi')),
                street=sum({'up': 1, 'down': -1}.get(v.get('direction'), 0) for v in r.get('street_view', [])))


def outlook(m, r):
    """A first reading of the direction of the open, for Claude to check against the research: night futures and the
    brokers' views count twice, SOX and Nasdaq once, the NDF won against. |score| >= 2 picks a side, else 'mixed'."""
    s = signals(m, r)
    if s['night_futures'] is None and not r.get('street_view'): return None
    parts = [('야간선물', 2 * sgn(s['night_futures'], 0.1)), ('증권가', 2 * sgn(s['street'])), ('SOX', sgn(s['sox'], 0.3)),
             ('나스닥', sgn(s['nasdaq'], 0.3)), ('NDF', -sgn(s['ndf_change'], 1.0))]
    score = sum(v for _, v in parts)
    return dict(direction='up' if score >= 2 else 'down' if score <= -2 else 'mixed', score=score,
                why=', '.join(f'{k} {v:+d}' for k, v in parts), signals=s)


WEATHER_PRIORITY = ['cold_wave', 'cold_drop', 'snow', 'rain', 'dust', 'heat', 'big_range', 'warm_up']


def weather_line(note, w):
    lo, lo_s = temp(w['today']['low']); hi, hi_s = temp(w['today']['high'])
    k = note['kind']
    if k in ('cold_wave', 'cold_drop'):
        d = abs(round(note['value'])) if k == 'cold_drop' else None
        t = f'오늘 아침 {w["city"]} 기온은 {lo}' + (f'로 어제보다 {d}도 낮습니다' if d else '까지 내려갑니다') + '. 감기 조심하세요.'
        s = f'오늘 아침 {w["city"]} 기온은 {lo_s}' + (f'로 어제보다 {sino(d)} 도 낮습니다' if d else '까지 내려갑니다') + '. 감기 조심하세요.'
    elif k == 'snow': t = s = f'오늘 {w["city"]}에는 눈 소식이 있습니다. 출근길 미끄러지지 않게 조심하세요.'
    elif k == 'rain': t = s = f'오늘 {w["city"]}에는 비 소식이 있습니다. 우산 챙겨서 나오세요.'
    elif k == 'dust': t = s = '오늘은 미세먼지가 나쁨 수준입니다. 출근길 마스크 챙기세요.'
    elif k == 'heat':
        t = f'오늘 낮 {w["city"]}은 {hi}까지 오릅니다. 물 자주 드세요.'; s = f'오늘 낮 {w["city"]}은 {hi_s}까지 오릅니다. 물 자주 드세요.'
    elif k == 'big_range':
        t = f'오늘은 아침 {lo}, 낮 {hi}로 일교차가 큽니다. 겉옷 하나 챙기세요.'
        s = f'오늘은 아침 {lo_s}, 낮 {hi_s}로 일교차가 큽니다. 겉옷 하나 챙기세요.'
    else:
        d = round(note['value'])
        t = f'오늘 아침은 어제보다 {d}도 포근한 {lo}입니다.'; s = f'오늘 아침은 어제보다 {sino(d)} 도 포근한 {lo_s}입니다.'
    return t, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('market', nargs='?', default='market_data.json'); ap.add_argument('research', nargs='?', default='research.json')
    ap.add_argument('--sk', default='s1'); ap.add_argument('--out', default='brief_draft.json')
    a = ap.parse_args()
    m = json.load(open(a.market, encoding='utf-8'))
    r = json.load(open(a.research, encoding='utf-8')) if os.path.exists(a.research) else {}
    ix, lines = m.get('indices', {}), []
    # only cross-checked numbers are spoken (the user, 2026-11-26): an index or stock whose two sources disagree, or that
    # only one source has, is left out here and shown in `unconfirmed` for Claude to check against the news
    unconfirmed = [k for k, v in ix.items() if v.get('check', {}).get('status') in ('mismatch', 'single', 'stale', 'missing')]
    unconfirmed += [w['ticker'] for w in m.get('watch', []) if w.get('check', {}).get('status', 'ok') != 'ok']
    m['watch'] = [w for w in m.get('watch', []) if w.get('check', {}).get('status', 'ok') == 'ok']

    def add(scene, text, say=None, src='', todo=False, figures=None):
        lines.append(dict(id=f'c{len(lines) + 1:02d}', scene=scene, text=text, say=say or text, src=src,
                          **({'figures': figures} if figures else {}), **({'todo': True} if todo else {})))

    if ix:
        sp, nq, sox = ix['sp500']['change_pct'], ix['nasdaq']['change_pct'], ix['sox']['change_pct']
        movers = sorted(m.get('watch', []), key=lambda x: abs(x['change_pct']), reverse=True)
        lead = movers[0] if movers else None
        # 1 hook: the night in one line (Claude sharpens it: the one thing that moved the market)
        if abs(sox) >= 1.5: mood = f'반도체가 크게 {"끌어올렸" if sox > 0 else "끌어내렸"}습니다'
        elif sp * nq < 0: mood = '지수마다 방향이 엇갈렸습니다'
        else: mood = f'{"오름세" if sp > 0 else "내림세"}로 마감했습니다'
        add('headline', f'간밤 미국 증시는 {mood}.', src='indices.sp500/nasdaq/sox')
        # 1b the question the outlook answers (the user, 2026-11-26: ask in the opening, answer before the weather)
        kp = (r.get('kospi_prev') or {}).get('change_pct', (ix.get('kospi') or {}).get('change_pct'))   # the news first: Yahoo can miss a session
        q = ('반등할 수 있을까요' if kp is not None and kp <= -1 else '상승을 이어갈 수 있을까요' if kp is not None and kp >= 1
             else '어느 쪽으로 출발할까요')
        add('question', f'오늘 국장은 {q}?', src=f'indices.kospi {kp:+.2f}% (the previous Korean session)' if kp is not None else 'no KOSPI close')
        # 2 the big indices. `text` (the caption) says what `say` says, in plain numbers; the signed ▲/▼ values for
        # the cards go in `figures` (market-brief.md "Colours and signs")
        fig = lambda label, p: dict(label=label, value=pct_text(p), dir='up' if p > 0 else 'down' if p < 0 else 'flat')
        if sp * nq > 0 or sp == nq == 0:
            add('number', f'S&P 500은 {pct_plain(sp)}, 나스닥은 {pct_plain(nq)} {verb(sp)}습니다.',
                f'에스앤피 오백은 {pct_say(sp)}, 나스닥은 {pct_say(nq)} {verb(sp)}습니다.', 'indices.sp500/nasdaq',
                figures=[fig('S&P 500', sp), fig('NASDAQ', nq)])
        else:
            add('number', f'S&P 500은 {pct_plain(sp)} {verb(sp, "올랐고", "내렸고", "보합이었고")}, 나스닥은 {pct_plain(nq)} {verb(nq)}습니다.',
                f'에스앤피 오백은 {pct_say(sp)} {verb(sp, "올랐고", "내렸고", "보합이었고")}, 나스닥은 {pct_say(nq)} {verb(nq)}습니다.',
                'indices.sp500/nasdaq', figures=[fig('S&P 500', sp), fig('NASDAQ', nq)])
        # 3 SOX, the index Korea's chip makers follow
        add('bars', f'우리 반도체와 함께 움직이는 필라델피아 반도체 지수는 {pct_plain(sox)} {verb(sox)}습니다.',
            f'우리 반도체와 함께 움직이는 필라델피아 반도체 지수는 {pct_say(sox)} {verb(sox)}습니다.', 'indices.sox',
            figures=[fig('SOX', sox)] + [fig(x['ticker'], x['change_pct']) for x in sorted((w for w in m.get('watch', []) if w['group'] == 'semis'), key=lambda w: -abs(w['change_pct']))][:4])
        # 4 rates and VIX, only on a day they matter (market-brief.md: |10y| >= 10 bp, VIX >= 25 or moved >= 10%)
        ty, vx = ix['us10y'], ix['vix']
        bp = round(ty['change'] * 100)
        if abs(bp) >= 10:
            add('number', f'미 국채 10년물 금리는 {ty["close"]:.2f}%로 {abs(bp)}bp {verb(bp)}습니다.',
                f'미 국채 십 년물 금리는 {decimal(round(ty["close"], 2), 2)} 퍼센트로 {decimal(abs(bp) / 100, 2)} 퍼센트포인트 {verb(bp)}습니다.',
                'indices.us10y', figures=[dict(label='US10Y', value=f'{ty["close"]:.2f}% ({bp:+d}bp)', dir='up' if bp > 0 else 'down')])
        if vx['close'] >= 25 or abs(vx['change_pct']) >= 10:
            v1 = round(vx['close'], 1); vs = decimal(v1, 1); pp = josa(vs, '으로/로')[len(vs):]
            add('pair', f'공포지수라 불리는 VIX는 {v1}{pp} {verb(vx["change_pct"], "올랐", "내려왔", "그대로였")}습니다.',
                f'공포지수라 불리는 브이아이엑스는 {vs}{pp} {verb(vx["change_pct"], "올랐", "내려왔", "그대로였")}습니다.',
                'indices.vix', figures=[fig('VIX', vx['change_pct'])])
        # 5 the heatmap: the colour of the night, then the names that drove it
        up = [x for x in m.get('watch', []) if x['change_pct'] > 0][:2]
        dn = sorted([x for x in m.get('watch', []) if x['change_pct'] < 0], key=lambda x: x['change_pct'])[:2]
        if up or dn:
            def part(xs, num, end): return ', '.join(f'{josa(x["name"], "이/가")} {num(x["change_pct"])}' for x in xs) + end
            t = '히트맵에서는 ' + ', '.join(filter(None, [part(dn, pct_plain, ' 내렸고') if dn else '', part(up, pct_plain, ' 올랐습니다') if up else '']))
            s = '히트맵에서는 ' + ', '.join(filter(None, [part(dn, pct_say, ' 내렸고') if dn else '', part(up, pct_say, ' 올랐습니다') if up else '']))
            if not up: t, s = t[:-3] + '습니다', s[:-3] + '습니다'
            add('capture', t + '.', s + '.', 'watch + heatmap', figures=[fig(x['ticker'], x['change_pct']) for x in dn + up])
    # 6 the news that moved the market, 7 after hours: Claude writes them from research.json
    for n in r.get('news', [])[:2]:
        add('news', f'TODO 뉴스: {n.get("fact", "")}', src=f'research.news: {n.get("source", "")}', todo=True)
    ah = r.get('after_hours')
    if ah: add('number', f'TODO 시간외: {ah.get("name")} {ah.get("change_pct")}% · {ah.get("event")}', src=f'research.after_hours: {ah.get("source")}', todo=True)
    # 8 the won and the night futures
    fx = r.get('ndf') or ({'value': ix['usdkrw']['close'], 'source': 'Yahoo KRW=X'} if ix.get('usdkrw', {}).get('close') else None)
    nf = r.get('night_futures')
    if fx or nf:
        pt, ps, figs = [], [], []
        if fx:
            wt, ws = won(fx['value']); pt.append(f'원/달러 환율은 {wt}'); ps.append(f'원 달러 환율은 {ws}')
            figs.append(dict(label='USD/KRW', value=wt, dir='flat'))
        if nf:
            pt.append(f'코스피200 야간선물은 {pct_plain(nf["change_pct"])} {verb(nf["change_pct"])}습니다')
            ps.append(f'코스피 야간선물은 {pct_say(nf["change_pct"])} {verb(nf["change_pct"])}습니다')
            figs.append(fig('KOSPI200 야간선물', nf['change_pct']))
        tail = '' if nf else '입니다'
        add('pair', ', '.join(pt) + tail + '.', ', '.join(ps) + tail + '.',
            f'ndf: {fx.get("source") if fx else "-"} · night_futures: {nf.get("source") if nf else "-"}', figures=figs)
    # 9 the outlook: the answer to 1b, from the night's signals and the brokers' views (market-brief.md "The outlook")
    ol = outlook(m, r)
    if ol:
        kp = (r.get('kospi_prev') or {}).get('change_pct', (ix.get('kospi') or {}).get('change_pct')) or 0
        say_dir = {'up': '반등 출발' if kp < 0 else '상승 출발', 'down': '약세 출발', 'mixed': '방향을 탐색하는 출발'}[ol['direction']]
        add('outlook', f'밤사이 신호와 증권가 시각을 종합하면, 오늘 코스피는 {say_dir} 가능성이 큽니다.'
            if ol['direction'] != 'mixed' else '밤사이 신호가 엇갈려, 오늘 코스피는 방향을 정하기 어려운 출발이 예상됩니다.',
            src=f'outlook score {ol["score"]:+d}: {ol["why"]}')
        ev = (r.get('korea_today') or r.get('events_tonight') or [None])[0]
        add('outlook', f'다만 {ev.get("short") or ev["name"]} 결과에 따라 장중 흔들림이 커질 수 있습니다.' if ev else 'TODO 변수: 판단이 바뀔 수 있는 오늘의 변수 한 줄',
            src=f'caveat: {ev.get("source") if ev else "-"}', todo=not ev)
    # 9b a sector to watch (never a buy or sell call), only on a strong US group move
    if ix and lead and lead['group'] in KR_MAP and abs(lead['change_pct']) >= 2:
        us, kr = KR_MAP[lead['group']]
        add('diagram', f'간밤 {josa(us, "이/가")} {verb(lead["change_pct"])}던 만큼, 오늘은 {kr} 흐름을 지켜볼 만합니다.',
            src=f'watch.{lead["ticker"]} {lead["change_pct"]:+}% -> KR_MAP.{lead["group"]}')
    # 10 tonight: the US session and the events (research)
    tn = m['session']['tonight']
    day = dt.date.fromisoformat(m['date'])
    if not tn['trading']: add('calendar', f'오늘 밤 미국 증시는 {josa(tn["holiday"], "으로/로")} 쉽니다.', src='session.tonight')
    elif tn['early_close']:
        h = 2 if us_dst(day) else 3
        add('calendar', f'오늘 밤 미국 증시는 {josa(tn["early_close"], "이라/라")} 새벽 {h}시에 일찍 문을 닫습니다.',
            f'오늘 밤 미국 증시는 {josa(tn["early_close"], "이라/라")} 새벽 {"두" if h == 2 else "세"} 시에 일찍 문을 닫습니다.', 'session.tonight (13:00 ET)')
    for e in r.get('events_tonight', [])[:1]:
        add('calendar', f'TODO 일정: {e.get("time_kst")} {e.get("name")}', src=f'research.events_tonight: {e.get("source")}', todo=True)
    # 11 the channel's sign-off opens the weather and closes the short (the user's words, 2026-11-26; project.json
    #    market_signoff overrides): "오늘 날씨 알려드리면서 브리핑을 마치겠습니다." ... weather ... "감사합니다."
    so = SIGNOFF
    if os.path.exists('project.json'):
        so = json.load(open('project.json', encoding='utf-8')).get('market_signoff', so)
    if isinstance(so, str): so = dict(before_weather=so, end='')
    if so.get('before_weather'): add('signoff', so['before_weather'], src='sign-off (before the weather)')
    term = (m.get('season') or {}).get('today')
    if term and term['name'] in TERM_LINES and not term.get('near_midnight'):
        for sent in TERM_LINES[term['name']][0].split('. '):
            add('season', sent if sent.endswith(('.', '?')) else sent + '.', src=f'season.today {term["name"]} {term["kst"]}')
    elif term and not term.get('near_midnight'):
        add('season', f'오늘은 절기상 {term["name"]}입니다.', src=f'season.today {term["name"]}')
    wx = m.get('weather') or {}
    notes = sorted(wx.get('notes', []), key=lambda n: WEATHER_PRIORITY.index(n['kind']))
    # the weather run is there every day: Seoul (the spoken city) said in one line, the other cities on the card
    # (the user, 2026-11-26: 부산·대구·대전·광주·인천 low / high, sky, rain); a trigger adds its line of care
    if wx.get('today'):
        td = wx['today']; lo, lo_s = temp(td['low']); hi, hi_s = temp(td['high'])
        cond = {'맑음': '맑겠습니다', '구름많음': '구름이 많겠습니다', '흐림': '흐리겠습니다'}[td['sky']]
        if td.get('precip'): cond = f'{td["precip"]} 소식이 있습니다'
        card = [dict(city=r['city'], low=temp(r['low'])[0], high=temp(r['high'])[0], sky=r['sky'], precip=r['precip'])
                for r in wx.get('regions', [])]
        add('season', f'오늘 {wx["city"]}은 아침 {lo}, 낮 {hi}로 {cond}.', f'오늘 {wx["city"]}은 아침 {lo_s}, 낮 {hi_s}로 {cond}.',
            'weather.today + weather.regions (card)', figures=card)
    notes = [n for n in notes if n['kind'] != 'warm_up']   # the base line already gives the temperature
    if notes:
        t, s = weather_line(notes[0], m['weather'])
        pairs = list(zip(t.split('. '), s.split('. ')))
        if notes[0]['kind'] in ('rain', 'snow'): pairs = pairs[-1:]   # the base line said 비/눈 소식; keep the care line
        for ti, si in pairs:   # one sentence per line (one cue each); same scene = one run
            add('season', ti.rstrip('.') + ('.' if not ti.endswith('?') else ''), si.rstrip('.') + ('.' if not si.endswith('?') else ''),
                f'weather.notes.{notes[0]["kind"]}: {notes[0]["fact"]}')
    if so.get('end'): add('thanks', so['end'], src='sign-off (the last line)')
    # neighbours may not share a scene kind (editing-spec 3): Claude fixes any repeat while editing (the season
    # beat's two sentences share one run on purpose)
    rep = [f'{a_["id"]}/{b["id"]} {a_["scene"]}' for a_, b in zip(lines, lines[1:]) if a_['scene'] == b['scene'] and a_['scene'] not in ('season', 'outlook')]
    out = dict(sk=a.sk, date=m['date'], disclaimer='투자 권유가 아닌 정보 제공 목적입니다. 투자 판단의 책임은 본인에게 있습니다.',
               outlook=ol, unconfirmed=unconfirmed, repeated_scene_neighbours=rep, lines=lines)
    json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for x in lines:                                    # an index line built on an unconfirmed number waits for Claude
        keys = [k for k in unconfirmed if f'indices.{k}' in x['src'] or f'/{k}' in x['src']]
        if keys and not x.get('todo'):
            x['todo'] = True; x['text'] = f'확인 필요({",".join(keys)}): ' + x['text']
    if unconfirmed: print(f'⚠ not cross-checked, left out or to confirm before speaking: {", ".join(unconfirmed)}')
    print(f'brief_draft: {a.out} · {len(lines)} lines · todo {sum(1 for x in lines if x.get("todo"))}'
          + (f' · same scene side by side: {rep}' if rep else ''))
    for x in lines: print(f'  {x["id"]} [{x["scene"]}] {x["text"]}\n      say: {x["say"]}')


if __name__ == '__main__':
    main()
