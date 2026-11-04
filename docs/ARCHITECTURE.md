# Architecture

OpenTrace is a local-first Python application with four layers:

1. **CLI** — parses explicit user commands and coordinates operations.
2. **SQLite ledger** — stores sessions, usage aggregates, checks, changed paths, and import fingerprints.
3. **Adapters** — opt-in readers that normalize local agent logs into aggregate token counts.
4. **Read surfaces** — a loopback-only dashboard and an optional read-only MCP server.

## Data flow

Agent JSONL files are parsed locally. Adapters extract only model labels and aggregate input/output token counts. The database stores those aggregates, an absolute source path, and a SHA-256 digest used to avoid re-importing an unchanged file. Raw log lines are not copied into the database.

Manual usage entry stores user-supplied rates and a derived estimate. Imported usage stores zero rates and zero estimated cost rather than inventing provider prices.

## Trust boundaries

- The CLI runs with the current user's filesystem permissions.
- The dashboard binds to 127.0.0.1 by default and is not an authenticated multi-user service.
- The MCP server opens the database in SQLite read-only mode and exposes aggregate session metadata only.
- The core package has no runtime network dependency.

## Compatibility

Agent log formats are not stable public APIs. Importers are best-effort adapters and should be tested against synthetic fixtures and documented schema samples. A parser must tolerate unknown fields and malformed lines without persisting raw content.
