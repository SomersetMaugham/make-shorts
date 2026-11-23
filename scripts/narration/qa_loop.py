"""Automated phrasing QA loop run after the person's recording approval.

Runs up to MAX_LOOP_ROUNDS rounds of:
  phrasing-check.mjs -> phrasing_audit.py -> split fixes -> say fixes -> capped --only
  re-takes -> autocut.py (-45 dB) -> tts.mjs cut apply.
All three hard limits are persisted in narration/<sk>/qa_state.json and are never
exceeded; counters reset only when --new-approval is passed for a new human approval.

Usage:
  python3 scripts/narration/qa_loop.py <narration_dir> [--new-approval] [--shorts <shorts.json>] [--sk <s1>]
"""
from __future__ import annotations

import array
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
for _p in (SCRIPT_DIR, PARENT_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import phrasing_audit
import prosody_prep

# ---------- hard limits (never exceeded) ----------
MAX_RETAKES_PER_PARAGRAPH = 3
MAX_LOOP_ROUNDS = 3
MAX_CRITIC_RUNS = 3

# ---------- audio / paragraph constants matching tts.mjs & phrasing-check.mjs ----------
SAMPLE_RATE = 44100
PARA_MAX_BYTES = 4500
DEFAULT_PARA_SIZE = 5
SILENCE_DETECT_DB = -42
SILENCE_DETECT_MIN_SEC = 0.15
EDGE_GUARD_SEC = 0.05
SPLIT_MIN_GAP_SEC = 0.05
PROPOSE_FRAME_SEC = 0.01
PROPOSE_VOICE_DROP_DB = 35.0
PROPOSE_MIN_PAUSE_FRAMES = 15
PROPOSE_WIN_FRAMES = 120

_SILENCE_START_RE = re.compile(r'silence_start:\s*([\d.]+)')
_SILENCE_END_RE = re.compile(r'silence_end:\s*([\d.]+)')


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat(timespec='seconds')


def _state_path(proj_dir: str) -> str:
    return os.path.join(proj_dir, 'qa_state.json')


def load_state(proj_dir: str, new_approval: bool = False) -> dict[str, Any]:
    """Load or reset qa_state.json; only --new-approval resets the hard-limit counters."""
    path = _state_path(proj_dir)
    if new_approval or not os.path.exists(path):
        state = {
            'approval': _now_iso(),
            'retakes': {},
            'rounds': 0,
            'critic_runs': 0,
        }
        save_state(proj_dir, state)
        return state
    state = json.load(open(path, encoding='utf-8'))
    state.setdefault('approval', _now_iso())
    state.setdefault('retakes', {})
    state.setdefault('rounds', 0)
    state.setdefault('critic_runs', 0)
    return state


def save_state(proj_dir: str, state: dict[str, Any]) -> None:
    with open(_state_path(proj_dir), 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=1, ensure_ascii=False)
        f.write('\n')


def _find_node(proj_dir: str) -> str:
    """Resolve Node binary from work/project.json when available, else `node`."""
    candidates = [
        os.path.join(os.getcwd(), 'project.json'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(proj_dir))), 'project.json'),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                node = json.load(open(p, encoding='utf-8')).get('node')
                if node:
                    return str(node)
            except (OSError, ValueError):
                pass
    return 'node'


def _find_shorts_json(proj_dir: str, explicit_path: str | None, explicit_sk: str | None) -> tuple[str | None, str | None]:
    """Locate work/shorts.json so say edits survive subsequent prep.sh runs."""
    abs_dir = os.path.abspath(proj_dir)
    sk = explicit_sk or os.path.basename(abs_dir)
    if explicit_path:
        return (explicit_path if os.path.exists(explicit_path) else None), sk
    parent = os.path.dirname(abs_dir)
    if os.path.basename(parent) == 'narration':
        cand = os.path.join(os.path.dirname(parent), 'shorts.json')
        if os.path.exists(cand):
            return cand, sk
    return None, sk


def _sync_say_to_shorts(shorts_path: str | None, sk: str | None, updated_says: dict[str, str]) -> None:
    """Mirror say mutations into shorts.json so narration_init.py will not overwrite them."""
    if not shorts_path or not sk or not updated_says or not os.path.exists(shorts_path):
        return
    try:
        data = json.load(open(shorts_path, encoding='utf-8'))
    except (OSError, ValueError):
        return
    if sk not in data:
        return
    changed = False
    for line in data[sk].get('lines', []):
        cid = line.get('id')
        if cid in updated_says and line.get('say') != updated_says[cid]:
            line['say'] = updated_says[cid]
            changed = True
    if changed:
        with open(shorts_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=False)
            f.write('\n')


def _paragraph_groups(script: dict[str, Any]) -> list[list[dict[str, Any]]]:
    """Replicate tts.mjs paragraphGroups() so retakes and splits target identical groups."""
    cues = script.get('cues', [])
    tts_cfg = script.get('tts') or {}
    provider = tts_cfg.get('provider') or ('fish' if script.get('voice') else 'google')
    para_setting = tts_cfg.get('paragraphs') if provider == 'google' else None
    if para_setting is None or para_setting is False or script.get('narration') is False:
        return [[c] for c in cues]

    if isinstance(para_setting, list):
        by_id = {c['id']: c for c in cues}
        return [[by_id[cid] for cid in grp] for grp in para_setting]

    max_len = para_setting if isinstance(para_setting, int) and para_setting > 0 else DEFAULT_PARA_SIZE
    groups: list[list[dict[str, Any]]] = []
    cur: list[dict[str, Any]] = []
    for c in cues:
        joined = ' '.join(x['say'] for x in cur + [c]).encode('utf-8')
        if cur and (len(cur) >= max_len or len(joined) > PARA_MAX_BYTES):
            groups.append(cur)
            cur = []
        cur.append(c)
    if cur:
        groups.append(cur)
    return groups


def _para_stable_key(group: list[dict[str, Any]]) -> str:
    """Stable paragraph identifier across say edits so retake caps cannot be bypassed."""
    return ','.join(c['id'] for c in group)


def _para_tts_key(script: dict[str, Any], group: list[dict[str, Any]]) -> str:
    """Exact sha256 paragraph key used by tts.mjs for .tts-cache/<pk>.pcm and script.splits."""
    voice_name = (script.get('tts') or {}).get('voice') or 'ko-KR-Chirp3-HD-Enceladus'
    payload = {
        'v': 'para1',
        'voice': 'google:' + voice_name,
        'says': [c['say'] for c in group],
        'sr': SAMPLE_RATE,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()[:24]


def _propose_splits(samples: array.array, group: list[dict[str, Any]]) -> list[float]:
    """Mirror tts.mjs proposeSplits() when script.json has no explicit splits entry yet."""
    h = round(SAMPLE_RATE * PROPOSE_FRAME_SEC)
    n_frames = len(samples) // h
    db: list[float] = []
    for f in range(n_frames):
        chunk = samples[f * h : (f + 1) * h]
        mean_sq = sum((x / 32768.0) ** 2 for x in chunk) / h
        db.append(10.0 * math.log10(mean_sq + 1e-18))
    if not db:
        return []
    top = max(db)
    voiced = [x > top - PROPOSE_VOICE_DROP_DB for x in db]
    if not any(voiced):
        return []
    first = voiced.index(True)
    last = len(voiced) - 1 - voiced[::-1].index(True)
    pauses: list[tuple[int, int]] = []
    f = first
    while f <= last:
        if not voiced[f]:
            e = f
            while e <= last and not voiced[e]:
                e += 1
            if e - f >= PROPOSE_MIN_PAUSE_FRAMES:
                pauses.append((f, e))
            f = e
        else:
            f += 1

    def _voiced_before(frame: int) -> int:
        return sum(1 for k in range(first, min(frame, len(voiced))) if voiced[k])

    total = _voiced_before(last + 1)
    syls = [
        prosody_prep.count_syllables(prosody_prep._PAUSE_TAG_RE.sub('', c['say'])) or 1
        for c in group
    ]
    all_syl = sum(syls)
    out: list[float] = []
    acc = 0
    floor = first
    for k in range(len(group) - 1):
        acc += syls[k]
        want = (acc / all_syl) * total
        near = [(p, abs(_voiced_before(p[0]) - want)) for p in pauses if p[0] > floor]
        if not near:
            break
        in_win = [x for x in near if x[1] < PROPOSE_WIN_FRAMES]
        if in_win:
            pick = max(in_win, key=lambda x: x[0][1] - x[0][0])[0]
        else:
            pick = min(near, key=lambda x: x[1])[0]
        out.append(round(((pick[0] + pick[1]) / 2.0) * h / SAMPLE_RATE, 3))
        floor = pick[1]
    return out


def _detect_wav_silences(wav_path: str) -> tuple[list[tuple[float, float]], float]:
    """Detect interior silences using the exact ffmpeg parameters of phrasing-check.mjs."""
    dur_res = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', wav_path],
        capture_output=True,
        text=True,
        encoding='utf-8',
    )
    dur = float((dur_res.stdout or '0').strip() or '0')
    sd_res = subprocess.run(
        [
            'ffmpeg', '-v', 'info', '-i', wav_path,
            '-af', f'silencedetect=n={SILENCE_DETECT_DB}dB:d={SILENCE_DETECT_MIN_SEC}',
            '-f', 'null', '-',
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
    )
    stderr = sd_res.stderr or ''
    starts = [float(m.group(1)) for m in _SILENCE_START_RE.finditer(stderr)]
    ends = [float(m.group(1)) for m in _SILENCE_END_RE.finditer(stderr)]
    gaps: list[tuple[float, float]] = []
    for idx, s in enumerate(starts):
        e = ends[idx] if idx < len(ends) else dur
        if s > EDGE_GUARD_SEC and e < dur - EDGE_GUARD_SEC:
            gaps.append((s, e))
    return gaps, dur


def _cut_time_to_uncut(t_cut: float, cut: dict[str, Any] | None, current_take: str | None) -> float:
    """Invert applyCut() ranges to map a timestamp in audio/cues/<id>.wav back to the uncut take."""
    if not cut or cut.get('take') != current_take:
        return t_cut
    ranges = sorted((float(a), float(b)) for a, b in cut.get('ranges', []))
    t = t_cut
    for a, b in ranges:
        if t >= a:
            t += b - a
    return t


def _piece_split_gap_index(
    pieces: list[str],
    target_say: str,
    take_from: str,
) -> int | None:
    """Pick the silence gap separating a cue's own words from words spilled across a split."""
    if len(pieces) <= 1:
        return None
    target_jamo = phrasing_audit.to_jamo(phrasing_audit._normalize_spoken_text(target_say))
    if not target_jamo:
        return 0 if take_from == 'start' else len(pieces) - 2

    best_gap = 0 if take_from == 'start' else len(pieces) - 2
    best_score = -1.0
    for g_idx in range(len(pieces) - 1):
        # For take_from == 'start', candidate kept portion is pieces[g_idx+1:];
        # for take_from == 'end', candidate kept portion is pieces[:g_idx+1].
        kept = ' '.join(pieces[g_idx + 1 :] if take_from == 'start' else pieces[: g_idx + 1])
        kept_jamo = phrasing_audit.to_jamo(phrasing_audit._normalize_spoken_text(kept))
        if not kept_jamo:
            continue
        _, _, scores, lead_ex, tail_ex = phrasing_audit._align_jamo(target_jamo, kept_jamo)
        coverage = sum(scores) / len(target_jamo)
        penalty = (lead_ex + tail_ex) / max(len(target_jamo), 1)
        score = coverage - 0.5 * penalty
        if score > best_score:
            best_score = score
            best_gap = g_idx
    return best_gap


def _fix_boundary_splits(
    proj_dir: str,
    script: dict[str, Any],
    audit: dict[str, Any],
    groups: list[list[dict[str, Any]]],
    actions: list[str],
) -> tuple[bool, set[str]]:
    """Step (b): move wrong paragraph splits into the silence between the two cues' words."""
    phrasing = json.load(open(os.path.join(proj_dir, 'phrasing.json'), encoding='utf-8'))
    changed = False
    resplit_cues: set[str] = set()
    splits_map = script.setdefault('splits', {})

    for group in groups:
        if len(group) <= 1:
            continue
        grp_ids = {c['id'] for c in group}
        has_boundary = any(
            any(iss['type'] == 'BOUNDARY' for iss in audit['cues'].get(cid, {}).get('issues', []))
            for cid in grp_ids
        )
        if not has_boundary:
            continue

        pk = _para_tts_key(script, group)
        pcm_path = os.path.join(proj_dir, '.tts-cache', f'{pk}.pcm')
        if not os.path.exists(pcm_path):
            actions.append(f'BOUNDARY in {_para_stable_key(group)}: paragraph cache {pk}.pcm not found, skipped')
            continue

        samples = array.array('h')
        with open(pcm_path, 'rb') as f:
            samples.frombytes(f.read())
        para_dur = len(samples) / SAMPLE_RATE

        sp = list(splits_map[pk]) if pk in splits_map else _propose_splits(samples, group)
        if len(sp) != len(group) - 1:
            actions.append(f'BOUNDARY in {_para_stable_key(group)}: could not determine base splits')
            continue

        edges = [0.0] + sp + [para_dur]
        new_sp = list(sp)
        grp_changed = False

        for k in range(len(group) - 1):
            c_left = group[k]
            c_right = group[k + 1]
            left_issues = [
                iss for iss in audit['cues'].get(c_left['id'], {}).get('issues', [])
                if iss['type'] == 'BOUNDARY' and iss.get('side') == 'end'
            ]
            right_issues = [
                iss for iss in audit['cues'].get(c_right['id'], {}).get('issues', [])
                if iss['type'] == 'BOUNDARY' and iss.get('side') == 'start'
            ]
            if not left_issues and not right_issues:
                continue

            candidate_t: float | None = None
            # Extra words of c_right landed at the end of c_left -> split moves earlier inside c_left.
            if (left_issues and not left_issues[0].get('missing_edge_word')) or (
                right_issues and right_issues[0].get('missing_edge_word')
            ):
                p_entry = phrasing.get(c_left['id'], {})
                pieces, _ = phrasing_audit.parse_heard(p_entry.get('heard', ''))
                wav = os.path.join(proj_dir, 'audio', 'cues', f'{c_left["id"]}.wav')
                if os.path.exists(wav) and len(pieces) > 1:
                    gaps, _ = _detect_wav_silences(wav)
                    g_idx = _piece_split_gap_index(pieces, c_left['say'], take_from='end')
                    if g_idx is not None and g_idx < len(gaps):
                        mid_cut = (gaps[g_idx][0] + gaps[g_idx][1]) / 2.0
                        mid_uncut = _cut_time_to_uncut(mid_cut, c_left.get('cut'), p_entry.get('take'))
                        candidate_t = edges[k] + mid_uncut

            # Extra words of c_left landed at the start of c_right -> split moves later inside c_right.
            if candidate_t is None and (
                (right_issues and not right_issues[0].get('missing_edge_word'))
                or (left_issues and left_issues[0].get('missing_edge_word'))
            ):
                p_entry = phrasing.get(c_right['id'], {})
                pieces, _ = phrasing_audit.parse_heard(p_entry.get('heard', ''))
                wav = os.path.join(proj_dir, 'audio', 'cues', f'{c_right["id"]}.wav')
                if os.path.exists(wav) and len(pieces) > 1:
                    gaps, _ = _detect_wav_silences(wav)
                    g_idx = _piece_split_gap_index(pieces, c_right['say'], take_from='start')
                    if g_idx is not None and g_idx < len(gaps):
                        mid_cut = (gaps[g_idx][0] + gaps[g_idx][1]) / 2.0
                        mid_uncut = _cut_time_to_uncut(mid_cut, c_right.get('cut'), p_entry.get('take'))
                        candidate_t = edges[k + 1] + mid_uncut

            if candidate_t is not None:
                lo = (new_sp[k - 1] if k > 0 else 0.0) + SPLIT_MIN_GAP_SEC
                hi = (new_sp[k + 1] if k + 1 < len(new_sp) else para_dur) - SPLIT_MIN_GAP_SEC
                if lo < candidate_t < hi and abs(candidate_t - new_sp[k]) > 0.01:
                    old_t = new_sp[k]
                    new_sp[k] = round(candidate_t, 3)
                    grp_changed = True
                    actions.append(
                        f'split {c_left["id"]}|{c_right["id"]} ({pk}): {old_t:.3f}s -> {new_sp[k]:.3f}s'
                    )

        if grp_changed:
            splits_map[pk] = new_sp
            changed = True
            resplit_cues.update(grp_ids)

    return changed, resplit_cues


def _apply_say_fixes(say: str, issues: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Apply step (c) edits to one cue's `say`: join FORBIDDEN_BREAKs and tag MISSING_BREAKs."""
    notes: list[str] = []
    working = say

    # Strip leftover quotes if F6 quote-clitic break appeared on an unsanitized say.
    if any(iss['type'] == 'FORBIDDEN_BREAK' and iss.get('rule') == 'F6' for iss in issues):
        stripped = prosody_prep.strip_quotes(working)
        if stripped != working:
            working = stripped
            notes.append('stripped quote characters (F6)')

    words = prosody_prep._tokenize_say(working)
    if not words:
        return working, notes

    join_indices: set[int] = set()
    pause_indices: set[int] = set()

    for iss in issues:
        if iss['type'] == 'FORBIDDEN_BREAK' and not iss.get('intra_word'):
            idx = iss.get('boundary_index')
            if isinstance(idx, int) and 0 <= idx < len(words) - 1:
                join_indices.add(idx)
        elif iss['type'] == 'MISSING_BREAK' and iss.get('severity', 'fix') == 'fix':
            idx = iss.get('boundary_index')
            if isinstance(idx, int) and 0 <= idx < len(words) - 1:
                if not words[idx].pause_tag_after:
                    pause_indices.add(idx)

    if not join_indices and not pause_indices:
        return working, notes

    out: list[str] = []
    i = 0
    while i < len(words):
        token = words[i].raw
        tag_after = words[i].pause_tag_after
        # Merge chained FORBIDDEN_BREAK joins into one eojeol without space.
        while i in join_indices and i + 1 < len(words):
            left_clean = re.sub(r',$', '', token)
            nxt = words[i + 1]
            notes.append(f'joined "{words[i].clean} {nxt.clean}"')
            token = left_clean + nxt.raw
            tag_after = nxt.pause_tag_after
            i += 1
        if i in pause_indices and not tag_after:
            if not token.endswith((',', '.', '?', '!')):
                token = token + ','
            tag_after = 'pause short'
            notes.append(f'inserted , [pause short] after "{words[i].clean}"')
        out.append(token)
        if tag_after:
            out.append(f'[{tag_after}]')
        i += 1

    return ' '.join(out), notes


def _run_cmd(cmd: list[str], allow_nonzero: bool = False) -> subprocess.CompletedProcess[str]:
    res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if res.returncode != 0 and not allow_nonzero:
        tail = ((res.stderr or '') + '\n' + (res.stdout or '')).strip()[-600:]
        raise RuntimeError(f'command failed (exit {res.returncode}): {" ".join(cmd)}\n{tail}')
    return res


def _save_script(proj_dir: str, script: dict[str, Any]) -> None:
    with open(os.path.join(proj_dir, 'script.json'), 'w', encoding='utf-8') as f:
        json.dump(script, f, indent=1, ensure_ascii=False)
        f.write('\n')


def _refresh_prosody_map(proj_dir: str, script: dict[str, Any]) -> None:
    pmap = {
        c['id']: prosody_prep.analyze_cue(c.get('say', ''), text=c.get('text', ''))
        for c in script.get('cues', [])
    }
    prosody_prep.write_prosody_map(os.path.join(proj_dir, 'prosody_map.json'), pmap)


def run_loop(
    proj_dir: str,
    new_approval: bool = False,
    shorts_path: str | None = None,
    sk: str | None = None,
) -> int:
    """Execute the bounded QA loop and print the final summary report."""
    node = _find_node(proj_dir)
    tts_js = os.path.join(SCRIPT_DIR, 'tts.mjs')
    phrasing_js = os.path.join(SCRIPT_DIR, 'phrasing-check.mjs')
    autocut_py = os.path.join(SCRIPT_DIR, 'autocut.py')

    resolved_shorts, resolved_sk = _find_shorts_json(proj_dir, shorts_path, sk)
    state = load_state(proj_dir, new_approval=new_approval)

    fixed_log: list[str] = []
    garble_notes: list[str] = []
    capped_paras: list[str] = []
    last_audit: dict[str, Any] | None = None
    stop_reason = ''

    if state['rounds'] >= MAX_LOOP_ROUNDS:
        stop_reason = f'round cap already reached ({state["rounds"]}/{MAX_LOOP_ROUNDS}); pass --new-approval after a new human recording approval'
        if os.path.exists(os.path.join(proj_dir, 'phrasing.json')):
            last_audit = phrasing_audit.audit_dir(proj_dir)
        _print_final_report(stop_reason, fixed_log, garble_notes, capped_paras, last_audit, state)
        return 0 if (last_audit and last_audit['clean']) else 1

    while state['rounds'] < MAX_LOOP_ROUNDS:
        round_num = state['rounds'] + 1
        print(f'\n=== qa_loop round {round_num}/{MAX_LOOP_ROUNDS} ({proj_dir}) ===')

        # (a) phrasing-check.mjs (all cues) -> phrasing_audit.py
        # phrasing-check.mjs exits 1 on missing pauses, which is expected input for the audit.
        pc_res = _run_cmd([node, phrasing_js, proj_dir], allow_nonzero=True)
        if not os.path.exists(os.path.join(proj_dir, 'phrasing.json')):
            raise RuntimeError(f'phrasing-check.mjs did not write phrasing.json:\n{(pc_res.stderr or pc_res.stdout)[-500:]}')

        audit = phrasing_audit.audit_dir(proj_dir)
        phrasing_audit.print_report(audit)
        last_audit = audit

        if audit['clean']:
            stop_reason = 'audit clean'
            break

        script = json.load(open(os.path.join(proj_dir, 'script.json'), encoding='utf-8'))
        groups = _paragraph_groups(script)
        round_changed = False

        # (b) BOUNDARY -> move paragraph splits into silence and re-run tts.mjs (no new API call)
        split_actions: list[str] = []
        split_changed, resplit_cues = _fix_boundary_splits(proj_dir, script, audit, groups, split_actions)
        if split_changed:
            _save_script(proj_dir, script)
            _run_cmd([node, tts_js, proj_dir])
            _run_cmd([sys.executable, autocut_py, proj_dir, ','.join(sorted(resplit_cues))])
            _run_cmd([node, tts_js, proj_dir])
            fixed_log.extend(f'[r{round_num}] {a}' for a in split_actions)
            round_changed = True
            # Reload script after autocut updated cuts.
            script = json.load(open(os.path.join(proj_dir, 'script.json'), encoding='utf-8'))
            groups = _paragraph_groups(script)

        # (c) FORBIDDEN_BREAK / MISSING_BREAK say fixes; GARBLE reported for the agent
        cue_by_id = {c['id']: c for c in script.get('cues', [])}
        para_of_cue: dict[str, tuple[str, list[dict[str, Any]]]] = {}
        for g in groups:
            pkey = _para_stable_key(g)
            for c in g:
                para_of_cue[c['id']] = (pkey, g)

        proposed_edits: dict[str, tuple[str, list[str]]] = {}
        for cid, entry in audit['cues'].items():
            issues = entry.get('issues', [])
            if not issues:
                continue
            for iss in issues:
                if iss['type'] == 'GARBLE':
                    syl = iss.get('syllables')
                    tag = ' [one-syllable word]' if syl == 1 else ''
                    msg = f'{cid}: GARBLE{tag} — {iss["detail"]} (needs agent/human decision; no automatic rewording)'
                    print(f'  ! {msg}')
                    if msg not in garble_notes:
                        garble_notes.append(msg)

            # Skip say mutations on cues whose paragraph was just resplit; audit them fresh next round.
            if cid in resplit_cues:
                continue
            cue = cue_by_id.get(cid)
            if not cue:
                continue
            new_say, notes = _apply_say_fixes(cue['say'], issues)
            if new_say != cue['say']:
                proposed_edits[cid] = (new_say, notes)

        # (d) Group mutated cues by paragraph and enforce MAX_RETAKES_PER_PARAGRAPH
        paras_to_retake: dict[str, list[dict[str, Any]]] = {}
        accepted_says: dict[str, str] = {}
        for cid, (new_say, notes) in proposed_edits.items():
            pkey, grp = para_of_cue[cid]
            used = int(state['retakes'].get(pkey, 0))
            if used >= MAX_RETAKES_PER_PARAGRAPH:
                cap_msg = f'paragraph [{pkey}] hit MAX_RETAKES_PER_PARAGRAPH ({used}/{MAX_RETAKES_PER_PARAGRAPH}); left unchanged'
                if cap_msg not in capped_paras:
                    capped_paras.append(cap_msg)
                print(f'  ! {cap_msg}')
                continue
            cue_by_id[cid]['say'] = new_say
            accepted_says[cid] = new_say
            paras_to_retake[pkey] = grp
            for n in notes:
                fixed_log.append(f'[r{round_num}] {cid}: {n}')

        if paras_to_retake:
            _save_script(proj_dir, script)
            _sync_say_to_shorts(resolved_shorts, resolved_sk, accepted_says)
            _refresh_prosody_map(proj_dir, script)

            # Persist incremented retake counters before invoking TTS so caps can never be exceeded.
            only_ids: list[str] = []
            recut_ids: list[str] = []
            for pkey, grp in paras_to_retake.items():
                state['retakes'][pkey] = int(state['retakes'].get(pkey, 0)) + 1
                only_ids.append(grp[0]['id'])
                recut_ids.extend(c['id'] for c in grp)
            save_state(proj_dir, state)

            _run_cmd([node, tts_js, proj_dir, '--approved', '--only', ','.join(only_ids)])

            # (e) Draft cuts with autocut.py (-45 dB interior threshold) and apply them.
            _run_cmd([sys.executable, autocut_py, proj_dir, ','.join(recut_ids)])
            _run_cmd([node, tts_js, proj_dir])
            fixed_log.append(f'[r{round_num}] re-took paragraphs: {", ".join(paras_to_retake)} and recut {len(recut_ids)} cue(s)')
            round_changed = True

        state['rounds'] += 1
        save_state(proj_dir, state)

        if not round_changed:
            stop_reason = 'no automatic changes possible in this round'
            break

        if state['rounds'] >= MAX_LOOP_ROUNDS:
            # Run one final audit after the last round's fixes so the final report reflects current state.
            _run_cmd([node, phrasing_js, proj_dir], allow_nonzero=True)
            if os.path.exists(os.path.join(proj_dir, 'phrasing.json')):
                last_audit = phrasing_audit.audit_dir(proj_dir)
                phrasing_audit.print_report(last_audit)
            stop_reason = (
                'audit clean'
                if (last_audit and last_audit['clean'])
                else f'reached MAX_LOOP_ROUNDS ({MAX_LOOP_ROUNDS})'
            )
            break

    _print_final_report(stop_reason, fixed_log, garble_notes, capped_paras, last_audit, state)
    return 0 if (last_audit and last_audit['clean']) else 1


def _print_final_report(
    stop_reason: str,
    fixed_log: list[str],
    garble_notes: list[str],
    capped_paras: list[str],
    last_audit: dict[str, Any] | None,
    state: dict[str, Any],
) -> None:
    print('\n================ QA LOOP REPORT ================')
    print(f'Stop reason : {stop_reason}')
    print(f'Approval    : {state.get("approval", "unknown")}')
    print(f'Rounds      : {state.get("rounds", 0)}/{MAX_LOOP_ROUNDS}')
    print(f'Critic runs : {state.get("critic_runs", 0)}/{MAX_CRITIC_RUNS}')
    retakes = state.get('retakes', {})
    if retakes:
        print('Retakes     :')
        for pkey, cnt in sorted(retakes.items()):
            print(f'  - [{pkey}]: {cnt}/{MAX_RETAKES_PER_PARAGRAPH}')
    else:
        print('Retakes     : none')

    print('\nFixed:')
    if fixed_log:
        for item in fixed_log:
            print(f'  - {item}')
    else:
        print('  (none)')

    print('\nRemaining:')
    remaining_any = False
    if last_audit and not last_audit['clean']:
        for cid, entry in last_audit['cues'].items():
            for iss in entry['issues']:
                remaining_any = True
                print(f'  - {cid} [{iss["type"]}/{iss.get("rule", "")}]: {iss["detail"]}')
    for note in garble_notes:
        if not remaining_any:
            print(f'  - {note}')
    for cap in capped_paras:
        remaining_any = True
        print(f'  - {cap}')
    if not remaining_any and not garble_notes:
        print('  (none — clean)')
    print('================================================')


def main(argv: list[str]) -> int:
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    args = list(argv)
    new_approval = False
    shorts_path: str | None = None
    sk: str | None = None
    positional: list[str] = []

    i = 0
    while i < len(args):
        a = args[i]
        if a == '--new-approval':
            new_approval = True
            i += 1
        elif a == '--shorts' and i + 1 < len(args):
            shorts_path = args[i + 1]
            i += 2
        elif a == '--sk' and i + 1 < len(args):
            sk = args[i + 1]
            i += 2
        else:
            positional.append(a)
            i += 1

    if not positional:
        print('error: <narration_dir> is required', file=sys.stderr)
        return 2
    return run_loop(positional[0], new_approval=new_approval, shorts_path=shorts_path, sk=sk)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
