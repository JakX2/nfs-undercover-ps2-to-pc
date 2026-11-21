#!/usr/bin/env python3
"""Original-free V211 source and owner runner regression."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v210_sc_y2_restore_next_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v211_sc_y2_resched_next_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v211_sc_y2_resched_next_runner import derive as runner, PATTERN, PASS
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
HERE=Path(__file__).resolve().parent

class V211(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        cls.before=previous(src);cls.after=derive(src)

    def test_native_continuation_preserves_previous_boundary(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER_HEADER+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for s in ("addr==0x80529940u&&ctx.lr==0x80526cb4u",
                  "v210_next_seen==1u&&v211_next_seen==0u",
                  "ctx.inst_count>v211_start_inst",
                  "v211_target_pc=addr;v211_target_lr=ctx.lr"):
            self.assertIn(s,CONTINUE+OBSERVER)

    def test_no_guest_mutation_or_implicit_ios(self):
        for needle in ("ipc70_bus.tick(","scheduler.service_one(",
                       "ipc70_bus.write32(","ipc70_ram.write8(",
                       "ctx.mmu.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for chunk in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write",
                              "service_one(","ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(forbidden,chunk)
        with self.assertRaises(ValueError):derive("unmatched")

    def test_16_owner_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v211_sc_y2_resched_next_harness.py",script)
        self.assertIn("V210_SC_Y2_RESTORE_NEXT verified=1",script)
        self.assertIn("V211_SC_Y2_RESCHED_NEXT verified=1",script)
        good="V211_Y2_RESCHED y2=1 irq_down=1 queue=1 open=1 replied=0 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=0 pc=80529434 lr=80526cb0"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("caller=1","caller=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v211-sc-y2-resched-next.yml").read_text()
        for marker in ("run_v211_sc_y2_resched_next.sh","test_v211_sc_y2_resched_next.py","V211_SC_Y2_RESCHED_NEXT verified=1"):
            self.assertIn(marker,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as td:
            for name,content in (("runner",script),("wrapper",(HERE/"run_v211_sc_y2_resched_next.sh").read_text())):
                p=Path(td)/name;p.write_text(content)
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
