#!/bin/bash
# One-time setup for a shorts project. No recording is needed: the shorts are made from a topic, material or a script,
# narrated with script-to-motion's TTS tools (scripts/narration, Google Chirp 3 HD by default).
#   bash <skill>/scripts/setup.sh [<project_folder>]      (default: the current folder; it may be empty)
# - creates <project>/.venv (local, nothing system-wide)
# - downloads the Korean typeface (Pretendard, SIL OFL 1.1, sha256-checked) into the skill once
# - creates <project>/work/ with the scripts, the narration tools, the graphics engine, the fonts and project.json,
#   and <project>/edit/ for the deliverables
# - checks the narration sign-in (gcloud) and prints it as a 🔑 line
export PYTHONUTF8=1   # Python reads/writes UTF-8 on Windows too
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
ARG="${1:-.}"
[ -d "$ARG" ] || mkdir -p "$ARG"
PROJ="$(cd "$ARG" && pwd)"
command -v uv >/dev/null || { echo "ERROR: uv not found (https://docs.astral.sh/uv/)"; exit 1; }
command -v ffmpeg >/dev/null || { echo "ERROR: ffmpeg not found"; exit 1; }
command -v node >/dev/null || { echo "ERROR: node (22+) not found"; exit 1; }
SKILL_ABS="$(cd "$SKILL" && (pwd -W 2>/dev/null || pwd))"
cd "$PROJ"
[ -d .venv ] || uv venv .venv --python 3.11
PY=.venv/Scripts/python.exe; [ -f "$PY" ] || PY=.venv/bin/python
"$PY" -c "import numpy, scipy, soundfile, pyloudnorm, cv2, PIL, fontTools" 2>/dev/null || \
  uv pip install --python "$PY" numpy scipy soundfile pyloudnorm opencv-python pillow fonttools

# Pretendard (the Korean typeface for captions, cover and graphics): the variable TTF from the commit script-to-motion
# pins, downloaded unmodified with its licence and checked against its sha256. Kept in the skill, not in git.
FONTS="$SKILL/assets/fonts"
fetch() {   # url dest sha256
  if [ -s "$2" ] && [ "$(shasum -a 256 "$2" | cut -c1-64)" = "$3" ]; then return 0; fi
  curl -fsSL -o "$2.part" "$1" || { rm -f "$2.part"; echo "ERROR: could not download $1"; exit 1; }
  [ "$(shasum -a 256 "$2.part" | cut -c1-64)" = "$3" ] || { rm -f "$2.part"; echo "ERROR: $2: sha256 mismatch"; exit 1; }
  mv "$2.part" "$2"
}
fetch https://raw.githubusercontent.com/orioncactus/pretendard/5c41199ea0024a9e0b2cb31735265056e5472d76/packages/pretendard/dist/public/variable/PretendardVariable.ttf \
  "$FONTS/PretendardVariable.ttf" 3090ccde0442bb347aa7685d9ba8b17436a60682df6e8f92a9a670de14056e22
fetch https://raw.githubusercontent.com/orioncactus/pretendard/0189074fdad117a5e360aad00a59b47225429c31/LICENSE \
  "$FONTS/Pretendard-OFL.txt" 82e9c8a4b203261f10ddba1296422d64914ff3d4b7bd8a12896d03f0f088d70a
# The sketch theme's handwriting (references/theme-sketch.md): Gaegu Bold (Hangul + Latin) and Architects Daughter
# (the schematic's uppercase labels), both SIL OFL 1.1, from the commits of google/fonts pinned here.
GF=https://raw.githubusercontent.com/google/fonts
fetch $GF/088df5c822dacc8fad9dd64dbbe5649cd6830e99/ofl/gaegu/Gaegu-Bold.ttf "$FONTS/Gaegu-Bold.ttf" cc38a4af9506a45254d1ce07c589ec473d9e5f0be319e5a77b17c214903f8c1c
fetch $GF/088df5c822dacc8fad9dd64dbbe5649cd6830e99/ofl/gaegu/OFL.txt "$FONTS/Gaegu-OFL.txt" 53a9ce47085d9fef613c7ecb3730dc80d25962510bbea231b89564f58240f251
fetch $GF/f81a0e9fb2ff01bf783fff251ece4ffe2df61278/ofl/architectsdaughter/ArchitectsDaughter-Regular.ttf "$FONTS/ArchitectsDaughter-Regular.ttf" 6159718a08898e34bc1cb7354086141a5f9a70b73e54dbec27ead0d59a697359
fetch $GF/f81a0e9fb2ff01bf783fff251ece4ffe2df61278/ofl/architectsdaughter/OFL.txt "$FONTS/ArchitectsDaughter-OFL.txt" 0e441ae9f18ad0c294cc5b6ae3974c2db1614cab220598578b1b58c4cc334485
# The brief theme's Korean serif (references/theme-brief.md): Hahmlet variable TTF (SIL OFL 1.1).
fetch $GF/c1eda9233c33ad7775b27efd794f931095cf6133/ofl/hahmlet/Hahmlet%5Bwght%5D.ttf "$FONTS/Hahmlet-VF.ttf" 892bffe530255770a7435226154a02f519055ff6bedf64254f37f21d15a59279
fetch $GF/c1eda9233c33ad7775b27efd794f931095cf6133/ofl/hahmlet/OFL.txt "$FONTS/Hahmlet-OFL.txt" ddadb10d28a303e3ef3b1f7ec55d3027903b9ec566d2f87d3ee03f3c87c91711

W=work
mkdir -p "$W/scripts" "$W/gfx/assets" "$W/fonts" "$W/narration" edit
cp "$SKILL"/scripts/*.py "$SKILL"/scripts/*.sh "$W/scripts/"
rm -rf "$W/scripts/narration"; cp -R "$SKILL/scripts/narration" "$W/scripts/narration"
rm -rf "$W/scripts/market"; cp -R "$SKILL/scripts/market" "$W/scripts/market"   # the morning market briefing (market-brief.md)
cp "$SKILL"/assets/gfx/* "$W/gfx/"
cp "$SKILL"/assets/fonts/*.ttf "$W/fonts/"; cp "$SKILL"/assets/fonts/*.ttf "$W/gfx/assets/"
cp "$SKILL/scripts/render.py" "$W/render.py"      # the MP4 render the user runs by hand, after checking index.html
(cd "$W" && "../$PY" scripts/init_project.py "$SKILL_ABS")

# the narration sign-in, as tts.mjs will find it (Google by default: gcloud, no key)
if command -v gcloud >/dev/null && gcloud auth print-access-token >/dev/null 2>&1; then
  echo "🔑 Google Cloud TTS: signed in with gcloud (project $(gcloud config get project 2>/dev/null))"
else
  echo "🔑 Google Cloud TTS: no gcloud sign-in yet. Build the shorts on placeholders; before recording the user runs: ! gcloud auth login"
fi
echo "setup done: .venv, work/ (scripts, narration tools, graphics engine, fonts), edit/"
