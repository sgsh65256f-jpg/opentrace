"""Optional read-only MCP server for local OpenTrace data.

Install with: pip install -e '.[mcp]'
Run with: opentrace-mcp
"""
from pathlib import Path
import sqlite3
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("OpenTrace")


def _db():
    path = Path(".opentrace/opentrace.db").resolve()
    if not path.exists():
        raise FileNotFoundError("OpenTrace database not found. Run 'opentrace init' first.")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


@mcp.tool()
def list_sessions(limit: int = 20) -> list[dict]:
    """List recent coding sessions and their status. Does not expose prompts or source contents."""
    limit = max(1, min(int(limit), 100))
    db = _db()
    try:
        rows = db.execute(
            "SELECT id,task,status,started_at,finished_at FROM sessions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            {"id": r[0], "task": r[1], "status": r[2], "started_at": r[3], "finished_at": r[4]}
            for r in rows
        ]
    finally:
        db.close()


@mcp.tool()
def usage_summary() -> dict:
    """Return aggregate token totals and recorded estimated cost."""
    db = _db()
    try:
        row = db.execute(
            "SELECT COUNT(DISTINCT s.id), COALESCE(SUM(u.input_tokens),0), "
            "COALESCE(SUM(u.output_tokens),0), COALESCE(SUM(u.estimated_cost),0) "
            "FROM sessions s LEFT JOIN usage u ON u.session_id=s.id"
        ).fetchone()
        return {
            "sessions": row[0],
            "input_tokens": row[1],
            "output_tokens": row[2],
            "estimated_cost_usd": round(row[3], 8),
            "costs_are_estimates": True,
        }
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run(transport="stdio")
