"""Reference graphics compositions for a Korean short. Every run is a full visual ('fv').
Timing anchors on spoken phrases with W(ws, '<phrase>'). Build with: python scripts/build_gfx.py s1"""
from build_gfx_common import *


def build():
    # R0 [number]: cover-safe hook. Hero card stays below y 620 on frame 0, then pushes on phrase
    r, ws = words('s1', 0)
    # card html carries its own padding and alignment: the engine only sizes and places the card
    num_html = ('<div style="height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px">'
                '<div class="display accent">10배</div><div class="h2">생산성 향상</div></div>')
    cards = [dict(id='num', kind='glass', x=540, y=880, w=960, h=420, html=num_html, highlight=True)]
    t_push = W(ws, '10배')
    moves = [dict(t=0.2, dur=t_push - 0.2, kind='glide', to=dict(x=540, y=874, s=1.02)),
             dict(t=t_push, dur=1.2, kind='push', to=dict(x=540, y=880, s=1.1))]   # the 960-wide card must stay inside 1080
    cfg = dict(id='s1_r0', dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=cards,
               moves=moves, heroes=[dict(t=0, id='num')], pushRef=1.02,
               thumb=[[0.4, t_push]])            # the landed card before the push (after it the run may already be over once recorded)
    page('s1_r0', cfg)

    # R1 [capture]: real page in capture_card; inner camera steps to row, highlight band sweeps in
    r, ws = words('s1', 1)
    fw, fh = D.get('pricing.png', (1920, 1080))
    t_step, t_hl = W(ws, '요금제') - 0.25, W(ws, '반값')
    band = '<div id="hlb" class="band" style="position:absolute;left:420px;top:510px;width:680px;height:70px"></div>'
    inner = [dict(t=t_step, dur=0.6, fx=760, fy=545, k=1.35)]
    cards = [capture_card('cap', fw, fh, inner0=dict(fx=960, fy=540, k=1.0), inner=inner,
                          img='assets/pricing.png', overlay=band, overlayBlend='multiply', credit='출처: 요금제 페이지')]
    moves = [dict(t=0.2, dur=r['dur'] - 0.2, kind='glide', to=dict(x=540, y=724, s=1.02))]
    cfg = dict(id='s1_r1', dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=cards,
               moves=moves, heroes=[dict(t=0, id='cap')],
               reveals=[dict(el='hlb', t=t_hl, dur=0.45, type='scaleX')],
               thumb=[[t_hl + 0.5, r['dur']]])
    page('s1_r1', cfg, backdrop=('img', 'assets/pricing.png', fw, fh))

    # R2 [diagram]: glass architecture cards with icon tile; steps focus to result card
    r, ws = words('s1', 2)
    tile = tile_html(color='mint', glyph='sparkle', size=110, tilt=-6)
    in_html = (f'<div style="height:100%;display:flex;align-items:center;gap:32px;padding:0 56px">{tile}'
               '<div><div class="h2">입력 데이터</div><div class="sub">자동 분석</div></div></div>')
    out_html = ('<div style="height:100%;display:flex;flex-direction:column;justify-content:center;gap:12px;padding:0 56px">'
                '<div class="label accent">OUTPUT</div><div class="h1">최적화 완료</div><div class="body">배포 파이프라인 연동</div></div>')
    cards = [dict(id='in_card', kind='glass', x=540, y=560, w=960, h=260, html=in_html),
             dict(id='out_card', kind='glass', x=540, y=910, w=960, h=340, html=out_html, highlight=True,
                  land=dict(t=W(ws, '자동화') - 0.35, dur=0.55))]
    t_step = W(ws, '자동화') - 0.25
    moves = [dict(t=t_step, dur=0.6, kind='step', to=dict(x=540, y=890, s=1.08))]
    cfg = dict(id='s1_r2', dur=r['dur'], mode='fv', cam0=dict(x=540, y=680, s=1.0), cards=cards,
               moves=moves, heroes=[dict(t=0, id='in_card'), dict(t=t_step, id='out_card')],
               accent='mint', thumb=[[t_step + 0.6, r['dur']]])
    page('s1_r2', cfg)

    # R3 [logo]: product logo lockup, then whip transition to real interface window
    r, ws = words('s1', 3)
    fw, fh = D.get('interface.png', (1920, 1080))
    t_whip = W(ws, '실행') - 0.45
    logo_card = dict(id='logo', kind='plain', x=540, y=720, w=580, h=160, html=logo_html('assets/logo.svg'))
    ui_card = capture_card('ui', fw, fh, x=540, y=720 + 2200, img='assets/interface.png', credit='출처: 제품 화면',
                           inner0=dict(fx=960, fy=540, k=1.15), backdrop={'tIn': t_whip + 0.35})
    moves = [dict(t=t_whip, kind='whip', to=dict(x=540, y=720 + 2200, s=1.0), via=dict(x=540, y=720 + 1100, s=0.88))]
    cfg = dict(id='s1_r3', dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1.0), cards=[logo_card, ui_card],
               moves=moves, heroes=[dict(t=0, id='logo'), dict(t=t_whip + 0.45, id='ui')],
               thumb=[[0, t_whip - 0.1]])
    page('s1_r3', cfg, backdrop=('img', 'assets/interface.png', fw, fh))
