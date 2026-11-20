#!/usr/bin/env python3
"""Original-free V130 PPC interrupt-restore continuation tests."""
from pathlib import Path
import subprocess,tempfile,unittest
from derive_v129_irq_disable_harness import derive as previous
from derive_v130_irq_restore_harness import derive,EDITS
from derive_v130_irq_restore_runner import derive as runner
HERE=Path(__file__).resolve().parent
class V130(unittest.TestCase):
    def test_harness_explicit_original_provenance(self):
        src=(HERE/"test_start_to_ipc_ack_v77.cpp").read_text()
        prev=previous(src);actual=derive(src);expected=prev
        for a,b in EDITS:
            self.assertEqual(expected.count(a),1,a[:90])
            expected=expected.replace(a,b,1)
        self.assertEqual(actual,expected)
        for m in ("addr==0x805265d4u&&ctx.lr==0x8052f92cu",
                  "V130_NEXT_CALL pc=",
                  "post130_next==1u&&nwii::runtime::post129_next==1u",
                  "nwii::runtime::post90_target==nwii::runtime::post130_pc&&"):
            self.assertIn(m,actual)
        for m in ("ctx.mmu.write","seed_stm_data(","ipc70_bus.reset()"):
            self.assertEqual(actual.count(m),prev.count(m))
    def test_runner_and_original_fixture(self):
        s=runner((HERE/"run_v79_continuous_reply_entry.sh").read_text())
        for m in ('python3 "$here/derive_v130_irq_restore_harness.py"',
                  'python3 "$here/derive_v128_next_function_generator.py"',
                  "restore_v128_next_function.py","V128_ORIGINAL_RESTORE ok=1",
                  "V129_NEXT_CALL pc=805265d4 lr=8052f92c",
                  "V130_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "V130_STAGE native_test_passed",
                  "BOOT_PROGRESS entry=0x8000403C pc=0x${candidate^^} stage=130"):
            self.assertIn(m,s)
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"run.sh";p.write_text(s)
            subprocess.run(["bash","-n",str(p)],check=True)
    def test_workflow(self):
        wf=(HERE.parents[1]/".github/workflows/wii-v130-irq-restore.yml").read_text()
        self.assertEqual(wf.count("      - name: Remove private owner and generated code"),1)
        for m in ("run_v130_continuous_irq_restore.sh","V130_STAGE native_test_passed",
                  "V128_ORIGINAL_RESTORE ok=1",
                  "V130_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8}",
                  "WII_ORIGINAL_DOL_ID","WII_ORIGINAL_ELF_ID"):
            self.assertIn(m,wf)
if __name__=="__main__":
    unittest.main()
