"""One-command contributor quickstart must remain synthetic and asset-free."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest


class NewcomerSmoke(unittest.TestCase):
    def test_demo_can_run_without_game_files(self):
        demo=Path(__file__).resolve().parents[1]/"examples"/"synthetic_smoke.py"
        r=subprocess.run([sys.executable,str(demo)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        self.assertEqual(result["fixture_data"],"SYNTHETIC_ONLY")
        self.assertEqual(result["archive_candidates_found"],2)
        self.assertEqual(result["old_public_hook_addresses_in_executable_sections"],4)
        self.assertFalse(result["real_original_game_input_used"])
        self.assertFalse(result["carbon_game_runtime_verified"])
        self.assertFalse(result["safe_to_install"])

    def test_demo_never_requires_original_game_paths(self):
        demo=Path(__file__).resolve().parents[1]/"examples"/"synthetic_smoke.py"
        source=demo.read_text(encoding="utf-8")
        self.assertIn("TemporaryDirectory",source)
        self.assertNotIn("STREAML5RA.BUN",source)
        self.assertNotIn("NFSC.exe",source.replace("FAKE_NFSC_NOT_RUN.exe",""))


if __name__=="__main__":
    unittest.main()
