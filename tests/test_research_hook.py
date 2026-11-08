import importlib.util
import io
import json
import sys
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

def run(prompt, judged=None, error=None, key="k"):
    out, err = io.StringIO(), io.StringIO()
    judge = mock.Mock(side_effect=error) if error else mock.Mock(return_value=judged)
    with mock.patch.object(hook, "judge", judge), mock.patch.object(hook, "api_key", return_value=key), \
         mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"prompt": prompt}))), mock.patch.object(sys, "stdout", out), mock.patch.object(sys, "stderr", err):
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
    def test_skips_slash_commands_short_prompts_and_missing_key(self):
        for prompt in ("/review", "ok thanks"):
            _, out, _, judge = run(prompt, answers(build=0.9))
            self.assertEqual(out, ""); judge.assert_not_called()
        _, out, err, judge = run("Which Postgres host is cheapest now?", answers(changing=0.9), key=None)
        self.assertEqual(out, ""); self.assertIn("no TYPESAFE_API_KEY", err); judge.assert_not_called()

if __name__ == "__main__":
    unittest.main()
