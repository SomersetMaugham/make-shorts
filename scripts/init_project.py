"""Write project.json for the shorts project (run inside work/). No source video: the values are the language, the
frame rate and where the skill lives. Existing values are kept, so hand edits survive a re-run of setup.sh.
usage: python scripts/init_project.py <skill_dir>"""
import json, os, sys

cfg = json.load(open('project.json', encoding='utf-8')) if os.path.exists('project.json') else {}
cfg.setdefault('lang', 'ko')          # every output is Korean unless the user asks for another language
cfg.setdefault('fps', 60)
cfg.setdefault('theme', 'stage')      # 'sketch' (hand-drawn schematics), 'reel' (code reel), 'sungkim' (paper news cards): references/theme-*.md
cfg['skill_dir'] = sys.argv[1] if len(sys.argv) > 1 else cfg.get('skill_dir')
json.dump(cfg, open('project.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print(json.dumps(cfg, ensure_ascii=False))
