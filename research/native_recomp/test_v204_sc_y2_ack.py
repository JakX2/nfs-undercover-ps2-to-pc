#!/usr/bin/env python3
"""V204 original-free second-Y2 real PPCCTRL acknowledgment tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v203_sc_y2_distinct_harness import derive as previous,NEXT_END as PREVIOUS_END
from derive_v204_sc_y2_ack_harness import derive,STOP,CONTINUE,ACK,NEXT_END
from derive_v204_sc_y2_ack_runner import derive as runner,PATTERN,PASS
from derive_v172_sc_y1_ack_harness import MMIO_ANCHOR
HERE=Path(__file__).resolve().parent

class V204(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")
        cls.before=previous(base)
        cls.after=derive(base)

    def test_guest_writer_executes_from_authenticated_second_y2_callsite(self):
        self.assertIn(STOP,self.before)
        self.assertNotIn(STOP,self.after)
        self.assertIn(CONTINUE,self.after)
        self.assertIn("addr==0x8051906cu&&ctx.lr==0x80519380u",CONTINUE)
        self.assertIn("v204_helper_inst=ctx.inst_count",CONTINUE)
        self.assertIn("v204_mmio_begin=mmio_writes.size()",CONTINUE)
        self.assertIn("v196_live&&v203_distinct_seen==1u&&v204_ack_seen==0u",ACK)
        for token in ("(value&M::Y2)!=0u","((*ctrl&M::Y2)==0u)",
                      "((*flags&H::IPC_PPC)!=0u)","queued_replies()==1u",
                      "ipc70_ram.cpu->lr==0x80519380u","v204_helper_inst",
                      "mmio_writes.size()>v204_mmio_begin",
                      "read8(sc_addr)==1u"):
            self.assertIn(token,ACK)
        self.assertIn(MMIO_ANCHOR+"\n"+ACK.rstrip("\n"),self.after)
        self.assertIn(NEXT_END,self.after)
        self.assertNotIn(PREVIOUS_END,self.after)

    def test_ack_is_observed_after_native_bus_write_not_injected(self):
        for token in ("ipc70_bus.tick(", "scheduler.service_one(", "ctx.mmu.write32(",
                      "ipc70_bus.write32(", "ipc70_ram.write8("):
            self.assertEqual(self.before.count(token),self.after.count(token))
        for snippet in (CONTINUE,ACK,NEXT_END):
            for forbidden in ("ipc70_bus.write","ipc70_ram.write","service_one(",
                              "ipc70_bus.tick(","ctx.mmu.write"):
                self.assertNotIn(forbidden,snippet)
        self.assertEqual(self.before.count(MMIO_ANCHOR),1)
        self.assertNotRegex(ACK,r"\bipc70_ram\.cpu->(?:msr|pc|lr|srr0|srr1)\s*=(?!=)")
        with self.assertRaises(ValueError):
            derive("invalid")

    def test_owner_original_gate_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        self.assertIn("derive_v204_sc_y2_ack_harness.py",script)
        self.assertIn("V203_SC_Y2_DISTINCT verified=1",script)
        self.assertIn("V204_SC_Y2_ACK verified=1",script)
        self.assertIn(')" -eq 16',script)
        good="V204_Y2_ACK write=1 w1c=1 flag=1 queued=1 guest=1 progressed=1 sc=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("flag=1","flag=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("queued=1","queued=0")))
        workflow=(HERE.parents[1]/".github/workflows/wii-v204-sc-y2-ack.yml").read_text()
        self.assertIn("run_v204_sc_y2_ack.sh",workflow)
        self.assertIn("test_v204_sc_y2_ack.py",workflow)
        self.assertIn("V204_SC_Y2_ACK verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"runner.sh";p.write_text(script,encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)
            p=Path(directory)/"entry.sh"
            p.write_text((HERE/"run_v204_sc_y2_ack.sh").read_text(),encoding="utf-8")
            subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
