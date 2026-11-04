# Agent log format support

## Claude Code

Default search root: ~/.claude/projects. The importer scans JSONL files recursively and looks for assistant message objects with a usage object. It aggregates input_tokens, cache_read_input_tokens, cache_creation_input_tokens, and output_tokens. Duplicate message IDs within a file are counted once.

## Codex

Default search root: ~/.codex/sessions. The importer reads session_meta model labels and event_msg token_count events. It uses the last total_token_usage snapshot because these values are cumulative; summing snapshots would double-count.

## Limitations

These are initial adapters, not a compatibility guarantee for every released version. They may skip logs that use different schemas. Imported records intentionally have zero estimated cost. Add sanitized synthetic fixtures when expanding support. Never commit real agent transcripts, prompts, completions, tool payloads, or customer data.
