"""Project settings, read from project.json in the work directory (the cwd every script runs in).
Written by init_project.py. Edit it by hand to override anything."""
from datetime import datetime, timedelta, timezone
import json, os

_KST = timezone(timedelta(hours=9))
_P = 'project.json'
_cfg = json.load(open(_P, encoding='utf-8')) if os.path.exists(_P) else {}


def get(key, default=None):
    return _cfg.get(key, default)


def save(**kw):
    _cfg.update(kw)
    json.dump(_cfg, open(_P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def market_brief_video_name(requested_at=None):
    """MarketBrief_YYYY_MM_DD_A.mp4 (KST < 15:30, before market close) or _P.mp4 (KST >= 15:30)."""
    if isinstance(requested_at, str) and requested_at.strip():
        try:
            dt = datetime.fromisoformat(requested_at.strip())
            dt = dt.astimezone(_KST) if dt.tzinfo else dt.replace(tzinfo=_KST)
        except ValueError:
            dt = datetime.now(_KST)
    elif isinstance(requested_at, datetime):
        dt = requested_at.astimezone(_KST) if requested_at.tzinfo else requested_at.replace(tzinfo=_KST)
    else:
        dt = datetime.now(_KST)
    suffix = 'P' if (dt.hour, dt.minute) >= (15, 30) else 'A'
    return f"MarketBrief_{dt.strftime('%Y_%m_%d')}_{suffix}.mp4"


def final_video_name():
    """Final MP4 filename for this project: explicit project.json 'output_name', else MarketBrief_YYYY_MM_DD_A/P.mp4."""
    name = _cfg.get('output_name')
    if isinstance(name, str) and name.strip():
        return name.strip()
    return market_brief_video_name(_cfg.get('requested_at'))


LANG = _cfg.get('lang', 'ko')
FPS = _cfg.get('fps', 60)
THEME = _cfg.get('theme', 'stage')     # the look of graphics, captions, chips and cover: 'stage' (theme.md), 'sketch' (theme-sketch.md),
                                       # 'reel' (theme-reel.md: code reel), 'sungkim' (theme-sungkim.md: paper news cards)
                                       # or 'brief' (theme-brief.md: modern research magazine)
NODE = _cfg.get('node', 'node')
NARRATION = 'scripts/narration'          # script-to-motion's TTS tools (tts.mjs, wave.mjs, sync.mjs, phrasing-check.mjs)


def ndir(sk):
    """the narration folder of a short: a script-to-motion-shaped project (script.json, js/cues.js, audio/, .tts-cache/)"""
    return f'narration/{sk}'


# The frame's zones (1080x1920), shared by the graphics, the captions, the preview and the thumbnail check:
# - content: every graphic's content, the main element's bottom edge at about 1360-1400 (y 620 at frame 0 of *_r0: the cover)
# - caption: the caption band (centre 1480; a chip's bottom edge ~1545); caption_top: the band for a picture whose content sits low ("caption": "top")
# - the bottom 360 px (from y 1560) stays empty: YouTube Shorts, TikTok and Reels draw the title, description and music
#   over it. No decoration fills it either (the old horizon wave of dots sat there and only took room).
LAYOUT = dict(content=(140, 1395), caption=(1410, 1550), caption_top=(180, 360), safe_bottom=1560,   # caption centre 1480
              ui_right=(960, 1000, 1700))   # Shorts/Reels/TikTok draw their like/comment/share column at x > 960, y 1000-1700:
                                            # no text and no key element there (a card's frame or a background may pass under)
