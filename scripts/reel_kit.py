"""The code-reel theme (references/theme-reel.md): every run is one page with a fixed header, a diagram card on top, a
divider and a code card whose white highlight box follows the narration. First made for the weight-decay short
(2026-11-23, modelled on a reference Short the user chose); layout option 1 approved by the user the same day.

Layout on the 1080x1920 canvas (fixed in every run):
  header    y  36-214  series label (red), title, subtitle
  #top      x 40-1040, y 228-836   the run's diagram card (inner box 1000 x 608 px)
  divider   y 850, x 80-1000
  #code     x 40-1040, y 866-1380  title bar + the code, 32 px Geist Mono on 54 px lines, up to 8 lines
  captions  y 1410-1550 (compose.py), nothing below 1560; code text ends left of x 960 (the button column)

Use (in a project's scripts/gfx_<tag>.py):
  from reel_kit import *
  reel_setup(label='머신러닝, 코드로 이해하기', title='가중치 감쇠', sub='weight decay · 매 단계, 모든 가중치를 조금씩',
             file='weight_decay.py', code=['# ...', 'def penalty(ws, lam):', ...])
  r, ws = words('s1', 4)
  reel_page('s1_r4', r, top_html='<svg width="1000" height="608">...</svg>',
            top_js='window.TOP_RENDER = function (t) { ... }',
            code_hl=[(0, [6]), (W(ws, '먼저') - 0.1, [7])], thumb=[[2.0, 3.5]])
top_js draws the diagram as a pure function of the run time t (window.REEL: clamp, lerp, ease, easeOut, prog): no state
between calls, no CSS transitions, no timers - the renderer seeks frames in any order.
"""
import html, re
from build_gfx_common import *

COL = dict(bg='#080E16', card='#0A121E', card2='#0F1725', line='#1A2235', divider='#212639', text='#F1F5F9',
           muted='#94A3B8', dim='#64748B', red='#E0342C', blue='#3B82F6', blue2='#60A5FA', amber='#F5A524',
           pink='#F0718C', green='#34D399', purple='#C084FC')

# layout (px); reel.js reads lh/top0 from the page's CFG, so these are the only copy
HDR_TOP, TOP_Y, TOP_H, DIV_Y, CODE_Y, CODE_H = 36, 228, 608, 850, 866, 514
LH, TOP0, CODE_PX, MAX_LINES = 54, 70, 32, 8

SET = dict(label='', title='', sub='', file='main.py', lang='python', code=[])


def reel_setup(label, title, sub='', file='main.py', code=(), lang='python'):
    """the short's fixed texts: series label, title, subtitle, the code file's name and lines (at most 8, each short
    enough to end left of x 960: about 40 Latin characters, fewer with Hangul in a comment)"""
    if len(code) > MAX_LINES: raise SystemExit(f'reel_setup: {len(code)} code lines - at most {MAX_LINES} fit the card')
    SET.update(label=label, title=title, sub=sub, file=file, code=list(code), lang=lang)


_KW = {'def', 'return', 'for', 'in', 'import', 'as', 'if', 'else', 'elif', 'while', 'class', 'from', 'lambda',
       'const', 'let', 'function', 'async', 'await'}


def _hl_code(line):
    """minimal colouring: comments, keywords, the name after def/function/class, numbers"""
    m = re.match(r'^(.*?)((?:#|//).*)?$', line)
    code, com = m.group(1), m.group(2) or ''
    out, after_def = [], False
    for tok in re.findall(r'\s+|[A-Za-z_]\w*|\d+(?:\.\d+)?|.', code):
        e = html.escape(tok)
        if tok in _KW:
            out.append(f'<span class="kw">{e}</span>'); after_def = tok in ('def', 'function', 'class')
        elif re.fullmatch(r'\d+(?:\.\d+)?', tok): out.append(f'<span class="nu">{e}</span>')
        elif after_def and not tok.isspace():
            out.append(f'<span class="fn">{e}</span>'); after_def = False
        else: out.append(e)
    if com: out.append(f'<span class="cm">{html.escape(com)}</span>')
    return ''.join(out)


REEL_CSS = f"""
#root.stage #ground{{background:{COL['bg']}}}
#root .beam,#root #vignette{{display:none}}
#hdr{{position:absolute;left:0;top:{HDR_TOP}px;width:1080px;text-align:center}}
#hdr .lbl{{font:800 32px/1 Pretendard;color:{COL['red']};letter-spacing:.04em}}
#hdr .ttl{{font:650 80px/1.08 Pretendard;color:#fff;letter-spacing:-.025em;margin-top:14px;white-space:nowrap}}
#hdr .sub{{font:400 30px/1.2 Pretendard;color:{COL['muted']};margin-top:10px;letter-spacing:.01em}}
.rcard{{position:absolute;left:40px;width:1000px;border:2px solid {COL['line']};border-radius:28px;overflow:hidden;box-sizing:border-box}}
#top{{top:{TOP_Y}px;height:{TOP_H}px;background:{COL['card']}}}
#rdiv{{position:absolute;left:80px;top:{DIV_Y}px;width:920px;height:2px;background:{COL['divider']}}}
#code{{top:{CODE_Y}px;height:{CODE_H}px;background:{COL['card2']}}}
#code .bar{{position:absolute;left:0;top:0;width:100%;height:56px;display:flex;align-items:center;gap:14px;padding:0 30px;box-sizing:border-box}}
#code .dot{{width:18px;height:18px;border-radius:50%}}
#code .fname{{font:500 30px/1 'Geist Mono';color:{COL['muted']};margin-left:16px}}
#code .lang{{font:500 30px/1 'Geist Mono';color:{COL['dim']};margin-left:auto}}
#code .ln{{position:absolute;left:0;height:{LH}px;white-space:pre;font:400 {CODE_PX}px/{LH}px 'Geist Mono',Pretendard;color:{COL['text']}}}
#code .no{{display:inline-block;width:62px;text-align:right;margin-right:26px;color:{COL['dim']}}}
#code .kw{{color:{COL['purple']}}}#code .fn{{color:{COL['blue2']}}}#code .nu{{color:{COL['amber']}}}
#code .cm{{color:{COL['dim']};font-style:italic}}
#hlbox{{position:absolute;left:72px;width:880px;border:3px solid #fff;border-radius:12px;opacity:0;box-sizing:border-box}}
#top .t{{font-family:Pretendard;color:{COL['text']}}}
#top .mono{{font-family:'Geist Mono',Pretendard}}
"""


def code_html():
    rows = ''.join(f'<div class="ln" style="top:{TOP0 + i * LH}px"><span class="no">{i + 1}</span>{_hl_code(s)}</div>'
                   for i, s in enumerate(SET['code']))
    return (f'<div id="code" class="rcard"><div class="bar"><span class="dot" style="background:{COL["pink"]}"></span>'
            f'<span class="dot" style="background:{COL["amber"]}"></span><span class="dot" style="background:{COL["green"]}"></span>'
            f'<span class="fname">{html.escape(SET["file"])}</span><span class="lang">{html.escape(SET["lang"])}</span></div>'
            f'{rows}<div id="hlbox"></div></div>')


def reel_page(rid, r, top_html, top_js='', code_hl=(), top_css='', sub=None, title=None, cover_safe=None, thumb=(), mapped=True):
    """one run in the code-reel look. code_hl: [(t, [line numbers]), ...] with run-relative t (use W()); [] = no box.
    cover_safe (default: run 0): frame 0 is the cover, so the header and the top card appear from the second frame."""
    if not SET['title']: raise SystemExit('reel_page: call reel_setup(label=..., title=..., code=[...]) first')
    if cover_safe is None: cover_safe = rid.endswith('_r0')
    cfg = dict(dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=[], moves=[], heroes=[],
               thumb=[list(x) if isinstance(x, (list, tuple)) else x for x in thumb],
               reel=dict(hl=[dict(t=round(max(0, t), 3), lines=list(ls)) for t, ls in code_hl], coverSafe=cover_safe,
                         lh=LH, top0=TOP0),
               uiOk=True)
    hdr = (f'<div id="hdr"><div class="lbl">{html.escape(SET["label"])}</div><div class="ttl">{html.escape(title or SET["title"])}</div>'
           f'<div class="sub">{html.escape(sub if sub is not None else SET["sub"])}</div></div>')
    body = f'{hdr}<div id="top" class="rcard">{top_html}</div><div id="rdiv"></div>{code_html()}<script src="reel.js"></script>'
    page(rid, cfg, extra_html=body, extra_css=REEL_CSS + top_css, extra_js=top_js, mapped=mapped)
