#!/usr/bin/env python3
"""Original-free third negative IOS Y1 registered IPC handler V220."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v219_sc_y1_osdisable_harness import derive as previous, OBSERVER as PREVIOUS_OBSERVER, NEXT_END as PREVIOUS_END
from derive_v220_sc_y1_ipc_handler_harness import derive, STOP, CONTINUE, OBSERVER, NEXT_END, V220_SCOPED_V98
from derive_v220_sc_y1_ipc_handler_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent
class V220(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base);cls.after=derive(base)
    def test_real_irq_dispatches_registered_ipc_handler(self):
        self.assertIn(STOP,PREVIOUS_OBSERVER)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn(OBSERVER,self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)
        from derive_v178_sc_reply_burst_harness import V98_ACTIVE
        self.assertEqual(self.before.count(V98_ACTIVE),1)
        self.assertNotIn(V98_ACTIVE,self.after)
        self.assertIn(V220_SCOPED_V98,self.after)
        self.assertEqual(self.after.count(V220_SCOPED_V98),1)
        for token in ("v219_disable_seen==1u","addr==0x80519318u",
                      "ctx.lr==0x80526cacu","ctx.gpr[3]==27u&&ctx.ctr==addr",
                      "ctx.mmu.read32(IRQ_TABLE+27u*4u)==addr",
                      "v215_saved_msr&undercover::wii::ExternalSrr1Mask",
                      "ctx.inst_count>v220_disable_inst",
                      "int32_t(ipc70_ram.read32(v183_second_phys+4u))==IOS::Invalid",
                      "++v220_ipc_seen"):
            self.assertIn(token,OBSERVER)
        # Categorize only public assertion failures; no private guest data.
        for label in ("Y1 signal","negative response","OS IRQ context",
                      "IRQ caller ABI","guest SDA and instruction progress",
                      "guest EE state","SC status"):
            self.assertIn("V220_NEG_IPC source-owned "+label+" check failed",OBSERVER)
        self.assertNotIn("ctx.gpr[3]==4u",OBSERVER)
        with self.assertRaises(ValueError):derive("unmatched source")
    def test_no_synthetic_game_or_ios_state(self):
        for needle in ("scheduler.service_one(","ipc70_ram.write8(",
                       "ipc70_bus.write32(","ctx.mmu.write32("):
            self.assertEqual(self.before.count(needle),self.after.count(needle))
        for body in (CONTINUE,OBSERVER,NEXT_END):
            for bad in ("ipc70_bus.write","ipc70_ram.write","ctx.mmu.write","ctx.pc=0x"):
                self.assertNotIn(bad,body)
            self.assertNotRegex(body,r"ctx\.gpr\[[0-9]+\]\s*=(?!=)")
    def test_sixteen_owner_original_trials_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("V219_SC_Y1_OSDISABLE verified=1",
                      "derive_v220_sc_y1_ipc_handler_harness.py",
                      "V220_SC_Y1_IPC_HANDLER verified=1"):
            self.assertIn(token,script)
        good="V220_NEG_IPC irq=1 reply=1 context=1 caller=1 guest=1 masked=1 sc=1 pc=80519318 lr=80526cac"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNone(re.fullmatch(PASS,good.replace("reply=1","reply=0")))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("guest=1","guest=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v220-sc-y1-ipc-handler.yml").read_text()
        for token in ("run_v220_sc_y1_ipc_handler.sh","test_v220_sc_y1_ipc_handler.py",
                      "V220_SC_Y1_IPC_HANDLER verified=1"):
            self.assertIn(token,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as directory:
            for name,content in (("runner.sh",script),
                                 ("entry.sh",(HERE/"run_v220_sc_y1_ipc_handler.sh").read_text())):
                p=Path(directory)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)
if __name__=="__main__":
    unittest.main()
