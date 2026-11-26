import os,subprocess,unittest
from pathlib import Path
from unittest.mock import patch
import audit_v1041_transfer_abi as a
D=b'V1034_QUEUE_DETAIL mismatch_mask=128 slot_kind=1 arg_time_zero=1 queue_time_zero=0'
H=b'V1037_QUEUE_HISTORY initial_mismatch=128 current_mismatch=128 changed=0 initial_slot_kind=1 samples=256'
T=b'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match=0 callback_known=1 admitted=0 visits=15 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
A=b'V1040_TRANSFER_ABI admission=2 timing_only=1 unchanged_slot=1 call_executed=0 boot_verified=0'
class Audit(unittest.TestCase):
    def test_independent_policy(self):
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            def inspect(*rows,rc=0):return a.inspect(b'\n'.join(rows),rc)
            self.assertTrue(inspect(D,H,T,A)[1])
            for mask in (64,192):
                self.assertTrue(inspect(D.replace(b'128',str(mask).encode()),H.replace(b'128',str(mask).encode()),T,A)[1])
            for rows in ((D,H,T),(D,H,T,A,A),(D,H,T,A,b'V958_ACK_INVALID'),(D,H,T,A.replace(b'admission=2',b'admission=1')),
                         (D.replace(b'128',b'129'),H.replace(b'128',b'129'),T,A),
                         (D,H.replace(b'changed=0',b'changed=128'),T,A),
                         (D,H.replace(b'initial_slot_kind=1',b'initial_slot_kind=2'),T,A),
                         (D,H.replace(b'current_mismatch=128',b'current_mismatch=64'),T,A),
                         (D,H,T.replace(b'callback_known=1',b'callback_known=0'),A),
                         (D,H,A,T),(D,H,T,A.replace(b'call_executed=0',b'call_executed=1'))):
                self.assertFalse(inspect(*rows)[1])
            self.assertFalse(inspect(D,H,T,A,rc=126)[1])
            rejected=A.replace(b'admission=2 timing_only=1 unchanged_slot=1',b'admission=0 timing_only=0 unchanged_slot=0')
            self.assertTrue(inspect(D,H.replace(b'changed=0',b'changed=128'),T,rejected)[1])
    def test_launch_contract(self):
        here=Path(__file__).resolve().parent
        env={k:v for k,v in os.environ.items() if not k.startswith('UNDERCOVER_RUN_')}
        env['UNDERCOVER_RUN_V1040_SIX_ARGS']='1'
        cmd=['bash',str(here/'run_v575_dsp_sc_launch.sh'),'--describe-mode','irq-si-handler-suffix']
        self.assertEqual(subprocess.run(cmd,env=env,capture_output=True,timeout=5).returncode,2)
        for flag in ('V919_HANDLER_EPILOGUE','V920_HANDLER_RETURN','V921_CAPTURE_JOIN','V922_IRQ_RETURN','V932_PENDING_RFI','V939_SECOND_VECTOR','V951_SECOND_DISPATCH','V958_SECOND_ACK','V967_POST_ACK','V989_SHARED_COMPLETION','V975_SECOND_TIME','V981_SECOND_FRONTIER','V995_SUCCESS_FRONTIER','V1015_ERROR_COMPLETION','V1021_ERROR_FRONTIER'):
            env['UNDERCOVER_RUN_'+flag]='1'
        self.assertEqual(subprocess.run(cmd,env=env,capture_output=True,timeout=5).returncode,2)
        env['UNDERCOVER_RUN_V1034_QUEUE_DETAIL']='1'
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=5)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('audit=audit_v1041_transfer_abi.py',p.stdout)
        self.assertIn('UNDERCOVER_V1040_SIX_ARGS=1',p.stdout)
        self.assertNotIn('UNDERCOVER_V1028_THIRD_TRANSFER=1',p.stdout)
if __name__=='__main__':unittest.main()
