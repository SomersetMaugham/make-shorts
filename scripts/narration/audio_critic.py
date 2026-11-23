"""Optional post-loop audio emphasis/intonation critic via Gemini Neon (agy, read-only).

Pitch heuristics could not separate unnatural emphasis from normal Korean intonational
contours. This script sends audio/narration.wav and the timed cue list to Gemini Neon
read-only, asking strictly for emphasis or intonation defects, writes qa_critic.json,
and enforces MAX_CRITIC_RUNS per recording approval via qa_state.json. It never edits
any script or audio file.

Usage:
  python3 scripts/narration/audio_critic.py <narration_dir> [--model gemini-4-neon-medium]
"""
from __future__ import annotations

import datetime
import json
import os
import re
import subprocess
import sys
import time
from typing import Any

# ---------- named limits and constants ----------
MAX_CRITIC_RUNS = 3
DEFAULT_MODEL = 'gemini-4-neon-medium'
AGY_BIN = os.path.expanduser('~/.local/bin/agy')  # never the zsh alias (adds skip-permissions)
SUBPROCESS_TIMEOUT_SEC = 300

_JSON_BLOCK_RE = re.compile(r'```(?:json)?\s*(\{.*?\})\s*```', re.S)


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='seconds')


def _load_state(proj_dir: str) -> dict[str, Any]:
    path = os.path.join(proj_dir, 'qa_state.json')
    if os.path.exists(path):
        state = json.load(open(path, encoding='utf-8'))
        state.setdefault('approval', _now_iso())
        state.setdefault('retakes', {})
        state.setdefault('rounds', 0)
        state.setdefault('critic_runs', 0)
        return state
    return {
        'approval': _now_iso(),
        'retakes': {},
        'rounds': 0,
        'critic_runs': 0,
    }


def _save_state(proj_dir: str, state: dict[str, Any]) -> None:
    path = os.path.join(proj_dir, 'qa_state.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=1, ensure_ascii=False)
        f.write('\n')


def _load_timed_cues(proj_dir: str) -> list[dict[str, Any]]:
    """Read cue start/end times from js/cues.js, falling back to script.json without times."""
    cues_js = os.path.join(proj_dir, 'js', 'cues.js')
    if os.path.exists(cues_js):
        raw = open(cues_js, encoding='utf-8').read()
        m = re.search(r'window\.VIDEO_DATA\s*=\s*', raw)
        if m:
            data = json.loads(raw[m.end() : raw.rindex('}') + 1])
            return list(data.get('cues', []))
    script = json.load(open(os.path.join(proj_dir, 'script.json'), encoding='utf-8'))
    return list(script.get('cues', []))


def _fmt_time(sec: float | None) -> str:
    if sec is None:
        return '?:??.??'
    mm, ss = divmod(float(sec), 60.0)
    return f'{int(mm)}:{ss:05.2f}'


def _build_prompt(audio_path: str, cues: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for c in cues:
        cid = c.get('id', '?')
        t0 = _fmt_time(c.get('start'))
        t1 = _fmt_time(c.get('end'))
        text = c.get('text', '')
        say = c.get('say', '')
        lines.append(f'- [{cid}] {t0}–{t1} | text: {text} | say: {say}')
    cue_block = '\n'.join(lines)

    return (
        'Hi, and thank you for taking this on. Could you please listen to the Korean narration audio file below '
        'and check only for emphasis or intonation that sounds unnatural to a native Korean listener?\n\n'
        'Please do not edit or create any file and do not run any command: your written answer is the report, '
        'and this script saves it.\n\n'
        f'Audio file (please open and listen directly): {audio_path}\n\n'
        'Cue list with times:\n'
        f'{cue_block}\n\n'
        'Please report ONLY clear emphasis or intonation defects:\n'
        '1. One-word or very short lines read with theatrical or exaggerated stress.\n'
        '2. A stressed topic or discourse opener (for example, "그래서/이렇게 + subject은/는") read with unnatural emphasis.\n'
        '3. A question read flat with no rising question contour, or a statement with a clearly wrong pitch contour.\n'
        '4. Any obvious robotic pitch jump or misplaced word stress.\n\n'
        'Please do NOT report pauses or phrase breaks (a separate tool checks those), do NOT suggest rewording, '
        'and do NOT give scores, grades, or praise. If every line sounds natural, return an empty findings list '
        'instead of inventing issues. If anything in the audio is unclear, please say so in the reason field.\n\n'
        'Please reply with a single JSON object inside a ```json fenced block using this exact schema:\n'
        '```json\n'
        '{\n'
        '  "findings": [\n'
        '    {\n'
        '      "cue_id": "c08",\n'
        '      "time": 42.10,\n'
        '      "kind": "theatrical_short_line | stressed_topic | flat_question | wrong_intonation",\n'
        '      "phrase": "exact Korean word or short phrase",\n'
        '      "reason": "brief explanation of what sounded wrong"\n'
        '    }\n'
        '  ]\n'
        '}\n'
        '```\n'
        'Thank you very much.'
    )


def _extract_json(stdout: str) -> tuple[dict[str, Any] | None, str | None]:
    m = _JSON_BLOCK_RE.search(stdout)
    if m:
        try:
            return json.loads(m.group(1)), None
        except ValueError as e:
            return None, f'failed to parse fenced JSON: {e}'
    start = stdout.find('{')
    end = stdout.rfind('}')
    if start >= 0 and end > start:
        try:
            return json.loads(stdout[start : end + 1]), None
        except ValueError as e:
            return None, f'failed to parse raw JSON: {e}'
    return None, 'no JSON object found in agy response'


def run_critic(proj_dir: str, model: str = DEFAULT_MODEL) -> int:
    """Invoke Gemini Neon read-only on audio/narration.wav and write qa_critic.json."""
    abs_dir = os.path.abspath(proj_dir)
    audio_path = os.path.join(abs_dir, 'audio', 'narration.wav')
    if not os.path.exists(audio_path):
        print(f'audio_critic: missing {audio_path}', file=sys.stderr)
        return 1
    if not os.path.exists(AGY_BIN):
        print(f'audio_critic: agy binary not found at {AGY_BIN}', file=sys.stderr)
        return 1

    state = _load_state(abs_dir)
    runs = int(state.get('critic_runs', 0))
    if runs >= MAX_CRITIC_RUNS:
        print(
            f'audio_critic: MAX_CRITIC_RUNS reached ({runs}/{MAX_CRITIC_RUNS}) for approval '
            f'{state.get("approval", "unknown")} — refusing to run again.',
            file=sys.stderr,
        )
        return 2

    cues = _load_timed_cues(abs_dir)
    prompt = _build_prompt(audio_path, cues)

    # Record the run before calling agy so the hard limit can never be exceeded.
    state['critic_runs'] = runs + 1
    _save_state(abs_dir, state)

    cmd = [
        AGY_BIN,
        '-p', prompt,
        '--model', model,
        '--settings', '{"allowNonWorkspaceAccess": false}',
        '--add-dir', abs_dir,
    ]
    t0 = time.time()
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=SUBPROCESS_TIMEOUT_SEC,
    )
    elapsed = round(time.time() - t0, 1)
    stdout = (res.stdout or '').strip()
    if res.returncode != 0 or not stdout:
        detail = (res.stderr or stdout)[-600:]
        print(f'audio_critic: agy failed (exit {res.returncode}): {detail}', file=sys.stderr)
        return 1

    parsed, parse_err = _extract_json(stdout)
    findings = parsed.get('findings', []) if isinstance(parsed, dict) and isinstance(parsed.get('findings'), list) else []

    out = {
        'audio': audio_path,
        'model': model,
        'approval': state.get('approval'),
        'run': state['critic_runs'],
        'max_runs': MAX_CRITIC_RUNS,
        'elapsed_sec': elapsed,
        'findings': findings,
        'parse_error': parse_err,
        'raw_response': stdout,
    }
    out_path = os.path.join(abs_dir, 'qa_critic.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
        f.write('\n')

    print(f'audio_critic: run {state["critic_runs"]}/{MAX_CRITIC_RUNS} ({model}, {elapsed}s) -> {out_path}')
    if parse_err:
        print(f'  warning: {parse_err} (raw response saved in qa_critic.json)')
    if not findings:
        print('  no emphasis/intonation issues reported.')
    else:
        for item in findings:
            cid = item.get('cue_id', '?')
            t = item.get('time', '?')
            kind = item.get('kind', '')
            phrase = item.get('phrase', '')
            reason = item.get('reason', '')
            print(f'  - [{cid} @ {t}s] ({kind}) "{phrase}": {reason}')
    return 0


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    model = DEFAULT_MODEL
    positional: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == '--model' and i + 1 < len(argv):
            model = argv[i + 1]
            i += 2
        else:
            positional.append(argv[i])
            i += 1
    if not positional:
        print('usage: python3 scripts/narration/audio_critic.py <narration_dir> [--model <name>]', file=sys.stderr)
        return 2
    return run_critic(positional[0], model=model)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
