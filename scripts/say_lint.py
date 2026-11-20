"""Before recording: the places in each cue's `say` that a listener will hear split or joined differently from the
words on the page (references/narration.md §3). It reads narration/<sk>/script.json (after narration_init.py, so the
lexicon and the comma pauses are in) and prints a suggested say; it changes nothing and never blocks — the say in
shorts.json is still yours to fix. prep.sh runs it.
usage: python scripts/say_lint.py [s1 s2 ...]

What it looks for (each from a review note the user had to write):
- a one-syllable word that sounds like a particle or ending (인, 은, 도 …) after a word with no pause between:
  "엔쪽 인 원자" was heard "엔쪽인"
- "즉" with no pause before it: "손 즉" was heard "손즉"
- spelled-out letters with spaces: "지 알 피 오" broke as "지 ‖ 알피오" (join them: "지알피오")
- digits, Latin letters, brackets or symbols left in say (narration.md: say is spoken Hangul)"""
import json, re, sys

sys.path.insert(0, 'scripts'); import config as C

# one-syllable words that sound like a particle or an ending: after a word with no pause they are heard as part of it
# ("엔쪽 인 원자" -> "엔쪽인", -인 the ending). Other one-syllable words (손, 빈, 맨) were heard fine on the PN short.
# A word before it that already ends in a particle ("실리콘에 인 원자") was heard apart, so it is not flagged.
ENDING = set('인 은 는 을 를 의 도 로 와 과 에 요 고 지 만 며 면 서 야 여 랑 나 든 엔'.split())
LETTERS = set('에이 비 씨 디 이 에프 지 에이치 아이 제이 케이 엘 엠 엔 오 피 큐 알 에스 티 유 브이 더블유 엑스 와이 제트'.split())
TAG = re.compile(r'\[[^\]]*\]')


def lint(say):
    out = []
    toks = TAG.sub(' ‖ ', say).split()
    for i, t in enumerate(toks):
        w = re.sub(r'[,.?!]', '', t)
        prev = toks[i - 1] if i else ''
        paused = not prev or prev == '‖' or prev.endswith((',', '.', '?', '!'))
        if w == '즉' and not paused:
            out.append(('즉', f'"{prev} 즉" is heard as one word: "{prev}, [pause short] 즉"'))
        elif w in ENDING and not paused and not re.search(r'[에은는을를의가이도로와과서]$', prev) and i + 1 < len(toks):
            out.append((w, f'"{prev} {w}" may be heard as "{prev}{w}": pause before it ("{prev}, [pause short] {w}"), '
                           f'join it if it is one word ("{prev}{w}"), or reword'))
    run = []
    for t in toks + ['']:
        if t in LETTERS: run.append(t); continue
        if len(run) >= 2 and not set(run) <= {'이', '오'}:
            out.append((' '.join(run), f'spelled letters with spaces break apart: "{"".join(run)}"'))
        run = []
    left = re.findall(r'[0-9A-Za-z%°℃/()+=<>~&#@*^]+', TAG.sub('', say))
    if left: out.append((' '.join(left), f'not spoken Hangul: {", ".join(left)} — write how it is read (narration.md)'))
    return out


if __name__ == '__main__':
    S = json.load(open('shorts.json', encoding='utf-8'))
    n = 0
    for sk in sys.argv[1:] or list(S):
        cues = json.load(open(f'{C.ndir(sk)}/script.json', encoding='utf-8'))['cues']
        for c in cues:
            for word, msg in lint(c['say']):
                n += 1; print(f'👂 {sk} {c["id"]}: {msg}')
    print(f'say_lint: {n} place(s) to read again before recording' if n else 'say_lint: nothing found')
