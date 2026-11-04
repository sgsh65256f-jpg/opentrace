import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from opentrace.db import connect
from opentrace.importers import import_claude, import_codex


class ImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = os.getcwd()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.old)
        self.tmp.cleanup()

    def write_rows(self, path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(x) for x in rows), encoding="utf-8")

    def test_claude_usage_and_repeat_import(self):
        root = Path("claude")
        self.write_rows(root / "one.jsonl", [
            {"message":{"id":"a","role":"assistant","model":"claude-test","usage":{"input_tokens":10,"cache_read_input_tokens":5,"output_tokens":3}}},
            {"message":{"id":"a","role":"assistant","model":"claude-test","usage":{"input_tokens":10,"cache_read_input_tokens":5,"output_tokens":3}}},
            {"message":{"id":"b","role":"assistant","model":"claude-test","usage":{"input_tokens":2,"output_tokens":1}}},
            {"message":{"role":"user","content":"secret prompt"}},
        ])
        self.assertEqual(import_claude(root)["imported"], 1)
        self.assertEqual(import_claude(root)["imported"], 0)
        db = connect()
        row = db.execute("SELECT input_tokens,output_tokens FROM usage").fetchone()
        self.assertEqual((row["input_tokens"], row["output_tokens"]), (17, 4))
        db.close()

    def test_codex_uses_last_cumulative_snapshot(self):
        root = Path("codex")
        self.write_rows(root / "one.jsonl", [
            {"type":"session_meta","payload":{"model":"codex-test"}},
            {"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":12,"output_tokens":4}}}},
            {"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":31,"output_tokens":8}}}},
        ])
        self.assertEqual(import_codex(root)["imported"], 1)
        db = connect()
        row = db.execute("SELECT input_tokens,output_tokens,model FROM usage").fetchone()
        self.assertEqual((row["input_tokens"],row["output_tokens"],row["model"]), (31,8,"codex-test"))
        db.close()


if __name__ == "__main__":
    unittest.main()
