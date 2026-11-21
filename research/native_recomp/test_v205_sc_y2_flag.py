#!/usr/bin/env python3
"""V205 original-free second Y2 Hollywood guest flag acknowledgment checks."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v204_sc_y2_ack_harness import derive as previous,ACK as PREVIOUS_ACK,NEXT_END as PREVIOUS_END
from derive_v205_sc_y2_flag_harness import derive,STOP,CONTINUE,OBSERVER,NEXT_END
from derive_v205_sc_y2_flag_runner import derive as runner,PATTERN,PASS
from derive_v172_sc_y1_ack_harness import MMIO_ANCHOR
HERE=Path(__file__).resolve().parent

class V205(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_original_guest_second_flag_write_is_not_synthesized(self):
        self.assertIn(STOP,PREVIOUS_ACK)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        for marker in ("v196_live&&v204_ack_seen==1u&&v205_flag_seen==0u",
                       "addr==B::IPC+H::PPC_FLAG",
                       "addr==B::MIRROR+H::PPC_FLAG",
                       "(value&H::IPC_PPC)!=0u","((*flags&H::IPC_PPC)==0u)",
                       "((*ctrl&M::Y2)==0u)","!ipc70_bus.external_irq_level()",
                       "queued_replies()==1u",
                       "ipc70_ram.cpu->inst_count>v205_after_y2_inst",
                       "read8(sc_addr)==1u"):
            self.assertIn(marker,OBSERVER)
        self.assertIn(MMIO_ANCHOR+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_hook_never_writes_bus_or_patches_cpu(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for snippet in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write","service_one(",
                              "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(forbidden,snippet)
        self.assertNotRegex(OBSERVER,r"\bipc70_ram\.cpu->(?:msr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_sixteen_trial_owner_gate_and_private_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v205_sc_y2_flag_harness.py",script)
        self.assertIn("V204_SC_Y2_ACK verified=1",script)
        self.assertIn("V205_SC_Y2_FLAG verified=1",script)
        self.assertIn(')" -eq 16',script)
        good="V205_Y2_FLAG write=1 cleared=1 ctrl=1 irq_down=1 queued=1 guest=1 progressed=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("ctrl=1","ctrl=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("irq_down=1","irq_down=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v205-sc-y2-flag.yml").read_text()
        self.assertIn("run_v205_sc_y2_flag.sh",wf)
        self.assertIn("test_v205_sc_y2_flag.py",wf)
        self.assertIn("V205_SC_Y2_FLAG verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)
            path=Path(directory)/"entry.sh"
            path.write_text((HERE/"run_v205_sc_y2_flag.sh").read_text(),encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
