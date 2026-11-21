#!/usr/bin/env python3
"""Original-free V252 isolated original NAND callback bctrl guest-entry proof."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as base
from derive_v250_restored_callback_nand_harness import derive as previous
from derive_v252_nand_guest_entry_harness import derive, FALLTHROUGH, BOUNDED_STOP, VERIFY
from derive_v252_nand_guest_entry_runner import derive as runner, PATTERN, PASS
HERE=Path(__file__).resolve().parent

class V252(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s=base((HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8"))
        cls.before=previous(s)
        cls.after=derive(s)

    def test_original_callback_guest_entry_stop_and_fail_closed_seam(self):
        self.assertIn(FALLTHROUGH,self.before)
        self.assertNotIn(FALLTHROUGH,self.after)
        self.assertIn(BOUNDED_STOP,self.after)
        self.assertIn(VERIFY,self.after)
        self.assertIn("if(v250_probe){",VERIFY)
        self.assertIn("continue; // candidate-only isolated proof",VERIFY)
        self.assertIn('V178 owner-original SC reply callee differs from V177 proof',self.after)
        self.assertEqual(self.before.count('V244 original callback nested link provenance missing'),
                         self.after.count('V244 original callback nested link provenance missing'))
        for x in ("v250_initial_sp-c.gpr[1]==16u",
                  "c.pc==0x8051e06cu",
                  "c.lr==0x804f0f54u",
                  "c.ctr==0x8051e06cu",
                  "v244_cb_registered&&v244_cb_abi",
                  "v244_nested_target==0x8051e06cu",
                  "v250_nand_seen==1u&&v252_nand_entry_seen==1u",
                  "v183_second_phys==0u",
                  "V252_NAND_GUEST checked="):
            self.assertIn(x,VERIFY)
        with self.assertRaises(ValueError):derive("unmatched source")

    def test_no_guest_mutation_and_unchanged_baseline_mode(self):
        for x in ("ipc70_bus.tick(","scheduler.service_one(",
                  "ipc70_bus.write32(","ipc70_ram.write8(",
                  "c.mmu.write32("):
            self.assertEqual(self.before.count(x),self.after.count(x))
        for x in ("c.mmu.write","ipc70_ram.write","ipc70_bus.write",
                  "c.gpr[3]=","c.pc=0x8051e06c"):
            self.assertNotIn(x,VERIFY+BOUNDED_STOP)
        self.assertIn('const bool v250_probe=std::string(argv[2])=="owner-callback";',self.after)
        self.assertIn('const bool owner=v250_probe||std::string(argv[2])=="owner";',self.after)
        self.assertIn("if(v250_probe){",VERIFY)

    def test_owner_trial_gates_and_cleanup(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for x in ("derive_v252_nand_guest_entry_harness.py",
                  "V249_SC_AUTH_CALLBACK_LINK verified=1",
                  "V250_SC_NAND_BCTRL verified=1",
                  "V252_SC_NAND_GUEST verified=1",
                  'for n in $(seq 1 16); do',
                  '"$work/private-v248.dol" owner-callback "$owner"'):
            self.assertIn(x,script)
        good="V252_NAND_GUEST checked=1 regs=1 reply=1 before_second=1 trial=16"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(PATTERN,good.replace("regs=1","regs=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("checked=1","checked=0")))
        wf=(HERE.parents[1]/".github/workflows/wii-v252-nand-guest-entry.yml").read_text()
        for x in ("run_v252_nand_guest_entry.sh","test_v252_nand_guest_entry.py",
                  "V252_SC_NAND_GUEST verified=1"):
            self.assertIn(x,wf)
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",wf)
        with tempfile.TemporaryDirectory() as d:
            for name,contents in (("runner",script),("entry",(HERE/"run_v252_nand_guest_entry.sh").read_text(encoding="utf-8"))):
                p=Path(d)/name;p.write_text(contents,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
