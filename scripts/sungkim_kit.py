"""The Sungkim theme (references/theme-sungkim.md), rebuilt 2026-11-23 from the creator's real Short
(youtube.com/shorts/UE1C-fwapU0, analysed frame by frame: /Users/admin/project/shorts/sungkim-ref/analysis.md).

Layout on the 1080x1920 canvas:
  cover run   run 0 only: dark full-bleed page, kicker, 2-3 line title (last line gold), an orange fact pill, a note pill
  header      y  91-300  kicker (grey, 46 px) and the title (800, 112 px, in the SECTION COLOUR, one line, shrinks)
  #skVis      x 56-1024, y 368-921  the upper card (968 x 553): a paper page, a paper figure, a chart you draw, an image
  #skSrc      y 930-966, x 72      the source line, always one of SOURCE_KINDS + " · " + the exact source
  #skCards    x 56-1024, y 984-1384 the lower cards (CARD KINDS below), at most 3 stacked (or one pair / units / tiles card)
  captions    y 1410-1550 (compose.py: black Pretendard on the paper, a thin paper-coloured outline), nothing below 1560

A section (kicker + title + colour) lasts 2-5 runs; the upper card changes within it; the lower area is rebuilt in
every run from the list you pass (pass earlier cards again with t 0 to keep them; leave them out to clear).

  from sungkim_kit import *
  SEC = section('진화가 일어났다', '5.5% → 92%', 'teal')
  r, ws = words('s1', 6)
  sungkim_page('s1_r6', r, SEC, vis_html=..., source=('계산해서 그린 그림', '논문 그림 6의 값'),
               cards=[(0, badge_card('시작', '복사를 잘 못하는 조상 100개')),
                      (W(ws, '16세대'), number_card('16세대 만에', '5.5% → 92%'))])
A card's t is the phrase it belongs to: the kit lands it LEAD (0.3 s) before the phrase, as the creator does.
"""
import html
from build_gfx_common import *

# section colours: (title / big text, badge / border / bar)
PALETTE = {'teal': ('#0A5F53', '#0F786C'), 'blue': ('#125783', '#1E6FA4'), 'gold': ('#9D6C0A', '#B37C10'),
           'red': ('#AB3E23', '#CD5130'), 'purple': ('#5E4877', '#745B94'), 'grey': ('#5D6268', '#989EA6')}
PAPER, INK, INK2, MUTED, TRACK, SRC = '#F6F3E9', '#1B1D21', '#4B4F55', '#767C89', '#E6E1D5', '#484644'
GOLD, PILL, DARK = '#F9CA60', '#E0532E', '#020611'
SOURCE_KINDS = ('개념 그림', '실제 자료', '실제 그림', '계산해서 그린 그림')
LEAD = 0.3
CARDS_Y, CARDS_H, GAP = 984, 400, 14


def section(kicker, title, color='teal'):
    """one section's header: a kicker that frames the topic, a one-line title (a hook question, a number, a 3-part
    summary or a conclusion, 6-11 characters), and its colour - each section gets its own (teal, blue, gold, red for
    risk, purple, back to teal), shared by the title, the badges and the card borders."""
    if color not in PALETTE: raise SystemExit(f'section colour {color!r}: one of {", ".join(PALETTE)}')
    return dict(kicker=kicker, title=title, color=color)


# ----------------------------------------------------------------------------------------------------- lower cards
# Every card is a dict: kind, the html builder's args, an optional colour (default: the section's; 'grey' for a
# question, 'red' for an error, a mutation, a risk). Heights are fixed per kind so the stack never passes y 1384.
H = dict(badge=118, statement=250, quote=250, number=250, bars=0, pair=320, units=300, tiles=340)


def badge_card(badge, text, color=None):
    """the most common card: a pill badge and one short line (a keyword phrase, not the spoken sentence)"""
    return dict(kind='badge', badge=badge, text=text, color=color, h=H['badge'])


def statement_card(text, sub='', badge='', color=None, round_=False):
    """a big centred statement (1-2 lines, \\n breaks), optional small line under it and optional badge; round_=True
    (radius 44) for a question card or the closing card"""
    return dict(kind='statement', text=text, sub=sub, badge=badge, color=color, round_=round_, h=H['statement'])


def quote_card(badge, quote, sub='', color=None):
    """a quoted sentence in the section colour, with what it means or where it is from beneath"""
    return dict(kind='quote', badge=badge, text=f'“{quote}”', sub=sub, color=color, h=H['quote'])


def number_card(badge, value, sub='', color=None):
    """the number the section is about, huge: '5.5% → 92%', '3분의 1', '2만 배 ↓'"""
    return dict(kind='number', badge=badge, text=value, sub=sub, color=color, h=H['number'])


def bars_card(title, rows, color=None, dur=1.2):
    """a comparison: rows = [(label, value 0..1, shown text, colour or None)]; the bars fill over dur s after landing"""
    return dict(kind='bars', title=title, rows=rows, color=color, dur=dur, h=70 + 96 * len(rows))


def pair_card(left, right):
    """two cards side by side (each a number_card or statement_card), e.g. what was lost vs what was gained"""
    return dict(kind='pair', left=left, right=right, h=H['pair'])


def units_card(badge, groups, summary='', total=20, color=None, step=0.06):
    """a row of units filling in: groups = [(count, colour name)], e.g. [(14, 'gold'), (6, 'red')] of 20"""
    return dict(kind='units', badge=badge, groups=groups, summary=summary, total=total, color=color, step=step, h=H['units'])


def tiles_card(title, tiles, step=0.9):
    """a 2x2 status grid: tiles = [(label, status, colour name)], landing one after another (step s apart)"""
    return dict(kind='tiles', title=title, tiles=tiles, step=step, h=H['tiles'])


MIN_CAPTURE_TEXT = 26     # px on screen: the body text of a capture must be at least this tall (the user's review, 2026-11-23)


def phrase_marks(json_path, phrase, t):
    """the boxes of one phrase found by scripts/capture_marks.py (its <capture>.json), to underline at run time t"""
    import json as _json
    d = _json.load(open(json_path, encoding='utf-8'))
    if phrase not in d.get('phrases', {}): raise SystemExit(f'phrase_marks: {phrase!r} not in {json_path} - run capture_marks.py with --phrase')
    return dict(boxes=d['phrases'][phrase], t=t)


def credit_chip(credit, pos='br'):
    """The source's name drawn on the capture itself (the user, 2026-11-26: every capture names its source in its
    top-right or bottom-right corner, so a crop passed around still carries it). pos 'br' (default) or 'tr'."""
    if not credit or not str(credit).strip():
        raise SystemExit('capture: credit="출처: <매체·사이트 이름>" is required on every real capture (top-right or bottom-right)')
    edge = 'top' if pos == 'tr' else 'bottom'
    return (f'<div class="cap-credit" style="position:absolute;right:14px;{edge}:14px;z-index:6;padding:5px 12px;'
            f'background:rgba(17,18,20,.84);color:#fff;font:600 26px/1.25 Pretendard,sans-serif;border-radius:6px;'
            f'letter-spacing:-.2px;white-space:nowrap">{html.escape(str(credit))}</div>')


def capture_html(src, fw, fh, focus=None, zoom=None, w=968, h=553, marks=(), text_px=None, keep=(), min_text=None,
                 credit='', credit_pos='br'):
    """a real source capture filling the upper card, cropped around focus=(x, y) in the image's own pixels.
    marks: [phrase_marks(...) or dict(boxes=[[x0,y0,x1,y1],...], t=...)] - a red underline sweeps under each box at t
    (use W() - 0.2: it lands as the narration names it). Without focus the crop centres on the marks.
    text_px: the page's body text height in the image (capture_marks.py prints it). The kit stops the build when the
    text would show under MIN_CAPTURE_TEXT px or a mark would fall outside the crop: an unreadable capture is a defect.
    Without zoom it picks the smallest zoom that makes the text readable.
    keep: boxes [x0, y0, x1, y1] (image pixels, e.g. a page title) that must stay whole in the crop - the build stops
    otherwise (the user, 2026-11-24, n020: a zoom for the byline cut the title's first and last letters).
    min_text: lower the readable-text floor for this crop only, when keeping a box whole needs a smaller zoom; say why
    in a comment at the call."""
    chip = credit_chip(credit, credit_pos)   # the source on the capture itself (required)
    floor = min_text or MIN_CAPTURE_TEXT
    base = max(w / fw, h / fh)
    if zoom is None: zoom = max(1.0, (floor / text_px) / base) if text_px else 1.0
    k = base * zoom
    if text_px and text_px * k < floor - 0.01:
        raise SystemExit(f'capture_html {src}: body text {text_px} px x {k:.2f} = {text_px * k:.0f} px on screen, under '
                         f'{floor} px - use zoom >= {floor / text_px / base:.2f} or crop a smaller region')
    allb = [b for m in marks for b in m['boxes']]
    if focus is None and allb:
        focus = ((min(b[0] for b in allb) + max(b[2] for b in allb)) / 2, (min(b[1] for b in allb) + max(b[3] for b in allb)) / 2)
    fx, fy = focus or (fw / 2, fh / 2)
    x = min(0, max(w - fw * k, w / 2 - fx * k)); y = min(0, max(h - fh * k, h / 2 - fy * k))
    out = (f'<img src="{html.escape(src)}" style="position:absolute;left:{x:.1f}px;top:{y:.1f}px;width:{fw * k:.1f}px;'
           f'height:{fh * k:.1f}px;display:block">')
    for x0, y0, x1, y1 in keep:
        if x + x0 * k < -1 or x + x1 * k > w + 1 or y + y0 * k < -1 or y + y1 * k > h + 1:
            raise SystemExit(f'capture_html {src}: the kept box ({x0},{y0})-({x1},{y1}) is cut by the crop - lower zoom (min_text) or move focus')
    for m in marks:
        for x0, y0, x1, y1 in m['boxes']:
            L, T, R = x + x0 * k, y + y1 * k + 2, x + x1 * k
            if L < -2 or R > w + 2 or T < 0 or T > h - 4:
                raise SystemExit(f'capture_html {src}: the mark at ({x0},{y0})-({x1},{y1}) falls outside the crop - move focus or lower zoom')
            out += (f'<div data-sweep="{max(0.02, m["t"]):.3f}" style="position:absolute;left:{L:.1f}px;top:{T:.1f}px;'
                    f'width:{R - L:.1f}px;height:6px;border-radius:3px;background:#E0342C;transform-origin:0 50%;transform:scaleX(0)"></div>')
    return out + chip


def _c(card, sec):
    return PALETTE[card.get('color') or sec['color']]


def _badge(text, col):
    return f'<span class="skb" style="background:{col}">{html.escape(text)}</span>' if text else ''


def _txt(s):
    return '<br>'.join(html.escape(x) for x in s.split('\n'))


def _card_html(c, sec, t, uid):
    dk, lt = _c(c, sec)
    land = f'data-t="{t:.3f}"'
    k = c['kind']
    if k == 'badge':
        return (f'<div class="skc row" {land} style="height:{c["h"]}px;border-color:{lt}">{_badge(c["badge"], lt)}'
                f'<span class="skl">{html.escape(c["text"])}</span></div>')
    if k in ('statement', 'quote', 'number'):
        size = {'statement': 52, 'quote': 54, 'number': 92}[k]
        rad = 44 if c.get('round_') else 20
        badge = f'<div class="skbw">{_badge(c.get("badge", ""), lt)}</div>' if c.get('badge') else ''
        sub = f'<div class="sks">{html.escape(c["sub"])}</div>' if c.get('sub') else ''
        pt = 'padding-top:84px;' if c.get('badge') else ''              # the badge sits top-left: keep the text below it
        return (f'<div class="skc col" {land} style="height:{c["h"]}px;border-color:{lt};border-radius:{rad}px;{pt}">{badge}'
                f'<div class="skbig" style="font-size:{size}px;color:{dk}">{_txt(c["text"])}</div>{sub}</div>')
    if k == 'bars':
        rows = ''
        for i, (label, v, shown, colr) in enumerate(c['rows']):
            bc = PALETTE[colr][1] if colr else lt
            rows += (f'<div class="skbr"><div class="skbl"><span>{html.escape(label)}</span><span style="color:{bc}">'
                     f'{html.escape(shown)}</span></div><div class="sktr"><div class="skf" data-fill="{v:.4f}" '
                     f'data-t="{t + 0.3 + i * 0.25:.3f}" data-dur="{c["dur"]}" style="background:{bc}"></div></div></div>')
        return (f'<div class="skc colbars" {land} style="height:{c["h"]}px;border-color:{lt}">'
                f'<div class="skbt">{html.escape(c["title"])}</div>{rows}</div>')
    if k == 'pair':
        a = _card_html(dict(c['left'], h=c['h']), sec, t, uid + 'a').replace('class="skc', 'class="skc half', 1)
        b = _card_html(dict(c['right'], h=c['h']), sec, t + 0.35, uid + 'b').replace('class="skc', 'class="skc half', 1)
        return f'<div class="skpair">{a}{b}</div>'
    if k == 'units':
        cells, n = '', 0
        for cnt, colr in c['groups']:
            for _ in range(cnt):
                cells += f'<i data-u="{t + 0.4 + n * c["step"]:.3f}" data-c="{PALETTE[colr][1]}"></i>'; n += 1
        cells += '<i></i>' * max(0, c['total'] - n)
        summ = f'<div class="sks" style="margin-top:14px">{html.escape(c["summary"])}</div>' if c.get('summary') else ''
        return (f'<div class="skc colunits" {land} style="height:{c["h"]}px;border-color:{lt}">'
                f'<div class="skbw">{_badge(c["badge"], lt)}</div><div class="sku">{cells}</div>{summ}</div>')
    if k == 'tiles':
        tl = ''
        for i, (label, status, colr) in enumerate(c['tiles']):
            d, l = PALETTE[colr]
            tl += (f'<div class="skt" data-t="{t + 0.3 + i * c["step"]:.3f}" style="border-color:{l}">'
                   f'<div class="sktl">{html.escape(label)}</div><div class="skts" style="color:{d}">{html.escape(status)}</div></div>')
        return (f'<div class="sktiles" {land}><div class="sktt">{html.escape(c["title"])}</div>'
                f'<div class="skgrid">{tl}</div></div>')
    raise SystemExit(f'unknown card kind {k!r}')


SK_CSS = f"""
#root.stage #ground{{background:{PAPER}}}
#root .beam,#root #vignette{{display:none}}
#root{{color:{INK}}}
#skHdr{{position:absolute;left:56px;width:968px;top:91px;height:215px;overflow:hidden}}
#skHdr .kick{{font:700 46px/58px Pretendard;color:#5D6268;letter-spacing:-.01em}}
#skTitle{{margin-top:22px;font:800 112px/130px Pretendard;letter-spacing:-.035em;white-space:nowrap;width:100%;overflow:hidden}}
#skVis{{position:absolute;left:56px;width:968px;top:368px;height:553px;background:#FDFDFD;border:2px solid rgba(0,0,0,.07);
  border-radius:20px;overflow:hidden;box-sizing:border-box;box-shadow:0 8px 22px -10px rgba(40,32,20,.25)}}
#skVis.dark{{background:{DARK};border:0;border-radius:44px}}
#skSrc{{position:absolute;left:72px;width:900px;top:930px;height:36px;font:500 30px/36px Pretendard;color:{SRC};
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
#skCards{{position:absolute;left:56px;width:968px;top:{CARDS_Y}px;height:{CARDS_H}px;display:flex;flex-direction:column;gap:{GAP}px}}
.skc{{position:relative;box-sizing:border-box;background:#FFFEFB;border:2.5px solid;border-radius:20px;opacity:0;flex:none}}
.skc.row{{display:flex;align-items:center;gap:22px;padding:0 84px 0 26px}}
.skc.col{{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:20px 84px 20px 40px;text-align:center}}
.skc.colbars,.skc.colunits{{padding:22px 84px 22px 30px}}
.skb{{display:inline-flex;align-items:center;height:50px;padding:0 22px;border-radius:25px;color:#fff;font:800 30px/1 Pretendard;white-space:nowrap;flex:none}}
.skbw{{position:absolute;left:24px;top:20px}}
.skl{{font:800 40px/1.2 Pretendard;color:{INK};letter-spacing:-.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.skbig{{font-weight:900;line-height:1.18;letter-spacing:-.03em}}
.sks{{margin-top:10px;font:500 30px/1.3 Pretendard;color:{MUTED}}}
.skbt{{font:700 32px/1.2 Pretendard;color:{INK2};margin-bottom:14px}}
.skbr{{margin-top:10px}}
.skbl{{display:flex;justify-content:space-between;font:800 32px/1.2 Pretendard;color:{INK};margin-bottom:8px}}
.sktr{{height:34px;background:{TRACK};border-radius:10px;overflow:hidden}}
.skf{{height:100%;width:0;border-radius:10px}}
.skpair{{display:flex;gap:24px}}
.skc.half{{width:472px;padding:70px 30px 20px 30px}}
.sku{{display:grid;grid-template-columns:repeat(10,1fr);gap:12px;margin-top:66px}}
.sku i{{display:block;height:58px;border-radius:12px;background:{TRACK}}}
.sktiles{{opacity:0}}
.sktt{{text-align:center;font:800 34px/1.2 Pretendard;color:{INK2};margin-bottom:14px}}
.skgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px 24px;padding:0 0 0 0}}
.skt{{height:138px;border:2.5px solid;border-radius:20px;background:#FFFEFB;display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0}}
.sktl{{font:700 32px/1.2 Pretendard;color:{INK2}}}
.skts{{font:900 46px/1.2 Pretendard;margin-top:6px}}
#skVis .t{{font-family:Pretendard;color:{INK}}}
#skVis .mono{{font-family:'Geist Mono',Pretendard}}
.skcover{{position:absolute;inset:0;background:{DARK};overflow:hidden}}
.skcover .bg{{position:absolute;inset:0;background-size:cover;background-position:center;opacity:.85}}
.skcover .kick{{position:absolute;left:60px;right:60px;top:150px;text-align:center;font:600 38px/1.2 Pretendard;color:#CFD4DF}}
.skcover .ttl{{position:absolute;left:50px;right:50px;top:220px;text-align:center;font:900 112px/134px Pretendard;color:#FAFDFF;letter-spacing:-.03em}}
.skcover .ttl .g{{color:{GOLD}}}
.skcover .pill{{position:absolute;left:50%;transform:translateX(-50%);top:1190px;padding:24px 44px;border-radius:30px;background:{PILL};
  color:#fff;font:800 44px/1.2 Pretendard;white-space:nowrap}}
.skcover .note{{position:absolute;left:50%;transform:translateX(-50%);top:1316px;padding:10px 26px;border-radius:22px;background:rgba(10,12,18,.72);
  color:#E6E9EF;font:500 30px/1.25 Pretendard;white-space:nowrap}}
"""


def sting(name='bulb', t0=0.0, x=540, y=900, size=432, cover=False, colours=None):
    """a pixel sting (assets/gfx/sting.js) on this run: starts at run time t0 (3 s long for 'bulb'), centred at
    (x, y), size px square. cover=True first fades the whole frame to paper over 0.35 s (the outro: the short's
    last picture gives way to the logo). The user chose the lightbulb on 2026-11-24 for the start and the end."""
    # colours overrides the sting palette, e.g. {'ink': '#E6E9EF'} on the dark cover where the ink outline would vanish
    return dict(name=name, t0=round(t0, 3), x=x, y=y, size=size, cover=cover, colours=colours)


def _sting_html(stings):
    out = ''
    for i, st in enumerate(stings):
        if st['cover']:
            out += f'<div id="skStingCover{i}" style="position:absolute;inset:0;background:{PAPER};opacity:0;z-index:40"></div>'
        out += (f'<canvas id="skSting{i}" width="{st["size"]}" height="{st["size"]}" style="position:absolute;'
                f'left:{st["x"] - st["size"] // 2}px;top:{st["y"] - st["size"] // 2}px;z-index:41"></canvas>')
    return out + ('<script src="sting.js"></script>' if stings else '')


def _cfg(r, thumb):
    return dict(dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=[], moves=[], heroes=[],
                thumb=[list(x) if isinstance(x, (list, tuple)) else x for x in thumb], sungkim=dict(), uiOk=True)


def sungkim_page(rid, r, sec, vis_html, source, cards=(), vis_dark=False, vis_js='', vis_css='', thumb=(), mapped=True, stings=()):
    """one body run. sec = section(...); source = (one of SOURCE_KINDS, the exact source: paper, figure number, date,
    what the values are); cards = [(t, card), ...] with t the run-relative time of the card's phrase (W()), 0 = in
    place on frame 0. vis_dark=True for a dark image or video in the upper card."""
    kind, src_text = source
    if kind not in SOURCE_KINDS: raise SystemExit(f'{rid}: source kind {kind!r} - one of {SOURCE_KINDS}')
    total = sum(c['h'] for _, c in cards) + GAP * max(0, len(cards) - 1)
    if total > CARDS_H: raise SystemExit(f'{rid}: the lower cards are {total} px tall - at most {CARDS_H} fit y 984-1384')
    dk, _ = PALETTE[sec['color']]
    cards_html = ''.join(_card_html(c, sec, 0.0 if t <= 0.02 else max(0.02, t - LEAD), f'{i}') for i, (t, c) in enumerate(cards))
    body = (f'<div id="skHdr"><div class="kick">{html.escape(sec["kicker"])}</div>'
            f'<div id="skTitle" style="color:{dk}">{html.escape(sec["title"])}</div></div>'
            f'<div id="skVis" class="{"dark" if vis_dark else ""}">{vis_html}</div>'
            f'<div id="skSrc">{html.escape(kind)} · {html.escape(src_text)}</div>'
            f'<div id="skCards">{cards_html}</div>{_sting_html(stings)}<script src="sungkim.js"></script>')
    cfg = _cfg(r, thumb); cfg['sungkim']['stings'] = list(stings)
    page(rid, cfg, extra_html=body, extra_css=SK_CSS + vis_css, extra_js=vis_js, mapped=mapped)


def sungkim_cover(rid, r, kicker, lines, pill, note='', bg_img=None, thumb=(), mapped=True, stings=()):
    """run 0: the cover, shown whole from frame 0 (it is the cover frame). lines = 2-3 title lines, the last in gold;
    pill = the one fact that makes the hook concrete ("자식 20개 중 14개가 똑같은 복사본"); note = what the picture is
    and how sure the claim is; bg_img = a dark image (a real capture darkened, or a picture made for this short)."""
    ttl = '<br>'.join(f'<span class="g">{html.escape(l)}</span>' if i == len(lines) - 1 else html.escape(l)
                      for i, l in enumerate(lines))
    bg = f'<div class="bg" style="background-image:url({html.escape(bg_img)})"></div>' if bg_img else ''
    note_html = f'<div class="note">{html.escape(note)}</div>' if note else ''
    body = (f'<div class="skcover">{bg}<div class="kick">{html.escape(kicker)}</div><div class="ttl">{ttl}</div>'
            f'<div class="pill">{html.escape(pill)}</div>{note_html}</div>{_sting_html(stings)}<script src="sungkim.js"></script>')
    cfg = _cfg(r, thumb); cfg['sungkim']['stings'] = list(stings)
    page(rid, cfg, extra_html=body, extra_css=SK_CSS, mapped=mapped)
