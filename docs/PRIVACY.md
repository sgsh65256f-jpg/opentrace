# Privacy and data handling

OpenTrace is local-first. The CLI and dashboard do not send data to a hosted service.

## Local agent imports

Importing is opt-in. The Claude Code and Codex adapters read local JSONL files and store aggregate token counts, a model label, the source file path, and a content hash to avoid importing the same unchanged log repeatedly. Prompt text, completions, tool arguments, diffs, and source-code contents are not intentionally persisted.

If a log file changes after import, its content hash changes and a new snapshot may be imported. The source path can contain local project names, so review exports before sharing them.

## Local storage

The database lives in the .opentrace/opentrace.db directory relative to the current working directory. Add .opentrace/ to .gitignore.

The dashboard binds to 127.0.0.1 by default. Do not bind it to a public interface unless you add authentication and understand the exposure.

## Costs

Imported token totals have zero estimated cost until rates are supplied. OpenTrace does not claim to reproduce provider invoices, cached-token billing, or account-level charges.
