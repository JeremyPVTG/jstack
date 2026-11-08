import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location("research_hook", Path(__file__).resolve().parents[1] / "skills/j-research/scripts/research_hook.py")
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

def answers(changing=0.0, build=0.0, reliance=0.0, contained=0.0):
    return {"changing_facts": changing, "build_or_choose": build, "reliance": reliance, "self_contained": contained}

class Decide(unittest.TestCase):
    def test_clear_signal_fires_even_if_contained(self):
        self.assertTrue(hook.decide(answers(build=0.9, contained=0.9)))
    def test_unsettled_fires_only_when_not_contained(self):
        self.assertTrue(hook.decide(answers(changing=0.5, contained=0.4)))
        self.assertFalse(hook.decide(answers(changing=0.5, contained=0.8)))
    def test_no_signal_does_not_fire(self):
        self.assertFalse(hook.decide(answers(changing=0.2, contained=0.1)))

LOG_DIR = tempfile.TemporaryDirectory()
LOG = Path(LOG_DIR.name) / "hook.jsonl"


def run(prompt, judged=None, error=None, key="k", log=LOG):
    out, err = io.StringIO(), io.StringIO()
    judge = mock.Mock(side_effect=error) if error else mock.Mock(return_value=judged)
    with mock.patch.object(hook, "judge", judge), mock.patch.object(hook, "api_key", return_value=key), \
         mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"prompt": prompt}))), mock.patch.object(sys, "stdout", out), mock.patch.object(sys, "stderr", err), \
         mock.patch.dict(os.environ, {"JSTACK_HOOK_LOG": str(log)}):
        code = hook.main()
    return code, out.getvalue(), err.getvalue(), judge

class Main(unittest.TestCase):
    def test_fires_with_reminder(self):
        code, out, _, _ = run("How would you build a booking page?", answers(build=0.95))
        self.assertEqual(code, 0)
        self.assertIn("j-research", json.loads(out)["hookSpecificOutput"]["additionalContext"])
    def test_quiet_when_not_research(self):
        _, out, _, _ = run("Rename getUser to fetchUser everywhere", answers(contained=0.9))
        self.assertEqual(out, "")
    def test_failure_adds_nothing_and_logs(self):
        code, out, err, _ = run("Is Bun stable enough for cron jobs?", error=TimeoutError())
        self.assertEqual((code, out), (0, ""))
        self.assertIn("classifier failed", err)
    def test_skips_host_delivered_results_and_notices(self):
        for prompt in ("Delegated task node:abc (Smoke 1) [completed]:\nThe current LTS is 26.", "<task-notification>\n<task-id>x</task-id>", "[SYSTEM NOTIFICATION - NOT USER INPUT] background task done"):
            _, out, _, judge = run(prompt, answers(changing=0.95))
            self.assertEqual(out, ""); judge.assert_not_called()

    def test_skips_slash_commands_short_prompts_and_missing_key(self):
        for prompt in ("/review", "ok thanks"):
            _, out, _, judge = run(prompt, answers(build=0.9))
            self.assertEqual(out, ""); judge.assert_not_called()
        _, out, err, judge = run("Which Postgres host is cheapest now?", answers(changing=0.9), key=None)
        self.assertEqual(out, ""); self.assertIn("no TYPESAFE_API_KEY", err); judge.assert_not_called()

class Log(unittest.TestCase):
    def setUp(self):
        LOG.unlink(missing_ok=True)

    def test_records_scores_decision_and_prompt(self):
        run("How would you build a booking page?", answers(build=0.95))
        run("Rename getUser to fetchUser everywhere", answers(contained=0.9))
        rows = [json.loads(line) for line in LOG.read_text().splitlines()]
        self.assertEqual([r["fire"] for r in rows], [True, False])
        self.assertEqual(rows[0]["scores"]["build_or_choose"], 0.95)
        self.assertIsNone(rows[0]["label"])

    def test_skipped_and_failed_prompts_are_not_recorded(self):
        run("/review", answers(build=0.9))
        run("Is Bun stable enough for cron jobs?", error=TimeoutError())
        self.assertFalse(LOG.exists())

    def test_off_disables_and_unwritable_path_is_harmless(self):
        _, out, _, _ = run("How would you build a booking page?", answers(build=0.95), log="off")
        self.assertIn("j-research", out)
        self.assertFalse(LOG.exists())
        _, out, _, _ = run("How would you build a booking page?", answers(build=0.95), log="/dev/null/nope.jsonl")
        self.assertIn("j-research", out)

    def test_report_counts_false_fires_and_misses(self):
        rows = [{"fire": True, "label": False}, {"fire": False, "label": True}, {"fire": True, "label": True}, {"fire": True, "label": None}]
        LOG.write_text("".join(json.dumps(r) + "\n" for r in rows))
        out = io.StringIO()
        with mock.patch.object(sys, "stdout", out):
            hook.report(LOG)
        self.assertEqual(json.loads(out.getvalue()), {"prompts": 4, "fired": 3, "labelled": 3, "false_fires": 1, "misses": 1})


if __name__ == "__main__":
    unittest.main()
