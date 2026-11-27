"""Final compositor for one short: every run is a full-frame graphic (no camera, no source video), with the captions
(glass keyword chips) and the cover on frame 0. Writes <sk>/final_video.mp4 (MarketBrief_YYYY_MM_DD_A/P.mp4 for a market briefing; config.final_video_name) (video + mix) and <sk>/captions.json.
usage: python compose.py s1 --events-only            captions.json only
       python compose.py s1 --preview t1,t2,...      full-resolution frames -> <sk>/preview/
       python compose.py s1 --preview t1,... --clean the same frames without captions or cover -> <sk>/thumb/ (thumbnail.py)
       python compose.py s1 --runs i --seg-out f.mp4 one run as a video segment (one process per run)
       python compose.py s1 --segments [--jobs N] [--no-concat] [--force]
                                                    every run as its own process in parallel, cached by its inputs (a run whose
                                                    graphic, captions and code are unchanged is skipped), frame counts verified,
                                                    then --concat
       python compose.py s1 --concat                stream-copy the segments + the mix -> <sk>/final_video.mp4 (or the briefing name)
  add --draft to any of these: the 10 fps draft graphics (gfx/draft/, each frame held for 6) instead of the full 60 fps
  renders, into <sk>/seg_draft/ and <sk>/draft_video.mp4 - the review copy the user watches before deciding to record."""
import json, sys, os, subprocess, re, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sk = sys.argv[1]
PREVIEW = None
ONLY = None; SEG_OUT = None; CONCAT = '--concat' in sys.argv; SEGMENTS = '--segments' in sys.argv
DRAFT = '--draft' in sys.argv
if '--runs' in sys.argv: ONLY = [int(x) for x in sys.argv[sys.argv.index('--runs') + 1].split(',')]
if '--seg-out' in sys.argv: SEG_OUT = sys.argv[sys.argv.index('--seg-out') + 1]
if CONCAT: ONLY = []
if '--preview' in sys.argv: PREVIEW = [float(x) for x in sys.argv[sys.argv.index('--preview') + 1].split(',')]
CLEAN = PREVIEW is not None and '--clean' in sys.argv   # thumbnail candidates: the picture alone
FPS = 60; Wc, Hc = 1080, 1920
C = json.load(open('cut.json', encoding='utf-8'))[sk]; S = json.load(open('shorts.json', encoding='utf-8'))[sk]
END = C['END']; NF = int(round(END * FPS))
RUNS = C['runs']
GFX_DIR, GFX_FPS = ('gfx/draft', 10) if DRAFT else ('gfx/out60', 60)
SEG_DIR = f'{sk}/seg_draft' if DRAFT else f'{sk}/seg'
import zlib
sys.path.insert(0, 'scripts'); import config as _cfg0
OUT_VIDEO = f'{sk}/draft_video.mp4' if DRAFT else f"{sk}/{os.environ.get('CVS_FINAL_NAME') or _cfg0.final_video_name()}"   # finish.sh sets the name once per render
F = 'fonts/'
# The skill's stage look (graphite stage, glass, one accent) with Pretendard for every word: the outputs are Korean
# (Figtree and Geist Mono have no Hangul), and Pretendard's Latin keeps names and numbers in the same voice.
FONT = 'PretendardVariable.ttf'
def vfont(name, size, weight):
    f = ImageFont.truetype(F + name, int(round(size)))
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f
CAP = vfont(FONT, 74, 700)                    # captions: Pretendard bold, white with a graphite stroke
SKETCH = _cfg0.THEME == 'sketch'               # theme-sketch.md: handwriting (Gaegu) in ink on a highlighter stroke
if SKETCH: CAP = ImageFont.truetype(F + 'Gaegu-Bold.ttf', 78)
SUNGKIM = _cfg0.THEME == 'sungkim'             # theme-sungkim.md: black Pretendard on the paper (a thin paper outline), keywords in teal, run 0 is the cover
BRIEF = _cfg0.THEME == 'brief'                 # theme-brief.md: ink Pretendard on newsprint paper, section-coloured keyword highlights, run 0 is the cover
if SUNGKIM or BRIEF: CAP = vfont(FONT, 50, 700)
SG_INK = (17, 18, 20); SG_PAPER = (246, 243, 233); SG_TEAL = (15, 120, 108)
BR_INK = (22, 22, 24); BR_PAPER = (245, 244, 240)
BR_ACCENTS = {'crimson': (180, 35, 35), 'navy': (32, 74, 128), 'forest': (30, 107, 85),
              'ochre': (176, 112, 22), 'plum': (106, 67, 130), 'slate': (93, 104, 120)}
BRIEF_COLORS = json.load(open('gfx/brief_colors.json', encoding='utf-8')) if (BRIEF and os.path.exists('gfx/brief_colors.json')) else {}
SK_INK = (34, 32, 28); SK_RED = (212, 56, 44); SK_HL = (255, 208, 0, 150)

def hl_band(d, box, seed, rgba=SK_HL):
    """a highlighter stroke over box: slightly slanted, ragged ends (deterministic per seed)"""
    import random, zlib
    rnd = random.Random(seed); x0, y0, x1, y1 = box; n = 9
    top = [(x0 + (x1 - x0) * k / n, y0 + rnd.uniform(-4, 4) - 4 * k / n) for k in range(n + 1)]
    bot = [(x1 - (x1 - x0) * k / n, y1 + rnd.uniform(-4, 4) - 4 * (n - k) / n) for k in range(n + 1)]
    d.polygon(top + [(x1 + rnd.uniform(4, 12), (y0 + y1) / 2)] + bot + [(x0 - rnd.uniform(4, 12), (y0 + y1) / 2)], fill=rgba)
INK = (17, 18, 20); STAGE950 = (11, 12, 14); STAGE800 = (24, 25, 28); STAGE700 = (33, 34, 38)
TEXT_MUTED = (126, 129, 138); AZURE = (47, 149, 255); AZURE_INK = (21, 96, 208)
ACCENTS = {'azure': (47, 149, 255), 'ember': (255, 138, 91), 'iris': (156, 124, 255), 'mint': (79, 214, 160)}
GLASS = (24, 25, 28, 224)                     # stage-800, more opaque than a slide's 62% (no backdrop blur here)

def run_at(t):
    for r in RUNS:
        if r['T0'] - 1e-6 <= t < r['T1'] - 1e-6: return r
    return RUNS[-1]

# ---------------------------------------------------------------- captions
_PUNCT = re.compile(r'[.,!?·…"\'“”‘’()\[\]]+$')
def _strip(s):
    """the word without its closing punctuation, but a bracket the word opened keeps its pair: 인(P) stays 인(P)"""
    t = _PUNCT.sub('', s)
    for o, c in ('()', '[]'):
        if t.count(o) > t.count(c) and c in s[len(t):]: t += c
    return t
def disp_tokens():
    """the words (Korean 어절, as in the cue text) with their times from timeline.py; p = the word ends a clause"""
    toks = []
    for w in C['words']:
        s = w['w']
        toks.append(dict(w=s, s=w['s'], e=w['e'], line=w['line'], p=s[-1] in '.,?!…', d=_strip(s) or s))
    return toks

_norm = _strip
HL = [[_norm(x) for x in h.split()] for h in S.get('highlights', [])]
sys.path.insert(0, 'scripts'); import config as _cfg
MAX_LINE = 2 * (_cfg.LAYOUT['ui_right'][0] - 540)    # 840: centred captions end at x 960, left of the platforms' button column

USED_HL = set()
def hl_at(toks, i):
    """the highlight that starts at word i: its words as written in "highlights" match the cue words; the last one may
    carry a particle (하네스 matches 하네스가). Each highlight becomes a chip once per short: its first occurrence that the
    spacing rules allow (a term said six times is not six chips)"""
    for k, h in enumerate(HL):
        if k in USED_HL: continue
        seg = [t['d'] for t in toks[i:i + len(h)]]
        if len(seg) == len(h) and seg[:-1] == h[:-1] and seg[-1].startswith(h[-1]): return k, h
    return None

# Korean words that must not end a chunk when the next word belongs to them: numerals, demonstratives and determiners
# before a counter or bound noun ("열여섯 개씩", "몇 점쯤", "그 답이", "한 문제에"), and bound nouns that must not start one
GLUE_BEFORE = set('한 두 세 네 다섯 여섯 일곱 여덟 아홉 열 열한 열두 열여섯 스무 몇 여러 그 이 저 각 모든 어느 무슨 어떤 첫 새 온갖'.split())
BOUND = re.compile(r'^(개|점|건|번|명|살|줄|것|때|배|초|분|쯤)(씩|만|가|를|의|은|는|과|을|이|쯤|에|지|입니다|이에요)?$')
CHIP_MIN = 0.9                                 # a keyword chip stays at least this long (its pop takes 0.4 s)

def glued(a, b):
    """True when a chunk must not break between words a and b ("열여섯 개씩", "몇 점쯤", "그 답이", "잘한 건지")"""
    return a['d'] in GLUE_BEFORE or BOUND.match(b['d']) is not None

def width(toks):
    """the drawn width of a chunk: words plus the wider word gaps caption_img uses"""
    dummy = ImageDraw.Draw(Image.new('L', (1, 1)))
    gap = dummy.textlength(' ', font=CAP) + 16
    return sum(dummy.textlength(t['d'], font=CAP) for t in toks) + gap * (len(toks) - 1)

def build_chunks():
    toks = disp_tokens(); chunks = []; i = 0; since = 3
    while i < len(toks):
        r = run_at(toks[i]['s'])
        hit = hl_at(toks, i)
        if hit and since >= 2 and (not chunks or not chunks[-1]['hl']):
            USED_HL.add(hit[0]); n = len(hit[1])
            # the chip shows the keyword as written in "highlights" (the noun, no particle: "GRPO", not "GRPO인데")
            chunks.append(dict(toks=toks[i:i + n], hl=True, label=' '.join(S['highlights'][hit[0]].split()))); i += n; since = 0; continue
        cur = [toks[i]]; i += 1
        while i < len(toks):
            nt = toks[i]
            must = glued(cur[-1], nt)
            if cur[-1]['p'] or run_at(nt['s']) is not r or nt['line'] != cur[-1]['line']: break   # never across a cue or a cut
            if not must:
                if len(cur) >= 3 or nt['s'] - cur[-1]['e'] > 0.32: break
                if hl_at(toks, i) and since + 1 >= 2: break
            if width(cur + [nt]) > MAX_LINE: break
            cur.append(nt); i += 1
        # never leave a numeral or demonstrative at a chunk's end with its noun in the next chunk: move it over
        while len(cur) > 1 and i < len(toks) and toks[i]['line'] == cur[-1]['line'] and glued(cur[-1], toks[i]):
            cur.pop(); i -= 1
        chunks.append(dict(toks=cur, hl=False)); since += 1
    for k, c in enumerate(chunks):
        c['text'] = c.get('label') or ' '.join(t['d'] for t in c['toks'])
        c['t0'] = max(1 / FPS, c['toks'][0]['s'])
        if k and chunks[k - 1]['hl']: c['t0'] = max(c['t0'], chunks[k - 1]['t0'] + CHIP_MIN)   # the chip before it holds
        nxt = chunks[k + 1]['toks'][0]['s'] if k + 1 < len(chunks) else END
        last_e = c['toks'][-1]['e']
        c['t1'] = min(END, nxt if nxt - last_e < 0.5 else last_e + 0.3)
        if c['hl']: c['t1'] = min(END, max(c['t1'], c['t0'] + CHIP_MIN))
    for k in range(len(chunks) - 1):                 # a chunk pushed later by a chip still ends before the next starts
        chunks[k]['t1'] = min(chunks[k]['t1'], max(chunks[k + 1]['t0'], chunks[k]['t0'] + 0.2))
    return chunks

def caption_img(text, hl=False):
    """a normal caption chunk: Pretendard bold, white, a 10 px graphite stroke, wide word gaps (the stroke never swallows
    the spaces). Highlighted chunks are glass chips instead (chip_parts)."""
    font = CAP
    pad = 30
    dummy = ImageDraw.Draw(Image.new('L', (1, 1)))
    lines = [text]
    if dummy.textlength(text, font=font) > 960 and ' ' in text:
        ws = text.split(); best = None
        for k in range(1, len(ws)):
            a, b = ' '.join(ws[:k]), ' '.join(ws[k:]); m = max(dummy.textlength(a, font=font), dummy.textlength(b, font=font))
            if best is None or m < best[0]: best = (m, [a, b])
        lines = best[1]
    lh = 88; gap = dummy.textlength(' ', font=font) + 16
    lw = lambda l: sum(dummy.textlength(wd, font=font) for wd in l.split()) + gap * (len(l.split()) - 1)
    w = int(max(lw(l) for l in lines)) + 2 * pad; h = lh * len(lines) + 2 * pad
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if SKETCH:                                    # ink handwriting on a highlighter stroke, no outline
        for j, l in enumerate(lines):
            x = (w - lw(l)) / 2; y = pad + j * lh
            hl_band(d, (x - 18, y + 4, x + lw(l) + 18, y + lh - 2), zlib.crc32(l.encode()))
            for wd in l.split():
                d.text((x, y), wd, font=font, fill=SK_INK + (255,)); x += dummy.textlength(wd, font=font) + gap
        return np.asarray(im)
    if SUNGKIM:                                   # black words on the paper; the paper-coloured outline keeps them readable on the dark cover
        for j, l in enumerate(lines):
            x = (w - lw(l)) / 2; y = pad + j * lh
            for wd in l.split():
                d.text((x, y), wd, font=font, fill=SG_INK + (255,), stroke_width=5, stroke_fill=SG_PAPER + (255,))
                x += dummy.textlength(wd, font=font) + gap
        return np.asarray(im)
    if BRIEF:                                     # ink words on newsprint #F5F4F0 with a crisp paper outline
        for j, l in enumerate(lines):
            x = (w - lw(l)) / 2; y = pad + j * lh
            for wd in l.split():
                d.text((x, y), wd, font=font, fill=BR_INK + (255,), stroke_width=5, stroke_fill=BR_PAPER + (255,))
                x += dummy.textlength(wd, font=font) + gap
        return np.asarray(im)
    for j, l in enumerate(lines):
        x = (w - lw(l)) / 2; y = pad + j * lh
        for wd in l.split():
            d.text((x, y), wd, font=font, fill=(255, 255, 255, 255), stroke_width=10, stroke_fill=STAGE950 + (255,))
            x += dummy.textlength(wd, font=font) + gap
    return np.asarray(im)



# ---------------------------------------------------------------- highlight chips (the long-form keyword pop, locked)
# A graphite glass chip (stage-800, accent hairline + bloom, top highlight, the long panel shadow), the words in Figtree
# 600 white at the title tracking, and the accent line drawn in beneath them. It pops in (0.18 s) and the line sweeps
# in from 0.08 s over 0.32 s; it cuts with the caption.
CHIP_SIZE, CHIP_TRACK, CHIP_PADX, CHIP_PADY, CHIP_SHPAD, CHIP_R = 70, -0.025, 40, 26, 150, 28
CHIP_IN, SWEEP_T0, SWEEP_DUR = 0.18, 0.08, 0.32


def tracked(draw, xy, text, f, fill, track_em):
    """text with letter-spacing, keeping the font's kerning"""
    x, y = xy; extra = track_em * f.size; prev = 0.0
    for i, ch in enumerate(text):
        draw.text((x + prev + i * extra, y), ch, font=f, fill=fill)
        prev = f.getlength(text[:i + 1])
    return prev + extra * (len(text) - 1)


def chip_parts_sketch(text):
    """the sketch theme's keyword: red handwriting on a strong highlighter stroke; the red pen line sweeps in beneath"""
    size = 88
    while True:
        f = ImageFont.truetype(F + 'Gaegu-Bold.ttf', size); tw = f.getlength(text)
        if tw + 80 <= MAX_LINE or size <= 56: break
        size -= 2
    asc = f.getbbox(text)[3]; pad = 60
    W_, H_ = int(tw + 2 * pad + 40), int(asc + 2 * pad + 30)
    im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = pad + 20, pad
    hl_band(d, (x0 - 24, y0 - 6, x0 + tw + 24, y0 + asc + 12), zlib.crc32(text.encode()), (255, 208, 0, 190))
    d.text((x0, y0), text, font=f, fill=SK_RED + (255,))
    ly = y0 + asc + 18
    return im, (x0, ly, x0 + tw, ly + 7), SK_RED


def chip_parts_sungkim(text):
    """the Sungkim theme's keyword: the word itself in teal, bolder, with a paper outline; a teal line sweeps beneath"""
    f = vfont(FONT, 56, 800); tw = f.getlength(text)
    cap = f.getbbox('H')[3] - f.getbbox('H')[1]; sp = 40
    im = Image.new('RGBA', (int(tw + 2 * sp), int(cap + 2 * sp + 30)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((sp, sp - f.getbbox('H')[1]), text, font=f, fill=SG_TEAL + (255,), stroke_width=5, stroke_fill=SG_PAPER + (255,))
    ly = sp + cap + 14
    return im, (sp, ly, sp + tw, ly + 4), SG_TEAL


def chip_parts_brief(text, accent='crimson'):
    """the Brief theme's keyword: Pretendard 800 in the run's section colour with a newsprint outline; a flat editorial
    rule sweeps beneath (no neon glow)"""
    col = BR_ACCENTS.get(accent, BR_ACCENTS['crimson'])
    f = vfont(FONT, 56, 800); tw = f.getlength(text)
    cap = f.getbbox('H')[3] - f.getbbox('H')[1]; sp = 40
    im = Image.new('RGBA', (int(tw + 2 * sp), int(cap + 2 * sp + 30)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((sp, sp - f.getbbox('H')[1]), text, font=f, fill=col + (255,), stroke_width=5, stroke_fill=BR_PAPER + (255,))
    ly = sp + cap + 12
    return im, (sp, ly, sp + tw, ly + 5), col


def chip_parts(text, accent='azure'):
    if SKETCH: return chip_parts_sketch(text)
    if SUNGKIM: return chip_parts_sungkim(text)
    if BRIEF: return chip_parts_brief(text, accent)
    acc = ACCENTS.get(accent, ACCENTS['azure'])
    size = CHIP_SIZE
    while True:                                                   # long phrases shrink to fit the 1080 frame
        f = vfont(FONT, size, 600)
        tw = f.getlength(text) + CHIP_TRACK * f.size * (len(text) - 1)
        if tw + 2 * CHIP_PADX <= 980 or size <= 50: break
        size -= 2
    cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    dsc = f.getbbox('gjpqy')[3] - f.getbbox('H')[3]               # descender depth: the line sits below it
    line_gap, line_h = dsc + 14, 5
    cw, ch = tw + 2 * CHIP_PADX, CHIP_PADY + cap + line_gap + line_h + CHIP_PADY
    sp = CHIP_SHPAD; size_px = (int(cw + 2 * sp), int(ch + 2 * sp)); box = (sp, sp, sp + cw, sp + ch); r = CHIP_R
    base = Image.new('RGBA', size_px, (0, 0, 0, 0))

    def soft(rect, rgba, blur):
        m = Image.new('L', size_px, 0); ImageDraw.Draw(m).rounded_rectangle(rect, r, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(blur))
        lay = Image.new('RGBA', size_px, rgba[:3] + (0,)); lay.putalpha(m.point(lambda v: int(v * rgba[3] / 255)))
        return lay
    x0, y0, x1, y1 = box
    base = Image.alpha_composite(base, soft((x0 + 40, y0 + 90, x1 - 40, y1 + 50), (0, 0, 0, 200), 50))   # 0 50 120 -40 shadow
    base = Image.alpha_composite(base, soft((x0 + 30, y0 + 30, x1 - 30, y1 - 30), acc + (150,), 46))    # accent bloom
    d = ImageDraw.Draw(base)
    d.rounded_rectangle(box, r, fill=GLASS)
    d.rounded_rectangle(box, r, outline=acc + (84,), width=2)                                          # accent hairline
    d.line((x0 + r, y0 + 1.5, x1 - r, y0 + 1.5), fill=(255, 255, 255, 22), width=1)                   # top highlight
    ty = y0 + CHIP_PADY
    tracked(d, (x0 + CHIP_PADX, ty - f.getbbox('H')[1]), text, f, (255, 255, 255, 255), CHIP_TRACK)
    ly = ty + cap + line_gap
    return base, (x0 + CHIP_PADX, ly, x0 + CHIP_PADX + tw, ly + line_h), acc


CHIP_CACHE = {}
def chip_render(k, parts, t_rel):
    """(RGBA PIL image, scale, alpha, y offset) of chip k at t_rel s after its caption starts; frames with the same
    state reuse the same image"""
    pin = min(1.0, max(0.0, t_rel / CHIP_IN))
    sw = min(1.0, max(0.0, (t_rel - SWEEP_T0) / SWEEP_DUR))
    sw = 1 - (1 - sw) ** 3                                        # power3.out
    key = (k, round(pin, 3), round(sw, 3))
    if key not in CHIP_CACHE:
        base, line, acc = parts; im = base
        if sw > 0 and SKETCH:                                     # the red pen line, no glow
            x0, y0, x1, y1 = line; xe = x0 + (x1 - x0) * sw; im = im.copy()
            ImageDraw.Draw(im).line((x0, y0 + 3, xe, y0 + 3 - 6 * sw), fill=acc + (255,), width=7)
        elif sw > 0 and BRIEF:                                    # crisp flat editorial rule, no glow
            x0, y0, x1, y1 = line; xe = x0 + (x1 - x0) * sw; im = im.copy()
            ImageDraw.Draw(im).rectangle((x0, y0, xe, y1), fill=acc + (255,))
        elif sw > 0:                                              # the accent line, with a soft glow, drawn left to right
            x0, y0, x1, y1 = line; xe = x0 + (x1 - x0) * sw
            glow = Image.new('L', im.size, 0); ImageDraw.Draw(glow).rounded_rectangle((x0, y0, xe, y1), 3, fill=255)
            glow = glow.filter(ImageFilter.GaussianBlur(7))
            gl = Image.new('RGBA', im.size, acc + (0,)); gl.putalpha(glow.point(lambda v: int(v * 0.8)))
            im = Image.alpha_composite(im, gl)
            ImageDraw.Draw(im).rounded_rectangle((x0, y0, xe, y1), 3, fill=acc + (255,))
        e = 1 - (1 - pin) ** 3
        CHIP_CACHE[key] = (im, 0.96 + 0.04 * e, min(1.0, pin * 1.6), 12 * (1 - e))
    return CHIP_CACHE[key]


def paste_rgba(dst, im, cx, cy, scale=1.0, alpha=1.0):
    """alpha-over a PIL RGBA image onto the float RGB frame, centred on (cx, cy)"""
    if scale != 1.0:
        im = im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.LANCZOS)
    a = np.asarray(im, np.float32); h, w = a.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    ys0, ys1 = max(0, y0), min(Hc, y0 + h); xs0, xs1 = max(0, x0), min(Wc, x0 + w)
    if ys1 <= ys0 or xs1 <= xs0: return
    src = a[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]; al = src[..., 3:4] / 255.0 * alpha
    sub = dst[ys0:ys1, xs0:xs1]; sub[:] = sub * (1 - al) + src[..., :3] * al


sys.path.insert(0, 'scripts'); import config as _cfg
def caption_center_y(r):
    """the caption band under every full visual (config.LAYOUT caption, centre 1520); "caption": "top" on a line in
    shorts.json moves its run's captions to the top band for a visual whose content sits low"""
    top = any(L.get('caption') == 'top' for L in S['lines'] if L['id'] in r['lines'])
    return sum(_cfg.LAYOUT['caption_top' if top else 'caption']) / 2

# ---------------------------------------------------------------- readers
def reader(path, pix='rgb24', ch=3, size=None, start=None, count=None):
    """decoded frames of a stream; start/count seek frame-exactly to frame `start` of these 60 fps CFR streams (previews)"""
    if size is None:
        o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip().split(',')
        size = (int(o[0]), int(o[1]))
    w, h = size
    pre = ['-ss', f'{(start - 0.5) / FPS:.6f}'] if start else []     # half a frame early: lands on frame `start` whatever the container's timestamp rounding
    post = ['-frames:v', str(count)] if count else []
    p = subprocess.Popen(['ffmpeg', '-v', 'error'] + pre + ['-i', path] + post + ['-f', 'rawvideo', '-pix_fmt', pix, '-'], stdout=subprocess.PIPE)
    n = w * h * ch
    while True:
        b = p.stdout.read(n)
        if len(b) < n: break
        yield np.frombuffer(b, np.uint8).reshape(h, w, ch)

# ---------------------------------------------------------------- cover (frame 0 only)
def cover_rgba(title_lines):
    """frame 0's title in the design system: white Pretendard 600 at the headline tracking on a graphite glass card (accent
    hairline + bloom, the long panel shadow) with the azure accent line drawn beneath the words - the keyword-pop chip at
    title size. Centred at y ~432 (the spec's 262-603 band for two lines); the graphic keeps everything below 620."""
    if SKETCH: return cover_sketch(title_lines)
    if SUNGKIM or BRIEF: return cover_sungkim(title_lines)
    acc = ACCENTS['azure']; track = -0.03; size = 104
    while True:
        ft = vfont(FONT, size, 600)
        tws = [ft.getlength(l) + track * ft.size * (len(l) - 1) for l in title_lines]
        if max(tws) <= 900 or size <= 72: break
        size -= 4
    cap = ft.getbbox('H')[3] - ft.getbbox('H')[1]; dsc = ft.getbbox('gjpqy')[3] - ft.getbbox('H')[3]
    lh = int(size * 1.08); padx, pady = 56, 44
    text_h = lh * (len(title_lines) - 1) + cap
    line_gap, line_h = dsc + 18, 6
    bw = int(max(tws) + 2 * padx); bh = int(pady + text_h + line_gap + line_h + pady)
    cyc = 432; bx0, by0 = (Wc - bw) // 2, int(cyc - bh / 2); bx1, by1 = bx0 + bw, by0 + bh; r = 36
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0))

    def soft(rect, rgba, blur):
        m = Image.new('L', (Wc, Hc), 0); ImageDraw.Draw(m).rounded_rectangle(rect, r, fill=255)
        m = m.filter(ImageFilter.GaussianBlur(blur))
        lay = Image.new('RGBA', (Wc, Hc), rgba[:3] + (0,)); lay.putalpha(m.point(lambda v: int(v * rgba[3] / 255)))
        return lay
    im = Image.alpha_composite(im, soft((bx0 + 40, by0 + 90, bx1 - 40, by1 + 50), (0, 0, 0, 210), 50))
    im = Image.alpha_composite(im, soft((bx0 + 30, by0 + 30, bx1 - 30, by1 - 30), acc + (140,), 50))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((bx0, by0, bx1, by1), r, fill=STAGE800 + (240,))
    d.rounded_rectangle((bx0, by0, bx1, by1), r, outline=acc + (84,), width=2)
    d.line((bx0 + r, by0 + 1.5, bx1 - r, by0 + 1.5), fill=(255, 255, 255, 24), width=1)
    ty = by0 + pady
    for j, (l, tw) in enumerate(zip(title_lines, tws)):
        tracked(d, ((Wc - tw) / 2, ty + j * lh - ft.getbbox('H')[1]), l, ft, (255, 255, 255, 255), track)
    ly = ty + text_h + line_gap; lw = max(tws); lx0 = (Wc - lw) / 2
    glow = Image.new('L', (Wc, Hc), 0); ImageDraw.Draw(glow).rounded_rectangle((lx0, ly, lx0 + lw, ly + line_h), 3, fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(8))
    gl = Image.new('RGBA', (Wc, Hc), acc + (0,)); gl.putalpha(glow.point(lambda v: int(v * 0.8)))
    im = Image.alpha_composite(im, gl)
    ImageDraw.Draw(im).rounded_rectangle((lx0, ly, lx0 + lw, ly + line_h), 3, fill=acc + (255,))
    return np.asarray(im).astype(np.float32)

def cover_sungkim(title_lines):
    """the Sungkim theme draws its cover in run 0 itself (sungkim_kit.sungkim_cover), so nothing is laid over frame 0"""
    return np.zeros((Hc, Wc, 4), np.float32)


def cover_sketch(title_lines):
    """the sketch theme's cover: the title handwritten in ink, each line on a highlighter stroke, a red pen line beneath"""
    size = 120
    while True:
        ft = ImageFont.truetype(F + 'Gaegu-Bold.ttf', size); tws = [ft.getlength(l) for l in title_lines]
        if max(tws) <= 880 or size <= 76: break
        size -= 4
    lh = int(size * 1.2); asc = ft.getbbox('가')[3]; top = 432 - (lh * len(title_lines) + 30) / 2
    im = Image.new('RGBA', (Wc, Hc), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for j, (l, tw) in enumerate(zip(title_lines, tws)):
        x = (Wc - tw) / 2; y = top + j * lh
        hl_band(d, (x - 26, y + asc * 0.35, x + tw + 26, y + asc + 14), j * 7 + 3)
        d.text((x, y), l, font=ft, fill=SK_INK + (255,))
    ly = top + (len(title_lines) - 1) * lh + asc + 34; lw = max(tws)
    d.line(((Wc - lw) / 2, ly + 6, (Wc + lw) / 2, ly - 4), fill=SK_RED + (255,), width=9)
    return np.asarray(im).astype(np.float32)

_BBOX = {}
def over(dst, rgba, y=None):
    """alpha-over an RGBA float canvas onto dst, touching only the rows/cols where its alpha is non-zero (elsewhere the
    blend is dst*1 + rgb*0 = dst exactly). The bounding box is cached per canvas object."""
    key = id(rgba)
    box = _BBOX.get(key)
    if box is None or box[0] is not rgba:
        rows = np.where(rgba[..., 3].any(1))[0]; cols = np.where(rgba[..., 3].any(0))[0]
        box = (rgba, (rows[0], rows[-1] + 1, cols[0], cols[-1] + 1) if len(rows) else None); _BBOX[key] = box
    if box[1] is None: return
    y0, y1, x0, x1 = box[1]
    a = rgba[y0:y1, x0:x1, 3:4] / 255.0
    sub = dst[y0:y1, x0:x1]
    sub[:] = sub * (1 - a) + rgba[y0:y1, x0:x1, :3] * a


# ---------------------------------------------------------------- main loop
chunks = build_chunks()
def _chunk_accent(c):
    if not BRIEF: return S.get('accent', 'azure')
    r = run_at(c['t0'])
    col = BRIEF_COLORS.get(f'{sk}_r{r["i"]}') or S.get('accent', 'crimson')
    return col if col in BR_ACCENTS else 'crimson'
cap_imgs = [chip_parts(c['text'], _chunk_accent(c)) if c['hl'] else caption_img(c['text']) for c in chunks]
json.dump([dict(text=c['text'], hl=c['hl'], t0=round(c['t0'], 3), t1=round(c['t1'], 3),
                **({'color': _chunk_accent(c)} if (BRIEF and c['hl']) else {})) for c in chunks],
          open(f'{sk}/captions.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
if '--events-only' in sys.argv:
    print(f'{sk}: {len(chunks)} caption chunks -> {sk}/captions.json'); sys.exit(0)

title = S.get('cover', [S['title']])
COVER = cover_rgba(title)

def gfx_reader(i, start=None, count=None):
    """the run's graphic as 60 fps frames: the full render, or the 10 fps draft with every frame held (scaled to the canvas)"""
    path = f'{GFX_DIR}/{sk}_r{i}.mp4'
    if not DRAFT:
        yield from reader(path, start=start, count=count); return
    rep = FPS // GFX_FPS                                      # each draft frame stands for 6 output frames
    j = start or 0; d = j // rep
    lim = ['-frames:v', str((j + count - 1) // rep - d + 1)] if count else []   # stop ffmpeg after the frames needed
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', f'{d / GFX_FPS:.6f}', '-i', path, '-vf', f'scale={Wc}:{Hc}'] + lim +
                         ['-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = Wc * Hc * 3
    def nxt(prev):
        b = p.stdout.read(n)
        if len(b) == n: return np.frombuffer(b, np.uint8).reshape(Hc, Wc, 3)
        if prev is None: raise SystemExit(f'{path}: no frame at {d / GFX_FPS:.2f} s')
        return prev                                           # past the draft's last frame: hold it
    cur = nxt(None); done = 0
    while count is None or done < count:
        while j // rep > d: cur = nxt(cur); d += 1
        yield cur; j += 1; done += 1

def frames():
    """yields (n, run, image); image is None for frames a preview doesn't need"""
    for r in RUNS:
        if ONLY is not None and r['i'] not in ONLY: continue
        n0, n1 = round(r['T0'] * FPS), round(r['T1'] * FPS)
        need = lambda n: want is None or n in want
        if want is not None and not any(need(n) for n in range(n0, n1)): continue
        if want is not None:
            for n in sorted(x for x in want if n0 <= x < n1):
                yield n, r, next(gfx_reader(r['i'], start=n - n0, count=1)).astype(np.float32)
            continue
        g = gfx_reader(r['i'], count=n1 - n0)
        for n in range(n0, n1):
            fr = next(g); yield n, r, (fr.astype(np.float32) if need(n) else None)

want = None if PREVIEW is None else {int(round(t * FPS)) for t in PREVIEW}
VENC = ['-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuv420p', '-c:v', 'libx264', '-preset', 'veryfast' if DRAFT else 'slow',
        '-crf', '23' if DRAFT else '14', '-profile:v', 'high', '-r', str(FPS), '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709']

def concat():
    segs = [f'{SEG_DIR}/run{r["i"]:02d}.mp4' for r in RUNS]
    open(f'{SEG_DIR}/list.txt', 'w').write(''.join("file '" + os.path.basename(p) + "'\n" for p in segs))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{SEG_DIR}/list.txt', '-i', f'{sk}/mix.wav', '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', OUT_VIDEO], check=True)
    print('concatenated', len(segs), 'segments ->', OUT_VIDEO)

if CONCAT:
    concat(); sys.exit(0)

# ---------------------------------------------------------------- parallel, cached segments
def seg_inputs(r):
    """everything a run's segment depends on: its graphic (path, size, mtime), its captions, the cover, this code"""
    i = r['i']; files = [f'{GFX_DIR}/{sk}_r{i}.mp4']
    fst = [(f, os.path.getsize(f), int(os.path.getmtime(f) * 1000)) if os.path.exists(f) else (f, None, None) for f in files]
    caps = [dict(text=c['text'], hl=c['hl'], t0=round(c['t0'], 4), t1=round(c['t1'], 4),
                 **({'color': _chunk_accent(c)} if (BRIEF and c['hl']) else {}))
            for c in chunks if c['t1'] > r['T0'] and c['t0'] < r['T1']]
    key = dict(run=r, files=fst, caps=caps, cover=title if i == 0 else None, code=CODE_HASH, venc=VENC, draft=DRAFT)
    return json.dumps(key, sort_keys=True, default=str, ensure_ascii=False), [f for f, s, m in fst if s is None]

if SEGMENTS:
    import hashlib, time
    CODE_HASH = hashlib.md5(open(__file__, 'rb').read()).hexdigest()
    jobs = int(sys.argv[sys.argv.index('--jobs') + 1]) if '--jobs' in sys.argv else len(RUNS)
    force = '--force' in sys.argv
    os.makedirs(SEG_DIR, exist_ok=True)
    todo, kept, missing = [], [], []
    for r in RUNS:
        key, miss = seg_inputs(r)
        if miss: missing += miss
        out = f'{SEG_DIR}/run{r["i"]:02d}.mp4'; kf = out[:-4] + '.key'
        if not force and os.path.exists(out) and os.path.getsize(out) > 0 and os.path.exists(kf) and open(kf, encoding='utf-8').read() == key:
            kept.append(r['i']); continue
        todo.append((r, out, kf, key))
    if missing: raise SystemExit('missing inputs: ' + ', '.join(sorted(set(missing))) + ('  (render_draft.sh first)' if DRAFT else '  (render_full.sh first)'))
    print(f'{sk}: {len(todo)} segment(s) to render {[r["i"] for r, *_ in todo]}, {len(kept)} unchanged {kept}, {min(jobs, len(todo)) if todo else 0} at a time', flush=True)
    t0 = time.time(); procs = []; pending = list(todo); failed = []
    while pending or procs:
        while pending and len(procs) < jobs:
            r, out, kf, key = pending.pop(0)
            if os.path.exists(kf): os.remove(kf)
            p = subprocess.Popen([sys.executable, __file__, sk, '--runs', str(r['i']), '--seg-out', out] + (['--draft'] if DRAFT else [])); procs.append((p, r, out, kf, key))
        time.sleep(0.5)
        for item in procs[:]:
            p, r, out, kf, key = item
            if p.poll() is None: continue
            procs.remove(item)
            if p.returncode != 0: failed.append(r['i']); continue
            open(kf, 'w', encoding='utf-8').write(key)
    # every segment must hold exactly its run's frames (a graphic re-rendering underneath a composite yields a short segment)
    bad = []
    for r in RUNS:
        out = f'{SEG_DIR}/run{r["i"]:02d}.mp4'
        n = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', out],
                           capture_output=True, text=True).stdout.strip()
        want_n = round(r['T1'] * FPS) - round(r['T0'] * FPS)
        if not n.isdigit() or int(n) != want_n: bad.append((r['i'], n, want_n))
    print(f'{sk}: segments done in {time.time() - t0:.0f}s' + (f'; FAILED runs {failed}' if failed else '') + (f'; FRAME COUNT MISMATCH (run, got, want): {bad}' if bad else ''), flush=True)
    if failed or bad: sys.exit(1)
    if '--no-concat' not in sys.argv: concat()
    sys.exit(0)
if PREVIEW is None:
    if SEG_OUT:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{Wc}x{Hc}', '-r', str(FPS), '-i', '-'] + VENC + [SEG_OUT], stdin=subprocess.PIPE)
    else:
        enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{Wc}x{Hc}', '-r', str(FPS), '-i', '-',
                                '-i', f'{sk}/mix.wav', '-map', '0:v', '-map', '1:a'] + VENC + ['-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-ac', '2', '-movflags', '+faststart', OUT_VIDEO], stdin=subprocess.PIPE)
PDIR = f'{sk}/thumb' if CLEAN else f'{sk}/preview'
os.makedirs(PDIR, exist_ok=True)
count = 0
for n, r, img in frames():
    if img is None: continue
    t = n / FPS
    # captions (never on frame 0)
    if n > 0 and not CLEAN:
        for k, (c, ci) in enumerate(zip(chunks, cap_imgs)):
            if c['t0'] <= t + 1e-6 < c['t1']:
                cy = caption_center_y(r)
                if c['hl']:                                   # the glass chip pops in and draws its accent line
                    im_, scl, al, dy = chip_render(k, ci, t - c['t0'])
                    paste_rgba(img, im_, Wc / 2, cy + dy, scl, al)
                    break
                h, w = ci.shape[:2]
                x0, y0 = (Wc - w) // 2, int(round(cy - h / 2))
                sub = img[y0:y0 + h, x0:x0 + w]; a = ci[..., 3:4] / 255.0
                sub[:] = sub * (1 - a) + ci[..., :3] * a
                break
    if n == 0 and not CLEAN: over(img, COVER)
    np.add(img, 0.5, out=img); np.clip(img, 0, 255, out=img); out = img.astype(np.uint8)   # in place: same values, no temporaries
    if want is not None:
        Image.fromarray(out).save(f'{PDIR}/f_{t:07.3f}.png')
    else:
        enc.stdin.write(out.tobytes())
    count += 1
if PREVIEW is None:
    enc.stdin.close(); enc.wait()
print('frames', count, 'of', NF)
