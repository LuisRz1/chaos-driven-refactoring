# IBM Bob Integration

Bob 2.0 participates in **both planes**: it builds the project at development time and performs
the runtime repository analysis. See [[Hackathon Context]] for the rules.

## Development-time (build plane)

- Bob IDE 2.1.0 is installed on the developer machine; Bob Shell 2.0.2 is installed globally.
- Headless tasks: `scripts/bob-task.ps1` wraps
  `bob run --trust --accept-license --format json --mode agent --max-cost <n> "<prompt>"`
  and saves the full result JSON (task id, duration, `session_costs`, tool calls, final message)
  to `bob_sessions/bobshell-<name>-<timestamp>.json`.
- Tasks completed so far: `queue-unit-tests` (0.94), `concurrency-bisector` (0.28),
  plus runtime E2E sessions (see [[Evidence]]).
- Bob IDE sessions must be exported manually: History → task → screenshot of the consumption
  summary + Export task history → `bob_sessions/phase-N-name.md/png`.

## Runtime (analysis plane)

`runner/cdr/repair.py` — `BobRepairer`:

1. `repo_context.ensure_repo_clone` shallow-clones the submitted repo into
   `artifacts/repos/<owner>-<name>` and resets it (`workspace.reset_workspace`).
2. One **agent** session runs inside the clone with a prescriptive prompt: read at most 6
   relevant files, apply the minimal fix to at most 3 files, never write plan/docs, never run
   builds or tests, then reply `ANALYSIS: / FILES: / PROPOSED_CHANGE:`.
3. The patch is the real `git diff` after staging tracked modifications and new source files;
   only files that exist in the clone can enter `target_files`.
4. `diagnoses` and `patches` store `bob_task_id` and `bobcoins`; the dashboard shows
   "IBM Bob task XXXXXXXX · N Bobcoins consumed".

Fallbacks: if Bob is unavailable, produces no diff, or errors, the pipeline uses plan-mode
analysis (`diagnoser.py`) with watsonx Granite or deterministic rules and a template patch
(`patches.source = "template"`). Runs never fail because of Bob.

## Configuration

| Env var | Default | Meaning |
| --- | --- | --- |
| `BOB_API_KEY` | — | key from bob.ibm.com portal (or `~/.cdr/bob-api-key.txt`) |
| `CDR_ANALYZER` | `auto` | `bob` / `watsonx` / `rules` / `auto` |
| `CDR_BOB_MAX_COST` | `2` | Bobcoin cap for plan-mode analyses |
| `CDR_BOB_PATCH_MAX_COST` | `2` | Bobcoin cap for the agent repair session |
| `CDR_BOB_TIMEOUT_S` | `420` | subprocess timeout |
| `CDR_BOB_PATCHES` | `1` | enable/disable the agent repair path |
| `CDR_CLONE_REPOS` | `1` | enable/disable cloning |

## Operational notes

- **Budget**: 50 Bobcoins on the trial. Roughly 1–3 Bobcoins per repo analysis; check
  `session_costs` in `bob_sessions/*.json` and the Bob portal.
- **Cost control**: prompt limits (≤3 files) plus `--max-cost`; runs that hit the cap still
  produce a diff but may be broader.
- **Windows encoding**: `BobClient.run` forces `encoding="utf-8", errors="replace"`; without it
  a single non-cp1252 character crashes the subprocess reader thread (`IndexError`).
- **Bob behavior**: sometimes it explores and produces no edits — handled by falling back to the
  template patch; occasionally it edits many files — the prompt limit mitigates this.
- **Guard**: never point Bob at a workspace outside `artifacts/repos/`
  (`is_managed_workspace`).
