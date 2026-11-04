# OpenTrace

**A local-first, provider-neutral ledger for AI-assisted coding sessions.**

OpenTrace records a developer's work sessions, manually supplied token usage, verification commands, and Git working-tree changes in a small SQLite database inside the project. It is designed to make session history exportable and inspectable without sending source code or prompts to a hosted service.

> OpenTrace is an independent community project. It is not affiliated with Anthropic, OpenAI, GitHub, or any coding-agent vendor.

## What works today

- Start and finish named work sessions.
- Record input/output token counts and user-supplied per-million-token rates.
- Calculate transparent estimated costs (not provider invoices).
- Record test/check commands and exit codes.
- Capture changed and untracked file paths from Git when a session finishes.
- List sessions and summarize recorded usage.
- Export session records as JSON or CSV.
- Store data locally in `.opentrace/opentrace.db`; no telemetry or network calls.

This is an early MVP. It includes opt-in local JSONL usage importers for Claude Code and Codex. These adapters support initial observed formats; they are not guaranteed to cover every version or configuration. Cursor is not implemented.

## Install from source

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
opentrace --help
```

## Quick start

Run from the Git repository you want to track:

```bash
opentrace init
opentrace start "Refactor the API client"
opentrace usage --model example-model --input-tokens 12000 --output-tokens 2500 --input-rate 3 --output-rate 15
opentrace check "pytest -q" --exit-code 0
opentrace finish
opentrace list
opentrace report
opentrace export --format json --output session-report.json

# Optional local agent usage imports
opentrace import-claude
opentrace import-codex

# Open the local dashboard
opentrace dashboard

# Optional MCP server (read-only)
pip install -e '.[mcp]'
opentrace-mcp
```

Rates are entered in USD per one million tokens. The estimate is simply:

`(input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`

It excludes provider-specific cached-token rates, tool charges, taxes, and billing adjustments unless you account for them separately. It is an estimate, not a statement of actual spend.

## Privacy and safety

- The database is created under `.opentrace/` in the current working directory.
- OpenTrace makes no network requests and collects no telemetry.
- It does not read prompts, source file contents, environment values, or credentials.
- Git capture stores changed file **paths only**, not diffs or file contents.
- Add `.opentrace/` to your `.gitignore` if session history should remain private.
- Do not publish session exports without reviewing them for sensitive project names and paths.

## Commands

| Command | Purpose |
| --- | --- |
| `init` | Initialize local storage |
| `start TASK` | Start a session |
| `usage` | Record token counts and estimated cost |
| `check COMMAND` | Record a check command and exit code (does not execute it) |
| `finish` | Finish the active session and capture Git paths |
| `list` | List recent sessions |
| `report` | Summarize recorded sessions and costs |
| `export` | Export JSON or CSV |

## Development

```bash
pip install -e ".[dev]"
python -m unittest discover -s tests -v
```

## Roadmap

1. Harden the event schema and export format.
2. Add tested, opt-in importers for documented agent session formats.
3. Add a read-only local dashboard.
4. Add machine-readable reports for CI and personal analytics.
5. Consider MCP support after the core data model stabilizes.

Roadmap items are proposals, not existing features.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributions should include tests and clearly document any change to data collection or privacy behavior.

## License

MIT. See [LICENSE](LICENSE).
