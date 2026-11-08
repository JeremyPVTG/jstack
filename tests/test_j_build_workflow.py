import shutil
import subprocess
import unittest
from pathlib import Path

SIM = Path(__file__).resolve().parent / "j_build_workflow_sim.mjs"


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class ReviewWorkflowVerdicts(unittest.TestCase):
    def test_review_stage_fails_closed(self):
        result = subprocess.run(["node", str(SIM)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
