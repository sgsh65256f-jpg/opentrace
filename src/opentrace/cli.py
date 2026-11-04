"""Command-line interface for the OpenTrace local ledger."""

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

from .db import DB_PATH, connect


def _active_session(db):
    row = db.execute(
        "SELECT * FROM sessions WHERE status = 'active' ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        raise SystemExit('No active session. Start one with: opentrace start "task name"')
    return row


def _git_changed_paths():
    """Return changed/untracked paths only; never read file contents."""
    try:
        result = subprocess.run(
            ["git", "status", "--short", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return []
    paths = []
    for line in result.stdout.splitlines():
        if len(line) > 3:
            paths.append(line[3:].strip())
    return sorted(set(paths))


def cmd_init(_args):
    db = connect()
    db.close()
    print(f"Initialized local database: {DB_PATH}")


def cmd_start(args):
    db = connect()
    current = db.execute(
        "SELECT id FROM sessions WHERE status = 'active' LIMIT 1"
    ).fetchone()
    if current:
        raise SystemExit(f"Session #{current['id']} is already active. Finish it first.")
    cursor = db.execute("INSERT INTO sessions(task) VALUES (?)", (args.task,))
    db.commit()
    print(f"Started session #{cursor.lastrowid}: {args.task}")
    db.close()


def cmd_usage(args):
    if min(args.input_tokens, args.output_tokens, args.input_rate, args.output_rate) < 0:
        raise SystemExit("Token counts and rates must be non-negative.")
    estimated_cost = (
        args.input_tokens * args.input_rate + args.output_tokens * args.output_rate
    ) / 1_000_000
    db = connect()
    session = _active_session(db)
    db.execute(
        """INSERT INTO usage
        (session_id, model, input_tokens, output_tokens, input_rate, output_rate, estimated_cost)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            session["id"], args.model, args.input_tokens, args.output_tokens,
            args.input_rate, args.output_rate, estimated_cost,
        ),
    )
    db.commit()
    print(f"Recorded estimated usage: ${estimated_cost:.6f}")
    db.close()


def cmd_check(args):
    db = connect()
    session = _active_session(db)
    db.execute(
        "INSERT INTO checks(session_id, command, exit_code) VALUES (?, ?, ?)",
        (session["id"], args.command, args.exit_code),
    )
    db.commit()
    print(f"Recorded check result: exit code {args.exit_code}")
    db.close()


def cmd_finish(_args):
    db = connect()
    session = _active_session(db)
    paths = _git_changed_paths()
    db.executemany(
        "INSERT OR IGNORE INTO changed_files(session_id, path) VALUES (?, ?)",
        [(session["id"], path) for path in paths],
    )
    db.execute(
        """UPDATE sessions SET status = 'finished', finished_at = CURRENT_TIMESTAMP
        WHERE id = ?""",
        (session["id"],),
    )
    db.commit()
    print(f"Finished session #{session['id']}; recorded {len(paths)} changed/untracked paths.")
    db.close()


def _session_records(db, limit=10000):
    sessions = db.execute(
        "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    records = []
    for session in sessions:
        usage = db.execute(
            "SELECT * FROM usage WHERE session_id = ? ORDER BY id",
            (session["id"],),
        ).fetchall()
        checks = db.execute(
            "SELECT * FROM checks WHERE session_id = ? ORDER BY id",
            (session["id"],),
        ).fetchall()
        paths = db.execute(
            "SELECT path FROM changed_files WHERE session_id = ? ORDER BY path",
            (session["id"],),
        ).fetchall()
        records.append(
            {
                "id": session["id"],
                "task": session["task"],
                "status": session["status"],
                "started_at": session["started_at"],
                "finished_at": session["finished_at"],
                "estimated_cost_usd": round(
                    sum(item["estimated_cost"] for item in usage), 8
                ),
                "usage": [dict(item) for item in usage],
                "checks": [dict(item) for item in checks],
                "changed_files": [item["path"] for item in paths],
            }
        )
    return records


def cmd_list(args):
    db = connect()
    for item in _session_records(db, args.limit):
        print(
            f"#{item['id']} [{item['status']}] "
            f"${item['estimated_cost_usd']:.4f} — {item['task']}"
        )
    db.close()


def cmd_report(_args):
    db = connect()
    records = _session_records(db)
    total = sum(item["estimated_cost_usd"] for item in records)
    print(f"Sessions: {len(records)}")
    print(f"Recorded estimated cost: ${total:.4f}")
    print(f"Usage entries: {sum(len(item['usage']) for item in records)}")
    print(f"Checks recorded: {sum(len(item['checks']) for item in records)}")
    print("Costs are estimates based on the rates supplied when recording usage.")
    db.close()


def cmd_export(args):
    db = connect()
    records = _session_records(db)
    target = Path(args.output)
    if args.format == "json":
        target.write_text(json.dumps(records, indent=2), encoding="utf-8")
    else:
        fields = [
            "id", "task", "status", "started_at", "finished_at",
            "estimated_cost_usd", "usage_count", "check_count", "changed_files",
        ]
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for item in records:
                writer.writerow(
                    {
                        "id": item["id"],
                        "task": item["task"],
                        "status": item["status"],
                        "started_at": item["started_at"],
                        "finished_at": item["finished_at"],
                        "estimated_cost_usd": item["estimated_cost_usd"],
                        "usage_count": len(item["usage"]),
                        "check_count": len(item["checks"]),
                        "changed_files": ";".join(item["changed_files"]),
                    }
                )
    print(f"Exported {len(records)} sessions to {target}")
    db.close()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="opentrace", description="Local-first AI coding session ledger"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def command(name, function, help_text):
        child = subparsers.add_parser(name, help=help_text)
        child.set_defaults(function=function)
        return child

    command("init", cmd_init, "initialize local storage")
    start = command("start", cmd_start, "start a work session")
    start.add_argument("task")

    usage = command("usage", cmd_usage, "record token usage and estimated cost")
    usage.add_argument("--model", required=True)
    usage.add_argument("--input-tokens", type=int, required=True)
    usage.add_argument("--output-tokens", type=int, required=True)
    usage.add_argument("--input-rate", type=float, required=True,
                       help="USD per million input tokens")
    usage.add_argument("--output-rate", type=float, required=True,
                       help="USD per million output tokens")

    check = command("check", cmd_check, "record a check result; does not run the command")
    check.add_argument("command")
    check.add_argument("--exit-code", type=int, required=True)

    command("finish", cmd_finish, "finish the active session and capture Git paths")
    listing = command("list", cmd_list, "list recent sessions")
    listing.add_argument("--limit", type=int, default=20)
    command("report", cmd_report, "summarize recorded sessions")
    export = command("export", cmd_export, "export session history")
    export.add_argument("--format", choices=("json", "csv"), default="json")
    export.add_argument("--output", default="opentrace-report.json")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
