"""Local agent log import helpers."""
import json
import hashlib
from pathlib import Path
from .db import connect


def import_claude(root):
    return _import(root, "claude-code", _claude_totals)


def import_codex(root):
    return _import(root, "codex", _codex_totals)


def _lines(path):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            yield row


def _claude_totals(path):
    inputs = outputs = 0
    seen = set()
    models = set()
    for row in _lines(path):
        msg = row.get("message") or {}
        if msg.get("role") != "assistant":
            continue
        mid = msg.get("id")
        if mid and mid in seen:
            continue
        if mid:
            seen.add(mid)
        usage = msg.get("usage") or {}
        inputs += int(usage.get("input_tokens") or 0)
        inputs += int(usage.get("cache_read_input_tokens") or 0)
        inputs += int(usage.get("cache_creation_input_tokens") or 0)
        outputs += int(usage.get("output_tokens") or 0)
        if msg.get("model"):
            models.add(str(msg["model"]))
    return inputs, outputs, ",".join(sorted(models)) or "claude-unknown"


def _codex_totals(path):
    latest = None
    model = "codex-unknown"
    for row in _lines(path):
        payload = row.get("payload") or {}
        if row.get("type") == "session_meta":
            model = str(payload.get("model") or model)
        if row.get("type") == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info") or {}
            if isinstance(info.get("total_token_usage"), dict):
                latest = info["total_token_usage"]
    if latest is None:
        return 0, 0, model
    return int(latest.get("input_tokens") or 0), int(latest.get("output_tokens") or 0), model


def _import(root, provider, parser):
    root = Path(root).expanduser()
    if not root.exists():
        return {"provider": provider, "files_seen": 0, "imported": 0, "skipped": 0}
    db = connect()
    seen = imported = skipped = 0
    try:
        for path in root.rglob("*.jsonl"):
            if not path.is_file():
                continue
            seen += 1
            try:
                identity = str(path.resolve())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                duplicate = db.execute(
                    "SELECT 1 FROM imported_sources WHERE provider=? AND sha256=?",
                    (provider, digest),
                ).fetchone()
                if duplicate:
                    skipped += 1
                    continue
                inputs, outputs, model = parser(path)
                if inputs == 0 and outputs == 0:
                    skipped += 1
                    continue
                db.execute(
                    "INSERT INTO sessions(task,status,finished_at) VALUES (?,'finished',CURRENT_TIMESTAMP)",
                    (f"Imported {provider} session: {path.stem[:40]}",),
                )
                sid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                db.execute(
                    """INSERT INTO usage
                    (session_id,model,input_tokens,output_tokens,input_rate,output_rate,estimated_cost)
                    VALUES (?,?,?,?,0,0,0)""",
                    (sid, model, inputs, outputs),
                )
                db.execute(
                    "INSERT INTO imported_sources(provider,sha256,source_name,session_id) VALUES (?,?,?,?)",
                    (provider, digest, identity, sid),
                )
                imported += 1
            except (OSError, ValueError, TypeError):
                skipped += 1
        db.commit()
    finally:
        db.close()
    return {"provider": provider, "files_seen": seen, "imported": imported, "skipped": skipped}
