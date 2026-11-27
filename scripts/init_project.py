"""Write project.json for the shorts project (run inside work/). No source video: the values are the language, the
frame rate and where the skill lives. Existing values are kept, so hand edits survive a re-run of setup.sh.
usage: python scripts/init_project.py <skill_dir>"""
from datetime import datetime, timedelta, timezone
import json, os, sys

_KST = timezone(timedelta(hours=9))
cfg = json.load(open('project.json', encoding='utf-8')) if os.path.exists('project.json') else {}
cfg.setdefault('lang', 'ko')          # every output is Korean unless the user asks for another language
cfg.setdefault('fps', 60)
cfg.setdefault('theme', 'stage')      # 'sketch' (hand-drawn schematics), 'reel' (code reel), 'sungkim' (paper news cards), 'brief' (research magazine): references/theme-*.md
now_kst = datetime.now(_KST)
cfg.setdefault('requested_at', now_kst.isoformat(timespec='seconds'))
if not cfg.get('output_name'):
    try:
        dt = datetime.fromisoformat(cfg['requested_at'])
        dt = dt.astimezone(_KST) if dt.tzinfo else dt.replace(tzinfo=_KST)
    except Exception:
        dt = now_kst
    suffix = 'P' if (dt.hour, dt.minute) >= (15, 30) else 'A'
    cfg['output_name'] = f"MarketBrief_{dt.strftime('%Y_%m_%d')}_{suffix}.mp4"
cfg['skill_dir'] = sys.argv[1] if len(sys.argv) > 1 else cfg.get('skill_dir')
json.dump(cfg, open('project.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps(cfg, ensure_ascii=False))
