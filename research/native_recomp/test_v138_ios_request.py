#!/usr/bin/env python3
"""V138 original-free pending request classification and privacy tests."""
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v137_ios_liveness_harness import derive as previous
from derive_v138_ios_request_harness import derive, ANCHOR, INJECTION
from derive_v138_ios_request_runner import derive as derive_runner
HERE=Path(__file__).resolve().parent

class V138(unittest.TestCase):
    def test_read_only_validation_and_path_classes(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src)
        self.assertEqual(old.count(ANCHOR),1)
        new=derive(src)
        self.assertEqual(new,old.replace(ANCHOR,INJECTION,1))
        for term in ("ipc70_bus.tick()", "ipc70_bus.reset()",
                     "ipc70_ram.write8(", "ctx.mmu.write8("):
            self.assertEqual(new.count(term),old.count(term))
        for term in ("V138_IOS_REQUEST valid=","ipc70_ram.valid(*v138_msg,64u)",
                     'name=="/shared2/sys/SYSCONF"',
                     'name=="/dev/fs"',
                     "if(!terminated)v138_kind=7u"):
            self.assertIn(term,new)

    def test_runner_syntax_and_inherited_verifications(self):
        base=(HERE/"run_v79_continuous_reply_entry.sh").read_text()
        derived=derive_runner(base)
        for term in ("derive_v138_ios_request_harness.py",
                     "V136_SECOND_RETRY verified=1","V137_IOS_PROBE verified=1",
                     "V138_REQUEST_PROBE verified=1","V133_STATUS_PROBE verified=1"):
            self.assertIn(term,derived)
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"run.sh"
            p.write_text(derived)
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_missing_anchors_are_fail_closed(self):
        with self.assertRaises(ValueError):derive("unrelated")
        with self.assertRaises(ValueError):derive_runner("unrelated")

if __name__=="__main__":unittest.main()
