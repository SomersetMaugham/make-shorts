# The morning market briefing (`"format": "market-brief"`)

A short made every weekday morning, before the Korean market opens at 09:00 KST, for Korean retail investors: what
the US market did overnight (closes, the Finviz heatmap, the news that moved it) and what that means for the Korean
open, closed by tonight's schedule and, on days that call for it, one line about the weather or the season.
Set up on 2026-11-26 from the user's planning chat with Gemini ("한국장 출근길 쇼츠 제작 가이드").

**When:** the user asks for "미국장 브리핑", "출근길 브리핑", "장 전 브리핑", "마켓 브리핑", "오늘 미국장 쇼츠" or
names this format. Every other short is a **question short** (one question answered as a story; SKILL.md and
script-writing.md, **Short videos: the story spine**). The two formats never mix in one short.

**What changes for a briefing, and nothing else.** Everything not named here follows the skill as it is: the
first-time-listener gates, the seam pass, the internal-name list and the cold-listener review on every line; the
narration (Chirp 3 HD, speed 1, `say` readings, the pronunciation lexicon); recording only on the user's word; the
preview, the review desk and no MP4 before the review is complete; the user's render; the publishing package.
The look is the Brief theme (`theme-brief.md`) unless the user names another, with both of its stings: the intro on
the cover and **the outro on the last run** (`script.json` `"tail": 3.4`, `stings=[brief_sting(t0=r['dur'] - 2.9,
mode='outro')]`; the first briefing shipped without it and the user caught it, 2026-11-26). Say so in the graphics brief.

| | question short | morning market briefing |
|---|---|---|
| shape | the story spine: hook, turns, answer, ending of at most three sentences | the briefing spine (below): a fixed order of beats, the same every day |
| hook | opens a gap | the night in one line, then the question the outlook answers ("오늘 국장은 반등할 수 있을까요?") |
| ending | answer, new angle, next part's question | the outlook (the answer), today's and tonight's schedule, the sign-off line, the weather, "감사합니다." |
| research | facts, 2+ sources each, captures | the numbers script (`fetch_market.py`) + the research step for news, after hours, NDF, night futures, tonight's events; 2 sources for every spoken figure |
| length | as the question needs | 60–90 s (the first briefing ran 90 s with its outro) |

## The briefing spine (the order of beats)

One beat is one or two lines, and every line is its own run (no run over ~8 s, no two neighbouring runs of one
scene kind). A beat with nothing worth saying is left out; the order of the rest never changes, so the daily viewer
knows where to look.

| # | beat | in it | left out when |
|---|---|---|---|
| 1 | the night + the question | one line: the one thing that moved the market ("간밤 미국 증시는 반도체가 끌어내렸습니다"); then the question beat 9 answers, chosen from the previous KOSPI session: "오늘 국장은 반등할 수 있을까요?" (fell 1 % or more), "…상승을 이어갈 수 있을까요?" (rose 1 % or more), "…어느 쪽으로 출발할까요?" | never |
| 2 | the indices | S&P 500 and Nasdaq (Claude adds the Dow when it went the other way; the draft leaves it out) | never |
| 3 | SOX | the Philadelphia semiconductor index, the index Korea's chip makers follow; its biggest names on the card | never |
| 4 | rates and fear | the 10-year Treasury yield; VIX | 10-year moved under 10 bp **and** VIX under 25 and moved under 10% |
| 5 | the heatmap | the Finviz map for its colour (about 2 s), then the 2–4 names that drove it on large cards | the capture failed (then cards only) |
| 6 | the news | the one or two stories that moved the market, each as cause → effect in one breath | no story moved the market as a whole |
| 7 | after hours | an earnings or other result after the close that moved a stock ±3% or more | none |
| 8 | the Korean open | the NDF 1-month dollar-won rate and the KOSPI 200 night futures | never (Yahoo's spot rate when the research has no NDF) |
| 9 | the outlook | the answer to beat 1's question: the direction of today's KOSPI open from the night's signals and the brokers' views, then one line on what could change it ("다만 …에 따라"); "The outlook" below | never ("방향을 정하기 어려운 출발" when the signals disagree) |
| 9b | the watch point | the US move → the Korean sector it usually pulls (the map below) | no US group moved ±2% or more |
| 10 | tonight | a US holiday or early close; the one event tonight that matters (CPI, jobs, FOMC, a big earnings report) with its KST time; a Korean event today (금통위, option expiry, a late open on 수능 day, a KRX holiday) | nothing scheduled |
| 11 | sign-off, weather, thanks | the channel's sign-off, word for word (the user, 2026-11-26), split around the weather: "오늘 날씨 알려드리면서 브리핑을 마치겠습니다." opens the beat (it is also the turn into the weather the cold listener kept asking for); then Seoul's low, high and sky in one spoken line, the regional card (below), a season line and a line of care when a trigger fires; the last line is "감사합니다." (`project.json` `market_signoff` `{"before_weather", "end"}` overrides) | never |

Lines are written so a listener who hears only the numbers still follows: one figure per clause, the direction in the
verb (올랐습니다 / 내렸습니다), never two indices compared in one breath without saying which went where. The
40-syllable breath rule holds; a beat that needs more is two lines.

## The outlook

The briefing answers its own opening question (the user, 2026-11-26: the facts alone inform, the outlook is the kick).
- **What it says:** the direction and mood of today's KOSPI open only: 반등 출발 / 상승 출발 / 약세 출발 / 방향을 정하기
  어려운 출발, and at most "변동성이 커질 수 있다". Never an index level, a target, a stock to buy or sell, or a
  certainty ("반드시", "확실히").
- **What it rests on:** the night's signals (KOSPI 200 night futures, SOX, Nasdaq, the NDF won) and the brokers'
  morning views (`street_view` in research.json, two houses or more, each with its source). `brief_draft.py` scores a
  first reading (night futures and the brokers count twice, SOX and Nasdaq once, a weaker won against; |score| ≥ 2
  picks a side); Claude checks it against the research and may change it, and says why in the log.
- **Always a caveat line:** "다만 …에 따라 장중 흔들림이 커질 수 있습니다", naming today's event (금통위, a US data
  release, option expiry) or, without one, the signal that disagrees.
- **When the signals disagree,** the line says so ("밤사이 신호가 엇갈려, …방향을 정하기 어려운 출발이 예상됩니다")
  instead of forcing a side.

## The outlook record

Every call goes into one log for the series, `<channel>/market-brief/outlooks.json` (project.json `outlook_log`
overrides): the date, the call as spoken, the draft's call and score, every signal's value, the brokers' views and
today's events. It is never mentioned in a short (the user, 2026-11-26); it is data for making the outlook right more
often: which signals to keep, weigh more, add or drop.
- **After the script is final:** `python3 scripts/market/outlook_log.py add [--direction up|down|mixed]` (the call as
  spoken when Claude changed the draft's).
- **Every morning, before the new briefing:** `.venv/bin/python scripts/market/outlook_log.py score` fills in the
  previous days' KOSPI open and close (Yahoo ^KS11) and whether the call hit (up: above +0.2 %, down: below −0.2 %,
  mixed: within ±0.5 %). Yahoo misses a KRX session now and then (2026-11-25 was missing): the tool then skips the
  day and says so; enter it from a news report with `score --manual <date> <open %> <close %>`.
- **Now and then (every 20 trading days or so):** `python3 scripts/market/outlook_log.py report` prints the hit rate
  of the calls and of every signal on its own against the open. Propose a change to the weights only from 20 days or
  more, and bring it to the user with the numbers; the weights live in `brief_draft.py` `outlook()`.

**A watch point, never a pick.** The briefing says what to *watch* ("오늘은 국내 전력기기 흐름을 지켜볼 만합니다"),
never what to buy or sell, and never a price call. The last run shows
"투자 권유가 아닌 정보 제공 목적입니다. 투자 판단의 책임은 본인에게 있습니다." in small type
(Pretendard 600, 26 px, above the caption band), and the same sentence ends every description in `PUBLISH.md`.

## The watch list and the US → Korea map

`fetch_market.py` reads the watch list (`WATCH`: ticker, Korean name, group) and `brief_draft.py` the map (`KR_MAP`).
Change either there, not in a project.

| US group (watch list) | Korean sector to watch |
|---|---|
| semis: NVDA, MU, AVGO, AMD, TSM | 국내 반도체 대형주 |
| semi_equip: AMAT, LRCX | 국내 반도체 소부장 |
| apple: AAPL | 국내 애플 부품주 |
| bigtech: MSFT, GOOGL, AMZN, META | 국내 인터넷·플랫폼주 |
| ev: TSLA | 국내 2차전지주 |
| power: GEV, VST, CEG | 국내 전력기기·원전주 |
| obesity: LLY, NVO | 국내 바이오주 |
| defense: LMT, RTX | 국내 방산주 |
| oil: XOM | 국내 정유주 |

Sectors are named, not single Korean stocks, unless the news itself names one (a supplier contract, a direct peer's
earnings), and then with its source.

## Colours and signs

- Finviz paints up green and down red; a Korean viewer reads red as up. The briefing follows Finviz everywhere, so the
  map and the cards never contradict each other: **up = `forest` (`#1E6B55`), down = `crimson` (`#B42323`)**, flat
  `slate`, from the Brief palette.
- Every number on a card carries its sign and arrow: `▲ +0.85%`, `▼ −2.10%` (the true minus `−`). `brief_draft.py`
  puts them in each line's `figures` for the graphics writer.
- Captions (`text`) carry plain numbers that match the spoken line ("0.62% 내렸습니다"); the direction is in the verb.

## The heatmap

- `fetch_market.py` saves `captures/finviz_<date>.png` (the map, 2400 × 1340 px) and `…_full.png` (the page with
  Finviz's own "Aftermarket · <day, time> ET" line, the proof of which session it shows). **Look at both**: the
  crop box is fixed, so an ad or a layout change moves it.
- The source strip reads `실제 자료 · finviz.com S&P 500 맵, <M/D> 미국 장 마감` (`SOURCE_KINDS` of the Brief theme).
- The whole map is shown for its colour; the names the narration says are cropped and zoomed so their tiles' text is
  26 px or more (the Brief theme's capture rules), or put on `number_card`s.

## The weather and season line

Beat 11 is there every day, as one run:
- **Spoken:** Seoul's morning low, daytime high and sky in one line ("오늘 서울은 아침 오 도, 낮 십오 도로 흐리겠습니다";
  rain or snow replaces the sky: "비 소식이 있습니다"). Then, only when a trigger fires, the season line and one line
  of care, each at most two short sentences, one sentence per cue.
- **On screen, not spoken (the user, 2026-11-26):** a regional card in the lower cards zone of the weather run
  (`#brCards`, above the caption band) with 서울, 부산, 대구, 대전, 광주, 인천, one row each: city, low / high in whole
  degrees, the sky (맑음 / 구름많음 / 흐림) and 비 or 눈 when there is any (precipitation code, or a chance of 60% or
  more). The data is `weather.regions` in `market_data.json` and the weather line's `figures` in `brief_draft.json`.
  Sky and rain get a small mark each, drawn in the Brief style (ink line icons, not emoji); temperatures in
  Pretendard 700, at least 30 px.

The lines speak to the viewer on the way to work, in the narrator's voice; the line of care is one small piece of care
("감기 조심하세요", "우산 챙기세요"), never a lecture, never two pieces of advice. It follows these triggers:

| trigger (`fetch_market.py` `weather.notes`, Seoul by default, `--city`) | threshold |
|---|---|
| `cold_wave` | morning low −10 °C or lower |
| `cold_drop` | morning low 5 °C or more below yesterday's |
| `snow` / `rain` | precipitation chance 60% or more (snow when the day's weather code is snow) |
| `dust` | PM2.5 day mean 36 µg/m³ or more, or PM10 81 or more (환경부 "나쁨") |
| `heat` | high 33 °C or more |
| `big_range` | high − low 10 °C or more |
| `warm_up` | morning low 5 °C or more above yesterday's (no line of care: the spoken line already gives the temperature) |

- One weather line: the first trigger in that order. Temperatures are said as whole degrees ("영하 사 도").
- **The season:** on the day of one of the 24 solar terms (절기), one line names it and, for the well-known ones, its
  custom (동지 팥죽, 입춘첩, 소한·대한 추위). `fetch_market.py` computes the terms from the Sun's longitude to about
  15 minutes; a term within 30 minutes of midnight KST is flagged and is said only after checking KASI's date.
  The day's season line comes first, then the weather line.
- Weather numbers are model forecasts (Open-Meteo), so lines say "오늘 아침 서울은 영하 사 도까지 내려갑니다", not an
  observed record. A line the user dictates wins over all of this.

## The data and the research

1. **The numbers:** in `work/`, `.venv/bin/python scripts/market/fetch_market.py` (yfinance is installed once:
   `uv pip install --python .venv/bin/python yfinance`). It writes `market_data.json`: the session calendar
   (the last completed US session, holidays since, tonight's holiday or early close), the indices and the watch list
   with their session dates, the heatmap, the weather and the season. It prints a ⚠ when an index's date is not the
   last session (Yahoo has not posted the close): stop and run it again later; never speak a stale close.
   Watch-list stocks without the last session's close are left out with a ⚠ (on 2026-11-26 a refetch returned
   every stock's 11-24 bar, not 11-25's), and so is the heatmap names line until they are back.
2. **The research** (agy Hydrogen, web tools only; roles.md): one request that returns `research.json` with a source
   URL for every value, in this shape:
   ```json
   {"news": [{"fact": "…", "source": "https://…", "source2": "https://…"}],
    "after_hours": {"ticker": "…", "name": "…", "event": "…", "change_pct": 0.0, "source": "https://…"},
    "ndf": {"value": 0.0, "change": 0.0, "source": "https://…"},
    "night_futures": {"change_pct": 0.0, "source": "https://…"},
    "events_tonight": [{"time_kst": "22:30", "name": "…", "source": "https://…"}],
    "korea_today": [{"name": "…", "short": "금통위", "source": "https://…"}],
    "kospi_prev": {"close": 0.0, "change_pct": 0.0, "source": "https://…"},
    "street_view": [{"house": "…증권", "view": "one line in Korean", "direction": "up|down|mixed", "source": "https://…"}],
    "check": [{"what": "S&P 500 close", "value": 0.0, "source": "https://…"}]}
   ```
   `kospi_prev` is the previous KRX session's close from the news (Yahoo can miss a session); `street_view` holds two
   brokers' morning views or more; `short` is the name the narration says. `check` holds a second source for every
   index figure that will be spoken. A figure that differs from
   `market_data.json` by more than 0.02 percentage points is not spoken until Claude has opened both sources.
3. **The draft:** `python3 scripts/market/brief_draft.py` writes `brief_draft.json`: the beats in order with draft
   `text` / `say` (numbers already read as 쩜, 원·전, sino-Korean), `src`, `figures`, and `todo` lines for the news,
   after hours and tonight's events. **It is a draft.** Claude rewrites every line (the gates, this spine, the
   narrator's voice), fills the `todo`s from `research.json`, fixes neighbouring runs of one scene kind, and only then
   copies the lines into `shorts.json`. From there the pipeline is the skill's: `prep.sh`, the graphics, the preview,
   the review, recording on the user's word.

## The daily routine

- **One project folder per day:** `<channel folder>/market-brief/<YYYY-MM-DD>/`, set up with `setup.sh` (uv reuses its
  cache, so the venv takes seconds). `project.json`: `"theme": "brief"`, `"format": "market-brief"`, and once the user
  has given them, `"market_signoff"` and `"market_city"`.
- Copy yesterday's graphics module as the start of today's: the layouts stay, the numbers and captures change. The
  look and the beat order stay the same every day; that sameness is the format.
- US closes are final from about 06:00 KST (07:00 in US daylight time); run `fetch_market.py` after that.
- The user still reviews every briefing and says when to record: a daily short is not a reason to skip the review or
  to record without their word.
- Finviz's terms are the user's call; the capture is credited on screen and in the description.
