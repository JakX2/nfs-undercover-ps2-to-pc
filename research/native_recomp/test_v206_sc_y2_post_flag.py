#!/usr/bin/env python3
"""V206 original-free second IRQ post-Hollywood guest successor assertions."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v205_sc_y2_flag_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v206_sc_y2_post_flag_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END
from derive_v206_sc_y2_post_flag_runner import derive as runner, PATTERN, PASS
from derive_v185_sc_reply_next_harness import OBSERVER_HEADER
HERE=Path(__file__).resolve().parent

class V206(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_real_guest_continues_only_from_authenticated_irq_ack(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER_HEADER+"\n"+OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        for marker in ("v196_live&&v205_flag_seen==1u&&v206_post_seen==0u",
                       "ctx.pc==addr","ctx.inst_count>v206_after_flag_inst",
                       "((*ctrl&Mail::Y2)==0u)","((*flag&Irq::IPC_PPC)==0u)",
                       "queued_replies()==1u","IOS::Open",
                       "ctx.gpr[13]==v147_first_r13","read8(sc_addr)==1u",
                       "v206_post_pc=addr;v206_post_lr=ctx.lr"):
            self.assertIn(marker,OBSERVER)

    def test_read_only_probe_no_host_ios_pump_or_cpu_patch(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for part in (CONTINUE,OBSERVER,NEXT_END):
            for forbidden in ("ipc70_bus.write", "ipc70_ram.write","service_one(",
                              "ipc70_bus.tick(","ctx.mmu.write","ctx.gpr["):
                self.assertNotIn(forbidden,part)
        self.assertNotRegex(OBSERVER,r"\bctx\.(?:msr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_owner_gate_sixteen_trials_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v206_sc_y2_post_flag_harness.py",script)
        self.assertIn("V205_SC_Y2_FLAG verified=1",script)
        self.assertIn("V206_SC_Y2_POST_FLAG verified=1",script)
        good="V206_Y2_POST ack=1 irq_down=1 queued=1 open=1 guest=1 masked=1 coherent=1 sc=1 pc=80529434 lr=80526cb0"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("open=1","open=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("queued=1","queued=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v206-sc-y2-post-flag.yml").read_text()
        self.assertIn("run_v206_sc_y2_post_flag.sh",wf)
        self.assertIn("test_v206_sc_y2_post_flag.py",wf)
        self.assertIn("V206_SC_Y2_POST_FLAG verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"runner.sh"
            path.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(path)],check=True)
            path=Path(d)/"entry.sh"
            path.write_text((HERE/"run_v206_sc_y2_post_flag.sh").read_text(encoding="utf-8"))
            subprocess.run(["bash","-n",str(path)],check=True)

if __name__=="__main__":
    unittest.main()
