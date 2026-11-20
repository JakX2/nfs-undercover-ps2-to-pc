#!/usr/bin/env python3
"""V129 original-free OSDisableInterrupts native successor regression."""
from pathlib import Path
import subprocess,tempfile,unittest
from derive_v128_next_function_harness import derive as previous
from derive_v129_irq_disable_harness import derive,EDITS
from derive_v129_irq_disable_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V129(unittest.TestCase):
    def test_original_interrupt_helper_is_not_stubbed(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        old=previous(src);actual=derive(src);expected=old
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:96])
            expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        for s in ("addr==0x805265acu&&ctx.lr==0x8052f84cu",
                  "V129_NEXT_CALL pc=",
                  "post129_next==1u&&nwii::runtime::post128_next==1u",
                  "nwii::runtime::post90_target==nwii::runtime::post129_pc&&"):
            self.assertIn(s,actual)
        for s in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(s),old.count(s))
    def test_runner_uses_v129_and_inherited_original_fixture(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for x in ('python3 "$here/derive_v129_irq_disable_harness.py"',
                  'python3 "$here/derive_v128_next_function_generator.py"',
                  "restore_v128_next_function.py","V128_ORIGINAL_RESTORE ok=1",
                  "V128_NEXT_CALL pc=805265ac lr=8052f84c",
                  "V129_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V129_STAGE native_test_passed",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=129"):
            self.assertIn(x,s)
        self.assertNotIn('python3 "$here/derive_v128_next_function_harness.py"',s)
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"run.sh";out.write_text(s)
            subprocess.run(["bash","-n",str(out)],check=True)
    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v129-irq-disable.yml").read_text()
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for s in ("run_v129_continuous_irq_disable.sh","V129_STAGE native_test_passed",
                  "V128_ORIGINAL_RESTORE ok=1",
                  "V129_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(s,wf)
if __name__=="__main__":unittest.main()
