#!/bin/bash
# The timeline of one or more shorts in one call, after the narration changed (placeholders, a recording, a cut, an "at"):
#   narration_init.py -> say_lint.py -> tts.mjs (records NOTHING: without --approved new cues stay silent placeholders) -> sync.mjs
#   -> timeline.py (cut.json + <sk>/voice.wav) -> captions.json
#   bash scripts/prep.sh s1 [s2 ...]          (all shorts in shorts.json if none given)
# Recording is never done here: it waits for the user's decision (tts.mjs <dir> --approved, references/narration.md).
export PYTHONUTF8=1
set -u
cd "$(dirname "$0")/.."
PY=../.venv/Scripts/python.exe; [ -f "$PY" ] || PY=../.venv/bin/python
NODE=$("$PY" -c "import sys; sys.path.insert(0,'scripts'); import config; print(config.NODE)")
mkdir -p logs
SKS="$*"; [ -n "$SKS" ] || SKS=$("$PY" -c "import json; print(' '.join(json.load(open('shorts.json', encoding='utf-8'))))")
"$PY" scripts/narration_init.py $SKS || exit 1
"$PY" scripts/say_lint.py $SKS    # where the spoken say will split or join wrongly: fix in shorts.json before recording
for sk in $SKS; do
  "$NODE" scripts/narration/tts.mjs narration/$sk > logs/tts_$sk.log 2>&1 || { echo "tts.mjs failed for $sk:"; tail -20 logs/tts_$sk.log; exit 1; }
  grep -E "^narration|^🔑|^⏸|^👂|^⚠" logs/tts_$sk.log
  "$NODE" scripts/narration/sync.mjs narration/$sk 2>&1 | tail -3
done
"$PY" scripts/timeline.py $SKS || exit 1
for sk in $SKS; do "$PY" scripts/compose.py $sk --events-only 2>&1 | tail -1; done
echo "prep done. Brief the graphics with: python scripts/brief_runs.py <sk>"
