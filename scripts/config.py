"""Project settings, read from project.json in the work directory (the cwd every script runs in).
Written by init_project.py. Edit it by hand to override anything."""
import json, os

_P = 'project.json'
_cfg = json.load(open(_P, encoding='utf-8')) if os.path.exists(_P) else {}


def get(key, default=None):
    return _cfg.get(key, default)


def save(**kw):
    _cfg.update(kw)
    json.dump(_cfg, open(_P, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


LANG = _cfg.get('lang', 'ko')
FPS = _cfg.get('fps', 60)
NODE = _cfg.get('node', 'node')
NARRATION = 'scripts/narration'          # script-to-motion's TTS tools (tts.mjs, wave.mjs, sync.mjs, phrasing-check.mjs)


def ndir(sk):
    """the narration folder of a short: a script-to-motion-shaped project (script.json, js/cues.js, audio/, .tts-cache/)"""
    return f'narration/{sk}'
