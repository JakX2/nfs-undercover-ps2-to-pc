#!/usr/bin/env python3
"""V151 original-free verification of SC guest continuation after IRQ flag W1C."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v150_sc_irq_flag_harness import derive as previous
from derive_v151_sc_post_flag_harness import (
    derive, STATE, RESET, MMIO_STOP, MMIO_CONTINUE, OBSERVER,
    V146_ONCE, NEXT_TRIAL,
)
from derive_v151_sc_post_flag_runner import derive as runner, PASS

HERE=Path(__file__).resolve().parent
class V151(unittest.TestCase):
    def setUp(self):
        self.base=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8")

    def test_releases_only_native_flag_checkpoint(self):
        old=previous(self.base)
        new=derive(self.base)
        for marker in (STATE,RESET,MMIO_STOP,V146_ONCE):
            self.assertEqual(old.count(marker),1,marker[:72])
        self.assertIn(MMIO_CONTINUE,new)
        self.assertIn(OBSERVER,new)
        self.assertIn(NEXT_TRIAL,new)
        self.assertEqual(new.count("V151_SC_AFTER_FLAG cleared="),1)
        self.assertIn("ctx.inst_count>v151_flag_inst",OBSERVER)
        self.assertIn("ctx.gpr[13]==v147_first_r13",OBSERVER)
        self.assertIn("queued_replies()==1u",OBSERVER)
        self.assertIn("!ipc70_bus.external_irq_level()",OBSERVER)
        self.assertIn("((*flags&H::IPC_PPC)==0u)",OBSERVER)
        self.assertIn("((*control&M::Y2)==0u)",OBSERVER)

    def test_no_artificial_ios_success_or_guest_writes(self):
        old=previous(self.base)
        new=derive(self.base)
        for token in ("ctx.mmu.write8(", "ctx.mmu.write16(",
                      "ctx.mmu.write32(", "ipc70_ram.write8(",
                      "ipc70_bus.write32(", "ipc70_bus.tick(",
                      "v139_scheduler.service_one("):
            self.assertEqual(new.count(token),old.count(token),token)
        for pattern in (r"ctx\.gpr\[[^\]]+\]\s*=(?!=)",
                        r"ctx\.cr\[0\]\.eq\s*=(?!=)",
                        r"ctx\.msr\s*=(?!=)"):
            self.assertEqual(len(re.findall(pattern,new)),
                             len(re.findall(pattern,old)),pattern)

    def test_sixteen_trial_source_only_regressions(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for token in ("derive_v151_sc_post_flag_harness.py",
                      "V149_SC_IPC_ACK verified=1",
                      "V150_SC_IRQ_CLEAR verified=1",
                      "V151_SC_AFTER_FLAG verified=1",
                      'test "$(grep -Ec'):
            self.assertIn(token,script)
        self.assertTrue(re.fullmatch(PASS,
            "V151_SC_AFTER_FLAG cleared=1 irq_down=1 queued=1 masked=1 progressed=1 text=1 target=8051905c lr=805193b8"))
        self.assertFalse(re.fullmatch(PASS,
            "V151_SC_AFTER_FLAG cleared=1 irq_down=0 queued=1 masked=1 progressed=1 text=1 target=8051905c lr=805193b8"))
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runner.sh";p.write_text(script)
            subprocess.run(["bash","-n",str(p)],check=True)

    def test_fail_closed_and_private_cleanup(self):
        with self.assertRaises(ValueError):derive("invalid")
        with self.assertRaises(ValueError):runner("invalid")
        wf=(HERE.parents[1]/".github/workflows/wii-v151-sc-post-flag.yml").read_text()
        self.assertIn("run_v151_sc_post_flag.sh",wf)
        self.assertIn("V151_SC_AFTER_FLAG verified=1",wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)

if __name__=="__main__":
    unittest.main()
