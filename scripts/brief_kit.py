"""The Brief theme (references/theme-brief.md): Modern Research Magazine editorial look.
Separated from sungkim_kit.py (2026-11-24) with its own newsprint surface (#F5F4F0), editorial rules,
3-tier typography (Hahmlet 700 + Pretendard + Geist Mono), section-coloured titles (1-B), segmented progress bar,
light magazine cover, archive source chips, ratio presets, section-aware caption highlights and the Minimal Ink & Rule
sting (assets/gfx/brief_sting.js).

Layout on the 1080x1920 canvas:
  cover run    run 0 only: light magazine cover on #F5F4F0 paper, masthead double rule, left-aligned Hahmlet 700
               headline, framed hero visual, left crimson-bar KEY FINDING strip
  progress     y   60-82   segmented section progress bar + '01 / 06' mono counter
  header       y   98-308  kicker (square marker + section accent) and Hahmlet 700 title (section dark colour),
                           closed by a 3px + 1px editorial double ink rule
  #brVis       x 60-1020, y 332+   upper card (default h 548, visual_tall 656, cards_tall 416)
  #brSrc       16 px below #brVis  archive source chip (solid / outline / dashed) + exact source text
  #brCards     68 px below #brSrc  lower cards (bottom <= y 1380; outer frame to x 1020, text strictly <= x 950)
  captions     y 1410-1550 (compose.py: ink Pretendard on paper outline; keyword highlights follow the run's section)
  bottom safe  y 1560-1920 empty

Example:
  from brief_kit import *
  SEC = section('진화가 일어났다', '16세대 만의 급격한 도약', 'ochre', index=3, total=6)
  r, ws = words('s1', 6)
  brief_page('s1_r6', r, SEC, vis_html=..., source=('계산해서 그린 그림', '논문 Figure 6 실측값'),
             cards=[(W(ws, '92퍼센트'), number_card('16세대 만에', '92%', prev='5.5%',
                                                    sub='스스로 복사본을 만든 비율이 약 17배 상승',
                                                    count_from=5.5, count_to=92, suffix='%'))])
"""
import html, json, os, time
from build_gfx_common import *

# Editorial section colours: (dark [title / big text], main [rule / bar / chip], wash [soft tag tint])
PALETTE = {
    'crimson': ('#8F1D1D', '#B42323', 'rgba(180,35,35,.10)'),
    'navy':    ('#16335B', '#204A80', 'rgba(32,74,128,.10)'),
    'forest':  ('#154D3D', '#1E6B55', 'rgba(30,107,85,.10)'),
    'ochre':   ('#8A560F', '#B07016', 'rgba(176,112,22,.11)'),
    'plum':    ('#4E3161', '#6A4382', 'rgba(106,67,130,.10)'),
    'slate':   ('#424B57', '#5D6878', 'rgba(93,104,120,.10)'),
}
# RGB tuples for compose.py / preview.py section-aware keyword highlights (main tone)
PALETTE_RGB = {
    'crimson': (180, 35, 35),
    'navy':    (32, 74, 128),
    'forest':  (30, 107, 85),
    'ochre':   (176, 112, 22),
    'plum':    (106, 67, 130),
    'slate':   (93, 104, 120),
}
PAPER, SHEET, INK, INK2, MUTED = '#F5F4F0', '#FCFBF8', '#161618', '#4A4A52', '#6E6E77'
RULE, TRACK, DARK = '#DCDAD2', '#E4E2DA', '#14171D'
SOURCE_KINDS = ('개념 그림', '실제 자료', '실제 그림', '계산해서 그린 그림')
LEAD = 0.3
THUMB_SETTLE = 0.6     # s after a card lands until its entrance (0.38 s) and rules (0.48 s) are done (brief.js)
THUMB_WINDOW = 1.5     # s: the default thumbnail window's length, ending just before the run (or its outro sting) ends
GAP = 16

# Vertical presets: (vis_h, src_y, cards_y, cards_h); vis always starts at y 332 and cards end <= y 1380
LAYOUTS = {
    'default':     (548, 896,  964, 416),
    'visual_tall': (656, 1004, 1072, 308),
    'cards_tall':  (416, 764,  832, 548),
}


def section(kicker, title, color='navy', index=None, total=None):
    """One section's header: kicker, one-line Hahmlet 700 title (in the section's dark colour), section accent colour,
    and optional (index, total) for the top segmented progress bar (e.g. index=1, total=6 -> '01 / 06')."""
    if color not in PALETTE:
        raise SystemExit(f'section colour {color!r}: one of {", ".join(PALETTE)}')
    return dict(kicker=kicker, title=title, color=color, index=index, total=total)


# ----------------------------------------------------------------------------------------------------- lower cards
H = dict(badge=126, statement=264, quote=264, number=282, bars=0, pair=336, units=308, tiles=344)


def badge_card(badge, text, idx='', color=None):
    """Editorial list row: left 6 px accent bar, mono-indexed tag and one concise summary line."""
    return dict(kind='badge', badge=badge, text=text, idx=str(idx), color=color, h=H['badge'])


def statement_card(text, sub='', badge='', color=None, quote_mark=True):
    """Magazine pull-quote card: double ink top rule, bottom ink rule, centred Hahmlet 700 statement."""
    return dict(kind='statement', text=text, sub=sub, badge=badge, color=color, quote_mark=quote_mark, h=H['statement'])


def quote_card(badge, quote, sub='', color=None):
    """Editorial quote card: thick left accent bar, serif quoted text, and attribution/meaning beneath."""
    return dict(kind='quote', badge=badge, text=f'“{quote}”', sub=sub, color=color, h=H['quote'])


def number_card(badge, value, sub='', prev='', color=None, count_from=None, count_to=None,
                count_dur=0.9, prefix='', suffix='', dec=0, comma=False):
    """Headline metric card: top 5 px accent rule, optional 'prev ->' comparison, huge Hahmlet 700 figure.
    Set count_from and count_to to animate a smooth count-up roll (e.g. count_from=5.5, count_to=92, suffix='%')."""
    return dict(kind='number', badge=badge, text=str(value), sub=sub, prev=str(prev), color=color,
                count_from=count_from, count_to=count_to, count_dur=count_dur,
                prefix=prefix, suffix=suffix, dec=dec, comma=comma, h=H['number'])


def bars_card(title, rows, color=None, dur=1.15):
    """Comparison bars: rows = [(label, value 0..1, shown text, colour or None)]."""
    return dict(kind='bars', title=title, rows=rows, color=color, dur=dur, h=74 + 94 * len(rows))


def pair_card(left, right):
    """Two side-by-side editorial top-rule cards (each a number_card, statement_card or quote_card)."""
    return dict(kind='pair', left=left, right=right, h=H['pair'])


def units_card(badge, groups, summary='', total=20, color=None, step=0.06):
    """Grid of units filling sequentially: groups = [(count, colour name)], e.g. [(14, 'ochre'), (6, 'crimson')]."""
    return dict(kind='units', badge=badge, groups=groups, summary=summary, total=total, color=color, step=step, h=H['units'])


def tiles_card(title, tiles, step=0.85):
    """2x2 editorial status grid: tiles = [(label, status, colour name)]."""
    return dict(kind='tiles', title=title, tiles=tiles, step=step, h=H['tiles'])


# ----------------------------------------------------------------------------------------------------- captures
MIN_CAPTURE_TEXT = 26


def phrase_marks(json_path, phrase, t):
    """The boxes of one phrase found by scripts/capture_marks.py (<capture>.json), to highlight/underline at t."""
    d = json.load(open(json_path, encoding='utf-8'))
    if phrase not in d.get('phrases', {}):
        raise SystemExit(f'phrase_marks: {phrase!r} not in {json_path} - run capture_marks.py with --phrase')
    return dict(boxes=d['phrases'][phrase], t=t)


def capture_html(src, fw, fh, focus=None, zoom=None, w=960, h=548, marks=(), text_px=None, keep=(), min_text=None,
                 mark_style='highlight', color='navy', dim=False):
    """Real source capture inside #brVis with readability & crop guards.
    mark_style: 'highlight' (editorial translucent wash + crisp 4 px underline) or 'underline' (4 px underline only).
    color: palette name (default 'navy') or hex colour for the mark.
    dim: when True and marks are present, subtly dims bands outside the cited paragraph so the quote pops cleanly."""
    floor = min_text or MIN_CAPTURE_TEXT
    base = max(w / fw, h / fh)
    if zoom is None:
        zoom = max(1.0, (floor / text_px) / base) if text_px else 1.0
    k = base * zoom
    if text_px and text_px * k < floor - 0.01:
        raise SystemExit(f'capture_html {src}: body text {text_px} px x {k:.2f} = {text_px * k:.0f} px on screen, under '
                         f'{floor} px - use zoom >= {floor / text_px / base:.2f} or crop a smaller region')
    allb = [b for m in marks for b in m['boxes']]
    if focus is None and allb:
        focus = ((min(b[0] for b in allb) + max(b[2] for b in allb)) / 2,
                 (min(b[1] for b in allb) + max(b[3] for b in allb)) / 2)
    fx, fy = focus or (fw / 2, fh / 2)
    x = min(0, max(w - fw * k, w / 2 - fx * k))
    y = min(0, max(h - fh * k, h / 2 - fy * k))
    out = (f'<img src="{html.escape(src)}" style="position:absolute;left:{x:.1f}px;top:{y:.1f}px;'
           f'width:{fw * k:.1f}px;height:{fh * k:.1f}px;display:block">')
    for x0, y0, x1, y1 in keep:
        if x + x0 * k < -1 or x + x1 * k > w + 1 or y + y0 * k < -1 or y + y1 * k > h + 1:
            raise SystemExit(f'capture_html {src}: the kept box ({x0},{y0})-({x1},{y1}) is cut by the crop - lower zoom (min_text) or move focus')
    _, main_col, wash_col = PALETTE.get(color, (color, color, 'rgba(32,74,128,.14)'))
    if dim and allb:
        y_top = max(0.0, min(y + b[1] * k for b in allb) - 10)
        y_bot = min(float(h), max(y + b[3] * k for b in allb) + 12)
        if y_top > 2:
            out += f'<div style="position:absolute;left:0;right:0;top:0;height:{y_top:.1f}px;background:rgba(255,255,255,.52);pointer-events:none"></div>'
        if h - y_bot > 2:
            out += f'<div style="position:absolute;left:0;right:0;top:{y_bot:.1f}px;bottom:0;background:rgba(255,255,255,.52);pointer-events:none"></div>'
    for m in marks:
        t_sw = max(0.02, m['t'])
        for x0, y0, x1, y1 in m['boxes']:
            L, T, R, B = x + x0 * k, y + y0 * k, x + x1 * k, y + y1 * k
            if L < -2 or R > w + 2 or B < 0 or B > h - 2:
                raise SystemExit(f'capture_html {src}: the mark at ({x0},{y0})-({x1},{y1}) falls outside the crop - move focus or lower zoom')
            if mark_style == 'highlight':
                out += (f'<div data-sweep="{t_sw:.3f}" style="position:absolute;left:{L - 3:.1f}px;top:{T - 2:.1f}px;'
                        f'width:{R - L + 6:.1f}px;height:{B - T + 5:.1f}px;background:{wash_col};'
                        f'mix-blend-mode:multiply;transform-origin:0 50%;transform:scaleX(0)"></div>')
            out += (f'<div data-sweep="{t_sw:.3f}" style="position:absolute;left:{L:.1f}px;top:{B + 2:.1f}px;'
                    f'width:{R - L:.1f}px;height:4px;background:{main_col};'
                    f'transform-origin:0 50%;transform:scaleX(0)"></div>')
    return out


# ----------------------------------------------------------------------------------------------------- HTML builders
def _c(card, sec):
    return PALETTE[card.get('color') or sec['color']]


def _txt(s):
    return '<br>'.join(html.escape(x) for x in str(s).split('\n'))


def _source_chip_html(kind, main_col, dk_col):
    esc_k = html.escape(kind)
    if kind in ('실제 자료', '실제 그림'):
        return f'<span class="brsc solid" style="background:{main_col}"><i class="dot"></i>{esc_k}</span>'
    if kind == '계산해서 그린 그림':
        return f'<span class="brsc outline" style="border-color:{main_col};color:{dk_col}">{esc_k}</span>'
    return f'<span class="brsc dashed">{esc_k}</span>'


def _progress_html(sec, main_col):
    idx, tot = sec.get('index'), sec.get('total')
    if not idx or not tot:
        return ''
    segs = ''
    for i in range(1, int(tot) + 1):
        if i < idx:
            segs += '<div class="brps past"></div>'
        elif i == idx:
            segs += f'<div class="brps cur" style="background:{main_col}"></div>'
        else:
            segs += '<div class="brps"></div>'
    return f'<div id="brProg"><div class="brpb">{segs}</div><div class="brpn">{int(idx):02d} / {int(tot):02d}</div></div>'


def _card_html(c, sec, t, uid):
    dk, mn, wash = _c(c, sec)
    land = f'data-t="{t:.3f}"'
    rule_t = f'data-rule="{t:.3f}"'
    k = c['kind']
    if k == 'badge':
        idx_html = f'<span class="brix">{html.escape(c["idx"])}</span>' if c.get('idx') else ''
        return (f'<div class="brc brrow" {land} style="height:{c["h"]}px">'
                f'<div class="brbar" {rule_t} data-axis="y" style="background:{mn}"></div>'
                f'<span class="brtag" style="background:{wash};color:{dk}">{idx_html}{html.escape(c["badge"])}</span>'
                f'<span class="brln">{html.escape(c["text"])}</span></div>')
    if k == 'statement':
        qmark = f'<span class="brqm" style="color:{mn}">“</span>' if c.get('quote_mark') else ''
        eyebrow = f'<div class="breye" style="color:{dk};margin-bottom:12px">{html.escape(c["badge"])}</div>' if c.get('badge') else ''
        sub = f'<div class="brsub">{html.escape(c["sub"])}</div>' if c.get('sub') else ''
        return (f'<div class="brc brpull" {land} style="height:{c["h"]}px">'
                f'<div class="brtop2" {rule_t} data-axis="x"></div>'
                f'{eyebrow}<div class="brpq">{qmark}{_txt(c["text"])}</div>{sub}</div>')
    if k == 'quote':
        eyebrow = f'<div class="breye" style="color:{dk}">{html.escape(c["badge"])}</div>' if c.get('badge') else ''
        sub = f'<div class="brsub">{html.escape(c["sub"])}</div>' if c.get('sub') else ''
        return (f'<div class="brc brquote" {land} style="height:{c["h"]}px">'
                f'<div class="brbar" {rule_t} data-axis="y" style="background:{mn}"></div>'
                f'{eyebrow}<div class="brqt" style="color:{dk}">{_txt(c["text"])}</div>{sub}</div>')
    if k == 'number':
        eyebrow = f'<div class="breye" style="color:{dk}">{html.escape(c["badge"])}</div>' if c.get('badge') else ''
        prev_h = f'<span class="brnp">{html.escape(c["prev"])}</span><span class="brna">→</span>' if c.get('prev') else ''
        if c.get('count_from') is not None and c.get('count_to') is not None:
            cnt_attr = (f'data-count="1" data-t="{t + 0.12:.3f}" data-dur="{c["count_dur"]}" '
                        f'data-from="{c["count_from"]}" data-to="{c["count_to"]}" '
                        f'data-prefix="{html.escape(c["prefix"])}" data-suffix="{html.escape(c["suffix"])}" '
                        f'data-dec="{int(c["dec"])}" data-comma="{"1" if c["comma"] else "0"}"')
        else:
            cnt_attr = ''
        sub = f'<div class="brsub">{html.escape(c["sub"])}</div>' if c.get('sub') else ''
        return (f'<div class="brc brnum" {land} style="height:{c["h"]}px">'
                f'<div class="brtrule" {rule_t} data-axis="x" style="background:{mn}"></div>'
                f'{eyebrow}<div class="brnr">{prev_h}<span class="brnm" {cnt_attr} style="color:{dk}">{html.escape(c["text"])}</span></div>'
                f'{sub}</div>')
    if k == 'bars':
        rows = ''
        for i, (label, v, shown, colr) in enumerate(c['rows']):
            bc = PALETTE[colr][1] if colr else mn
            bd = PALETTE[colr][0] if colr else dk
            rows += (f'<div class="brbr"><div class="brbl"><span>{html.escape(label)}</span>'
                     f'<span class="mono" style="color:{bd}">{html.escape(shown)}</span></div>'
                     f'<div class="brtk"><div class="brfl" data-fill="{v:.4f}" '
                     f'data-t="{t + 0.28 + i * 0.24:.3f}" data-dur="{c["dur"]}" style="background:{bc}"></div></div></div>')
        return (f'<div class="brc brbars" {land} style="height:{c["h"]}px">'
                f'<div class="brtrule" {rule_t} data-axis="x" style="background:{mn}"></div>'
                f'<div class="brbt">{html.escape(c["title"])}</div>{rows}</div>')
    if k == 'pair':
        a = _pair_half(c['left'], sec, t, c['h'], False)
        b = _pair_half(c['right'], sec, t + 0.32, c['h'], True)
        return f'<div class="brpair">{a}{b}</div>'
    if k == 'units':
        cells, n = '', 0
        for cnt, colr in c['groups']:
            for _ in range(cnt):
                cells += f'<i data-u="{t + 0.35 + n * c["step"]:.3f}" data-c="{PALETTE[colr][1]}"></i>'
                n += 1
        cells += '<i></i>' * max(0, c['total'] - n)
        summ = f'<div class="brsub" style="margin-top:16px">{html.escape(c["summary"])}</div>' if c.get('summary') else ''
        return (f'<div class="brc brunits" {land} style="height:{c["h"]}px">'
                f'<div class="brtrule" {rule_t} data-axis="x" style="background:{mn}"></div>'
                f'<div class="breye" style="color:{dk}">{html.escape(c["badge"])}</div>'
                f'<div class="bru">{cells}</div>{summ}</div>')
    if k == 'tiles':
        tl = ''
        for i, (label, status, colr) in enumerate(c['tiles']):
            d, m, _ = PALETTE[colr]
            tl += (f'<div class="brt" data-t="{t + 0.28 + i * c["step"]:.3f}">'
                   f'<div class="brtrule" data-rule="{t + 0.28 + i * c["step"]:.3f}" data-axis="x" style="background:{m}"></div>'
                   f'<div class="brtl">{html.escape(label)}</div>'
                   f'<div class="brts" style="color:{d}">{html.escape(status)}</div></div>')
        return (f'<div class="brtiles" {land}><div class="brtt">{html.escape(c["title"])}</div>'
                f'<div class="brgrid">{tl}</div></div>')
    raise SystemExit(f'unknown card kind {k!r}')


def _pair_half(c, sec, t, h, is_right):
    dk, mn, _ = _c(c, sec)
    eyebrow = f'<div class="breye" style="color:{dk}">{html.escape(c.get("badge", ""))}</div>' if c.get('badge') else ''
    sub = f'<div class="brhsub">{_txt(c["sub"])}</div>' if c.get('sub') else ''
    cls = 'brc brhalf right' if is_right else 'brc brhalf'
    return (f'<div class="{cls}" data-t="{t:.3f}" style="height:{h}px">'
            f'<div class="brtrule" data-rule="{t:.3f}" data-axis="x" style="background:{mn}"></div>'
            f'{eyebrow}<div class="brhval" style="color:{dk}">{_txt(c["text"])}</div>{sub}</div>')


# ----------------------------------------------------------------------------------------------------- CSS
BR_CSS = f"""
@font-face{{font-family:'Hahmlet';src:url(assets/Hahmlet-VF.ttf);font-weight:100 900;font-display:block}}
#root.stage #ground{{background:{PAPER}}}
#root .beam,#root #vignette{{display:none}}
#root{{color:{INK};font-family:Pretendard,sans-serif}}
#brGrain{{position:absolute;inset:0;pointer-events:none;z-index:35;opacity:.22;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' seed='11'/%3E%3CfeColorMatrix values='0 0 0 0 .25 0 0 0 0 .24 0 0 0 0 .21 0 0 0 .16 0'/%3E%3C/filter%3E%3Crect width='260' height='260' filter='url(%23n)'/%3E%3C/svg%3E")}}
#brProg{{position:absolute;left:60px;top:60px;width:960px;display:flex;align-items:center;gap:18px}}
.brpb{{flex:1;display:flex;gap:8px;align-items:center}}
.brps{{flex:1;height:5px;background:{RULE}}}
.brps.past{{background:#8A8A92}}
.brps.cur{{height:6px}}
.brpn{{font:600 25px/1 'Geist Mono',monospace;color:{INK2};letter-spacing:.04em;flex:none}}
#brHdr{{position:absolute;left:60px;top:98px;width:960px;padding-bottom:20px;border-bottom:3px solid {INK}}}
#brHdr::after{{content:'';position:absolute;left:0;right:0;bottom:-8px;height:1px;background:rgba(22,22,24,.35)}}
#brHdr .kick{{display:flex;align-items:center;gap:12px;font:700 34px/1.2 Pretendard;letter-spacing:-.01em}}
#brHdr .sq{{width:12px;height:12px;display:inline-block;flex:none}}
#brTitle{{margin-top:14px;font:700 84px/1.16 'Hahmlet',serif;letter-spacing:-.035em;white-space:nowrap;width:100%;overflow:hidden}}
#brVis{{position:absolute;left:60px;top:332px;width:960px;background:{SHEET};border:1.5px solid {INK};border-radius:6px;overflow:hidden;box-sizing:border-box}}
#brVis.dark{{background:{DARK};border-color:{DARK}}}
#brSrc{{position:absolute;left:60px;width:900px;height:40px;display:flex;align-items:center;gap:14px}}
.brsc{{display:inline-flex;align-items:center;gap:8px;padding:6px 13px;border-radius:3px;font:700 23px/1 Pretendard;white-space:nowrap;flex:none}}
.brsc.solid{{color:{SHEET}}}
.brsc.solid .dot{{width:8px;height:8px;border-radius:50%;background:{SHEET};display:inline-block}}
.brsc.outline{{background:transparent;border:1.5px solid}}
.brsc.dashed{{background:transparent;border:1.5px dashed #5D6878;color:#4A525E}}
.brstxt{{font:500 27px/1.2 Pretendard;color:{INK2};white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
#brCards{{position:absolute;left:60px;width:960px;display:flex;flex-direction:column;gap:{GAP}px}}
.brc{{position:relative;box-sizing:border-box;background:{SHEET};border:1px solid rgba(22,22,24,.15);border-radius:4px;opacity:0;flex:none;overflow:hidden}}
.brbar{{position:absolute;left:0;top:0;bottom:0;width:6px;transform-origin:50% 0}}
.brtrule{{position:absolute;left:0;right:0;top:0;height:5px;transform-origin:0 50%}}
.brc.brrow{{display:flex;align-items:center;gap:22px;padding:0 86px 0 32px}}
.brtag{{display:inline-flex;align-items:center;gap:8px;padding:9px 15px;border-radius:3px;font:700 25px/1 Pretendard;white-space:nowrap;flex:none}}
.brix{{font-family:'Geist Mono',monospace;font-weight:600;opacity:.75}}
.brln{{font:700 37px/1.25 Pretendard;color:{INK};letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.breye{{font:600 25px/1.2 'Geist Mono',Pretendard,sans-serif;letter-spacing:.05em;text-transform:uppercase}}
.brsub{{margin-top:14px;font:500 30px/1.3 Pretendard;color:#5A5A63}}
.brc.brpull{{padding:32px 86px 30px 48px;border:0;border-top:3.5px solid {INK};border-bottom:2px solid {INK};border-radius:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}}
.brtop2{{position:absolute;left:0;right:0;top:6px;height:1px;background:rgba(22,22,24,.30);transform-origin:0 50%}}
.brpq{{font:700 54px/1.28 'Hahmlet',serif;color:{INK};letter-spacing:-.03em}}
.brqm{{font:700 66px/.5 'Hahmlet',serif;display:inline-block;vertical-align:-8px;margin-right:8px}}
.brc.brquote{{padding:28px 86px 26px 38px;display:flex;flex-direction:column;justify-content:center}}
.brqt{{margin-top:14px;font:700 48px/1.26 'Hahmlet',serif;letter-spacing:-.03em}}
.brc.brnum{{padding:28px 86px 24px 36px;display:flex;flex-direction:column;justify-content:center}}
.brnr{{margin-top:14px;display:flex;align-items:baseline;gap:20px}}
.brnp{{font:700 68px/1 'Hahmlet',serif;color:#8A8A92;letter-spacing:-.03em}}
.brna{{font:400 52px/1 Pretendard;color:#8A8A92}}
.brnm{{font:700 104px/1 'Hahmlet',serif;letter-spacing:-.035em}}
.brc.brbars,.brc.brunits{{padding:26px 86px 22px 32px}}
.brbt{{font:700 31px/1.2 Pretendard;color:{INK2};margin-bottom:14px}}
.brbr{{margin-top:12px}}
.brbl{{display:flex;justify-content:space-between;font:700 31px/1.2 Pretendard;color:{INK};margin-bottom:8px}}
.brtk{{height:30px;background:{TRACK};border-radius:3px;overflow:hidden}}
.brfl{{height:100%;width:0;border-radius:2px}}
.brpair{{display:flex;gap:18px}}
.brc.brhalf{{flex:1;padding:28px 28px 24px}}
.brc.brhalf.right{{padding-right:76px}}
.brhval{{margin-top:18px;font:700 54px/1.16 'Hahmlet',serif;letter-spacing:-.03em}}
.brhsub{{margin-top:14px;font:500 28px/1.35 Pretendard;color:#5A5A63}}
.bru{{display:grid;grid-template-columns:repeat(10,1fr);gap:11px;margin-top:26px}}
.bru i{{display:block;height:56px;border-radius:3px;background:{TRACK}}}
.brtiles{{opacity:0}}
.brtt{{font:700 31px/1.2 Pretendard;color:{INK2};margin-bottom:14px}}
.brgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px 18px}}
.brt{{position:relative;height:140px;background:{SHEET};border:1px solid rgba(22,22,24,.15);border-radius:4px;
  display:flex;flex-direction:column;justify-content:center;padding:18px 24px;opacity:0;overflow:hidden}}
.brt:nth-child(even){{padding-right:76px}}
.brtl{{font:600 28px/1.2 Pretendard;color:{INK2}}}
.brts{{font:700 44px/1.2 'Hahmlet',serif;margin-top:8px}}
#brVis .t{{font-family:Pretendard;color:{INK}}}
#brVis .serif{{font-family:'Hahmlet',serif}}
#brVis .mono{{font-family:'Geist Mono',Pretendard,monospace}}
/* Light magazine cover (Run 0) */
.brcov{{position:absolute;inset:0;background:{PAPER};overflow:hidden}}
.brcov .mast{{position:absolute;left:60px;top:74px;width:960px;border-top:3.5px solid {INK};border-bottom:1px solid rgba(22,22,24,.35);
  padding:16px 0 14px;display:flex;align-items:center;justify-content:space-between}}
.brcov .brand{{display:flex;align-items:baseline;gap:14px}}
.brcov .logo{{font:700 34px/1 'Hahmlet',serif;letter-spacing:.05em;color:{INK}}}
.brcov .dot{{display:inline-block;width:10px;height:10px;margin-left:4px}}
.brcov .sec{{font:500 24px/1 'Geist Mono',Pretendard,monospace;letter-spacing:.12em;color:{MUTED}}}
.brcov .iss{{font:500 24px/1 'Geist Mono',Pretendard,monospace;letter-spacing:.08em;color:{MUTED}}}
.brcov .kick{{position:absolute;left:60px;top:174px;display:flex;align-items:center;gap:12px;font:700 34px/1.2 Pretendard}}
.brcov .kick .bar{{width:28px;height:4px;display:inline-block}}
.brcov .ttl{{position:absolute;left:60px;top:234px;width:960px;font:700 100px/1.18 'Hahmlet',serif;color:{INK};letter-spacing:-.035em}}
.brcov .ttl .hi{{display:inline-block;border-bottom:6px solid;padding-bottom:4px}}
.brcov .fig{{position:absolute;left:60px;top:636px;width:960px;height:434px;background:{DARK};border:1.5px solid {INK};border-radius:6px;overflow:hidden}}
.brcov .fig.light{{background:{SHEET}}}
.brcov .figcap{{position:absolute;left:0;right:0;bottom:0;height:44px;background:rgba(20,23,29,.92);border-top:1px solid rgba(255,255,255,.12);
  padding:0 22px;display:flex;align-items:center;justify-content:space-between;font:500 21px/1 'Geist Mono',Pretendard,monospace;color:#9CA3AF;letter-spacing:.06em}}
.brcov .fact{{position:absolute;left:60px;top:1106px;width:960px;background:{SHEET};border:1px solid rgba(22,22,24,.15);border-left:7px solid;
  padding:24px 86px 22px 30px;border-radius:0 4px 4px 0}}
.brcov .fk{{font:600 23px/1 'Geist Mono',monospace;letter-spacing:.14em}}
.brcov .fv{{margin-top:12px;font:800 42px/1.25 Pretendard;color:{INK};letter-spacing:-.02em}}
.brcov .fn{{margin-top:10px;font:500 27px/1.25 Pretendard;color:{MUTED}}}
"""


# ----------------------------------------------------------------------------------------------------- stings & meta
def brief_sting(t0=0.0, cover=None, mode='outro', brand='BRIEF', tagline='RESEARCH  ·  ANALYSIS  ·  INSIGHT',
                accent='crimson', x=540, y=890, width=680):
    """Minimal Ink & Rule editorial sting (assets/gfx/brief_sting.js).
    mode='outro' (2.8 s, default cover=True): fades the frame to paper over 0.35 s, then draws double ink rules +
    Hahmlet 700 wordmark + crimson square period + convergence close.
    mode='intro' (1.4 s, default cover=False): subtle registration sweep along the cover masthead hairline."""
    acc_hex = PALETTE[accent][1] if accent in PALETTE else accent
    if cover is None:
        cover = (mode == 'outro')
    return dict(mode=mode, t0=round(t0, 3), cover=bool(cover), brand=brand, tagline=tagline,
                accent=acc_hex, ink=INK, paper=PAPER, x=x, y=y, width=width)


def _sting_html(stings):
    out = ''
    for i, st in enumerate(stings):
        if st.get('cover'):
            out += f'<div id="brStingCover{i}" style="position:absolute;inset:0;background:{PAPER};opacity:0;z-index:40"></div>'
        out += f'<canvas id="brSting{i}" width="1080" height="1920" style="position:absolute;inset:0;z-index:41;pointer-events:none"></canvas>'
    return out + ('<script src="brief_sting.js"></script>' if stings else '')


def _record_run_color(rid, color, mapped=True):
    """Persist mapped run id -> section colour name in gfx/brief_colors.json so compose.py and preview.py
    automatically match keyword caption highlights to each run's section colour."""
    from build_gfx_common import _mapped_id, OUT
    m_rid = _mapped_id(rid) if mapped else rid
    if not m_rid:
        return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'brief_colors.json')
    lock = os.path.join(OUT, '.brief_colors.lock')
    for _ in range(400):
        try:
            os.mkdir(lock)
            break
        except FileExistsError:
            time.sleep(0.02)
    try:
        data = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
        data[m_rid] = color
        json.dump(data, open(path, 'w', encoding='utf-8'), indent=1, sort_keys=True)
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


def _card_settle(c):
    """s from a card's landing until everything in it is at rest, from the offsets _card_html writes"""
    k = c['kind']
    if k == 'number':
        return max(THUMB_SETTLE, 0.12 + float(c.get('count_dur') or 0) + 0.1)
    if k == 'bars':
        return max(THUMB_SETTLE, 0.28 + 0.24 * max(0, len(c['rows']) - 1) + c['dur'] + 0.1)
    if k == 'units':
        return max(THUMB_SETTLE, 0.35 + c['step'] * c['total'] + 0.1)
    if k == 'tiles':
        return max(THUMB_SETTLE, 0.28 + c['step'] * max(0, len(c['tiles']) - 1) + 0.48 + 0.1)
    return THUMB_SETTLE


def _default_thumb(r, cards=(), stings=(), cover=False):
    """The run's thumbnail candidate when the caller marks none (thumb=()): a window near the run's end, after the last
    lower card has landed and settled (_card_settle: entrance, count-up, bar fill, unit/tile steps) and before an outro sting fades the
    frame to paper. build_gfx.py collects it into gfx/thumbs.json, so finish.sh always has candidates to show (the HN
    BRIEF short, 2026-11-24: no run was marked and chk/s1_thumbs.png came out empty)."""
    dur = r['dur']
    end = dur - 0.2
    for st in stings:
        if st.get('mode') == 'outro':
            end = min(end, st['t0'] - 0.1)
    start = 1.6 if cover else 0.0                 # the cover's intro sting runs 0.15-1.55 s
    for t, c in cards:
        start = max(start, (t - LEAD if t > 0.02 else 0.0) + _card_settle(c))
    start = max(start, end - THUMB_WINDOW)        # the late part of the run: the upper visual's own motion has settled
    return [[round(start, 3), round(end, 3)]] if end - start >= 0.1 else []


def _cfg(r, thumb):
    return dict(dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=[], moves=[], heroes=[],
                thumb=[list(x) if isinstance(x, (list, tuple)) else x for x in thumb], brief=dict(), uiOk=True)


# ----------------------------------------------------------------------------------------------------- page builders
def brief_page(rid, r, sec, vis_html, source, cards=(), layout='default', vis_dark=False,
               vis_js='', vis_css='', thumb=(), mapped=True, stings=()):
    """One body run in the `brief` editorial magazine theme.
    sec = section(kicker, title, color, index=..., total=...);
    source = (one of SOURCE_KINDS, exact source text);
    cards = [(t, card), ...] with t from W() (0 = in place on frame 0; lands LEAD s early);
    layout = 'default' (vis 548 / cards 416) | 'visual_tall' (656 / 308) | 'cards_tall' (416 / 548)."""
    kind, src_text = source
    if kind not in SOURCE_KINDS:
        raise SystemExit(f'{rid}: source kind {kind!r} - one of {SOURCE_KINDS}')
    if layout not in LAYOUTS:
        raise SystemExit(f'{rid}: layout {layout!r} - one of {tuple(LAYOUTS)}')
    vis_h, src_y, cards_y, cards_h = LAYOUTS[layout]
    total = sum(c['h'] for _, c in cards) + GAP * max(0, len(cards) - 1)
    if total > cards_h:
        raise SystemExit(f'{rid}: lower cards are {total} px tall - at most {cards_h} fit in layout {layout!r} (y {cards_y}-{cards_y + cards_h})')
    dk, mn, _ = PALETTE[sec['color']]
    cards_html = ''.join(_card_html(c, sec, 0.0 if t <= 0.02 else max(0.02, t - LEAD), f'{i}') for i, (t, c) in enumerate(cards))
    body = (f'{_progress_html(sec, mn)}'
            f'<div id="brHdr"><div class="kick" style="color:{mn}"><span class="sq" style="background:{mn}"></span>{html.escape(sec["kicker"])}</div>'
            f'<div id="brTitle" style="color:{dk}">{html.escape(sec["title"])}</div></div>'
            f'<div id="brVis" class="{"dark" if vis_dark else ""}" style="height:{vis_h}px">{vis_html}</div>'
            f'<div id="brSrc" style="top:{src_y}px">{_source_chip_html(kind, mn, dk)}<span class="brstxt">{html.escape(src_text)}</span></div>'
            f'<div id="brCards" style="top:{cards_y}px;height:{cards_h}px">{cards_html}</div>'
            f'<div id="brGrain"></div>{_sting_html(stings)}<script src="brief.js"></script>')
    cfg = _cfg(r, thumb or _default_thumb(r, cards, stings))
    cfg['brief'] = dict(stings=list(stings), color=sec['color'], layout=layout)
    _record_run_color(rid, sec['color'], mapped=mapped)
    page(rid, cfg, extra_html=body, extra_css=BR_CSS + vis_css, extra_js=vis_js, mapped=mapped)


def brief_cover(rid, r, kicker, lines, fact, note='', vis_html='', vis_cap='', vis_light=False,
                fact_label='KEY FINDING', issue='NO. 01 · 2026', brand='BRIEF',
                section_label='RESEARCH BRIEFING', accent='crimson', vis_js='', vis_css='',
                thumb=(), mapped=True, stings=()):
    """Run 0: Light Magazine Cover on #F5F4F0 newsprint paper (seamless transition into Run 1).
    lines = 2-3 headline lines in Hahmlet 700 (last line highlighted in accent with editorial underline);
    fact = the single concrete fact in the left-bar strip; note = source/caveat beneath it;
    vis_html = hero visual inside the sharp editorial frame (y 636-1070)."""
    if accent not in PALETTE:
        raise SystemExit(f'{rid}: cover accent {accent!r}: one of {", ".join(PALETTE)}')
    dk, mn, _ = PALETTE[accent]
    ttl = '<br>'.join(
        f'<span class="hi" style="color:{dk};border-bottom-color:{mn}">{html.escape(l)}</span>'
        if i == len(lines) - 1 else html.escape(l)
        for i, l in enumerate(lines)
    )
    cap_bar = (f'<div class="figcap"><span>{html.escape(vis_cap[0])}</span><span>{html.escape(vis_cap[1])}</span></div>'
               if isinstance(vis_cap, (list, tuple)) and len(vis_cap) == 2
               else (f'<div class="figcap"><span>{html.escape(vis_cap)}</span><span></span></div>' if vis_cap else ''))
    fig_html = f'<div class="fig{" light" if vis_light else ""}">{vis_html}{cap_bar}</div>'
    note_html = f'<div class="fn">{html.escape(note)}</div>' if note else ''
    body = (f'<div class="brcov">'
            f'<div class="mast"><div class="brand"><span class="logo">{html.escape(brand)}'
            f'<span class="dot" style="background:{mn}"></span></span>'
            f'<span class="sec">{html.escape(section_label)}</span></div>'
            f'<span class="iss">{html.escape(issue)}</span></div>'
            f'<div class="kick" style="color:{mn}"><span class="bar" style="background:{mn}"></span>{html.escape(kicker)}</div>'
            f'<div class="ttl">{ttl}</div>'
            f'{fig_html}'
            f'<div class="fact" style="border-left-color:{mn}"><div class="fk" style="color:{mn}">{html.escape(fact_label)}</div>'
            f'<div class="fv">{html.escape(fact)}</div>{note_html}</div>'
            f'</div><div id="brGrain"></div>{_sting_html(stings)}<script src="brief.js"></script>')
    cfg = _cfg(r, thumb or _default_thumb(r, stings=stings, cover=True))
    cfg['brief'] = dict(stings=list(stings), color=accent, cover=True)
    _record_run_color(rid, accent, mapped=mapped)
    page(rid, cfg, extra_html=body, extra_css=BR_CSS + vis_css, extra_js=vis_js, mapped=mapped)
