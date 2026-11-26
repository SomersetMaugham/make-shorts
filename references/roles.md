# Workflow and roles — who does each step

The user's standing assignment of every step of a short (set 2026-11-21/22 on the PN-junction series). Follow it for
every short unless the user says otherwise; ask before moving a step to someone else (e.g. when a tool fails).

| step | what | who | checked by |
|---|---|---|---|
| 0. Setup | `setup.sh`, or refresh an existing project's copies of the kit and scripts (back up the old ones first) | Claude | parts sheet, regression |
| 1. Research and fact-check | the facts list, 2+ sources each, `factcheck_<sk>.md` + `research_<sk>/` | **agy Hydrogen** (`gemini-4-hydrogen-high`, web tools only) | Claude opens the sources and compares |
| 2. Script | story spine → lines, first-time-listener gates (script-writing.md) | **Claude** | step 3 |
| 3. Cold-listener review | reads only `script.txt`, as a viewer who knows nothing (script-writing.md §0b, step 5) | **Gemini app** (Hydrogen, a new chat; if it fails, ask the user, then a Claude subagent) | Claude applies it |
| (optional) Fun and easy discussion | ideas to make the explanation more fun and easier; at most 3 rounds per short, many items batched per round | **agy Neon** (`gemini-4-neon-*`) | Claude checks every factual claim |
| 4. Timeline | `shorts.json` → `prep.sh` (silent placeholders, nothing recorded) → read the runs | **Claude** | runs ≤ ~8 s, no two neighbours of one scene kind |
| 5. Graphics brief | `GFX_BRIEF_<sk>.md`: 3–5 sections, a hero run each, the parts catalogue PNGs attached | **Claude** | — |
| 6. Look development | hero runs first → compare with the approved look + defect check | graphics code: **Gemini app** / defect check: **agy Neon** (`defect_check.py lookdev`) | Claude confirms each finding on its frame |
| 7. Full build | the remaining runs | **Gemini app** (if it fails, ask the user, then **agy Hydrogen** with a write grant to one output folder) | `check_parts.py` warnings 0 |
| 8. Motion and whole check | frame-by-frame boundaries and camera moves, whole-short sheets | **agy Neon** (`defect_check.py motion` / `whole`); Claude counts the camera pushes (4–5 max) | no confirmed defect left |
| 9. Preview | hand over `work/index.html` + `script.txt`, ask whether to record | Claude → **the user reviews** | review notes applied |
| 10. Recording | Chirp 3 HD Enceladus, speed 1, **only after the user says so** | Claude | `check_narration.py`, chip `at`s |
| 11. Render | `python3 render.py <sk> <NN> <slug>` | **the user** | Claude checks the MP4 (LUFS, length) |
| 12. Wrap-up | thumbnail, `PUBLISH.md`, `check_publish.py`, STATUS | Claude | — |
| Commit / push | skill changes | **only on the user's word** (each push asked) | — |

**The morning market briefing** (market-brief.md) changes only these steps; the rest of the table holds:

| step | what | who | checked by |
|---|---|---|---|
| 1a. Numbers | `fetch_market.py` → `market_data.json` (closes, session calendar, heatmap, weather, solar terms) | **Claude** | no ⚠ date line; Claude looks at both heatmap PNGs |
| 1b. Research | `research.json`: news, after hours, NDF, night futures, the previous KOSPI close, tonight's and Korea's events, two brokers' morning views or more, a second source for every spoken index figure | **agy Hydrogen** (`gemini-4-hydrogen-high`, web tools only) | Claude opens the sources of every spoken figure |
| 2. Script | `brief_draft.py` → rewrite every line by the briefing spine and the gates → `shorts.json`; the outlook checked against the research | **Claude** | step 3 (the cold-listener review, as for every short) |
| 2b. Outlook record | `outlook_log.py add` after the script is final; `score` every morning; `report` every 20 trading days or so | **Claude** | weight changes only from 20+ days, proposed to the user with the numbers |

Rules that go with it:
- **Delegate in polite, unambiguous English** to agy and the Gemini app (user, 2026-11-22; global CLAUDE.md "위임 말투와
  언어"): a kind manager asking a trusted colleague, never commands, and no room for the other side's own interpretation —
  numbers with units, file paths, a numbered list of tasks, the files not to touch, the finish condition and the DIGEST
  format, and "if anything is unclear or conflicts, stop and report it instead of guessing". No vague words ("roughly",
  "if possible", "as needed", "etc.", "nice"). Prompts built into scripts follow the same rule.
- **The Gemini app's model menu** (`mcp__gemini-app__ask_gemini`; user, 2026-11-26) has 5 rows, top to bottom:
  1 자동 모드 (auto), 2 **Hydrogen**, 3 **Neon**, 4 Carbon (unavailable), 5 사고 수준 (thinking level). The app shows
  no model names to accessibility, so the MCP server picks a row by number: `GEMINI_MODEL_ROW` / `GEMINI_MODEL_ROWS` in
  the `gemini-app` entry of `~/.claude.json` (now `2` / `5` = Hydrogen, the model for the graphics code and the
  cold-listener review). Neon is row `3`; never rows 1, 4 or 5. Changing the row needs a Claude Code restart, so ask
  the user first. The row is enforced only while the Gemini window is visible: hidden or minimized, the app's last
  chosen model answers. If Google reorders the menu again, the user tells you the new order and you update this line.
- **No score decides anything** (elevate.md): the checker finds defects; taste is the user's and the approved
  references' (earlier parts of the series, the parts catalogue).
- **Verify every delegated result yourself**: agy's "done" is a claim. Build, shoot and check before reporting.
- agy is called by its absolute path `~/.local/bin/agy` (the zsh alias adds `--dangerously-skip-permissions`), with
  narrow grants: `--add-dir` for reading, `write_file(<folder or file>)` for writing, web tools only for research.
