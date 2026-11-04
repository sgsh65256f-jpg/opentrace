import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from opentrace.db import connect


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_cwd = os.getcwd()
        os.chdir(self.temp_dir.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp_dir.cleanup()

    def test_database_creates_session_and_usage(self):
        db = connect()
        cursor = db.execute("INSERT INTO sessions(task) VALUES (?)", ("test task",))
        session_id = cursor.lastrowid
        cost = (1000 * 2 + 500 * 10) / 1_000_000
        db.execute(
            """INSERT INTO usage
            (session_id, model, input_tokens, output_tokens, input_rate, output_rate, estimated_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, "test-model", 1000, 500, 2, 10, cost),
        )
        db.commit()
        saved = db.execute(
            "SELECT estimated_cost FROM usage WHERE session_id = ?", (session_id,)
        ).fetchone()
        self.assertAlmostEqual(saved["estimated_cost"], 0.007)
        db.close()

    def test_foreign_keys_reject_orphan_check(self):
        db = connect()
        with self.assertRaises(Exception):
            db.execute(
                "INSERT INTO checks(session_id, command, exit_code) VALUES (999, 'pytest', 0)"
            )
        db.close()

    def test_negative_tokens_rejected_by_database(self):
        db = connect()
        cursor = db.execute("INSERT INTO sessions(task) VALUES ('negative test')")
        with self.assertRaises(Exception):
            db.execute(
                """INSERT INTO usage
                (session_id, model, input_tokens, output_tokens, input_rate, output_rate, estimated_cost)
                VALUES (?, 'model', -1, 0, 0, 0, 0)""",
                (cursor.lastrowid,),
            )
        db.close()


if __name__ == "__main__":
    unittest.main()
