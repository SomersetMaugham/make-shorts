"""Post-recording phrasing auditor for Chirp 3 HD narration takes.

phrasing-check.mjs only checks missing pauses at commas/tags; unwanted pauses inside
phrases, STT garbles, and wrong paragraph splits slipped through. This script aligns
the heard pieces in phrasing.json against prosody_map.json using Hangul jamo DP
alignment and reports MISSING_BREAK, FORBIDDEN_BREAK, GARBLE, and BOUNDARY defects.

Usage:
  python3 scripts/narration/phrasing_audit.py <narration_dir> [c01 c02 ...]
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import prosody_prep

# ---------- named thresholds ----------
MIN_BREAK_SEC = 0.15
MIN_PAUSE_TAG_SEC = 0.40
MIN_PAUSE_LONG_SEC = 0.70

GAP_ALIGN_TOL_JAMO = 3
INTRA_WORD_MARGIN_JAMO = 2

GARBLE_MIN_JAMO_MATCH = 0.30
BOUNDARY_EDGE_MIN_MATCH = 0.35
BOUNDARY_EXTRA_JAMO = 4

DP_MATCH_COST = 0.0
DP_SIMILAR_COST = 0.40
DP_SUB_COST = 1.00
DP_INDEL_COST = 0.85

# ---------- Hangul jamo & spoken normalization tables ----------
_CHOSEONG = (
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ',
    'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ',
)
_JUNGSEONG = (
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ',
    'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ',
)
_JONGSEONG = (
    '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ',
    'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ',
    'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ',
)

_SIMILAR_JAMO_GROUPS = (
    frozenset({'ㅐ', 'ㅔ', 'ㅒ', 'ㅖ'}),
    frozenset({'ㅙ', 'ㅞ', 'ㅚ'}),
    frozenset({'ㅡ', 'ㅣ', 'ㅢ', 'ㅜ'}),
    frozenset({'ㅓ', 'ㅏ', 'ㅗ'}),
    frozenset({'ㄱ', 'ㄲ', 'ㅋ'}),
    frozenset({'ㄷ', 'ㄸ', 'ㅌ'}),
    frozenset({'ㅂ', 'ㅃ', 'ㅍ'}),
    frozenset({'ㅅ', 'ㅆ'}),
    frozenset({'ㅈ', 'ㅉ', 'ㅊ'}),
    frozenset({'ㅇ', 'ㅎ'}),
    frozenset({'ㄴ', 'ㄹ'}),
)

LATIN_LETTER_TO_HANGUL = {
    'a': '에이', 'b': '비', 'c': '씨', 'd': '디', 'e': '이', 'f': '에프',
    'g': '지', 'h': '에이치', 'i': '아이', 'j': '제이', 'k': '케이', 'l': '엘',
    'm': '엠', 'n': '엔', 'o': '오', 'p': '피', 'q': '큐', 'r': '알',
    's': '에스', 't': '티', 'u': '유', 'v': '브이', 'w': '더블유', 'x': '엑스',
    'y': '와이', 'z': '제트',
}

_DIGIT_HANGUL = ('영', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구')
_SMALL_UNITS = ('', '십', '백', '천')
_BIG_UNITS = ('', '만', '억', '조')

_GAP_SPLIT_RE = re.compile(r'\s*‖([\d.]+)‖\s*')
_HEX_GARBLE_RE = re.compile(r'<0x[0-9a-fA-F]{2}>|\ufffd')
_DECIMAL_RE = re.compile(r'(\d+)\.(\d+)')
_INT_RE = re.compile(r'\d+')
_LATIN_RE = re.compile(r'[A-Za-z]+')
_PAUSE_TAG_RE = re.compile(r'\[(pause(?:\s+(?:short|long))?)\]')


def _int_to_sino_korean(n: int) -> str:
    """Convert a non-negative integer into Sino-Korean Hangul for STT/say alignment."""
    if n == 0:
        return '영'
    chunks: list[str] = []
    unit_idx = 0
    while n > 0 and unit_idx < len(_BIG_UNITS):
        part = n % 10000
        n //= 10000
        if part:
            sub: list[str] = []
            for p_idx in range(4):
                d = part % 10
                part //= 10
                if d:
                    digit_str = '' if (d == 1 and p_idx > 0) else _DIGIT_HANGUL[d]
                    sub.append(digit_str + _SMALL_UNITS[p_idx])
            chunks.append(''.join(reversed(sub)) + _BIG_UNITS[unit_idx])
        unit_idx += 1
    return ''.join(reversed(chunks))


def _normalize_spoken_text(text: str) -> str:
    """Map STT digits and Latin letters to spoken Hangul, dropping tags/spaces/punctuation."""
    s = _HEX_GARBLE_RE.sub('', text)
    s = _PAUSE_TAG_RE.sub('', s)

    def _dec_sub(m: re.Match[str]) -> str:
        int_part = _int_to_sino_korean(int(m.group(1)))
        frac_part = ''.join(_DIGIT_HANGUL[int(ch)] for ch in m.group(2))
        return f'{int_part}점{frac_part}'

    s = _DECIMAL_RE.sub(_dec_sub, s)
    s = _INT_RE.sub(lambda m: _int_to_sino_korean(int(m.group(0))), s)
    s = _LATIN_RE.sub(
        lambda m: ''.join(LATIN_LETTER_TO_HANGUL.get(ch.lower(), '') for ch in m.group(0)),
        s,
    )
    # Treat `쩜` as `점` during alignment so sanitized and unsanitized decimals match cleanly.
    s = s.replace('쩜', '점')
    return ''.join(ch for ch in s if '가' <= ch <= '힣')


def to_jamo(hangul_text: str) -> list[str]:
    """Decompose Hangul syllables to jamo so phonetic STT respellings align accurately."""
    out: list[str] = []
    for ch in hangul_text:
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            idx = code - 0xAC00
            out.append(_CHOSEONG[idx // 588])
            out.append(_JUNGSEONG[(idx % 588) // 28])
            jong = _JONGSEONG[idx % 28]
            if jong:
                out.append(jong)
    return out


def _jamo_sub_cost(a: str, b: str) -> float:
    if a == b:
        return DP_MATCH_COST
    for grp in _SIMILAR_JAMO_GROUPS:
        if a in grp and b in grp:
            return DP_SIMILAR_COST
    return DP_SUB_COST


def _align_jamo(
    say_jamo: list[str], heard_jamo: list[str]
) -> tuple[list[int], list[int], list[float], int, int]:
    """Needleman-Wunsch DP alignment returning position maps and per-say-jamo match scores.

    Returns:
      say_to_heard: length len(say_jamo)+1 mapping each say boundary to heard jamo index
      heard_to_say: length len(heard_jamo)+1 mapping each heard boundary to say jamo index
      say_scores:   length len(say_jamo) with 1.0 (exact), 0.6 (similar), or 0.0 (unmatched)
      lead_extra:   unaligned heard jamo before the first matched say jamo
      tail_extra:   unaligned heard jamo after the last matched say jamo
    """
    n = len(say_jamo)
    m = len(heard_jamo)
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    bt = [[0] * (m + 1) for _ in range(n + 1)]  # 0=diag, 1=up(del say), 2=left(ins heard)
    for x in range(1, n + 1):
        dp[x][0] = x * DP_INDEL_COST
        bt[x][0] = 1
    for y in range(1, m + 1):
        dp[0][y] = y * DP_INDEL_COST
        bt[0][y] = 2

    for x in range(1, n + 1):
        ax = say_jamo[x - 1]
        row = dp[x]
        prev = dp[x - 1]
        brow = bt[x]
        for y in range(1, m + 1):
            diag = prev[y - 1] + _jamo_sub_cost(ax, heard_jamo[y - 1])
            up = prev[y] + DP_INDEL_COST
            left = row[y - 1] + DP_INDEL_COST
            if diag <= up and diag <= left:
                row[y] = diag
                brow[y] = 0
            elif up <= left:
                row[y] = up
                brow[y] = 1
            else:
                row[y] = left
                brow[y] = 2

    say_to_heard = [-1] * (n + 1)
    heard_to_say = [-1] * (m + 1)
    say_scores = [0.0] * n

    x, y = n, m
    say_to_heard[n] = m
    heard_to_say[m] = n
    first_matched_y = m
    last_matched_y = 0

    while x > 0 or y > 0:
        move = bt[x][y]
        if move == 0 and x > 0 and y > 0:
            cost = _jamo_sub_cost(say_jamo[x - 1], heard_jamo[y - 1])
            if cost == DP_MATCH_COST:
                say_scores[x - 1] = 1.0
                first_matched_y = min(first_matched_y, y - 1)
                last_matched_y = max(last_matched_y, y)
            elif cost == DP_SIMILAR_COST:
                say_scores[x - 1] = 0.6
                first_matched_y = min(first_matched_y, y - 1)
                last_matched_y = max(last_matched_y, y)
            x -= 1
            y -= 1
        elif move == 1 and x > 0:
            x -= 1
        else:
            y -= 1
        if say_to_heard[x] < 0:
            say_to_heard[x] = y
        if heard_to_say[y] < 0:
            heard_to_say[y] = x

    lead_extra = first_matched_y if last_matched_y > 0 else m
    tail_extra = (m - last_matched_y) if last_matched_y > 0 else 0
    return say_to_heard, heard_to_say, say_scores, lead_extra, tail_extra


def parse_heard(heard: str) -> tuple[list[str], list[float]]:
    """Split phrasing.json's `piece ‖0.28‖ piece` string into pieces and gap durations."""
    parts = _GAP_SPLIT_RE.split(heard)
    pieces = parts[0::2]
    gaps = [float(x) for x in parts[1::2]]
    return pieces, gaps


def _min_pause_for_boundary(word_tok: prosody_prep._WordTok, boundary: dict[str, Any]) -> float:
    tag = word_tok.pause_tag_after
    if tag == 'pause long':
        return MIN_PAUSE_LONG_SEC
    if tag == 'pause':
        return MIN_PAUSE_TAG_SEC
    return MIN_BREAK_SEC


def audit_cue(
    cue_id: str,
    say: str,
    text: str,
    heard: str,
    pmap_entry: dict[str, Any],
    no_pause: bool = False,
    phrasing_ok: bool = False,
) -> list[dict[str, Any]]:
    """Audit one recorded cue and return all detected phrasing/garble/boundary issues."""
    issues: list[dict[str, Any]] = []
    pieces, gaps = parse_heard(heard)

    # 1. Explicit STT error / hex byte garbles.
    if not heard or heard.strip() == '∅' or any(p.startswith('ERR') for p in pieces):
        issues.append({
            'type': 'GARBLE',
            'rule': 'STT_ERR',
            'word': '',
            'detail': f'STT failed or returned empty audio: "{heard}"',
        })
        return issues

    hex_hits = _HEX_GARBLE_RE.findall(heard)
    if hex_hits:
        issues.append({
            'type': 'GARBLE',
            'rule': 'HEX_BYTES',
            'word': ''.join(hex_hits),
            'detail': f'raw hex/replacement bytes in heard text: {" ".join(hex_hits)}',
        })

    # Tokenize `say` identically to prosody_prep so boundary indices match 1-to-1.
    words = prosody_prep._tokenize_say(say)
    prosody_prep._inherit_quotes_from_text(words, text)
    if not words:
        return issues

    say_jamo: list[str] = []
    word_ranges: list[tuple[int, int]] = []
    clitic_positions: list[tuple[int, dict[str, Any]]] = []

    qc_by_idx = {q['word_index']: q for q in pmap_entry.get('quote_clitics', [])}

    for i, w in enumerate(words):
        w_start = len(say_jamo)
        norm_w = _normalize_spoken_text(w.clean)
        w_jamo = to_jamo(norm_w)
        say_jamo.extend(w_jamo)
        w_end = len(say_jamo)
        word_ranges.append((w_start, w_end))

        qc = qc_by_idx.get(i)
        if qc is None and w.quote_clitic_split is not None:
            left_part, right_part = w.quote_clitic_split
            qc = {'word_index': i, 'word': w.clean, 'left': left_part, 'right': right_part, 'rule': 'F6'}
        if qc is not None:
            left_jamo = to_jamo(_normalize_spoken_text(qc['left']))
            if left_jamo:
                clitic_positions.append((w_start + len(left_jamo), qc))

    heard_jamo: list[str] = []
    gap_jamo_pos: list[int] = []
    for k, piece in enumerate(pieces):
        heard_jamo.extend(to_jamo(_normalize_spoken_text(piece)))
        if k < len(gaps):
            gap_jamo_pos.append(len(heard_jamo))

    if not say_jamo or not heard_jamo:
        return issues

    say_to_heard, heard_to_say, say_scores, lead_extra, tail_extra = _align_jamo(say_jamo, heard_jamo)

    # Per-word match ratio for GARBLE and BOUNDARY checks.
    word_matches: list[float] = []
    for s0, s1 in word_ranges:
        if s1 <= s0:
            word_matches.append(1.0)
        else:
            word_matches.append(sum(say_scores[s0:s1]) / (s1 - s0))

    # 2. BOUNDARY: wrong split at start or end of cue.
    first_bad = word_matches[0] < BOUNDARY_EDGE_MIN_MATCH
    last_bad = word_matches[-1] < BOUNDARY_EDGE_MIN_MATCH
    if first_bad or lead_extra >= BOUNDARY_EXTRA_JAMO:
        reason = (
            f'missing first word "{words[0].clean}"'
            if first_bad
            else f'extra leading speech ({lead_extra} jamo) before "{words[0].clean}"'
        )
        issues.append({
            'type': 'BOUNDARY',
            'rule': 'SPLIT_START',
            'side': 'start',
            'word': words[0].clean,
            'extra_leading_jamo': lead_extra,
            'missing_edge_word': first_bad,
            'detail': f'wrong split at start: {reason}',
        })
    if last_bad or tail_extra >= BOUNDARY_EXTRA_JAMO:
        reason = (
            f'missing last word "{words[-1].clean}"'
            if last_bad
            else f'extra trailing speech ({tail_extra} jamo) after "{words[-1].clean}"'
        )
        issues.append({
            'type': 'BOUNDARY',
            'rule': 'SPLIT_END',
            'side': 'end',
            'word': words[-1].clean,
            'extra_trailing_jamo': tail_extra,
            'missing_edge_word': last_bad,
            'detail': f'wrong split at end: {reason}',
        })

    # 3. GARBLE: interior word of `say` with no match in `heard` (skip edge words already flagged BOUNDARY).
    for i, (w, ratio) in enumerate(zip(words, word_matches)):
        if i == 0 and first_bad:
            continue
        if i == len(words) - 1 and last_bad:
            continue
        if word_ranges[i][1] - word_ranges[i][0] == 0:
            continue
        if ratio < GARBLE_MIN_JAMO_MATCH:
            issues.append({
                'type': 'GARBLE',
                'rule': 'NO_MATCH',
                'word_index': i,
                'word': w.clean,
                'syllables': prosody_prep.count_syllables(w.clean),
                'match_ratio': round(ratio, 2),
                'detail': f'word "{w.clean}" unmatched in heard text (match {ratio:.2f})',
            })

    if phrasing_ok:
        return issues

    boundaries = pmap_entry.get('boundaries', [])
    b_by_idx = {b['index']: b for b in boundaries}

    # 4. MISSING_BREAK: REQUIRED boundary or comma/tag with no pause >= threshold.
    for i in range(len(words) - 1):
        b = b_by_idx.get(i, {'index': i, 'kind': 'OPTIONAL', 'rule': 'OPT', 'after_word': words[i].clean})
        w = words[i]
        is_req = b['kind'] == 'REQUIRED'
        has_tag = w.pause_tag_after is not None
        has_comma = w.has_comma and not no_pause and b['kind'] != 'FORBIDDEN'
        if not (is_req or has_tag or has_comma):
            continue
        need = _min_pause_for_boundary(w, b)
        b_say_pos = word_ranges[i][1]
        expected_heard_pos = say_to_heard[b_say_pos]
        got = 0.0
        for gp, gdur in zip(gap_jamo_pos, gaps):
            if abs(gp - expected_heard_pos) <= GAP_ALIGN_TOL_JAMO:
                got = max(got, gdur)
        if got < need:
            rule_name = b['rule'] if is_req else ('TAG' if has_tag else 'COMMA')
            # Only a comma, a pause tag or R1/R2 (stance adverb, quotation) is a defect to fix; R3 without a comma, R4
            # and R5 are advice: they shape `say` before recording, but on a finished take the user did not flag them,
            # and re-taking for them would make the voice choppy (user review, 2026-11-24).
            severity = 'fix' if (has_tag or has_comma or rule_name in ('R1', 'R2')) else 'advise'
            issues.append({
                'type': 'MISSING_BREAK',
                'severity': severity,
                'rule': rule_name,
                'boundary_index': i,
                'after_word': words[i].clean,
                'before_word': words[i + 1].clean,
                'need': need,
                'got': round(got, 2),
                'has_pause_tag': has_tag,
                'detail': (
                    f'missing pause after "{words[i].clean}" ({rule_name}): '
                    f'got {got:.2f}s, need >={need:.2f}s'
                ),
            })

    # 5. FORBIDDEN_BREAK: any pause >= MIN_BREAK_SEC at a FORBIDDEN boundary or inside a word/quote-clitic.
    for gap_idx, (gp, gdur) in enumerate(zip(gap_jamo_pos, gaps)):
        if gdur < MIN_BREAK_SEC:
            continue
        say_pos = heard_to_say[gp]

        # First check sub-word quote-clitic junctions (e.g. 보여준다"는 -> 보여준다 | 는).
        matched_qc = None
        for qc_pos, qc in clitic_positions:
            if abs(say_pos - qc_pos) <= INTRA_WORD_MARGIN_JAMO:
                matched_qc = qc
                break
        if matched_qc is not None:
            issues.append({
                'type': 'FORBIDDEN_BREAK',
                'rule': matched_qc['rule'],
                'boundary_index': matched_qc['word_index'],
                'gap_index': gap_idx,
                'after_word': matched_qc['left'],
                'before_word': matched_qc['right'],
                'intra_word': True,
                'duration': round(gdur, 2),
                'detail': (
                    f'pause {gdur:.2f}s at quote clitic ({matched_qc["rule"]}): '
                    f'"{matched_qc["left"]} | {matched_qc["right"]}"'
                ),
            })
            continue

        # Next find the closest inter-eojeol boundary to `say_pos`.
        if len(words) > 1:
            best_i = min(range(len(words) - 1), key=lambda idx: abs(word_ranges[idx][1] - say_pos))
            dist = abs(word_ranges[best_i][1] - say_pos)
            if dist <= GAP_ALIGN_TOL_JAMO:
                b = b_by_idx.get(best_i)
                if b and b['kind'] == 'FORBIDDEN':
                    issues.append({
                        'type': 'FORBIDDEN_BREAK',
                        'rule': b['rule'],
                        'boundary_index': best_i,
                        'gap_index': gap_idx,
                        'after_word': words[best_i].clean,
                        'before_word': words[best_i + 1].clean,
                        'intra_word': False,
                        'duration': round(gdur, 2),
                        'detail': (
                            f'pause {gdur:.2f}s at FORBIDDEN boundary ({b["rule"]}): '
                            f'"{words[best_i].clean} | {words[best_i + 1].clean}"'
                        ),
                    })
                continue

        # Fallback: pause fell strictly inside a single eojeol far from word boundaries.
        for wi, (s0, s1) in enumerate(word_ranges):
            if s0 + INTRA_WORD_MARGIN_JAMO <= say_pos <= s1 - INTRA_WORD_MARGIN_JAMO:
                issues.append({
                    'type': 'FORBIDDEN_BREAK',
                    'rule': 'INTRA_WORD',
                    'boundary_index': wi,
                    'gap_index': gap_idx,
                    'after_word': words[wi].clean,
                    'before_word': words[wi].clean,
                    'intra_word': True,
                    'duration': round(gdur, 2),
                    'detail': f'pause {gdur:.2f}s inside single word "{words[wi].clean}"',
                })
                break

    return issues


def audit_dir(proj_dir: str, cue_ids: list[str] | None = None) -> dict[str, Any]:
    """Run phrasing audit across `<proj_dir>`, write qa_audit.json, and return the report dict."""
    script_path = os.path.join(proj_dir, 'script.json')
    phrasing_path = os.path.join(proj_dir, 'phrasing.json')
    pmap_path = os.path.join(proj_dir, 'prosody_map.json')

    script = json.load(open(script_path, encoding='utf-8'))
    phrasing = json.load(open(phrasing_path, encoding='utf-8'))
    pmap = json.load(open(pmap_path, encoding='utf-8')) if os.path.exists(pmap_path) else {}

    target_ids = set(cue_ids) if cue_ids else None
    counts = {'MISSING_BREAK': 0, 'FORBIDDEN_BREAK': 0, 'GARBLE': 0, 'BOUNDARY': 0}
    cues_out: dict[str, Any] = {}

    for c in script.get('cues', []):
        cid = c['id']
        if target_ids is not None and cid not in target_ids:
            continue
        p_entry = phrasing.get(cid)
        if not p_entry:
            continue
        say = c.get('say', '')
        text = c.get('text', '')
        heard = p_entry.get('heard', '')

        # Reuse prosody_map.json when it matches the current say; otherwise analyze in memory.
        m_entry = pmap.get(cid)
        if not m_entry or m_entry.get('say') != say:
            m_entry = prosody_prep.analyze_cue(say, text=text)

        issues = audit_cue(
            cue_id=cid,
            say=say,
            text=text,
            heard=heard,
            pmap_entry=m_entry,
            no_pause=bool(c.get('noPause')) or not bool(script.get('autoPause', True)),
            phrasing_ok=bool(c.get('phrasingOk')),
        )
        for iss in issues:
            t = iss['type'] if iss.get('severity', 'fix') == 'fix' else 'ADVICE'
            counts[t] = counts.get(t, 0) + 1

        cues_out[cid] = {
            'take': p_entry.get('take'),
            'say': say,
            'heard': heard,
            'issues': issues,
        }

    total_issues = sum(v for k, v in counts.items() if k != 'ADVICE')
    report = {
        'dir': os.path.abspath(proj_dir),
        'clean': total_issues == 0,
        'counts': counts,
        'total_issues': total_issues,
        'cues': cues_out,
    }
    out_path = os.path.join(proj_dir, 'qa_audit.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
        f.write('\n')
    return report


def print_report(report: dict[str, Any]) -> None:
    """Print a compact table of audit findings to stdout."""
    rows: list[tuple[str, str, str, str]] = []
    for cid, entry in report['cues'].items():
        for iss in entry['issues']:
            kind = iss['type'] if iss.get('severity', 'fix') == 'fix' else 'advice'
            rows.append((cid, kind, str(iss.get('rule', '')), iss['detail']))

    if not any(r[1] != 'advice' for r in rows) and not rows:
        print(f'phrasing_audit: CLEAN ({len(report["cues"])} cues checked)')
        return

    print(f'{"CUE":<6} {"TYPE":<16} {"RULE":<11} DETAIL')
    print('-' * 78)
    for cid, kind, rule, detail in rows:
        print(f'{cid:<6} {kind:<16} {rule:<11} {detail}')
    print('-' * 78)
    c = report['counts']
    print(
        f'phrasing_audit: {report["total_issues"]} issue(s) '
        f'(MISSING_BREAK={c["MISSING_BREAK"]}, FORBIDDEN_BREAK={c["FORBIDDEN_BREAK"]}, '
        f'GARBLE={c["GARBLE"]}, BOUNDARY={c["BOUNDARY"]}) -> qa_audit.json'
    )


def main(argv: list[str]) -> int:
    if not argv:
        print('usage: python3 scripts/narration/phrasing_audit.py <narration_dir> [c01 c02 ...]', file=sys.stderr)
        return 2
    proj_dir = argv[0]
    cue_ids = argv[1:] or None
    report = audit_dir(proj_dir, cue_ids)
    print_report(report)
    return 0 if report['clean'] else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
