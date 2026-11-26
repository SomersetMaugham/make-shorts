"""The outlook record (references/market-brief.md "The outlook record"): every briefing's call on the Korean open, the
signals it rested on, and, a day later, what the KOSPI actually did. Never spoken in a short (the user, 2026-11-26):
it is data for deciding which signals to keep, add or drop so the outlook is right more often.

  python3 scripts/market/outlook_log.py add [--direction up|down|mixed] [--text "the spoken outlook line"]
  .venv/bin/python scripts/market/outlook_log.py score          fills in the KOSPI open and close of past entries
  python3 scripts/market/outlook_log.py score --manual 2026-11-26 0.45 -1.20   when Yahoo misses the session
  python3 scripts/market/outlook_log.py report                  hit rates: the outlook and every signal on its own

The log is one JSON file for the whole series, outside the daily folders: project.json "outlook_log", by default
../../outlooks.json from work/ (<channel>/market-brief/outlooks.json). `add` reads market_data.json, research.json
and brief_draft.json in work/; --direction records the call as finally spoken when Claude changed the draft's.

How a call is scored (KOSPI, ^KS11, the session of the briefing's date):
- open  = (open − previous close) / previous close; close = (close − previous close) / previous close, in %.
- 'up' hits when the move is above +0.2 %, 'down' when below −0.2 %, 'mixed' when within ±0.5 %.
- A signal "agrees" when its sign matches the open's sign; signals near zero (|x| under its flat band) and flat opens
  (within ±0.2 %) are left out of its count.
"""
import argparse, datetime as dt, json, os, sys

FLAT = dict(night_futures=0.1, sox=0.3, nasdaq=0.3, sp500=0.3, ndf_change=1.0, vix_change=3.0, kospi_prev=0.5, street=0)
INVERT = {'ndf_change', 'vix_change'}            # a weaker won and a rising VIX point down
OPEN_FLAT = 0.2


def log_path():
    pj = json.load(open('project.json', encoding='utf-8')) if os.path.exists('project.json') else {}
    return pj.get('outlook_log', os.path.join('..', '..', 'outlooks.json'))


def load(p):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []


def save(p, rows):
    rows.sort(key=lambda r: r['date'])
    json.dump(rows, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def sgn(x, flat):
    return 0 if x is None or abs(x) <= flat else (1 if x > 0 else -1)


def cmd_add(a):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import brief_draft
    m = json.load(open('market_data.json', encoding='utf-8'))
    r = json.load(open('research.json', encoding='utf-8')) if os.path.exists('research.json') else {}
    d = json.load(open('brief_draft.json', encoding='utf-8')) if os.path.exists('brief_draft.json') else {}
    ol = d.get('outlook') or brief_draft.outlook(m, r) or {}
    text = a.text or next((x['text'] for x in d.get('lines', []) if x.get('scene') == 'outlook'), '')
    row = dict(date=m['date'], us_session=m['session']['last_session'], direction=a.direction or ol.get('direction'),
               draft_direction=ol.get('direction'), score=ol.get('score'), text=text,
               signals=brief_draft.signals(m, r),
               street=[dict(house=v.get('house'), direction=v.get('direction'), source=v.get('source'))
                       for v in r.get('street_view', [])],
               events=[e.get('name') for e in r.get('korea_today', [])], actual=None)
    if row['direction'] not in ('up', 'down', 'mixed'): sys.exit('outlook_log: no direction (pass --direction up|down|mixed)')
    p = log_path(); rows = [x for x in load(p) if x['date'] != row['date']] + [row]
    save(p, rows)
    print(f'outlook_log: {p} · {row["date"]} {row["direction"]} (draft {row["draft_direction"]}, score {row["score"]})')


def kospi_day(date):
    try:
        import yfinance as yf
    except ImportError:
        sys.exit('outlook_log score: yfinance is missing (uv pip install --python .venv/bin/python yfinance)')
    d = dt.date.fromisoformat(date)
    h = yf.Ticker('^KS11').history(start=str(d - dt.timedelta(days=10)), end=str(d + dt.timedelta(days=1)), auto_adjust=False)
    h = h[h['Close'].notna()]
    days = [str(i.date()) for i in h.index]
    if date not in days: return None
    i = days.index(date)
    if i == 0: return None
    gap = (d - dt.date.fromisoformat(days[i - 1])).days
    if gap > (3 if d.weekday() == 0 else 1):        # Yahoo misses KRX sessions now and then (11-25-2026 was missing)
        print(f'  {date}: Yahoo has no session between {days[i - 1]} and {date} (missing data or a KRX holiday): '
              f'check, then: score --manual {date} <open %> <close %>'); return None
    prev, row = float(h['Close'].iloc[i - 1]), h.iloc[i]
    return dict(prev_close=round(prev, 2), open=round(float(row['Open']), 2), close=round(float(row['Close']), 2),
                open_pct=round((float(row['Open']) - prev) / prev * 100, 2), close_pct=round((float(row['Close']) - prev) / prev * 100, 2))


def hit(direction, pct):
    return dict(up=pct > OPEN_FLAT, down=pct < -OPEN_FLAT, mixed=abs(pct) <= 0.5)[direction]


def cmd_score(a):
    p = log_path(); rows = load(p); now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    if a.manual:                                      # date open% close% read from a news report or KRX
        date, op, cl = a.manual[0], float(a.manual[1]), float(a.manual[2])
        row = next((x for x in rows if x['date'] == date), None)
        if not row: sys.exit(f'outlook_log: no entry for {date}')
        row['actual'] = dict(open_pct=op, close_pct=cl, source='manual', hit_open=hit(row['direction'], op), hit_close=hit(row['direction'], cl))
        save(p, rows); print(f'  {date}: open {op:+.2f}% close {cl:+.2f}% (manual)'); return
    for row in rows:
        if row.get('actual'): continue
        if row['date'] > str(now.date()) or (row['date'] == str(now.date()) and now.hour < 16): continue   # KRX closes 15:30
        k = kospi_day(row['date'])
        if not k: print(f'  {row["date"]}: no KOSPI session found (holiday?)'); continue
        k.update(hit_open=hit(row['direction'], k['open_pct']), hit_close=hit(row['direction'], k['close_pct']))
        row['actual'] = k
        print(f'  {row["date"]} {row["direction"]:5s} open {k["open_pct"]:+.2f}% close {k["close_pct"]:+.2f}% '
              f'-> open {"hit" if k["hit_open"] else "miss"}, close {"hit" if k["hit_close"] else "miss"}')
    save(p, rows)


def cmd_report(a):
    rows = [x for x in load(log_path()) if x.get('actual')]
    if not rows: sys.exit('outlook_log report: no scored entries yet (run score after the KRX close)')
    n = len(rows)
    ho = sum(x['actual']['hit_open'] for x in rows); hc = sum(x['actual']['hit_close'] for x in rows)
    print(f'outlook: {n} days · open {ho}/{n} ({ho / n:.0%}) · close {hc}/{n} ({hc / n:.0%})')
    dr = [x for x in rows if x.get('draft_direction') and x['draft_direction'] != x['direction']]
    if dr:
        dh = sum(hit(x['draft_direction'], x['actual']['open_pct']) for x in dr)
        print(f'  days the spoken call differed from the draft score: {len(dr)}; the draft would have hit the open {dh}/{len(dr)}')
    print('signal agreement with the direction of the open (flat signals and flat opens left out):')
    out = []
    for k, fl in FLAT.items():
        used = [(sgn(x['signals'].get(k), fl) * (-1 if k in INVERT else 1), sgn(x['actual']['open_pct'], OPEN_FLAT)) for x in rows]
        used = [(s, o) for s, o in used if s and o]
        if used: out.append((sum(s == o for s, o in used) / len(used), k, len(used), sum(s == o for s, o in used)))
    for rate, k, m_, h_ in sorted(out, reverse=True):
        print(f'  {k:14s} {h_:3d}/{m_:<3d} {rate:5.0%}' + ('   (few days: not a basis yet)' if m_ < 20 else ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['add', 'score', 'report'])
    ap.add_argument('--direction', choices=['up', 'down', 'mixed']); ap.add_argument('--text')
    ap.add_argument('--manual', nargs=3, metavar=('DATE', 'OPEN_PCT', 'CLOSE_PCT'))
    a = ap.parse_args()
    dict(add=cmd_add, score=cmd_score, report=cmd_report)[a.cmd](a)


if __name__ == '__main__':
    main()
