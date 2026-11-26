"""The pronunciation lexicon: readings the user corrected once, applied to every later `say` (references/narration.md §3).
Two files, the project's entries after the skill's:
  <skill_dir>/references/pronunciation.json   readings that hold for any short ("마이너스 극" -> "마이너스극")
  pronunciation.json (in work/)               readings for this project only
Each entry: {"from": "...", "to": "...", "note": "why / which review note"}; "regex": true makes "from" a regular expression
(for a reading that holds only in a context; "to" may use \\1); "word": true never matches inside a
longer word ("1점" not in "10점"), though a particle may follow ("GRPO는"). Applied by narration_init.py to new or reworded lines before the comma pauses."""
import json, os, re


def _read(p):
    try: return json.load(open(p, encoding='utf-8')).get('entries', [])
    except FileNotFoundError: return []


def load():
    skill = ''
    if os.path.exists('project.json'): skill = json.load(open('project.json', encoding='utf-8')).get('skill_dir', '')
    return (_read(os.path.join(skill, 'references', 'pronunciation.json')) if skill else []) + _read('pronunciation.json')


def apply(say, entries):
    for e in entries:
        if e.get('regex'):   # a reading that holds only in a context (e.g. after a number): "to" may use \\1
            say = re.sub(e['from'], e['to'], say); continue
        f = re.escape(e['from'])
        if e.get('word'): f = r'(?<![가-힣A-Za-z0-9])' + f + r'(?![A-Za-z0-9])'   # a particle may follow: GRPO는
        say = re.sub(f, lambda m: e['to'], say)
    return say
