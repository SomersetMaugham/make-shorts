# create-video-shorts 개편 계획: 소스 영상 없는 쇼츠 + script-to-motion 내레이션 이식

작성 2026-11-19. 대상: `~/.claude/skills/create-video-shorts` (이하 **cvs**), 이식 원본:
`~/.claude/skills/script-to-motion` → `~/.hermes/skills/creative/script-to-motion` (이하 **s2m**).

## 0. 확정된 결정 (사용자, 2026-11-19)

| # | 결정 | 의미 |
|---|------|------|
| A | **레이아웃은 전부 풀 비주얼** | 풀 캠·분할(머리 팝아웃) 삭제. 소스 영상 경로(원본 음성 컷) 자체를 걷어 낸다. 원본은 백업으로 보존 |
| B | **오디오는 내레이션만 (s2m 그대로)** | SFX 라이브러리, 라이저, ACE-Step 음악, 합성 대체음, 그 믹스 규칙을 모두 삭제. s2m의 TTS·컷·싱크·승인 절차·무음 규칙을 그대로 가져온다 |
| C | **캡션 타이밍은 s2m 방식 그대로** | 받아쓰기·강제 정렬 없음. 큐 안 글자 위치 추정(player.js `when()`과 같은 가중치)이 기본이고, 정확해야 하는 곳은 에이전트가 `wave.mjs`를 읽고 `at`으로 고정한다 |

## 1. 현재 구조 요약 (조사 결과)

**cvs 파이프라인 (소스 영상 기반)**
`setup.sh` → `analyze.sh`(ingest·Whisper 전사·카메라 검출·시선·줌 스캔) → 계획(`shorts.json`: 소스 타임코드 `a/b`,
레이아웃 `split|fc|fv`, 단어 단위 switch) → `cut.sh`(wav2vec2 정렬 → `cut2.py` J-cut·RMS 끝점 → `verify_voice.py`
재전사) → 병렬: 그래픽 에이전트(HyperFrames, `render_draft.sh`/`render_full.sh`) + `music_takes.py`(ACE-Step) +
`prep.sh`(카메라 클립·RVM 매트·캡션 이벤트) → `finish.sh`(audio.py 믹스, compose 세그먼트, concat, 썸네일) → 납품.

핵심 데이터 계약은 **`cut.json[sk]`** 하나다: `runs[{i,T0,T1,dur,layout,lines,text}]`, `words[{w,line,s,e}]`, `END`,
`lines`, `pieces`, `segs`, 그리고 `<sk>/voice.wav`. compose.py·audio.py·brief_runs.py·report_data.py·thumbnail.py가
모두 이것을 읽는다. → **새 타임라인 생성기가 같은 모양의 cut.json을 쓰면 하류 대부분을 살릴 수 있다.**

**s2m 오디오 (= 이식 대상)**
- TTS: Google Cloud TTS **Chirp 3 HD `ko-KR-Chirp3-HD-Enceladus`** 기본 (gcloud 토큰, 키 없음). Fish Audio(drama-3,
  스킬 `.env`의 키)와 edge-tts는 사용자가 요청할 때만. 속도는 항상 1.
- **녹음은 사용자 결정 후에만** (`tts.mjs --approved`). 그 전에는 무음 플레이스홀더 + 추정 길이로 영상 전체를 완성한다.
- 테이크는 받은 그대로 캐시(`.tts-cache/`, 비결정적이라 재녹음하면 다른 테이크). **코드가 무음·단어 위치를 정하지 않는다**:
  에이전트가 `wave.mjs` 수치(50 ms·10 ms 레벨/ZCR)를 읽고 `cut`·`at`을 script.json에 쓰고, `tts.mjs`·`sync.mjs`가 적용한다.
  `autocut.py`는 초안만 쓴다.
- Google 테이크의 끊어 읽기 오류 → `phrasing-check.mjs`(STT로 쉼 위치만 확인, 허용된 유일한 STT 용도) → `[pause short]`.
- **0.4초 이상 무음 금지** (끝 홀드 `tail` 제외), 기본값 `leadIn 0.3 / gap 0.12 / tail 1.5`.
- 음악·SFX 없음. 외부 음원 사용 금지(Originality 규칙). 시간 늘이기·속도 조절 금지. 숫자 보고 규칙(sound.md §5).
- 산출: `audio/cues/<id>.wav`, `audio/narration.wav|mp3`, `js/cues.js`(VIDEO_DATA), `js/sync.js`, `script.txt`, `generated.json`.

## 2. 설계 충돌과 해법

| 충돌 | cvs 현재 | s2m | 해법 |
|------|----------|-----|------|
| 자율성 | "끝까지 묻지 말고 final.mp4까지" | "녹음은 사용자 결정 후에만" | **2단계로 나눈다.** 1단계: 플레이스홀더로 쇼츠 전체를 완성하고 무음 검토본 + `script.txt`를 넘기며 녹음 여부를 묻는다(이 질문 하나만 허용). 2단계: 승인 후 녹음·후처리·최종 렌더. 녹음 외 판단은 지금처럼 자율 |
| 타임라인 | 소스 컷(J-cut, 40 ms 리드, 조인 ≤150 ms, RMS 끝점) | 큐 + gap + cut | cut 규칙 전부 삭제. 큐 타이밍(`js/cues.js`)이 곧 타임라인 |
| END | 음성 마지막 프레임 | 마지막 큐 + `tail`(1.5 s 끝 홀드) | s2m 그대로. 끝 홀드는 CTA 카드 타이핑 시간이 된다 |
| 캡션 단어 시각 | 강제 정렬된 단어 경계 | 글자 위치 추정 + `at` | 결정 C. `timeline.py`가 player.js와 **같은 가중치 함수**로 추정하고, `at`이 있으면 그 값 사용 |
| 그래픽 타이밍 | 런 기준 초 단위 하드코딩 (단어 시각은 brief_runs.py로 받음) | `when('phrase')` 앵커 | 녹음하면 모든 시각이 바뀐다. 그래픽 코드에서 **구절 앵커**(`W('구절')`)를 쓰고 build 때 cut.json에서 풀도록 바꿔서, 재타이밍이 코드 수정 없이 재빌드·재렌더로 끝나게 한다 |
| 렌더 비용 | 240 fps 풀 렌더 | — | 1단계는 10 fps 드래프트만. 240 fps 풀 렌더는 녹음 승인 후 타임라인이 확정된 뒤 한 번 |
| 언어·폰트 | 영어, Figtree/Geist Mono (한글 글리프 없음) | 한국어 Enceladus | 기본 언어가 한국어가 된다. 캡션·커버·CTA·그래픽에 한글 OFL 폰트(Pretendard, s2m의 sha256 검증 다운로드 방식) 추가. 1~3단어 청크 → 1~3어절 |
| 원본성 | 실제 출처 캡처·공식 로고 사용 | 외부 이미지·로고 금지 | 이번 범위는 오디오뿐이다. 음원 금지만 가져오고 시각 규칙(실제 캡처·로고)은 cvs 규칙을 유지한다고 명시한다 |
| 라우드니스 | 음성 −14 LUFS, 믹스 −14 LUFS / TP −1 | 정규화 규칙 없음(Fish ≈ −22 LUFS 기준) | **미결정 D1** (§8) |

## 3. 새 파이프라인

```
입력: 주제 · 자료 · 대본(있으면 그대로) [+ 사용자 제공 이미지·스크린샷, 전체 영상 URL(있으면)]
 1 setup.sh <폴더>            빈 폴더 OK. .venv(가벼움), node 의존성, gcloud 🔑 확인, work/ 생성
 2 리서치 + 기획               research subagent 팩트체크(2+ 출처) → research.md
                               쇼츠 1~5편, 편마다 "질문 하나, 답 하나"
 3 대본 → 큐                   shorts.json(편별 큐·장면·하이라이트·커버) → narration_init.py가 편마다 narration/<sk>/script.json 생성
                               대본을 내가 쓰면 s2m 대본 규칙 + 첫 청취자 게이트 + 냉정한 청취자 리뷰(subagent)
 4 플레이스홀더 타이밍         node scripts/narration/tts.mjs narration/<sk>     (API 호출 없음, 추정 길이)
                               python scripts/timeline.py <sk>                  → cut.json[sk] + <sk>/voice.wav(무음)
 5 그래픽 팬아웃(병렬)         GFX_BRIEF + brief_runs.py → 장기 그래픽 에이전트 2~4개, 10 fps 드래프트까지
 6 검토본                      finish.sh <sk> --draft → 드래프트 그래픽 + 캡션 + 커버 + CTA, 무음 MP4
                               ★ 사용자에게 script.txt와 검토본을 넘기고 녹음할지 묻는다 (유일한 질문)
 7 녹음 (승인 후)              tts.mjs --approved → wave.mjs --unreviewed → (autocut.py 초안 →) cut 확정
                               → phrasing-check.mjs → [pause short] 재녹음 루프 → at(캡션 키워드·그래픽 앵커)
                               → sync.mjs → wave.mjs 전체 무음 판독 → timeline.py
 8 최종                        build_gfx 재빌드(구절 앵커로 자동 재타이밍) → render_full.sh(240 fps)
                               → finish.sh <sk> NN slug → 썸네일 선택 → report.md, PUBLISH.md, check_publish.py
```

`narration/<sk>/`는 s2m 프로젝트와 같은 배치(script.json, js/cues.js, js/sync.js, audio/, .tts-cache/,
generated.json, script.txt)를 써서 s2m 스크립트를 수정 없이 돌린다. `.tts-cache/`는 재녹음하면 다른 테이크가 나오므로
지우지 않는다고 문서화한다.

## 4. 파일 단위 변경

### 4.1 삭제 (백업 후)
| 분류 | 파일 |
|------|------|
| 소스 수집·분석 | `ingest.py` `transcribe.py` `detect_camera.py` `gaze.py` `zoomscan.py` `faces.py` `analyze.sh` |
| 시선·얼굴 시트 | `eyesheet.py` `eyecrop.py` `rawsheet.py` `sheet3.py`(용도 확인 후) |
| 소스 컷 | `align.py` `align_lines.py` `cut2.py` `verify_voice.py` `cut.sh` |
| 카메라·매트 | `cam_prep.py` `matte_rvm.py` `matte_gpu.py` |
| 장편 연동 | `import_longform.py` `build_raw_map.py` `clean_from_stem.py` |
| 오디오 | `audio.py`(→ 축소 대체) `sfxlib.py` `sfx_library.py` `music.py` `music_gen.py` `music_takes.py` |
| 에셋 | `assets/sfx/` (약 40 MB, manifest 포함) `assets/models/` (얼굴 모델) |
| setup.sh 블록 | RVM 다운로드, SFX 라이브러리 빌드, ACE-Step 설치(약 37 GB), faster-whisper·mediapipe·torch·onnxruntime 설치 |

삭제 전에 `grep`으로 남는 파일에서 import·호출이 없는지 확인한다(예: `align.spoken`, `sfxlib`, `config.SRC`, `cam/plan.json`).
기계에 이미 깔린 `~/.venvs/music-gen`, `~/.cache/pro-edit-models`는 **davinci-resolve-pro-edit와 공유**하므로 건드리지 않는다.

### 4.2 이식 (s2m → cvs `scripts/narration/`, 내용 수정 없이 복사)
- `tts.mjs` `wave.mjs` `sync.mjs` `phrasing-check.mjs` `autocut.py`
- `lib/env.mjs` `lib/generated.mjs` `lib/phrases.mjs` `lib/scriptsig.mjs` (+ `wave.mjs`가 쓰는 `lib/browser.mjs`는 아래 참고)
- `package.json`은 내레이션에 필요한 것만 남긴 최소본
- `narration/SOURCE.md`: 원본 경로, 복사 날짜, 파일별 sha256, **로컬 수정 목록**. `scripts/narration/sync_upstream.sh`:
  s2m 원본과 비교해 바뀐 파일을 알려 준다(자동 덮어쓰기 없음)
- 스킬 `.env` (Fish 키용, git 제외). `env.mjs`의 `SKILL_ENV` 경로가 `scripts/narration/lib/../../.env` =
  `scripts/.env`로 바뀌므로 위치를 확인해 문서에 적는다. 키 값은 복사하지 않는다

**유일한 로컬 수정 후보**: `wave.mjs`의 전체 음 모드는 `index.html`을 브라우저로 열어 클립 소리를 합친다. cvs에는
`index.html`도 클립도 없으므로, `index.html`이 없으면 `audio/narration.wav`만 읽는 분기를 넣는다(Playwright 의존 제거).
`--cue`/`--unreviewed`는 이미 브라우저 없이 동작한다. 수정은 SOURCE.md에 기록한다.

### 4.3 문서 이식
- `references/narration.md` (신규): s2m SKILL.md §3·§4 내레이션 부분 + `sound.md` + `google-tts.md` +
  `fish-audio.md` §2~§3(큐 나누기, `say` 쓰기) + `edge-tts-voice.md` 요지. 규칙 문장은 바꾸지 않고, 경로만 cvs에 맞춘다
- `references/script-writing.md` (s2m에서 복사): 대본을 에이전트가 쓸 때의 규칙. **D4에서 확정**
- SKILL.md 상단에 s2m의 "첫 청취자" STOP 박스와 "쿠션" 규칙의 요약 + 링크

### 4.4 신규 스크립트
| 파일 | 역할 |
|------|------|
| `narration_init.py <sk…>` | shorts.json의 편별 큐 → `narration/<sk>/script.json` (tts 기본값: google/Enceladus, leadIn 0.3, gap 0.12, tail 1.5). 이미 있으면 `text`/`say`/`gapAfter`만 병합하고 `cut`·`at`은 보존 |
| `timeline.py <sk>` | `js/cues.js` + `js/sync.js` + `audio/narration.wav` → **cut.json[sk]** (기존 스키마) + `<sk>/voice.wav`(48 kHz, 큐 시작 정렬). 런: 큐 → 장면, 장면 전환 switch는 구절 기준 → 프레임 스냅. 단어: 큐 text를 어절로 나누고 player.js `weight()`와 같은 정규식으로 시각 추정, `sync.js`에 구절이 있으면 그 시각을 고정점으로 사이를 보간. 각 단어에 `est: true/false` 표시 |
| `check_narration.py <sk>` | 납품 게이트: unreviewed 테이크 없음, placeholder 없음(`--draft` 제외), sync.js가 script.json `at`과 일치, cues.js가 script.json과 같은 서명. 무음 판정은 하지 않는다(에이전트 몫, wave.mjs) |
| `mix.py <sk>` (audio.py 대체) | `stems/voice.wav` + `mix.wav`. 내레이션 외 소리 없음. 라우드니스는 D1 결과에 따름 |

### 4.5 수정
| 파일 | 변경 |
|------|------|
| `setup.sh` | 소스 영상 탐색·하드링크·init_project 프로브 제거. 빈 폴더 허용. `.venv`는 numpy·scipy·soundfile·pyloudnorm·pillow·opencv만. `scripts/narration`에서 `npm ci`. `gcloud auth print-access-token` 확인 결과를 🔑 줄로 출력(실패하면 `! gcloud auth login` 안내) |
| `init_project.py` / `config.py` | source·camera·asr 항목 제거. 남는 것: fps 60, 언어, 폰트, 전체 영상 URL/제목, CTA 모드 |
| `compose.py` (46 KB, 가장 큰 수정) | split·fc 경로, 카메라 카드, 매트, 지오메트리 제거 → fv 전용. 캡션 위치는 fv 하단 1/3(y 1290–1560)과 콘텐츠가 적을 때 위쪽(365–634), outro는 CTA 위. 한글 폰트로 캡션·칩·커버·CTA. 어절 단위 청크와 줄바꿈. `--draft`(10 fps 그래픽을 60 fps로 홀드, 무음 또는 플레이스홀더 음). 믹스 입력은 voice만 |
| `prep.sh` | cam_prep·matte·분할 프레임 체크 제거 → `compose.py --events-only`만 (CTA 이벤트도 SFX가 없으므로 캡션만 남는지 확인) |
| `finish.sh` | check_text → **check_narration** → mix.py ∥ 세그먼트 → concat → verify_final → 썸네일. music_takes·music_takes MP3 납품 제거, stems는 `voice.wav` 하나. `--draft` 모드 추가 |
| `brief_runs.py` | 단어 시각에 `est` 표시. 그래픽 코드가 쓸 구절 앵커 목록 출력 |
| `build_gfx_common.py` / `build_gfx.py` | `W('구절', run)` 앵커를 cut.json에서 풀어 런 기준 초로 바꾼다. `sfx=` 필드와 `gfx/sfx_events.json` 작성 제거(남아 있으면 경고). 한글 폰트를 gfx 프로젝트에 복사 |
| `assets/gfx/engine.js` | 폰트 스택에 한글 폰트 추가(Figtree 뒤 폴백 또는 한국어 모드에서 우선). 에셋 경로만, 연출 로직은 그대로 |
| `thumbnail.py` | "분할 + 얼굴" 우선순위 제거 → 풀 비주얼에서 주제가 크게 보이는 정지 프레임. 입 모양 조건 제거 |
| `report_data.py` | 싱크·컷·시선·SFX·음악 항목 제거 → TTS 공급자·음성·테이크 id·cut 범위·at·재녹음 이력·무음 판독 결과·라우드니스 |
| `verify_final.py` | 1080x1920 / 60 fps / AAC 48 kHz 확인 유지. 오디오 기준은 D1에 따름 |
| `check_text.py` | 한글 텍스트 검사 확인(모지바케 판별이 한글을 오탐하지 않는지) |
| `check_publish.py` | CTA 줄이 D2 결과에 맞게. 한국어 카피일 때의 길이·해시태그 규칙 확인(D3) |
| `render_draft.sh` / `render_full.sh` / `draftsheet.py` / `sheet.py` | 변경 없음 예상. 확인만 |

### 4.6 사양·문서 재작성
- **SKILL.md**: description을 "주제·자료·대본으로 녹화 없이 9:16 쇼츠를 만든다, 내레이션은 Google Chirp 3 HD"로 다시 쓴다
  (트리거: 쇼츠·릴스·틱톡을 주제나 대본으로 만들어 달라는 요청. "녹화본으로"는 더 이상 트리거가 아님). Inputs, Workflow,
  "틀리기 쉬운 것", Files를 새 파이프라인에 맞춘다
- **editing-spec.md**: §1 싱크·전사 → 내레이션(s2m), §2 컷 → 큐 타임라인, §3 시선 → 삭제, §4 세 레이아웃 → 풀 비주얼 하나
  + **장면 유형 순환 규칙**(아래), §5 그래픽 → 소스 영상에서 따오는 푸티지 조항 삭제, §6 캡션 위치 fv 기준, §7 오디오 →
  s2m 규칙 전문으로 교체, §8 리포트 항목 갱신, 납품물에서 sfx·riser·music stem과 music_takes 제거
- **장면 유형 순환 규칙** (분할·풀 캠이 빠진 자리를 메우는 것): 훅은 가장 강한 시각(숫자·실제 출처·결과물), 런 ~8 s 이하
  유지, 연속 두 런이 같은 장면 유형(실제 캡처 / 제품 UI / 개념 다이어그램 / 키 넘버 / 로고 락업)을 쓰지 않는다,
  아웃트로는 CTA 카드 + 요약 한 줄
- **pipeline.md / speed.md / graphics.md / lessons.md**: 카메라·매트·시선·SFX·음악 절 삭제, 내레이션 단계와 재타이밍 절 추가
- **examples/**: `harness-engineering/`은 그래픽 품질 기준으로만 남기고 "카메라 레이아웃·오디오 부분은 이 스킬에 해당 없음"이라고
  README 머리에 명시. 첫 실사용 후 소스 없는 레퍼런스 예시(`examples/<첫 주제>/`)를 추가

## 5. 작업 순서

| 단계 | 내용 | 산출·검증 |
|------|------|-----------|
| P0 | 작업 공간: 설치된 cvs를 이 폴더(`~/project/skills/create-video-shorts`)로 복사 → `git init` → 원본 그대로 첫 커밋(기준선). 설치본은 `~/.claude/skills/create-video-shorts.bak-20261119`로 보존할 계획만 세우고 **교체는 P7에서 사용자 확인 후** | 기준선 커밋 |
| P1 | 내레이션 이식: `scripts/narration/` 복사, SOURCE.md, `npm ci`, wave.mjs 분기 | 빈 테스트 프로젝트에서 `tts.mjs`(플레이스홀더), `wave.mjs` 전체/`--cue`, `sync.mjs`가 오류 없이 돈다 |
| P2 | 삭제: §4.1 파일·에셋·setup 블록 | `grep -rE "sfxlib|music_|matte|gaze|cam_prep|clean48|align_lines|import_longform" scripts references SKILL.md` 결과 0 |
| P3 | 신규: narration_init.py, timeline.py, check_narration.py, mix.py | 픽스처 단위 테스트: player.js `about()`과 timeline.py 추정이 같은 큐에서 1 ms 이내 일치(node로 player.js 함수 실행해 대조, 무작위 큐 수백 개), cut.json 스키마가 기존 하류 키를 모두 가짐 |
| P4 | 하류 수정: compose(fv 전용·한글·draft), prep/finish, build_gfx 앵커, thumbnail, report_data, verify_final | 플레이스홀더 2~3큐 짧은 쇼츠로 `finish.sh --draft` 통과, 캡션 한글 렌더 프레임을 직접 확인 |
| P5 | 문서: SKILL.md, editing-spec.md, narration.md, script-writing.md, pipeline/speed/graphics/lessons, examples README | 문서에 남은 삭제 기능 언급 grep 0, 모든 상대 경로 링크가 실제 파일을 가리킴 |
| P6 | 종단 시험 | (a) `"narration": false`로 무비용 전체 실행 (b) **사용자 승인을 받고** Google 테이크 실녹음 1편: cut·at·phrasing-check·재타이밍·240 fps 렌더·납품·check_publish까지 |
| P7 | 설치: 백업 후 `~/.claude/skills/create-video-shorts`를 새 버전으로 교체(심볼릭 링크 또는 복사). **사용자 확인 후 실행** | 새 세션에서 스킬 description 트리거 확인 |

**위임 판단 (전역 지침)**: P2(삭제·참조 정리)와 P5 중 기계적 문서 가지치기는 반복 작업이라 agy 위임 손익분기를 넘는다.
전용 브랜치에서 `flash` 이상, 좁은 grant(`--add-dir` + 이 폴더 `write_file`)로 맡기고 `git diff`로 직접 검수한다.
P3·P4(timeline.py, compose.py)와 사양 재작성은 판단이 많아 직접 한다. P6 실녹음은 사용자 쿼터라 반드시 승인 후.

## 6. 위험과 대응

| 위험 | 대응 |
|------|------|
| 녹음 후 런 길이가 바뀌어 그래픽이 어긋남 | 구절 앵커(`W()`)로 그래픽 시각을 데이터에서 푼다. 하드코딩된 초 단위를 쓰면 build_gfx가 경고 |
| 글자 위치 추정 캡션이 실제 발화와 어긋남 (결정 C의 비용) | 키워드 칩과 구절 앵커에는 `at`을 반드시 설정하는 것을 규칙으로 하고, check_narration이 칩 단어에 `at`이 없으면 경고. 나머지 청크는 추정 허용 |
| Google 테이크 비결정성 | `.tts-cache/` 보존 규칙, 재녹음은 사용자 결정, `--only`로 줄 단위 |
| s2m 원본이 계속 바뀜 (hermes 쪽에서 갱신) | 복사 + SOURCE.md sha256 + sync_upstream.sh로 차이만 알림 |
| 한글 폰트 누락 시 두부(□) | check_text.py에 글리프 커버리지 검사 추가(폰트 cmap 대조) |
| `scripts/.env` 위치 이동으로 Fish 키를 못 찾음 | tts.mjs 🔑 줄로 확인. Fish는 요청할 때만 쓰므로 기본 경로엔 영향 없음 |
| 공유 모델 폴더 오삭제 | `~/.cache/pro-edit-models`, `~/.venvs/music-gen`은 손대지 않는다고 명시 |

## 7. 범위 밖 (이번에 하지 않음)
- 브랜드·디자인 시스템("Leon YouTube"), PUBLISH의 Skool 커뮤니티 문구 교체 (D5 참고)
- 소스 영상 모드 유지 (결정 A로 제외. 필요하면 백업에서 되살린다)
- s2m의 시각 규칙(원본성, 시네마틱 룩, 브라우저 런타임) 이식

## 8a. 결정 결과 (사용자, 2026-11-19) — §8 표보다 우선

| # | 결정 | 반영 |
|---|------|------|
| D1 | 라우드니스 정규화 **남김** | mix.py: 게인 + 리미터만, −14 LUFS 통합 / TP ≤ −1 dBFS. 타이밍·속도 변경 없음 |
| D2 | **원본 동영상에 기대는 부분 모두 제거** | "Watch the full video" CTA 카드(`cta_mode`, `cta_keyword` 포함), PUBLISH의 전체 영상 줄·Related video·oEmbed 조회, 장편 PUBLISH.md 탐색, check_publish의 CTA 검사 삭제. 아웃트로는 요약 한 줄로 끝난다(끝 홀드 `tail`) |
| D3 | **모든 산출물 한국어 기본** | 대본·`say`·캡션·커버·그래픽 문구·리포트·PUBLISH 카피. 캡션 청크는 1~3어절. 영어는 요청 시(음성도 바꿈) |
| D4 | s2m 대본 규칙 **함께 이식** | `references/script-writing.md` 복사 + SKILL.md에 첫 청취자 STOP 박스·쿠션·"짧은 영상은 질문 하나 답 하나" |
| D5 | 브랜드·커뮤니티 문구 **모두 제거** | Skool 두 줄, 채널명, "Leon" 인용·개인 규칙 표현, 화자 개인 아이콘 타일·재생 타일, `references/design-system/`(Leon YouTube 번들), Leon 브랜드가 박힌 예시(`examples/harness-engineering/`, paper 예시, `PUBLISH_example.md`, `report_example.md`). 엔진의 graphite·glass 룩은 **스킬 자체의 중립 기본 테마**로 남기고 이름만 바꾼다(`references/theme.md`에 토큰 정리). 근거 없이 사람 이름이 붙은 규칙은 규칙 문장만 남긴다 |

## 8. 남은 결정 (구현 전에 정할 것) — 8a로 모두 결정됨

| # | 질문 | 권장 | 이유 |
|---|------|------|------|
| D1 | 최종 라우드니스 정규화(−14 LUFS, TP ≤ −1 dBFS)를 남길까? s2m에는 없다 | **남긴다(게인만)** | 쇼츠 플랫폼이 −14 근처로 맞추므로 −22 LUFS 내레이션은 작게 들린다. 게인과 리미터만이라 s2m이 금지하는 속도·타이밍 변경이 아니다 |
| D2 | 원본 장편이 없으니 "Watch the full video" CTA는 어디로 보내나? | **URL을 주면 전체 영상 카드, 없으면 채널 구독/팔로우 카드** | 지금 규칙은 장편이 있다는 전제다. 가리킬 영상 없이 쓰면 거짓 CTA가 된다 |
| D3 | 언어: Enceladus가 한국어 음성이므로 캡션·커버·CTA·PUBLISH 카피를 한국어로 할까? | **기본 한국어, 요청 시 영어(음성도 변경)** | 음성과 자막 언어가 같아야 한다 |
| D4 | s2m의 대본 작성 규칙(첫 청취자 게이트, 쿠션, 구어체, 냉정한 청취자 리뷰)도 함께 가져올까? | **가져온다** | 소스가 없으면 대본을 에이전트가 쓰고, 이 규칙들은 TTS용 `say` 쓰기와 붙어 있다 |
| D5 | Leon 채널 브랜드·PUBLISH 문구를 그대로 둘까? | 이번엔 그대로, 별도 작업으로 | 요청 범위 밖이지만 사용자 채널이 다르면 손봐야 한다 |
| D6 | 1단계 검토본을 MP4로 렌더할까? | **한다(10 fps 그래픽, 무음 + 캡션)** | s2m은 사용자가 영상을 본 뒤 녹음을 결정한다. 쇼츠는 브라우저 플레이어가 없으니 MP4가 그 역할을 한다 |

## 9. 진행 상황 (2026-11-19)

| 단계 | 상태 | 검증 |
|------|------|------|
| P0 기준선 | 완료 | 설치본 그대로 첫 커밋, 브랜치 `rework` |
| P1 내레이션 이식 | 완료 | 플레이스홀더 tts·wave·sync가 브라우저 없이 동작. 로컬 수정 2건(wave.mjs, env.mjs)은 SOURCE.md |
| P2 삭제 | 완료 | 삭제 기능 언급 grep: 부정문만 남음 |
| P3 신규 스크립트 | 완료 | timeline.py 추정 = player.js about() (500건, 최대 0.5 ms) |
| P4 하류 수정 | 완료 | 빈 폴더 종단 시험: setup → prep → draft → (합성 톤 테이크) cut·at·sync → 재빌드 → 240 fps → finish → 썸네일 → 리포트 → check_publish. 버그 2건 수정(런 경계 내림, 리미터 후 음량 보정) |
| P5 문서 | 완료 | 참고 문서 4개 + 템플릿 + 예시는 agy 초안(Gemini 3.8 Flash) → 검수·수정. 예시 그래픽은 빌드·드래프트 렌더로 확인 |
| P6 실녹음 시험 | **대기: 사용자 승인 필요** (Google TTS 쿼터) |
| P7 설치 교체 | **대기: 사용자 확인 필요** |
