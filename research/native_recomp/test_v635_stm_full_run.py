import unittest
from pathlib import Path
from test_v628_startup_census import ALL,log,D
from audit_v629_stm_open import inspect,STAGES
from audit_v591_memory_init import STAGES as MI,mapper_diagnostic
HERE=Path(__file__).parent
class Tests(unittest.TestCase):
    def test_full_launch_contract(self):
        workflow=(HERE.parent.parent/'.github/workflows/wii-v628-startup-exec.yml').read_text()
        self.assertEqual(workflow.count('--run-stm-open'),1)
        self.assertNotIn('--run-ipc-client',workflow)
        self.assertIn('cancel-in-progress: false',workflow)
        launcher=(HERE/'run_v575_dsp_sc_launch.sh').read_text()
        self.assertIn('UNDERCOVER_V629_STM=1);audit=audit_v629_stm_open.py',launcher)
        self.assertIn('UNDERCOVER_V625_IPC=1',launcher)
        self.assertIn('mapper_diagnostic',launcher)
    def test_stm_failure_preserves_verified_ipc(self):
        rows,ok=inspect(log(ALL+STAGES[:2]+[b'V629_STM_INVALID reason=5 stage=2']),121)
        self.assertFalse(ok)
        self.assertIn('sc=1 dsp=1 mi=1 report=1 arena=1 irq=1 ipc=1',rows[2])
        self.assertIn('ipc=1 stages=2 verified=0',rows[-1])
    def test_early_mi_failure_not_a_stm_proof(self):
        diag=b'V620_MI_MAPPER refusal=6750272 bat_count=0 msr=2'
        raw=log(D+MI[:11]+[b'V591_MI_INVALID reason=4 stage=11',diag])
        rows,ok=inspect(raw,115)
        self.assertFalse(ok)
        self.assertIn('mi=11/20',rows[1])
        self.assertIn('ipc=0 stages=0 verified=0',rows[-1])
        self.assertEqual(mapper_diagnostic(raw,115),diag.decode())
if __name__=='__main__':unittest.main()
