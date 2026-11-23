"""The Sungkim theme (references/theme-sungkim.md): a warm paper page for news and tech explainers. Taken from the
user's own template (gemini-code-1795429352680.html, 2026-11-23) and fitted to the skill's frame zones.

Layout on the 1080x1920 canvas (fixed in every run):
  header    y 120-270   kicker (34 px, 700) and the title (78 px, 900, one line, shrinks to fit, at least 48 px)
  #skVis    x 64-1016, y 290-850   the run's visual box (inner box 952 x 560 px; position things absolutely in it)
  #skSrc    y 862-898   the source line ("출처: ...", 30 px muted) - where the picture or the number comes from
  #skCards  x 64-1016, y 920-1380  up to three info cards stacking down (title, optional metric, body)
  captions  y 1410-1550 (compose.py: white Pretendard on a dark box), nothing below 1560; card text ends left of x 960

Use (in a project's scripts/gfx_<tag>.py):
  from sungkim_kit import *
  r, ws = words('s1', 2)
  sungkim_page('s1_r2', r, kicker='AI 칩 설계', title='AI가 처음부터 설계한 CPU',
               vis_html=capture_html('assets/a_blog.png', 1920, 1080, focus=(960, 300), zoom=1.4),
               source='출처: Architect Labs 기술 블로그',
               cards=[(0, card('전력당 성능', '비슷한 코어 대비, 시뮬레이션 기준', metric='4.59배', kind='accent')),
                      (W(ws, '그물처럼'), card('그물형 동시 실행', '서로 무관한 연산 조각을 병렬 처리', kind='blue'))],
               vis_js='window.TOP_RENDER = function (t) { ... }', thumb=[[1.0, 2.5]])
Cards keep stacking inside one section: pass the earlier cards again with t 0 so they are in place on frame 0.
vis_js is a pure function of the run time t (window.REEL: clamp, lerp, ease, easeOut, prog): no state, no transitions.
"""
import html
from build_gfx_common import *

COL = dict(canvas='#F7F4EC', card='#FFFDF8', card_accent='#EEF4FF', line='#E3DDD0', line_accent='#BFD4FF',
           text='#16181D', text2='#4A4F5A', muted='#767C89', blue='#1D5BFF', red='#D9483B', track='#ECE7DC',
           sleep='#EFECE4')

HDR_TOP, VIS_Y, VIS_H, SRC_Y, CARDS_Y, CARDS_H = 120, 290, 560, 862, 920, 460
MAX_CARDS = 3

SK_CSS = f"""
#root.stage #ground{{background:{COL['canvas']}}}
#root .beam,#root #vignette{{display:none}}
#root{{color:{COL['text']}}}
#skHdr{{position:absolute;left:64px;right:64px;top:{HDR_TOP}px;height:150px;display:flex;flex-direction:column;gap:12px;overflow:hidden}}
#skHdr .kick{{font:700 34px/1.25 Pretendard;color:{COL['text2']};letter-spacing:-.01em}}
#skTitle{{font:900 78px/92px Pretendard;color:{COL['text']};letter-spacing:-.03em;white-space:nowrap;width:100%;overflow:hidden}}
#skVis{{position:absolute;left:64px;width:952px;top:{VIS_Y}px;height:{VIS_H}px;background:{COL['card']};
  border:1.5px solid {COL['line']};border-radius:24px;overflow:hidden;box-sizing:border-box}}
#skSrc{{position:absolute;left:64px;width:880px;top:{SRC_Y}px;height:36px;font:500 30px/36px Pretendard;color:{COL['muted']};
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
#skCards{{position:absolute;left:64px;width:952px;top:{CARDS_Y}px;height:{CARDS_H}px;display:flex;flex-direction:column;gap:16px}}
.skc{{position:relative;background:{COL['card']};border:1.5px solid {COL['line']};border-left:8px solid {COL['line']};
  border-radius:20px;padding:18px 72px 18px 28px;box-sizing:border-box;opacity:0}}
.skc.accent{{background:{COL['card_accent']};border-color:{COL['line_accent']};border-left-color:{COL['blue']}}}
.skc.blue{{border-left-color:{COL['blue']}}}
.skc.warn{{border-left-color:{COL['red']}}}
.skc .row{{display:flex;align-items:baseline;justify-content:space-between;gap:16px}}
.skc .ct{{font:800 36px/1.25 Pretendard;color:{COL['text']};letter-spacing:-.02em}}
.skc .cm{{font:900 56px/1.05 Pretendard;color:{COL['blue']};letter-spacing:-.03em;white-space:nowrap}}
.skc.warn .cm{{color:{COL['red']}}}
.skc .cb{{margin-top:6px;font:500 30px/1.35 Pretendard;color:{COL['text2']}}}
#skVis .t{{font-family:Pretendard;color:{COL['text']}}}
#skVis .mono{{font-family:'Geist Mono',Pretendard}}
"""


def card(title, body='', metric='', kind=''):
    """one info card. kind: '' (plain), 'accent' (blue-tinted, the key number), 'blue' (blue edge), 'warn' (red edge:
    a limit, a caveat, what is not proven yet). Title at most 16 Korean characters, body one line (about 26)."""
    return dict(title=title, body=body, metric=metric, kind=kind)


def capture_html(src, fw, fh, focus=None, zoom=1.0):
    """a real source capture filling the visual box (952 x 560), cropped around focus=(x, y) in the image's own pixels"""
    k = max(952 / fw, 560 / fh) * zoom
    fx, fy = focus or (fw / 2, fh / 2)
    x = min(0, max(952 - fw * k, 476 - fx * k)); y = min(0, max(560 - fh * k, 280 - fy * k))
    return (f'<img src="{html.escape(src)}" style="position:absolute;left:{x:.1f}px;top:{y:.1f}px;width:{fw * k:.1f}px;'
            f'height:{fh * k:.1f}px;display:block">')


def sungkim_page(rid, r, kicker, title, vis_html, source='', cards=(), vis_js='', vis_css='', cover_safe=None,
                 thumb=(), mapped=True):
    """one run in the Sungkim look. cards: [(t, card(...)), ...] with run-relative t (use W(); 0 = in place at frame 0).
    cover_safe (default: run 0): frame 0 is the cover, so the header, the visual box and the source line appear from
    the second frame (the cards sit below y 920 and may be there)."""
    if len(cards) > MAX_CARDS: raise SystemExit(f'{rid}: {len(cards)} cards - at most {MAX_CARDS} fit y 920-1380')
    if cover_safe is None: cover_safe = rid.endswith('_r0')
    cfg = dict(dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=[], moves=[], heroes=[],
               thumb=[list(x) if isinstance(x, (list, tuple)) else x for x in thumb],
               sungkim=dict(cards=[dict(t0=round(t, 3)) for t, _ in cards], coverSafe=cover_safe), uiOk=True)
    cards_html = ''
    for i, (_, c) in enumerate(cards):
        met = f'<div class="cm">{html.escape(c["metric"])}</div>' if c['metric'] else ''
        body = f'<div class="cb">{html.escape(c["body"])}</div>' if c['body'] else ''
        cards_html += (f'<div id="skCard{i}" class="skc {c["kind"]}"><div class="row"><div class="ct">{html.escape(c["title"])}</div>'
                       f'{met}</div>{body}</div>')
    body = (f'<div id="skHdr"><div class="kick">{html.escape(kicker)}</div><div id="skTitle">{html.escape(title)}</div></div>'
            f'<div id="skVis">{vis_html}</div><div id="skSrc">{html.escape(source)}</div>'
            f'<div id="skCards">{cards_html}</div><script src="sungkim.js"></script>')
    page(rid, cfg, extra_html=body, extra_css=SK_CSS + vis_css, extra_js=vis_js, mapped=mapped)
