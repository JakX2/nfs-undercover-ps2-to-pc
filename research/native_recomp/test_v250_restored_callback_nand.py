#!/usr/bin/env python3
"""V250 original-free candidate-only genuine NAND callback callsite tests."""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from derive_v244_sc_callback_link_harness import derive as previous_cpp
from derive_v250_restored_callback_nand_harness import (
    derive as candidate_cpp, OBSERVER, OWNER, OWNER_NEW,
)
from derive_v250_restored_callback_nand_runner import derive as runner, NAND, PASS, STAGE
HERE=Path(__file__).resolve().parent

class V250(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cxx=previous_cpp((HERE/"test_start_to_ipc_ack_v77.cpp").read_text(encoding="utf-8"))
        cls.before=cxx
        cls.after=candidate_cpp(cxx)

    def test_candidate_mode_isolated_from_previous_owner(self):
        self.assertIn(OWNER,self.before)
        self.assertNotIn(OWNER,self.after)
        self.assertIn(OWNER_NEW,self.after)
        self.assertIn('std::string(argv[2])=="owner"',self.after)
        self.assertIn('std::string(argv[2])=="owner-callback"',self.after)
        # The first test-only ExceptionStop precedes the IOS callback.
        self.assertNotIn("V250 original restored callback NAND checkpoint missing",self.after)
        self.assertNotIn("V250_PHASE cb=",self.after)
        self.assertIn('check(exception_stop,"exception initialization did not reach exact test-only syscall");',self.after)
        self.assertIn('V244 original callback nested link provenance missing',self.after)
        with self.assertRaises(ValueError):candidate_cpp("invalid public C++")
        self.assertEqual(self.after.count('V250_NAND_BCTRL auth='),1)

    def test_authentic_ppc_nested_callback_contract(self):
        for marker in (
            'addr==0x804f0e04u','addr==0x8051e06cu',
            'v244_cb_seen==1u','v244_nested_target==addr',
            'v250_initial_sp-ctx.gpr[1]==16u',
            'ctx.lr==0x804f0f54u',
            'ctx.ctr==addr',
            'ctx.gpr[3]==v250_initial_r3',
            'ctx.gpr[4]==ctx.mmu.read32(v250_userdata+260u)',
            'ctx.inst_count>v250_initial_inst',
            'ipc70_ram.read32(v153_phys)==undercover::wii::StmIos::Reply',
            '++v250_nand_seen',
            'return; // continue executing original NAND callback',
            'V250_CB_BEGIN candidate=1 reply='
        ):
            self.assertIn(marker,OBSERVER)
        self.assertNotIn("throw ExceptionStop{};",OBSERVER)
        self.assertIn("ctx.pc==addr&&addr==0x8051e06cu",OBSERVER)
        for fragment in ("ipc70_ram.write","ctx.mmu.write","ipc70_bus.write"):
            self.assertNotIn(fragment,OBSERVER)
        self.assertIsNone(re.search(r"ctx\.pc\s*=(?!=)",OBSERVER))
        self.assertIsNone(re.search(r"ctx\.gpr\[3\]\s*=(?!=)",OBSERVER))
        self.assertEqual(self.after.count('V244 original callback nested link provenance missing'),
                         self.before.count('V244 original callback nested link provenance missing'))

    def test_owner_original_checks_and_16_trials(self):
        script=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text(encoding="utf-8"))
        for marker in ('V249_SC_AUTH_CALLBACK_LINK verified=1',
                       'V250_SC_NAND_BCTRL verified=1',
                       'derive_v250_restored_callback_nand_harness.py',
                       '"$work/v250-harness.o" "$work/v249-generated.o" "$work/loader.o"',
                       '"$work/private-v248.dol" owner-callback "$owner"',
                       'timeout 90', 'test "$(grep -Ec'):
            self.assertIn(marker,script)
        good="V250_NAND_BCTRL auth=1 frame16=1 link=1 ctr=1 abi=1 userdata=1 progressed=1 reply=1"
        self.assertIsNotNone(re.fullmatch(PASS,good))
        self.assertIsNotNone(re.fullmatch(NAND,good.replace("link=1","link=0")))
        self.assertIsNone(re.fullmatch(PASS,good.replace("frame16=1","frame16=0")))
        self.assertNotIn("cat \"$work",STAGE)
        self.assertNotIn("upload-artifact",STAGE)
        from diagnose_v250_native_phase import describe
        pub='check(false,"V250 sample public assertion");'
        log='V250_CB_BEGIN candidate=1 reply=1 captured=1\nwhat(): V250 sample public assertion'
        self.assertEqual(describe(log,pub),
            "V250_PUBLIC_FAILURE id=0001 label=V250 sample public assertion callback=1 nand=0 trials=0")
        self.assertEqual(describe("what(): PRIVATE_SECRET",pub),
            "V250_PUBLIC_FAILURE id=0000 label=other callback=0 nand=0 trials=0")
        self.assertIn("diagnose_v250_native_phase.py",STAGE)
        self.assertNotIn('cat "$work/v250-native.log"',STAGE)
        workflow=(HERE.parents[1]/".github/workflows/wii-v250-restored-callback-nand.yml").read_text()
        for marker in ('run_v250_restored_callback_nand.sh',
                       'test_v250_restored_callback_nand.py',
                       'V250_SC_NAND_BCTRL verified=1'):
            self.assertIn(marker,workflow)
        self.assertEqual(workflow.count("      - name: Remove private owner and generated code"),1)
        self.assertNotIn("upload-artifact",workflow)
        with tempfile.TemporaryDirectory() as temp:
            for name,content in (("runner",script),
                                 ("wrapper",(HERE/"run_v250_restored_callback_nand.sh").read_text(encoding="utf-8"))):
                p=Path(temp)/name;p.write_text(content,encoding="utf-8")
                subprocess.run(["bash","-n",str(p)],check=True)

if __name__=="__main__":
    unittest.main()
