#!/usr/bin/env python3
"""Ensure the V109 CI success gate follows V109 evidence, not stale V104/V107 routes."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
class Gate(unittest.TestCase):
    def test_workflow(self):
        y=(ROOT/".github/workflows/wii-v109-sc-nonempty.yml").read_text()
        _,tail=y.split("          # Preserve earlier stage evidence for context",1)
        tail=tail.split("      - name: Remove private owner and generated code",1)[0]
        for marker in ("V109_WRAPPER derived","V109_WRAPPER syntax_ok",
                       "V109_NATIVE_EXIT ok=1","V109_STAGE native_test_passed",
                       "V109_SC_SECOND_COPY input=1 bounded=1",
                       "V109_SC_NEXT_LENGTH route=1 data=1 prior=1",
                       "BOOT_PROGRESS entry=0x8000403C pc=0x80544AC0 stage=109"):
            self.assertIn("grep -Fx '"+marker+"'",tail)
        self.assertNotIn("grep -Fx 'V107_SC_SOURCE",tail)
        self.assertNotIn("grep -Fx 'V108_SC_RESTORE",tail)
        self.assertNotIn("diagnose_sc_literal_restore_v108",tail)
        self.assertIn("rm -rf -- \"$RUNNER_TEMP/nwii\" \"$RUNNER_TEMP/originals\" \"$RUNNER_TEMP/sc109.log\"",y)
if __name__=="__main__":unittest.main()
