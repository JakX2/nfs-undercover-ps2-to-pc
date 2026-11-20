#!/usr/bin/env python3
"""Owner-free V128 71-instruction original helper checkpoint regression."""
from pathlib import Path
import subprocess,tempfile,unittest
from derive_v127_osinit_first_bl_harness import derive as previous
from derive_v128_next_function_harness import derive,EDITS
from derive_v128_next_function_runner import derive as runner
HERE=Path(__file__).resolve().parent

class OriginalHelperV128(unittest.TestCase):
    def test_harness_still_preserves_earlier_original_logic(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        original=previous(src);actual=derive(src);expected=original
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:95])
            expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        self.assertEqual(actual,derive(src))
        for m in ("V128_NEXT_CALL pc=","addr==0x8052f830u&&ctx.lr==0x80520970u",
                  "post128_next==1u&&nwii::runtime::post127_next==1u",
                  "post90_target==nwii::runtime::post128_pc&&"):
            self.assertIn(m,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),original.count(m))
    def test_runner_extends_authentic_v127_fixture(self):
        actual=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ('python3 "$here/derive_v128_next_function_harness.py"',
                  'python3 "$here/derive_v128_next_function_generator.py"',
                  "make_v125_canonical_fixture.py","restore_v127_osinit_tail.py",
                  "restore_v128_next_function.py",
                  "V127_OSINIT_RESTORE ok=1","V128_ORIGINAL_RESTORE ok=1",
                  "V128_STAGE native_test_passed",
                  "V127_NEXT_CALL pc=8052f830 lr=80520970",
                  "V128_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=128"):
            self.assertIn(m,actual)
        self.assertNotIn('python3 "$here/derive_v127_osinit_first_bl_harness.py"',actual)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"runner.sh"
            p.write_text(actual)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_private_workflow_and_cleanup(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v128-next-function-execution.yml").read_text()
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for key in ("run_v128_continuous_next_function.sh","restore_v128_next_function.py",
                    "V128_ORIGINAL_RESTORE ok=1","V128_STAGE native_test_passed",
                    "V128_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                    "BOOT_PROGRESS entry=0x8000403C pc=0x[0-9A-F]{8} stage=128",
                    "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(key,wf)
        for name in ("run_v128_continuous_next_function.sh","diagnose_next_function_v128.py"):
            self.assertTrue((HERE/name).is_file())
if __name__=="__main__":
    unittest.main()
