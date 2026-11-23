"""Audio emphasis/intonation critic via Gemini Neon (agy, read-only).

Pitch heuristics could not separate unnatural emphasis from normal Korean intonational
contours, and a 2026-11-24 calibration showed single-recording review misses isolated-line
emphasis while randomized A/B comparison catches it with high confidence.

Primary mode (--compare) sends an old and new WAV to Gemini Neon read-only in randomized
A/B order and maps the JSON verdict back to old/new. Legacy whole-narration mode remains
available as advisory only. Both modes enforce MAX_CRITIC_RUNS via qa_state.json when a
narration directory is provided. Neither mode edits any script or audio file.

Usage:
  python3 scripts/narration/audio_critic.py --compare OLD.wav NEW.wav [--text "the lines"] [--narration-dir DIR] [--model gemini-4-neon-medium]
  python3 scripts/narration/audio_critic.py <narration_dir> [--model gemini-4-neon-medium]
"""
from __future__ import annotations

import datetime
import json
import os
import random
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


class CriticCapReached(RuntimeError):
    """Raised when MAX_CRITIC_RUNS in qa_state.json has been reached."""


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


def _build_compare_prompt(path_a: str, path_b: str, cue_text: str = '') -> str:
    text_block = f'\nLines spoken: {cue_text.strip()}\n' if cue_text and cue_text.strip() else '\n'
    return (
        'Hi, could you help me compare two short Korean narration recordings? Thank you very much.\n\n'
        'Please do not edit or create any file and do not run any command: your written answer is the report.\n\n'
        f'Please open and listen to both audio files: A ({path_a}) and B ({path_b}). '
        'They read almost the same sentences with the same synthetic voice.'
        f'{text_block}\n'
        'A listener who reviews these videos judges by one standard: the narration should sound like one calm '
        'explainer talking naturally, and no word should stand out as if it were acted or announced (for example, '
        'a short answer read like a dramatic stage line, with a different tone, a longer pause around it, or extra '
        'weight).\n\n'
        'For each file (A and B), list any Korean word or words that stand out, with the time in seconds and what '
        'makes them stand out (tone, pause, loudness, pitch, speed), or an empty list if none. '
        'If you cannot open a file, please say so plainly instead of guessing (set "heard_both" to false and '
        '"preferred" to "same").\n\n'
        'Please reply in English with one valid JSON object inside a ```json fenced block using these exact keys:\n'
        '- "preferred": "A" or "B" or "same"\n'
        '- "confidence": "high" or "medium" or "low"\n'
        '- "stand_out": {"A": [{"words": "...", "time": 0.0, "why": "..."}], "B": [...]}\n'
        '- "heard_both": true or false\n\n'
        '```json\n'
        '{\n'
        '  "preferred": "A",\n'
        '  "confidence": "high",\n'
        '  "stand_out": {\n'
        '    "A": [],\n'
        '    "B": [{"words": "...", "time": 0.0, "why": "..."}]\n'
        '  },\n'
        '  "heard_both": true\n'
        '}\n'
        '```\n'
        'Thank you very much.'
    )


def compare(
    old_wav: str,
    new_wav: str,
    cue_text: str = '',
    model: str = DEFAULT_MODEL,
    narration_dir: str | None = None,
) -> dict[str, Any]:
    """Compare old vs. new cue WAV in randomized A/B order via Gemini Neon (read-only)."""
    abs_old = os.path.abspath(old_wav)
    abs_new = os.path.abspath(new_wav)
    if not os.path.exists(abs_old):
        raise FileNotFoundError(f'audio_critic: missing {abs_old}')
    if not os.path.exists(abs_new):
        raise FileNotFoundError(f'audio_critic: missing {abs_new}')
    if not os.path.exists(AGY_BIN):
        raise FileNotFoundError(f'audio_critic: agy binary not found at {AGY_BIN}')

    if narration_dir:
        abs_narration_dir = os.path.abspath(narration_dir)
        state = _load_state(abs_narration_dir)
        runs = int(state.get('critic_runs', 0))
        if runs >= MAX_CRITIC_RUNS:
            msg = (
                f'audio_critic: MAX_CRITIC_RUNS reached ({runs}/{MAX_CRITIC_RUNS}) for approval '
                f'{state.get("approval", "unknown")} — refusing to run again.'
            )
            print(msg, file=sys.stderr)
            raise CriticCapReached(msg)
        # Record the run before calling agy so the hard limit can never be exceeded.
        state['critic_runs'] = runs + 1
        _save_state(abs_narration_dir, state)

    old_is_a = random.choice([True, False])
    path_a, path_b = (abs_old, abs_new) if old_is_a else (abs_new, abs_old)
    prompt = _build_compare_prompt(path_a, path_b, cue_text=cue_text)

    cmd = [
        AGY_BIN,
        '-p', prompt,
        '--model', model,
        '--settings', '{"allowNonWorkspaceAccess": false}',
    ]
    for folder in dict.fromkeys((os.path.dirname(abs_old), os.path.dirname(abs_new))):
        cmd.extend(['--add-dir', folder])

    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=SUBPROCESS_TIMEOUT_SEC,
    )
    stdout = (res.stdout or '').strip()
    if res.returncode != 0 or not stdout:
        detail = (res.stderr or stdout)[-600:]
        raise RuntimeError(f'audio_critic: agy failed (exit {res.returncode}): {detail}')

    parsed, _parse_err = _extract_json(stdout)
    if not isinstance(parsed, dict):
        return {
            'preferred': 'same',
            'confidence': 'low',
            'stand_out_old': [],
            'stand_out_new': [],
            'heard_both': False,
            'raw': stdout,
        }

    raw_pref = parsed.get('preferred')
    pref_norm = raw_pref.strip() if isinstance(raw_pref, str) else ''
    if pref_norm.upper() == 'A':
        preferred = 'old' if old_is_a else 'new'
    elif pref_norm.upper() == 'B':
        preferred = 'new' if old_is_a else 'old'
    elif pref_norm.lower() == 'same':
        preferred = 'same'
    else:
        preferred = 'same'

    raw_conf = parsed.get('confidence')
    conf_norm = raw_conf.strip().lower() if isinstance(raw_conf, str) else 'low'
    confidence = conf_norm if conf_norm in ('high', 'medium', 'low') else 'low'

    stand_out = parsed.get('stand_out')
    if isinstance(stand_out, dict):
        so_a = stand_out.get('A') if isinstance(stand_out.get('A'), list) else []
        so_b = stand_out.get('B') if isinstance(stand_out.get('B'), list) else []
    else:
        so_a, so_b = [], []
    stand_out_old = so_a if old_is_a else so_b
    stand_out_new = so_b if old_is_a else so_a

    heard_both = parsed.get('heard_both') is True

    return {
        'preferred': preferred,
        'confidence': confidence,
        'stand_out_old': stand_out_old,
        'stand_out_new': stand_out_new,
        'heard_both': heard_both,
        'raw': stdout,
    }


def run_critic(proj_dir: str, model: str = DEFAULT_MODEL) -> int:
    """Invoke Gemini Neon read-only on audio/narration.wav and write qa_critic.json."""
    print(
        'audio_critic: note — whole-narration mode is advisory only; the 2026-11-24 calibration '
        'showed single-recording review misses isolated-line emphasis (use --compare for A/B checks).'
    )
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
    compare_pair: tuple[str, str] | None = None
    cue_text = ''
    narration_dir: str | None = None
    positional: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--model':
            if i + 1 >= len(argv):
                print('audio_critic: --model requires a value', file=sys.stderr)
                return 2
            model = argv[i + 1]
            i += 2
        elif a == '--compare':
            if i + 2 >= len(argv):
                print(
                    'usage: python3 scripts/narration/audio_critic.py --compare OLD.wav NEW.wav '
                    '[--text "the lines"] [--narration-dir DIR] [--model <name>]',
                    file=sys.stderr,
                )
                return 2
            compare_pair = (argv[i + 1], argv[i + 2])
            i += 3
        elif a == '--text':
            if i + 1 >= len(argv):
                print('audio_critic: --text requires a value', file=sys.stderr)
                return 2
            cue_text = argv[i + 1]
            i += 2
        elif a == '--narration-dir':
            if i + 1 >= len(argv):
                print('audio_critic: --narration-dir requires a value', file=sys.stderr)
                return 2
            narration_dir = argv[i + 1]
            i += 2
        else:
            positional.append(a)
            i += 1

    if compare_pair is not None:
        old_wav, new_wav = compare_pair
        try:
            result = compare(
                old_wav,
                new_wav,
                cue_text=cue_text,
                model=model,
                narration_dir=narration_dir,
            )
        except CriticCapReached:
            return 2
        except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as e:
            print(str(e), file=sys.stderr)
            return 1
        print(json.dumps(result, indent=1, ensure_ascii=False))
        return 0

    if not positional:
        print(
            'usage:\n'
            '  python3 scripts/narration/audio_critic.py --compare OLD.wav NEW.wav [--text "the lines"] [--narration-dir DIR] [--model <name>]\n'
            '  python3 scripts/narration/audio_critic.py <narration_dir> [--model <name>]',
            file=sys.stderr,
        )
        return 2
    return run_critic(positional[0], model=model)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
