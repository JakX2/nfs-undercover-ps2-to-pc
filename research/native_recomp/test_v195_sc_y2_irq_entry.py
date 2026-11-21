#!/usr/bin/env python3
"""V195 original-free checks for second IOS Y2 native external IRQ entry."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v194_osrestore_next_harness import derive as previous
from derive_v195_sc_y2_irq_entry_harness import derive,TAIL,IRQ
from derive_v195_sc_y2_irq_entry_runner import derive as runner,PASS,PATTERN
HERE=Path(__file__).resolve().parent

class V195(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        cls.before=previous(base)
        cls.after=derive(base)

    def test_irq_entry_is_after_all_original_guest_invariants(self):
        self.assertIn(TAIL,self.before)
        self.assertNotIn("V195_SC_Y2_VECTOR",self.before)
        self.assertEqual(self.after.count("V195_SC_Y2_VECTOR pending="),1)
        pos=self.after.index(IRQ)
        self.assertGreater(pos,self.after.index("original BSS byte not zero"))
        self.assertGreater(pos,self.after.index("original interrupt-disable MSR.EE side effect changed"))
        self.assertLess(pos,self.after.index("unexpected syscall/interpreter fallback"))
        self.assertIn("oldpc==0x8052f830u&&oldlr==0x80520970u",IRQ)
        self.assertIn("nwii::runtime::v194_next_seen==1u",IRQ)
        self.assertIn("irq74_vector,safe",IRQ)
        self.assertIn("c.srr0==oldpc",IRQ)
        self.assertIn("pending&&safe&&entered&&saved&&regs&&mail&&masked",IRQ)

    def test_no_fake_ios_service_or_guest_status(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(",
                      "ctx.mmu.write32(", "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for forbidden in ("c.mmu.write","ipc70_bus.write","ipc70_ram.write",
                          "service_one(","ipc70_bus.tick("):
            self.assertNotIn(forbidden,IRQ)
        self.assertNotRegex(IRQ,r"\bc\.(?:pc|msr|gpr|srr0|srr1)\s*=(?!=)")
        self.assertIn("enter_external_irq(",IRQ)
        self.assertIn("c.dispatch_saved_ctx",IRQ)
        with self.assertRaises(ValueError):derive("invalid")

    def test_native_runner_original_free_gates(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v195_sc_y2_irq_entry_harness.py",script)
        self.assertIn("V195_SC_Y2_VECTOR verified=1",script)
        self.assertIn("V195_ENTRY_COUNT lines=$v195_count",script)
        self.assertIn("grep -Ec '^V195_SC_Y2_VECTOR '",script)
        good=("V195_SC_Y2_VECTOR pending=1 safe=1 entered=1 saved=1 regs=1 "
              "mail=1 masked=1 resume=8052f830 pc=80000500")
        self.assertTrue(re.fullmatch(PASS,good))
        self.assertFalse(re.fullmatch(PASS,good.replace("saved=1","saved=0")))
        self.assertTrue(re.fullmatch(PATTERN,good.replace("pending=1","pending=0")))
        with tempfile.TemporaryDirectory() as temp:
            f=Path(temp)/"script.sh";f.write_text(script)
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_private_owner_workflow_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v195-sc-y2-irq-entry.yml").read_text()
        self.assertIn("run_v195_sc_y2_irq_entry.sh",wf)
        self.assertIn("V195_SC_Y2_VECTOR verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)

if __name__=="__main__":
    unittest.main()
