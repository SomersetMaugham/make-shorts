#!/bin/bash
# Final assembly of one short in one call: the text and narration gates, the mix and every compose segment in parallel,
# then the stream-copy concat, verify_final, and delivery into ../edit/short-NN_<slug>/. Alongside the concat it renders the
# thumbnail candidates the graphics marked (gfx/thumbs.json; clean frames, one seek each) -> chk/<sk>_thumbs.png.
#   bash scripts/finish.sh s1 [NN slug]        e.g. bash scripts/finish.sh s1 01 harness-10x
#   bash scripts/finish.sh s1 --draft          the review copy before recording: the 10 fps draft graphics, placeholder
#                                              narration allowed -> chk/<sk>_draft.mp4 (hand it over with script.txt)
# Segments are cached by their inputs: after an edit only the runs that changed are re-rendered (seconds to a minute).
# Run it only after every render_full.sh (or render_draft.sh for --draft) has finished for this short's graphics.
export PYTHONUTF8=1
set -u
cd "$(dirname "$0")/.."
PY=../.venv/Scripts/python.exe; [ -f "$PY" ] || PY=../.venv/bin/python
sk=$1; shift
DRAFT=; [ "${1:-}" = "--draft" ] && { DRAFT=--draft; shift; }
NN=${1:-}; SLUG=${2:-}
mkdir -p logs chk
t0=$(date +%s)
since() { echo "[$(( $(date +%s) - t0 ))s] $*"; }
# garbled or untypeable on-screen text, then the narration state, stop everything before a frame is rendered
"$PY" scripts/check_text.py $sk || { echo "fix the text above (check_text.py docstring), then re-run finish.sh"; exit 1; }
"$PY" scripts/check_narration.py $sk $DRAFT || { echo "fix the narration above (references/narration.md), then re-run finish.sh"; exit 1; }
"$PY" scripts/mix.py $sk > logs/mix_$sk.log 2>&1 &
AU=$!
"$PY" scripts/compose.py $sk --segments --no-concat $DRAFT 2>&1 | tee logs/segments_$sk.log | grep -E "segment|FAILED|MISMATCH|missing"
SEG=${PIPESTATUS[0]}
wait $AU || { echo "mix failed:"; tail -20 logs/mix_$sk.log; exit 1; }
cat logs/mix_$sk.log
[ "$SEG" -eq 0 ] || { echo "segments failed (see logs/segments_$sk.log)"; exit 1; }
if [ -n "$DRAFT" ]; then
  "$PY" scripts/compose.py $sk --concat --draft && cp $sk/draft_video.mp4 chk/${sk}_draft.mp4
  since "$sk review copy -> chk/${sk}_draft.mp4 (narration/$sk/script.txt is the script). Hand both over and ask whether to record."
  exit 0
fi
"$PY" scripts/thumbnail.py $sk > logs/thumbs_$sk.log 2>&1 &
TH=$!
"$PY" scripts/compose.py $sk --concat
"$PY" scripts/verify_final.py $sk/final_video.mp4 chk/${sk}_final.png 2>&1 | grep -vE "^\s*$" | tail -6
wait $TH && grep -E " s  run " logs/thumbs_$sk.log || { echo "thumbnail candidates: none rendered:"; tail -3 logs/thumbs_$sk.log; }
if [ -n "$NN" ] && [ -n "$SLUG" ]; then
  D=../edit/short-${NN}_${SLUG}; mkdir -p "$D/stems"
  cp $sk/final_video.mp4 "$D/final.mp4"; cp $sk/stems/voice.wav "$D/stems/"
  cp narration/$sk/script.txt "$D/script.txt"
  since "delivered $D/final.mp4 + stems/voice.wav + script.txt (pick the thumbnail: thumbnail.py $sk --pick <t> $NN $SLUG; write report.md there and the PUBLISH.md section)"
fi
since "$sk finished. LOOK at chk/${sk}_final.png and chk/${sk}_thumbs.png"
