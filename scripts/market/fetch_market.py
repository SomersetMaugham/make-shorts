"""The morning market briefing's numbers (references/market-brief.md, step 1): one file, market_data.json.

  .venv/bin/python scripts/market/fetch_market.py [--date 2026-11-26] [--city 서울] [--out market_data.json]
                                                  [--no-heatmap] [--heatmap captures/finviz_<date>.png]

What it collects, and from where (every value keeps its source and the session date it belongs to):
- Every number is fetched twice and cross-checked (`check` on each index and stock): Yahoo via yfinance and CNBC's
  quote service. brief_draft.py speaks only numbers whose `check.status` is 'ok'.
- US closes of the last completed session: S&P 500, Nasdaq, Dow, SOX (Philadelphia semiconductor index), the 10-year
  Treasury yield, VIX, and the watch list of single stocks (references/market-brief.md "The watch list"), through
  yfinance (Yahoo Finance; unofficial, so the research step checks every figure that is spoken against a second
  source). The dollar-won rate here is Yahoo's KRW=X spot; the briefing speaks the NDF 1-month rate from the research
  step when there is one.
- The US session calendar: the last completed session, whether a holiday fell in between, and whether tonight's US
  session is a holiday or an early close (NYSE rules computed here; Korean holidays come from the research step).
- The Finviz S&P 500 heatmap (headless Chrome; 2x scale, cropped to the map). LOOK at the PNG: an ad or a layout change
  moves the crop. Finviz's own timestamp line is kept in the full screenshot (`*_full.png`) as the capture's proof.
- Weather for one city (Open-Meteo forecast + air quality, no key): today's and yesterday's low/high, rain or snow
  chance, PM10 / PM2.5 day means, and the notes that pass a trigger (market-brief.md "The weather and season line").
- The 24 solar terms (절기) computed from the Sun's apparent longitude (Meeus, low precision: ~15 min), in KST. A term
  within 30 min of midnight is flagged: check it against KASI (천문연구원) before saying it.

Nothing here writes narration. brief_draft.py turns this file (plus research.json) into draft lines for Claude to edit.
"""
import argparse, datetime as dt, json, math, os, subprocess, sys, urllib.parse, urllib.request

KST = dt.timezone(dt.timedelta(hours=9))
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131 Safari/537.36'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

INDICES = {   # key: (Yahoo symbol, Korean name)
    'sp500': ('^GSPC', 'S&P 500'), 'nasdaq': ('^IXIC', '나스닥'), 'dow': ('^DJI', '다우'),
    'sox': ('^SOX', '필라델피아 반도체 지수'), 'us10y': ('^TNX', '미 국채 10년물 금리'), 'vix': ('^VIX', 'VIX'),
    'usdkrw': ('KRW=X', '원/달러 (야후 현물)'), 'kospi': ('^KS11', '코스피 (전 거래일)'),
}
# The watch list: the US names whose moves Korean sectors follow (market-brief.md "US -> Korea map").
WATCH = [
    ('NVDA', '엔비디아', 'semis'), ('MU', '마이크론', 'semis'), ('AVGO', '브로드컴', 'semis'), ('AMD', 'AMD', 'semis'),
    ('TSM', 'TSMC', 'semis'), ('AMAT', '어플라이드 머티리얼즈', 'semi_equip'), ('LRCX', '램리서치', 'semi_equip'),
    ('AAPL', '애플', 'apple'), ('MSFT', '마이크로소프트', 'bigtech'), ('GOOGL', '알파벳', 'bigtech'),
    ('AMZN', '아마존', 'bigtech'), ('META', '메타', 'bigtech'), ('TSLA', '테슬라', 'ev'),
    ('GEV', 'GE 버노바', 'power'), ('VST', '비스트라', 'power'), ('CEG', '컨스텔레이션 에너지', 'power'),
    ('LLY', '일라이 릴리', 'obesity'), ('NVO', '노보 노디스크', 'obesity'), ('LMT', '록히드 마틴', 'defense'),
    ('RTX', 'RTX', 'defense'), ('XOM', '엑슨모빌', 'oil'),
]
CITIES = {'서울': (37.5665, 126.9780), '부산': (35.1796, 129.0756), '대구': (35.8714, 128.6014),
          '인천': (37.4563, 126.7052), '광주': (35.1595, 126.8526), '대전': (36.3504, 127.3845)}

SOLAR_TERMS = ['춘분', '청명', '곡우', '입하', '소만', '망종', '하지', '소서', '대서', '입추', '처서', '백로',
               '추분', '한로', '상강', '입동', '소설', '대설', '동지', '소한', '대한', '입춘', '우수', '경칩']
# Customs a line may mention on the day (market-brief.md); a term without one is said by name and meaning only.
TERM_CUSTOMS = {
    '입춘': '봄의 시작, 대문에 입춘첩을 붙이는 날', '경칩': '개구리가 깨어난다는 날', '춘분': '낮과 밤의 길이가 같아지는 날',
    '하지': '낮이 가장 긴 날', '입추': '가을의 시작', '처서': '더위가 물러간다는 날', '추분': '밤이 낮보다 길어지기 시작하는 날',
    '입동': '겨울의 시작, 김장을 준비하는 무렵', '소설': '첫눈이 내린다는 날', '대설': '눈이 많이 내린다는 날',
    '동지': '밤이 가장 긴 날, 팥죽을 먹는 날', '소한': '한 해 중 가장 춥다는 무렵', '대한': '큰 추위라는 날',
}


# ---------------------------------------------------------------- US market data
def quotes(symbols, before=None):
    """before: {symbol: 'YYYY-MM-DD'} keeps only bars dated earlier (the KOSPI's last session before a briefing made
    while the Korean market is open: yfinance's last bar is then today's, still moving)."""
    before = before or {}
    try:
        import yfinance as yf
    except ImportError:
        sys.exit('fetch_market: yfinance is missing. Install it into the project venv:\n'
                 '  uv pip install --python .venv/bin/python yfinance')
    out = {}
    for sym in symbols:
        h = yf.Ticker(sym).history(period='10d', auto_adjust=False)
        h = h[h['Close'].notna()]
        if sym in before: h = h[[str(i.date()) < before[sym] for i in h.index]]
        if len(h) < 2:
            out[sym] = None; continue
        last, prev = h.iloc[-1], h.iloc[-2]
        c, p = float(last['Close']), float(prev['Close'])
        out[sym] = dict(date=str(h.index[-1].date()), close=round(c, 4), prev_date=str(h.index[-2].date()),
                        prev_close=round(p, 4), change=round(c - p, 4), change_pct=round((c - p) / p * 100, 2))
    return out


CNBC = {'^GSPC': '.SPX', '^IXIC': '.IXIC', '^DJI': '.DJI', '^SOX': '.SOX', '^TNX': 'US10Y', '^VIX': '.VIX',
        'KRW=X': 'KRW=', '^KS11': '.KS11'}                     # Yahoo symbol -> CNBC symbol; stocks keep their ticker


def cnbc_quotes(yahoo_syms):
    """The second source for every number (the user, 2026-11-26: cross-check prices and indices): CNBC's public quote
    service, no key. Returns {yahoo symbol: {close, prev_close, change_pct, date}}; date is the session's date in the
    exchange's own time zone, read from last_time."""
    out, syms = {}, [CNBC.get(s, s) for s in yahoo_syms]
    back = {CNBC.get(s, s): s for s in yahoo_syms}
    num = lambda x: float(str(x).replace(',', '').replace('%', '').replace('+', '')) if x not in (None, '', 'UNCH') else None
    for i in range(0, len(syms), 20):
        url = ('https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol?symbols='
               + urllib.parse.quote('|'.join(syms[i:i + 20])) + '&requestMethod=itv&noform=1&partnerId=2&fund=1&exthrs=0&output=json')
        try:
            rows = get_json(url)['FormattedQuoteResult']['FormattedQuote']
        except Exception as e:
            print(f'  ⚠ CNBC: no answer ({e}); every number is single-source'); return out
        for q in rows:
            ys = back.get(q.get('symbol'))
            if not ys or num(q.get('last')) is None: continue
            close, prev = num(q.get('last')), num(q.get('previous_day_closing'))
            out[ys] = dict(close=close, prev_close=prev, date=str(q.get('last_time', ''))[:10],
                           change_pct=round((close - prev) / prev * 100, 2) if prev else num(q.get('change_pct')))
    return out


def cross_check(sym, y, c, last_session):
    """'ok' when both sources have the same session and agree (0.05 %p on a % change; 2 bp on the 10-year yield),
    'mismatch' when they disagree, 'single' when only one has it, 'stale' when neither has the expected session."""
    if not y and not c: return dict(status='missing')
    yd, cd = (y or {}).get('date'), (c or {}).get('date')
    if not c or cd != (y or {}).get('date'):
        good = [s for s, d in (('Yahoo', yd), ('CNBC', cd)) if d == last_session]
        return dict(status='single' if good else 'stale', source2='CNBC', date2=cd, close2=(c or {}).get('close'),
                    change_pct2=(c or {}).get('change_pct'), note=f'Yahoo {yd}, CNBC {cd}; expected {last_session}')
    if sym == '^TNX':
        ok = abs((y['close'] - c['close']) * 100) <= 2.0
    else:
        ok = abs(y['change_pct'] - c['change_pct']) <= 0.05
    return dict(status='ok' if ok else 'mismatch', source2='CNBC', date2=cd, close2=c['close'], change_pct2=c['change_pct'])


def easter(y):   # anonymous Gregorian computus
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mo = (h + l - 7 * m + 114) // 31; da = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, mo, da)


def nth_weekday(y, m, wd, n):   # n-th weekday (0=Mon) of a month; n=-1 the last
    if n > 0:
        d = dt.date(y, m, 1); d += dt.timedelta((wd - d.weekday()) % 7)
        return d + dt.timedelta(weeks=n - 1)
    d = dt.date(y, m + 1, 1) - dt.timedelta(1) if m < 12 else dt.date(y, 12, 31)
    return d - dt.timedelta((d.weekday() - wd) % 7)


def observed(d):   # a fixed-date holiday on Saturday is observed Friday, on Sunday Monday
    return d - dt.timedelta(1) if d.weekday() == 5 else d + dt.timedelta(1) if d.weekday() == 6 else d


def nyse_holidays(y):
    h = {observed(dt.date(y, 1, 1)): '신정', nth_weekday(y, 1, 0, 3): '마틴 루터 킹 데이',
         nth_weekday(y, 2, 0, 3): '대통령의 날', easter(y) - dt.timedelta(2): '성금요일',
         nth_weekday(y, 5, 0, -1): '메모리얼 데이', observed(dt.date(y, 6, 19)): '준틴스',
         observed(dt.date(y, 7, 4)): '독립기념일', nth_weekday(y, 9, 0, 1): '노동절',
         nth_weekday(y, 11, 3, 4): '추수감사절', observed(dt.date(y, 12, 25)): '크리스마스'}
    return {d: n for d, n in h.items() if d.year == y}   # 1 Jan on a Saturday is not observed on 31 Dec


def nyse_early_closes(y):   # 13:00 ET closes; other years' special closes come from the research step
    e = {}
    tg = nth_weekday(y, 11, 3, 4); e[tg + dt.timedelta(1)] = '추수감사절 다음 날'
    xe = dt.date(y, 12, 24)
    if xe.weekday() < 5: e[xe] = '크리스마스 이브'
    j3 = dt.date(y, 7, 3)
    if j3.weekday() < 5 and observed(dt.date(y, 7, 4)) != j3: e[j3] = '독립기념일 전날'
    return e


def us_session(kst_date):
    """The US session tonight (KST evening of kst_date) and the last one completed before this morning."""
    hol = {**nyse_holidays(kst_date.year - 1), **nyse_holidays(kst_date.year), **nyse_holidays(kst_date.year + 1)}
    early = {**nyse_early_closes(kst_date.year), **nyse_early_closes(kst_date.year + 1)}
    def trading(d): return d.weekday() < 5 and d not in hol
    d = kst_date - dt.timedelta(1)
    skipped = []
    while not trading(d):
        if d.weekday() < 5: skipped.append(dict(date=str(d), holiday=hol[d]))
        d -= dt.timedelta(1)
    return dict(last_session=str(d), holidays_since=skipped,
                tonight=dict(date=str(kst_date), trading=trading(kst_date), holiday=hol.get(kst_date),
                             early_close=early.get(kst_date) if trading(kst_date) else None))


def finviz_heatmap(out_png):
    """Headless Chrome screenshot of the S&P 500 map at 2x, plus a crop of the map itself."""
    os.makedirs(os.path.dirname(out_png) or '.', exist_ok=True)
    full = out_png.replace('.png', '_full.png')
    prof = os.path.join(os.path.dirname(os.path.abspath(out_png)), '.chrome-finviz')
    r = subprocess.run([CHROME, '--headless', '--disable-gpu', '--hide-scrollbars', f'--user-data-dir={prof}',
                        f'--user-agent={UA}', '--window-size=1440,1000', '--force-device-scale-factor=2',
                        '--timeout=20000', f'--screenshot={full}', 'https://finviz.com/map.ashx?t=sec'],
                       capture_output=True, timeout=120)
    if not os.path.exists(full):
        return dict(ok=False, error='no screenshot (Chrome exit %d)' % r.returncode)
    # the map sits under the toolbar band and right of the side menu at 1440x1000 CSS px (2026-11-26 layout)
    x, y, w, h = 226 * 2, 270 * 2, 1200 * 2, 670 * 2
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', full, '-vf', f'crop={w}:{h}:{x}:{y}', out_png], check=False)
    return dict(ok=os.path.exists(out_png), image=out_png, full=full, source='https://finviz.com/map.ashx?t=sec',
                note='LOOK at both PNGs: the crop box is fixed; the full shot shows Finviz\'s own date/time line')


# ---------------------------------------------------------------- weather
def get_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'create-video-shorts/market-brief'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


SNOW = {71, 73, 75, 77, 85, 86}


RAIN = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
REGIONS = ['부산', '대구', '대전', '광주', '인천']   # the on-screen strip beside the spoken city (the user, 2026-11-26)


def sky(code, rain_pct):
    """WMO weather code -> (맑음 / 구름많음 / 흐림, 비 / 눈 / None). Precipitation counts when the day's code is rain or
    snow, or its chance is 60% or more."""
    s = '맑음' if code in (0, 1) else '구름많음' if code == 2 else '흐림'
    wet = '눈' if code in SNOW else '비' if code in RAIN or (rain_pct or 0) >= 60 else None
    return s, wet


def weather(city, kst_date):
    names = [city] + [c for c in REGIONS if c != city]
    lats = ','.join(str(CITIES[c][0]) for c in names); lons = ','.join(str(CITIES[c][1]) for c in names)
    allf = get_json('https://api.open-meteo.com/v1/forecast?latitude=%s&longitude=%s&timezone=Asia%%2FSeoul'
                    '&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code'
                    '&past_days=1&forecast_days=2' % (lats, lons))
    allf = allf if isinstance(allf, list) else [allf]
    regions = []
    for name, loc in zip(names, allf):
        d = loc['daily']; j = d['time'].index(str(kst_date))
        sk, wet = sky(d['weather_code'][j], d['precipitation_probability_max'][j])
        regions.append(dict(city=name, low=d['temperature_2m_min'][j], high=d['temperature_2m_max'][j],
                            rain_pct=d['precipitation_probability_max'][j], code=d['weather_code'][j], sky=sk, precip=wet))
    f = allf[0]['daily']
    lat, lon = CITIES[city]
    i = f['time'].index(str(kst_date))
    today = dict(low=f['temperature_2m_min'][i], high=f['temperature_2m_max'][i],
                 rain_pct=f['precipitation_probability_max'][i], code=f['weather_code'][i])
    today['sky'], today['precip'] = sky(today['code'], today['rain_pct'])
    yday = dict(low=f['temperature_2m_min'][i - 1], high=f['temperature_2m_max'][i - 1])
    aq = get_json('https://air-quality-api.open-meteo.com/v1/air-quality?latitude=%s&longitude=%s'
                  '&timezone=Asia%%2FSeoul&hourly=pm10,pm2_5&start_date=%s&end_date=%s' % (lat, lon, kst_date, kst_date))['hourly']
    mean = lambda xs: round(sum(x for x in xs if x is not None) / max(1, sum(x is not None for x in xs)))
    today['pm10'], today['pm25'] = mean(aq['pm10']), mean(aq['pm2_5'])
    # triggers: market-brief.md "The weather and season line" (Korean KMA / 환경부 thresholds where one exists)
    notes = []
    dlow = round(today['low'] - yday['low'], 1)
    if dlow <= -5: notes.append(dict(kind='cold_drop', value=dlow, fact=f'아침 최저 {today["low"]}도, 어제보다 {abs(dlow)}도 낮음'))
    if today['low'] <= -10: notes.append(dict(kind='cold_wave', value=today['low'], fact=f'아침 최저 {today["low"]}도 (한파 수준)'))
    if dlow >= 5: notes.append(dict(kind='warm_up', value=dlow, fact=f'아침 최저 {today["low"]}도, 어제보다 {dlow}도 높음'))
    if today['high'] - today['low'] >= 10:
        notes.append(dict(kind='big_range', value=round(today['high'] - today['low'], 1),
                          fact=f'최저 {today["low"]}도, 최고 {today["high"]}도'))
    if today['high'] >= 33: notes.append(dict(kind='heat', value=today['high'], fact=f'낮 최고 {today["high"]}도'))
    if (today['rain_pct'] or 0) >= 60:
        notes.append(dict(kind='snow' if today['code'] in SNOW else 'rain', value=today['rain_pct'],
                          fact=f'강수확률 {today["rain_pct"]}%'))
    if today['pm25'] >= 36 or today['pm10'] >= 81:
        notes.append(dict(kind='dust', value=[today['pm10'], today['pm25']],
                          fact=f'미세먼지 PM10 {today["pm10"]}, 초미세먼지 PM2.5 {today["pm25"]} (나쁨 이상)'))
    return dict(city=city, today=today, yesterday=yday, notes=notes, regions=regions,
                source='Open-Meteo (open-meteo.com) forecast + air quality, model data, not KMA observations')


# ---------------------------------------------------------------- solar terms
def sun_longitude(t_utc):
    jd = t_utc.timestamp() / 86400 + 2440587.5
    T = (jd - 2451545.0) / 36525
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = math.radians(357.52911 + 35999.05029 * T - 0.0001537 * T * T)
    C = ((1.914602 - 0.004817 * T - 0.000014 * T * T) * math.sin(M) + (0.019993 - 0.000101 * T) * math.sin(2 * M)
         + 0.000289 * math.sin(3 * M))
    om = math.radians(125.04 - 1934.136 * T)
    return (L0 + C - 0.00569 - 0.00478 * math.sin(om)) % 360


def term_moment(year, lon):
    """KST moment the Sun reaches `lon` degrees within `year` (bisection on a ~15-day bracket)."""
    approx = dt.datetime(year, 3, 20, tzinfo=dt.timezone.utc) + dt.timedelta(days=(lon / 360) * 365.2422)
    if approx.year != year: approx -= dt.timedelta(days=365.2422)
    if lon >= 285: approx = dt.datetime(year, 1, 5, tzinfo=dt.timezone.utc) + dt.timedelta(days=(lon - 285) / 360 * 365.2422)
    diff = lambda t: ((sun_longitude(t) - lon + 180) % 360) - 180
    a, b = approx - dt.timedelta(days=10), approx + dt.timedelta(days=10)
    for _ in range(60):
        m = a + (b - a) / 2
        if diff(m) < 0: a = m
        else: b = m
    return (a + (b - a) / 2).astimezone(KST)


def solar_terms(kst_date):
    rows = []
    for y in (kst_date.year, kst_date.year + 1):
        for k, name in enumerate(SOLAR_TERMS):
            t = term_moment(y, k * 15)
            mins = t.hour * 60 + t.minute
            near = mins < 30 or mins >= 23 * 60 + 30
            rows.append(dict(name=name, kst=t.strftime('%Y-%m-%d %H:%M'), date=str(t.date()), near_midnight=near))
    rows.sort(key=lambda r: r['kst'])
    today = next((r for r in rows if r['date'] == str(kst_date)), None)
    nxt = next(r for r in rows if r['date'] > str(kst_date))
    if today: today['custom'] = TERM_CUSTOMS.get(today['name'])
    return dict(today=today, next=nxt, days_to_next=(dt.date.fromisoformat(nxt['date']) - kst_date).days,
                source='computed from the Sun\'s apparent longitude (Meeus low precision); KASI publishes the official dates')


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--date', default=dt.datetime.now(KST).date().isoformat(), help='the KST morning of the briefing')
    pj = json.load(open('project.json', encoding='utf-8')) if os.path.exists('project.json') else {}
    ap.add_argument('--city', default=pj.get('market_city', '서울'), choices=sorted(CITIES))
    ap.add_argument('--out', default='market_data.json')
    ap.add_argument('--heatmap'); ap.add_argument('--no-heatmap', action='store_true')
    ap.add_argument('--no-market', action='store_true', help='weather and season only (a quick test)')
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.date)
    data = dict(date=a.date, made_at=dt.datetime.now(KST).isoformat(timespec='seconds'), session=us_session(day))
    if not a.no_market:
        q = quotes([s for s, _ in INDICES.values()] + [t for t, _, _ in WATCH], before={'^KS11': a.date})
        data['indices'] = {k: dict(symbol=s, name=n, **(q[s] or {})) for k, (s, n) in INDICES.items()}
        cq = cnbc_quotes([s for s, _ in INDICES.values()] + [t for t, _, _ in WATCH])
        last0 = data['session']['last_session']
        for k, (s, n) in INDICES.items():
            if k == 'kospi':                                # KRX: compare the previous session's close
                c = cq.get(s) or {}
                prev_c = c.get('prev_close') if c.get('date') == a.date else c.get('close')
                y = data['indices'][k]
                data['indices'][k]['check'] = dict(source2='CNBC', close2=prev_c,
                    status='ok' if y.get('close') and prev_c and abs(y['close'] - prev_c) <= 0.5 else 'single' if prev_c else 'missing')
            elif k == 'usdkrw':
                data['indices'][k]['check'] = dict(source2='CNBC', close2=(cq.get(s) or {}).get('close'), status='info')
            else:
                data['indices'][k]['check'] = cross_check(s, q.get(s), cq.get(s), last0)
        last = data['session']['last_session']
        moves = [dict(ticker=t, name=n, group=g, **q[t], check=cross_check(t, q[t], cq.get(t), last))
                 for t, n, g in WATCH if q.get(t) and q[t]['date'] == last]
        data['watch_stale'] = [dict(ticker=t, date=q[t]['date']) for t, n, g in WATCH if q.get(t) and q[t]['date'] != last]
        moves.sort(key=lambda m: m['change_pct'], reverse=True)
        data['watch'] = moves
        stale = sorted({v['date'] for k, v in data['indices'].items() if v.get('date') and k not in ('usdkrw', 'kospi')}
                       - {data['session']['last_session']})
        kd = data['indices']['kospi'].get('date')
        prev_wd = day - dt.timedelta(days=3 if day.weekday() == 0 else 1)
        kospi_gap = bool(kd) and kd != str(prev_wd)
        data['checks'] = dict(index_dates_not_last_session=stale, kospi_not_previous_weekday=kd if kospi_gap else None,
                              note='KRW=X and KOSPI (^KS11) follow other calendars and are not checked; any other mismatch means '
                                   'Yahoo has not posted the close yet or the session calendar is wrong: stop and look')
        data['market_source'] = 'Yahoo Finance via yfinance (unofficial); research step confirms spoken figures'
        if not a.no_heatmap:
            data['heatmap'] = finviz_heatmap(a.heatmap or f'captures/finviz_{a.date.replace("-", "")}.png')
    data['weather'] = weather(a.city, day)
    data['season'] = solar_terms(day)
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    s = data['session']
    print(f'market_data: {a.out}  last US session {s["last_session"]}'
          + (f' (holiday since: {", ".join(h["holiday"] for h in s["holidays_since"])})' if s['holidays_since'] else '')
          + f' · tonight: ' + ('휴장 ' + s['tonight']['holiday'] if not s['tonight']['trading'] else
                               '조기 폐장 ' + s['tonight']['early_close'] if s['tonight']['early_close'] else '정상 개장'))
    if not a.no_market:
        for k, v in data['indices'].items():
            print(f'  {k:7s} {v.get("date")} {v.get("close")} ({v.get("change_pct"):+}%)' if v.get('close') else f'  {k}: no data')
        if data['checks']['index_dates_not_last_session']: print('  ⚠ dates off the last session:', data['checks']['index_dates_not_last_session'])
        bad = [f'{k} ({v["check"]["status"]})' for k, v in data['indices'].items() if v.get('check', {}).get('status') in ('mismatch', 'single', 'stale', 'missing')]
        bad += [f'{w["ticker"]} ({w["check"]["status"]})' for w in data['watch'] if w['check']['status'] != 'ok']
        n_ok = sum(v.get('check', {}).get('status') == 'ok' for v in data['indices'].values()) + sum(w['check']['status'] == 'ok' for w in data['watch'])
        print(f'  cross-check (Yahoo vs CNBC): {n_ok} agree' + (f'; ⚠ not confirmed, not spoken until checked: {", ".join(bad)}' if bad else ''))
        if data.get('watch_stale'):
            print(f'  ⚠ watch list: {len(data["watch_stale"])} stock(s) have no {data["session"]["last_session"]} close on Yahoo yet '
                  f'(last: {sorted({w["date"] for w in data["watch_stale"]})}) and were left out; run again later before speaking stock moves')
        if data['checks']['kospi_not_previous_weekday']:
            print(f'  ⚠ KOSPI: Yahoo\'s last session before {a.date} is {kd}, not {prev_wd} (a KRX holiday, or a session missing '
                  'from Yahoo): take the previous close from the research (research.json "kospi_prev")')
        if 'heatmap' in data: print('  heatmap:', data['heatmap'].get('image') or data['heatmap'].get('error'))
    w = data['weather']; print(f'  weather {w["city"]}: {w["today"]} notes={[n["kind"] for n in w["notes"]]}')
    t = data['season']; print(f'  절기 today: {t["today"]} · next: {t["next"]["name"]} {t["next"]["kst"]} (in {t["days_to_next"]} d)')


if __name__ == '__main__':
    main()
