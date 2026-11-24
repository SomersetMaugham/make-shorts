"""Pre-recording prosody prep for Korean Chirp 3 HD narration.

Chirp 3 HD skips most plain commas and invents breath pauses inside tightly bound
Korean phrases when spans run long. This module strips quote characters, joins
spaced Hangul decimals, classifies every inter-eojeol boundary (REQUIRED /
FORBIDDEN / OPTIONAL) via kiwipiepy rules R1-R5 and F1-F8, inserts `, [pause short]`
at REQUIRED boundaries, writes prosody_map.json for post-recording audit, and prints
non-blocking pre-recording warnings.

Usage (preview or write map):
  python3 scripts/prosody_prep.py [shorts.json | narration/<sk>/script.json | narration/<sk>] [s1 ...] [--write]
"""
from __future__ import annotations

import dataclasses
import json
import os
import re
import sys
from typing import Any

# ---------- named thresholds and rule tables ----------
R1_MIN_SYLLABLES = 14
R1_ADVERBS = frozenset({
    '실제로', '반대로', '반면', '다만', '특히', '결국', '먼저', '대신',
    '그러니까', '그런데', '그렇다면', '사실', '자', '덕분에',
})
R1_BIGRAM_ADVERBS = frozenset({('예를', '들어')})

R3_LEFT_MIN_SYLLABLES = 12
R3_RIGHT_MIN_SYLLABLES = 8
R3_CONNECTIVE_ENDINGS = frozenset({
    '면', '으면', '지만', '는데', '은데', 'ㄴ데', '니까', '으니까',
    '자', '고', '며', '으며', '어서', '아서', '여서', '어', '아', '여', '해',
})

R4_LEFT_MIN_SYLLABLES = 12
R4_RIGHT_MIN_SYLLABLES = 10
R4_TOPIC_PARTICLES = frozenset({'은', '는', '이', '가', '에서도', '에서는'})

R5_MAX_UNTAGGED_SYLLABLES = 22
R5_MIN_EDGE_SYLLABLES = 5

F1_OVERRIDE_MIN_SYLLABLES = 10
F2_COMPLEMENT_ENDINGS = frozenset({'는지', '은지', 'ㄴ지', '게', '도록'})
F3_MAX_OBJECT_SYLLABLES = 4
F4_MAX_ADVERB_SYLLABLES = 2
F4_SHORT_ADVERBS = frozenset({'결국', '더', '잘', '못', '안', '확', '꼭'})
F6_CLITICS = frozenset({'는', '고', '라는', '라고', '란', '라', '며', '면서', '면'})

WARN_SHORT_CUE_MAX_SYLLABLES = 6
WARN_ANIRA_MIN_SYLLABLES = 30
# One sentence = one breath of meaning (script-writing.md §5, the user 2026-11-24: a long compound sentence makes the
# listener work to follow it). A sentence over 40 spoken syllables, or chaining 2+ clauses, is split into two
# sentences with every word kept. 40 = the HN short's median sentence (38), a starting point to tune, not evidence.
WARN_SENTENCE_MAX_SYLLABLES = 40
WARN_SENTENCE_MAX_LINKS = 1
CLAUSE_LINK_ENDINGS = frozenset({   # Kiwi EC forms that join two clauses ("-어"/"-게"/"-지" are left out: auxiliaries)
    '고', '면', '으면', '면서', '으면서', '는데', '은데', 'ᆫ데', '지만', '니', '으니', '니까', '으니까',
    '며', '으며', '어서', '아서', '여서',
})
_SIMULTANEOUS_RE = re.compile(r'는 동시에')   # "-는 동시에" joins two clauses without an EC
_SENTENCE_END_RE = re.compile(r'(?<=[.?!])\s+')
_TAG_RE = re.compile(r'\[[^\]]*\]')
# Common light/grammatical one-syllable verb stems are not acoustically fragile.
SAFE_SHORT_VV_STEMS = frozenset({
    '하', '되', '오', '가', '보', '주', '쓰', '서', '나', '내', '두', '들', '살',
})

OPEN_QUOTES = '“‘'
CLOSE_QUOTES = '”’'
ALL_QUOTES = '"\'“”‘’'
PAUSE_TAG_TEXT = '[pause short]'

_PAUSE_TAG_RE = re.compile(r'\[(pause(?:\s+(?:short|long))?)\]')
_HANGUL_RE = re.compile(r'[가-힣]')
_DECIMAL_PARTICLE_TAIL = (
    r'(?:에서|으로|까지|부터|보다|이나|정도|퍼센트|은|는|이|가|을|를|의|에|로|도|만|와|과|나|쯤|배)?'
)
_SPACED_DECIMAL_RE = re.compile(
    r'(?<![가-힣])([영공일이삼사오육칠팔구십백천만]+)\s+점\s+([영공일이삼사오육칠팔구]+'
    + _DECIMAL_PARTICLE_TAIL
    + r')(?=$|[\s,.?!;:"\'“”‘’])'
)
_QUOTE_CLITIC_RE = re.compile(r'([가-힣0-9A-Za-z]+)["\'”’]([가-힣]+)')

_KIWI_INSTANCE: Any = None
_KIWI_CHECKED = False
_KIWI_WARNED = False


def _get_kiwi() -> Any:
    """Lazy-load kiwipiepy once so fallback and user-word registration happen cleanly."""
    global _KIWI_INSTANCE, _KIWI_CHECKED, _KIWI_WARNED
    if _KIWI_CHECKED:
        return _KIWI_INSTANCE
    _KIWI_CHECKED = True
    try:
        from kiwipiepy import Kiwi  # type: ignore
    except ImportError:
        if not _KIWI_WARNED:
            _KIWI_WARNED = True
            print(
                'warning: kiwipiepy is not installed; prosody_prep falling back to basic behaviour',
                file=sys.stderr,
            )
        _KIWI_INSTANCE = None
        return None
    kiwi = Kiwi()
    _register_lexicon_words(kiwi)
    _KIWI_INSTANCE = kiwi
    return _KIWI_INSTANCE


def _register_lexicon_words(kiwi: Any) -> None:
    """Teach Kiwi domain proper nouns from pronunciation.json so loanwords tag as NNP."""
    candidates: list[str] = []
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [
        os.path.join(skill_dir, 'references', 'pronunciation.json'),
        os.path.join(os.getcwd(), 'pronunciation.json'),
    ]
    if os.path.exists('project.json'):
        try:
            sd = json.load(open('project.json', encoding='utf-8')).get('skill_dir', '')
            if sd:
                paths.append(os.path.join(sd, 'references', 'pronunciation.json'))
        except (OSError, ValueError):
            pass
    seen: set[str] = set()
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            entries = json.load(open(p, encoding='utf-8')).get('entries', [])
        except (OSError, ValueError):
            continue
        for entry in entries:
            word = str(entry.get('to', '')).strip()
            if word and ' ' not in word and _HANGUL_RE.search(word) and word not in seen:
                seen.add(word)
                candidates.append(word)
    for term in ('오픈에이아이', '챗지피티', '지피티', '에이아이', '퍼플렉시티', '해커뉴스', '파초키'):
        if term not in seen:
            seen.add(term)
            candidates.append(term)
    for word in candidates:
        try:
            kiwi.add_user_word(word, 'NNP', 0.0)
        except Exception:
            pass


def count_syllables(text: str) -> int:
    """Count Hangul syllables because Korean breath-group budgets scale with syllable count."""
    return len(_HANGUL_RE.findall(text))


def join_spaced_decimals(say: str) -> str:
    """Read a decimal point as 쩜, joined to the whole part, the digits after it as one word: `영 점 구구` -> `영쩜 구구`
    (the user, 2026-11-24, notes n017-n019: "0.99는 '영쩜 99'로, 소수점은 '쩜'으로")."""
    return _SPACED_DECIMAL_RE.sub(r'\1쩜 \2', say)


def strip_quotes(text: str) -> str:
    """Strip quote characters from `say` because raw quotes trigger spurious Chirp pauses."""
    return ''.join(ch for ch in text if ch not in ALL_QUOTES)


@dataclasses.dataclass
class _WordTok:
    raw: str
    clean: str
    has_comma: bool
    has_stop: bool
    pause_tag_after: str | None = None
    quote_open_before: bool = False
    quote_close_after: bool = False
    quote_clitic_split: tuple[str, str] | None = None


def _tokenize_say(say: str) -> list[_WordTok]:
    """Split `say` into eojeols while attaching pause tags and quote metadata to boundaries."""
    parts = _PAUSE_TAG_RE.split(say)
    words: list[_WordTok] = []
    # parts alternates: [text, tag_or_missing, text, ...]
    for idx, chunk in enumerate(parts):
        if idx % 2 == 1:
            if words:
                words[-1].pause_tag_after = chunk.strip()
            continue
        for piece in chunk.split():
            if not piece:
                continue
            q_open = False
            q_close = False
            q_clitic: tuple[str, str] | None = None

            work = piece
            while work and work[0] in ALL_QUOTES:
                if work[0] in OPEN_QUOTES or work[0] in '"\'':
                    q_open = True
                work = work[1:]

            # Closing quote stuck before a bound clitic, e.g. 보여준다"는 -> (보여준다, 는)
            m_clitic = _QUOTE_CLITIC_RE.search(work)
            if m_clitic:
                left_part, right_part = m_clitic.group(1), m_clitic.group(2)
                if right_part in F6_CLITICS or len(right_part) <= 2:
                    q_clitic = (left_part, right_part)

            tail_stripped = work.rstrip(',.?!;:')
            if tail_stripped and tail_stripped[-1] in ALL_QUOTES:
                q_close = True

            no_q = strip_quotes(work)
            if not no_q:
                if q_open and words:
                    # Standalone quote char before next word is rare; ignore empty token.
                    pass
                continue
            has_comma = bool(re.search(r'(?<!\d),(?!\d)$', no_q))
            has_stop = bool(re.search(r'[.?!]$', no_q))
            clean = re.sub(r'[,.?!;:]+$', '', no_q)
            clean = re.sub(r'^[,.?!;:]+', '', clean)
            words.append(
                _WordTok(
                    raw=no_q,
                    clean=clean,
                    has_comma=has_comma,
                    has_stop=has_stop,
                    quote_open_before=q_open,
                    quote_close_after=q_close,
                    quote_clitic_split=q_clitic,
                )
            )
    return words


def _inherit_quotes_from_text(words: list[_WordTok], text: str) -> None:
    """Recover opening/closing quote markers from `text` when `say` already stripped quotes."""
    if not text or not any(ch in ALL_QUOTES for ch in text):
        return
    if any(w.quote_open_before or w.quote_close_after or w.quote_clitic_split for w in words):
        return
    text_words = _tokenize_say(text)
    open_targets = [tw.clean for tw in text_words if tw.quote_open_before and tw.clean]
    clitic_targets = [tw.quote_clitic_split for tw in text_words if tw.quote_clitic_split]

    t_idx = 0
    for w in words:
        if t_idx < len(open_targets):
            target = open_targets[t_idx]
            if w.clean == target or (len(target) >= 2 and w.clean.startswith(target[:2])):
                w.quote_open_before = True
                t_idx += 1
    for left_part, right_part in clitic_targets:
        joined = left_part + right_part
        for w in words:
            if w.clean == joined and w.quote_clitic_split is None:
                w.quote_clitic_split = (left_part, right_part)
                break


def _kiwi_morphs_per_word(kiwi: Any, words: list[_WordTok]) -> list[list[tuple[str, str]]]:
    """Run Kiwi on the joined eojeols and map each morpheme back to its exact eojeol index."""
    if kiwi is None or not words:
        return [[] for _ in words]
    spans: list[tuple[int, int]] = []
    pieces: list[str] = []
    cursor = 0
    for w in words:
        token_text = w.raw
        spans.append((cursor, cursor + len(token_text)))
        pieces.append(token_text)
        cursor += len(token_text) + 1
    sentence = ' '.join(pieces)
    tokens = kiwi.tokenize(sentence)
    out: list[list[tuple[str, str]]] = [[] for _ in words]
    w_idx = 0
    for tok in tokens:
        if tok.tag in ('SF', 'SP', 'SS', 'SE', 'SO', 'SW'):
            continue
        while w_idx < len(spans) and tok.start >= spans[w_idx][1]:
            w_idx += 1
        if w_idx < len(spans) and tok.start >= spans[w_idx][0]:
            out[w_idx].append((tok.form, tok.tag))
    return out


def _first_content_tag(morphs: list[tuple[str, str]]) -> str:
    return morphs[0][1] if morphs else ''


def _last_morph(morphs: list[tuple[str, str]]) -> tuple[str, str]:
    return morphs[-1] if morphs else ('', '')


def _has_vcp_before_ec(morphs: list[tuple[str, str]]) -> bool:
    return len(morphs) >= 2 and morphs[-1][1] == 'EC' and morphs[-2][1] == 'VCP'


def _classify_boundaries(
    words: list[_WordTok],
    morphs: list[list[tuple[str, str]]],
    has_kiwi: bool,
) -> list[dict[str, Any]]:
    """Classify every inter-eojeol boundary as REQUIRED, FORBIDDEN, or OPTIONAL (R1-R5, F1-F8)."""
    n = len(words)
    if n <= 1:
        return []

    total_syl = sum(count_syllables(w.clean) for w in words)
    word_syls = [count_syllables(w.clean) for w in words]

    kinds = ['OPTIONAL'] * (n - 1)
    rules = [''] * (n - 1)

    # Track running syllables since previous sentence stop or REQUIRED break for span thresholds.
    span_start_idx = 0

    for i in range(n - 1):
        left = words[i]
        right = words[i + 1]
        lm = morphs[i]
        rm = morphs[i + 1]
        l_form, l_tag = _last_morph(lm)
        r_tag = _first_content_tag(rm)

        left_span = sum(word_syls[span_start_idx : i + 1])
        # Right span up to the next sentence stop or cue end.
        stop_end = n
        for k in range(i + 1, n):
            if words[k].has_stop:
                stop_end = k + 1
                break
        right_span = sum(word_syls[i + 1 : stop_end])

        # Sentence-ending punctuation inside a multi-sentence cue.
        if left.has_stop:
            kinds[i], rules[i] = 'REQUIRED', 'STOP'
            span_start_idx = i + 1
            continue

        # R2: pre-quotation boundary always requires a break.
        if right.quote_open_before:
            kinds[i], rules[i] = 'REQUIRED', 'R2'
            span_start_idx = i + 1
            continue

        # F6: closed quote + bound clitic after space.
        if left.quote_close_after and right.clean in F6_CLITICS:
            kinds[i], rules[i] = 'FORBIDDEN', 'F6'
            continue

        # R7 (the user, 2026-11-24, note n016): "즉" is said, then a pause - "즉, 단어나". The earlier rule forbade the
        # pause after 즉 and the QA loop joined "즉단어나"; the user heard that as wrong.
        if left.clean == '즉':
            kinds[i], rules[i] = 'REQUIRED', 'R7'
            continue

        # R1: sentence-initial stance/discourse adverb in cues >= 14 syllables.
        if i == 0 and total_syl >= R1_MIN_SYLLABLES and left.clean in R1_ADVERBS:
            kinds[i], rules[i] = 'REQUIRED', 'R1'
            span_start_idx = i + 1
            continue
        if (
            i == 1
            and total_syl >= R1_MIN_SYLLABLES
            and (words[0].clean, words[1].clean) in R1_BIGRAM_ADVERBS
        ):
            kinds[i], rules[i] = 'REQUIRED', 'R1'
            span_start_idx = i + 1
            continue

        # Morphological FORBIDDEN rules (F5, F2, F1, F3, F4, F8) when Kiwi is available.
        if has_kiwi:
            # F5: main verb + auxiliary verb VX.
            if r_tag == 'VX' and l_tag in ('EC', 'VV', 'VA', 'VX', 'XSV', 'XSA'):
                kinds[i], rules[i] = 'FORBIDDEN', 'F5'
                continue

            # F2: interrogative/manner complement (-는지/-은지/-ㄴ지/-게/-도록) + governing verb,
            # excluding copula `-인지` clauses (`상황인지 눈치채는`) which act as clause pivots.
            if (
                l_tag == 'EC'
                and l_form in F2_COMPLEMENT_ENDINGS
                and not _has_vcp_before_ec(lm)
                and r_tag in ('VV', 'VA')
            ):
                kinds[i], rules[i] = 'FORBIDDEN', 'F2'
                continue

            # F1: adnominal modifier (ETM) + head noun (NNG/NNP/NNB), with >= 10 syl NNP override.
            if l_tag == 'ETM' and r_tag in ('NNG', 'NNP', 'NNB'):
                if not (r_tag == 'NNP' and left_span >= F1_OVERRIDE_MIN_SYLLABLES):
                    kinds[i], rules[i] = 'FORBIDDEN', 'F1'
                    continue

            # F3: short direct object (<= 4 syl, JKO) + governing verb.
            if (
                l_tag == 'JKO'
                and word_syls[i] <= F3_MAX_OBJECT_SYLLABLES
                and r_tag in ('VV', 'VA')
            ):
                kinds[i], rules[i] = 'FORBIDDEN', 'F3'
                continue

            # F4: short adverb (<= 2 syl, MAG) + modified word.
            if (
                (l_tag == 'MAG' or left.clean in F4_SHORT_ADVERBS)
                and word_syls[i] <= F4_MAX_ADVERB_SYLLABLES
                and r_tag in ('NNG', 'VV', 'VA')
            ):
                kinds[i], rules[i] = 'FORBIDDEN', 'F4'
                continue

            # F8: determiner MM + noun, or numeral + bound counter NNB.
            if (l_tag == 'MM' and r_tag in ('NNG', 'NNP', 'NNB')) or (
                l_tag in ('NR', 'SN') and r_tag == 'NNB'
            ):
                kinds[i], rules[i] = 'FORBIDDEN', 'F8'
                continue

        # Pause before appositive `즉` (paired with F7).
        if right.clean == '즉':
            kinds[i], rules[i] = 'REQUIRED', 'R3'
            span_start_idx = i + 1
            continue

        # R3: explicit comma (unless already blocked by F1) or long connective EC pivot.
        if left.has_comma:
            kinds[i], rules[i] = 'REQUIRED', 'R3'
            span_start_idx = i + 1
            continue
        if has_kiwi and l_tag == 'EC' and r_tag != 'VX':
            if (
                l_form in R3_CONNECTIVE_ENDINGS
                and left_span >= R3_LEFT_MIN_SYLLABLES
                and right_span >= R3_RIGHT_MIN_SYLLABLES
            ):
                kinds[i], rules[i] = 'REQUIRED', 'R3'
                span_start_idx = i + 1
                continue

        # R4: heavy topic/subject (JX/JKS) with >= 12 syl left and >= 10 syl right.
        if has_kiwi and l_tag in ('JX', 'JKS'):
            if (
                any(left.clean.endswith(p) for p in R4_TOPIC_PARTICLES)
                and left_span >= R4_LEFT_MIN_SYLLABLES
                and right_span >= R4_RIGHT_MIN_SYLLABLES
            ):
                kinds[i], rules[i] = 'REQUIRED', 'R4'
                span_start_idx = i + 1
                continue

    # R5: breath-budget relief valve for untagged spans > 22 syllables.
    if has_kiwi:
        _apply_breath_relief(words, word_syls, morphs, kinds, rules)

    boundaries: list[dict[str, Any]] = []
    for i in range(n - 1):
        boundaries.append({
            'after_word': words[i].clean,
            'index': i,
            'kind': kinds[i],
            'rule': rules[i] or 'OPT',
        })
    return boundaries


def _r5_priority(word: _WordTok, morphs: list[tuple[str, str]]) -> int:
    """Rank OPTIONAL boundaries for R5 breath relief: -인지/은지 > JKB > JX/JKS > EC > other."""
    l_form, l_tag = _last_morph(morphs)
    if l_tag == 'EC' and (l_form in ('는지', '은지', 'ㄴ지') or word.clean.endswith(('인지', '은지', '는지'))):
        return 4
    if l_tag == 'JKB' or word.clean.endswith(('에서', '으로', '동시에', '때')):
        return 3
    if l_tag in ('JX', 'JKS'):
        return 2
    if l_tag == 'EC':
        return 1
    return 0


def _apply_breath_relief(
    words: list[_WordTok],
    word_syls: list[int],
    morphs: list[list[tuple[str, str]]],
    kinds: list[str],
    rules: list[str],
) -> None:
    """Split spans exceeding R5_MAX_UNTAGGED_SYLLABLES at the best OPTIONAL midpoint."""
    n = len(words)
    changed = True
    while changed:
        changed = False
        req_edges = [-1] + [i for i, k in enumerate(kinds) if k == 'REQUIRED'] + [n - 1]
        for seg_idx in range(len(req_edges) - 1):
            start_w = req_edges[seg_idx] + 1
            end_w = req_edges[seg_idx + 1]  # inclusive word index
            span_syl = sum(word_syls[start_w : end_w + 1])
            if span_syl <= R5_MAX_UNTAGGED_SYLLABLES:
                continue
            candidates = [j for j in range(start_w, end_w) if kinds[j] == 'OPTIONAL']
            if not candidates:
                continue
            mid = span_syl / 2.0

            def _score(j: int) -> tuple[int, int, float]:
                l_syl = sum(word_syls[start_w : j + 1])
                r_syl = span_syl - l_syl
                balanced = 1 if (l_syl >= R5_MIN_EDGE_SYLLABLES and r_syl >= R5_MIN_EDGE_SYLLABLES) else 0
                prio = _r5_priority(words[j], morphs[j])
                return (balanced, prio, -abs(l_syl - mid))

            best = max(candidates, key=_score)
            kinds[best] = 'REQUIRED'
            rules[best] = 'R5'
            changed = True
            break


def _collect_warnings(
    words: list[_WordTok],
    morphs: list[list[tuple[str, str]]],
    raw_say: str,
    text: str,
) -> list[str]:
    """Emit non-blocking pre-recording warnings for known Chirp/ear-read traps."""
    warnings: list[str] = []
    total_syl = sum(count_syllables(w.clean) for w in words)

    if 0 < total_syl <= WARN_SHORT_CUE_MAX_SYLLABLES:
        sample = (text or raw_say).strip()
        warnings.append(
            f'cue has only {total_syl} syllables ("{sample}") — suggest merging it into the next cue'
        )

    for w, m in zip(words, morphs):
        if len(m) == 2 and m[0][1] == 'VV' and m[1][1] == 'ETM':
            stem = m[0][0]
            if count_syllables(stem) == 1 and stem not in SAFE_SHORT_VV_STEMS and count_syllables(w.clean) <= 2:
                warnings.append(
                    f'one-syllable verb in adnominal form "{w.clean}" ({stem}/VV+{m[1][0]}/ETM) — often garbled by TTS; consider rewording (e.g. 측정한/측정하는)'
                )

    if total_syl > WARN_ANIRA_MIN_SYLLABLES and ('아니라,' in text or '아니라,' in raw_say):
        warnings.append(
            f'"아니라," in a {total_syl}-syllable cue (> {WARN_ANIRA_MIN_SYLLABLES}) — consider splitting into two sentences ("아닙니다.")'
        )
    warnings.extend(long_sentence_warnings(raw_say))
    return warnings


def long_sentence_warnings(say: str) -> list[str]:
    """Sentences too long to follow by ear: over WARN_SENTENCE_MAX_SYLLABLES spoken syllables, or chaining more than
    WARN_SENTENCE_MAX_LINKS clause links. Counted on `say` (numbers in their spoken form, tags removed). Advice for the
    writer: split into two sentences, keeping every word (script-writing.md §5); it never blocks."""
    kiwi = _get_kiwi()
    out: list[str] = []
    for sent in _SENTENCE_END_RE.split(_TAG_RE.sub('', say).strip()):
        sent = re.sub(r'\s+', ' ', re.sub(r'\s*,\s*,', ',', sent)).strip()
        if not sent:
            continue
        syl = count_syllables(sent)
        links = len(_SIMULTANEOUS_RE.findall(sent))
        if kiwi is not None:
            links += sum(1 for t in kiwi.tokenize(sent) if t.tag == 'EC' and t.form in CLAUSE_LINK_ENDINGS)
        over = []
        if syl > WARN_SENTENCE_MAX_SYLLABLES:
            over.append(f'{syl} syllables > {WARN_SENTENCE_MAX_SYLLABLES}')
        if links > WARN_SENTENCE_MAX_LINKS:
            over.append(f'{links} clause links > {WARN_SENTENCE_MAX_LINKS}')
        if over:
            short = sent if len(sent) <= 40 else sent[:38] + '…'
            out.append(f'long sentence ({", ".join(over)}): "{short}" — split it into two sentences, keeping every word')
    return out


def _render_say(
    words: list[_WordTok],
    boundaries: list[dict[str, Any]],
    insert_pauses: bool,
) -> str:
    """Reassemble sanitized `say`, inserting `, [pause short]` at untagged REQUIRED boundaries."""
    out: list[str] = []
    for i, w in enumerate(words):
        token = w.raw
        tag_after = w.pause_tag_after
        if insert_pauses and i < len(boundaries):
            b = boundaries[i]
            if b['kind'] == 'REQUIRED' and b['rule'] != 'STOP' and not tag_after:
                if not token.endswith((',', '.', '?', '!')):
                    token = token + ','
                tag_after = 'pause short'
        out.append(token)
        if tag_after:
            out.append(f'[{tag_after}]')
    return ' '.join(out)


def _quote_clitics_list(words: list[_WordTok]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for i, w in enumerate(words):
        if w.quote_clitic_split:
            left_part, right_part = w.quote_clitic_split
            items.append({
                'word_index': i,
                'word': w.clean,
                'left': left_part,
                'right': right_part,
                'rule': 'F6',
            })
    return items


def analyze_cue(say: str, text: str = '') -> dict[str, Any]:
    """Classify boundaries for an existing `say` without modifying `say` (used by phrasing_audit)."""
    kiwi = _get_kiwi()
    words = _tokenize_say(say)
    _inherit_quotes_from_text(words, text)
    morphs = _kiwi_morphs_per_word(kiwi, words)
    boundaries = _classify_boundaries(words, morphs, has_kiwi=kiwi is not None)
    entry: dict[str, Any] = {'say': say, 'boundaries': boundaries}
    qc = _quote_clitics_list(words)
    if qc:
        entry['quote_clitics'] = qc
    return entry


def prepare_cue(
    say: str,
    text: str = '',
    insert_pauses: bool = True,
    cue_id: str = '',
) -> tuple[str, dict[str, Any], list[str]]:
    """Sanitize `say`, classify boundaries, insert REQUIRED pauses, and return `(say, map_entry, warnings)`.

    When kiwipiepy is unavailable, prints one warning and falls back to today's behaviour
    (returns `say` unchanged while emitting a minimal surface boundary map).
    """
    kiwi = _get_kiwi()
    if kiwi is None:
        words = _tokenize_say(say)
        _inherit_quotes_from_text(words, text)
        boundaries = _classify_boundaries(words, [[] for _ in words], has_kiwi=False)
        entry: dict[str, Any] = {'say': say, 'boundaries': boundaries}
        qc = _quote_clitics_list(words)
        if qc:
            entry['quote_clitics'] = qc
        warnings = _collect_warnings(words, [[] for _ in words], say, text)
        return say, entry, warnings

    dec_say = join_spaced_decimals(say)
    words = _tokenize_say(dec_say)
    _inherit_quotes_from_text(words, text)
    morphs = _kiwi_morphs_per_word(kiwi, words)
    boundaries = _classify_boundaries(words, morphs, has_kiwi=True)
    new_say = _render_say(words, boundaries, insert_pauses=insert_pauses)
    warnings = _collect_warnings(words, morphs, new_say, text)

    entry = {'say': new_say, 'boundaries': boundaries}
    qc = _quote_clitics_list(words)
    if qc:
        entry['quote_clitics'] = qc
    return new_say, entry, warnings


def write_prosody_map(path: str, pmap: dict[str, Any]) -> None:
    """Write prosody_map.json in UTF-8 next to script.json."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(pmap, f, indent=1, ensure_ascii=False)
        f.write('\n')


def _load_cues_from_target(
    target: str, short_keys: list[str]
) -> list[tuple[str, list[dict[str, Any]], str | None]]:
    """Accept a shorts.json, a script.json, or a narration/<sk> directory."""
    if os.path.isdir(target):
        sp = os.path.join(target, 'script.json')
        data = json.load(open(sp, encoding='utf-8'))
        sk = os.path.basename(os.path.abspath(target))
        return [(sk, data.get('cues', []), os.path.join(target, 'prosody_map.json'))]

    data = json.load(open(target, encoding='utf-8'))
    if 'cues' in data:
        out_path = os.path.join(os.path.dirname(os.path.abspath(target)), 'prosody_map.json')
        sk = os.path.basename(os.path.dirname(os.path.abspath(target))) or 'script'
        return [(sk, data['cues'], out_path)]

    keys = short_keys or list(data.keys())
    work_dir = os.path.dirname(os.path.abspath(target))
    result = []
    for sk in keys:
        sh = data[sk]
        out_path = os.path.join(work_dir, 'narration', sk, 'prosody_map.json')
        result.append((sk, sh.get('lines', []), out_path))
    return result


def main(argv: list[str]) -> int:
    write_flag = '--write' in argv
    args = [a for a in argv if a != '--write']

    if args and (os.path.exists(args[0])):
        target = args[0]
        short_keys = args[1:]
    else:
        target = 'shorts.json'
        short_keys = args

    if not os.path.exists(target):
        print(f'prosody_prep: file not found: {target}', file=sys.stderr)
        return 1

    groups = _load_cues_from_target(target, short_keys)
    for sk, cues, out_path in groups:
        pmap: dict[str, Any] = {}
        print(f'=== {sk} ({len(cues)} cues) ===')
        for c in cues:
            cid = c['id']
            raw_say = c.get('say') or c.get('text', '')
            text = c.get('text', '')
            insert_pauses = not bool(c.get('noPause'))
            new_say, entry, warns = prepare_cue(raw_say, text=text, insert_pauses=insert_pauses, cue_id=cid)
            pmap[cid] = entry

            req = [b for b in entry['boundaries'] if b['kind'] == 'REQUIRED']
            forb = [b for b in entry['boundaries'] if b['kind'] == 'FORBIDDEN']
            qcs = entry.get('quote_clitics', [])
            if req or forb or qcs:
                print(f'{cid}: {new_say}')
                for b in req:
                    print(f'  REQUIRED  [{b["rule"]}] after "{b["after_word"]}" (idx {b["index"]})')
                for b in forb:
                    print(f'  FORBIDDEN [{b["rule"]}] after "{b["after_word"]}" (idx {b["index"]})')
                for q in qcs:
                    print(f'  FORBIDDEN [{q["rule"]}] quote-clitic "{q["left"]} | {q["right"]}" (word {q["word_index"]})')
            for w in warns:
                print(f'  WARN {cid}: {w}')

        if write_flag and out_path:
            write_prosody_map(out_path, pmap)
            print(f'wrote {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
