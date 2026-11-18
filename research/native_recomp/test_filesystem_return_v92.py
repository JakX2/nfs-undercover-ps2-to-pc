#!/usr/bin/env python3
"""V92 original-free exact overlay and runner checks."""
import unittest
import subprocess
import tempfile
from pathlib import Path
from derive_v91_resource_open_harness import derive as previous
from derive_v92_filesystem_return_harness import EDITS, derive
from derive_v92_filesystem_return_runner import derive as runner
HERE=Path(__file__).resolve().parent
class FilesystemReturnTest(unittest.TestCase):
    def test_harness(self):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prior=previous(base);s=derive(base)
        for a,_ in EDITS:self.assertEqual(prior.count(a),1)
        self.assertEqual(s,derive(base))
        for marker in ("V92_FS_ACK","V92_FS_RETURN","V92_TRIAL_PASS","POST_OWNER=0x8051908cu","V91_RESOURCE_OPEN"):
            self.assertEqual(s.count(marker),1)
        self.assertEqual(s.count("ctx.mmu.write"),prior.count("ctx.mmu.write"))
        self.assertEqual(s.count("ipc70_bus.reset()"),prior.count("ipc70_bus.reset()"))
        self.assertEqual(s.count("ipc70_ram.read32(submit72_phys+4u)==(post92_active?2u:open84_active?1u:0u)&&"),4)
        self.assertIn('mount_filesystem(std::make_shared<undercover::wii::GuestFiles>())',s)
    def test_runner(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("BOOT_PROGRESS entry=0x8000403C pc=0x8051908C stage=92",s)
        self.assertIn("restore_resource_init_v91.py",s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":unittest.main()
