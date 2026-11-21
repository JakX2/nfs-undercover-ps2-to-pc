#!/usr/bin/env python3
"""Original-free V212 genuine guest context restoration regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v211_sc_y2_resched_next_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v212_sc_y2_rfi_harness import derive, STOP, CONTINUE, CALLBACK, OBSERVER, NEXT_END
from derive_v212_sc_y2_rfi_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V212(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(source)
        cls.after=derive(source)

    def test_genuine_osloadcontext_rfi_and_snapshot(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("addr==0x805229b4u&&ctx.lr==0x80526cbcu",
                       "ctx.gpr[3]","v212_expected_pc=ctx.mmu.read32(selected+408u)",
                       "v212_expected_msr=ctx.mmu.read32(selected+412u)",
                       "v211_next_seen==1u&&v212_rfi_seen==0u",
                       "ctx.gpr==v212_expected_gprs",
                       "ctx.inst_count>v212_load_inst"):
            self.assertIn(marker,CONTINUE+OBSERVER)
        self.assertIn(CALLBACK,self.after)

    def test_no_synthetic_guest_restore_or_ios_pump(self):
        for token in ("ipc70_bus.tick(","scheduler.service_one(","ipc70_bus.write32(",
                      "ipc70_ram.write8(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for segment in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "service_one(","ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(forbidden,segment)
        with self.assertRaises(ValueError):derive("invalid base")

    def test_owner_16_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v212_sc_y2_rfi_harness.py",script)
        self.assertIn("V211_SC_Y2_RESCHED_NEXT verified=1",script)
        self.assertIn("V212_SC_Y2_RFI verified=1",script)
        line="V212_Y2_RFI pc=1 msr=1 regs=1 irq_down=1 queue=1 open=1 coherent=1 sc=1 ee=1 idle=0 thread=1"
        self.assertIsNotNone(re.fullmatch(PASS,line))
        self.assertIsNotNone(re.fullmatch(PATTERN,line.replace("regs=1","regs=0")))
        self.assertIsNone(re.fullmatch(PASS,line.replace("pc=1","pc=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v212-sc-y2-rfi.yml").read_text()
        for marker in ("run_v212_sc_y2_rfi.sh","test_v212_sc_y2_rfi.py","V212_SC_Y2_RFI verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v212_sc_y2_rfi.sh").read_text())):
                path=Path(td)/name;path.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
