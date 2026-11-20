#!/usr/bin/env python3
"""V152 source-only protection of original SC post-IRQ helper execution."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v151_sc_post_flag_harness import derive as previous
from derive_v152_sc_post_helper_harness import (
    derive,STATE,RESET,STOP,CONTINUE,OBSERVER,V146_ONCE,NEXT_TRIAL,
)
from derive_v152_sc_post_helper_runner import derive as runner, PASS
HERE=Path(__file__).resolve().parent

class V152(unittest.TestCase):
    def setUp(self):
        self.original=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_execute_original_first_post_irq_helper(self):
        prior=previous(self.original)
        actual=derive(self.original)
        for anchor in (STATE,RESET,STOP,V146_ONCE):
            self.assertEqual(prior.count(anchor),1,anchor[:60])
        self.assertNotIn(STOP,actual)
        self.assertIn(CONTINUE,actual)
        self.assertIn(OBSERVER,actual)
        self.assertIn(NEXT_TRIAL,actual)
        self.assertIn("addr==0x8051b060u&&ctx.lr==0x805193a4u",CONTINUE)
        self.assertIn("ctx.inst_count>v152_start_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertIn("!ipc70_bus.external_irq_level()",OBSERVER)
        self.assertEqual(actual.count("V152_SC_POST_HELPER clean="),1)

    def test_guest_and_ios_state_are_read_only(self):
        prior=previous(self.original)
        actual=derive(self.original)
        for expr in ("ctx.mmu.write8(", "ctx.mmu.write16(", "ctx.mmu.write32(",
                     "ipc70_ram.write8(", "ipc70_bus.write32(", "ipc70_bus.tick(",
                     "v139_scheduler.service_one("):
            self.assertEqual(prior.count(expr),actual.count(expr),expr)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,prior)),len(re.findall(pattern,actual)),pattern)

    def test_runner_maintains_all_previous_native_gates(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ("derive_v152_sc_post_helper_harness.py",
                  "V150_SC_IRQ_CLEAR verified=1",
                  "V151_SC_AFTER_FLAG verified=1",
                  "V152_SC_POST_HELPER verified=1",
                  'test "$(grep -Ec'):
            self.assertIn(m,script)
        self.assertTrue(re.fullmatch(PASS,
            "V152_SC_POST_HELPER clean=1 idle=1 queued=1 guest=1 text=1 target=8051905c lr=8051b090"))
        self.assertFalse(re.fullmatch(PASS,
            "V152_SC_POST_HELPER clean=1 idle=0 queued=1 guest=1 text=1 target=8051905c lr=8051b090"))
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"runner.sh";f.write_text(script)
            subprocess.run(["bash","-n",str(f)],check=True)

    def test_fail_closed_and_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        workflow=(HERE.parents[1]/".github/workflows/wii-v152-sc-post-helper.yml").read_text()
        self.assertIn("run_v152_sc_post_helper.sh",workflow)
        self.assertIn("V152_SC_POST_HELPER verified=1",workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
