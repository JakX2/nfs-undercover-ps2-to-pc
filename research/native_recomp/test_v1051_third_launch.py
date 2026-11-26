import os,subprocess,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
FLAGS=('V919_HANDLER_EPILOGUE','V920_HANDLER_RETURN','V921_CAPTURE_JOIN','V922_IRQ_RETURN','V932_PENDING_RFI','V939_SECOND_VECTOR','V951_SECOND_DISPATCH','V958_SECOND_ACK','V967_POST_ACK','V989_SHARED_COMPLETION','V975_SECOND_TIME','V981_SECOND_FRONTIER','V995_SUCCESS_FRONTIER','V1015_ERROR_COMPLETION','V1021_ERROR_FRONTIER','V1034_QUEUE_DETAIL','V1040_SIX_ARGS','V1051_THIRD_TRANSFER')
class Launch(unittest.TestCase):
    def plan(self,env,build=False,mode=None):
        script='run_v572_full_sc_translation.sh' if build else 'run_v575_dsp_sc_launch.sh'
        return subprocess.run(['bash',str(HERE/script),'--describe-mode',mode or ('--run-si-handler-suffix' if build else 'irq-si-handler-suffix')],env=env,capture_output=True,text=True,timeout=5)
    def setup_env(self):
        env={k:v for k,v in os.environ.items() if not k.startswith(('UNDERCOVER_RUN_','UNDERCOVER_PREPARE_'))}
        env.update({'UNDERCOVER_RUN_'+f:'1' for f in FLAGS})
        env['UNDERCOVER_PREPARE_V1029_THIRD_TRANSFER']='1'
        return env
    def test_opt_in(self):
        env=self.setup_env()
        for build in (False,True):
            p=self.plan(env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('abi_proof_required=1' if build else 'audit=audit_v1045_third_transfer_abi.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1028_THIRD_TRANSFER=1',p.stdout)
        env.pop('UNDERCOVER_RUN_V1051_THIRD_TRANSFER')
        p=self.plan(env);self.assertIn('audit=audit_v1041_transfer_abi.py',p.stdout)
        self.assertNotIn('UNDERCOVER_V1028_THIRD_TRANSFER=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1040_SIX_ARGS','UNDERCOVER_RUN_V1034_QUEUE_DETAIL','UNDERCOVER_RUN_V1021_ERROR_FRONTIER','UNDERCOVER_RUN_V1015_ERROR_COMPLETION','UNDERCOVER_PREPARE_V1029_THIRD_TRANSFER'):
            env=self.setup_env();env.pop(key)
            for build in (False,True):self.assertEqual(self.plan(env,build).returncode,2,key)
        for key,val in (('UNDERCOVER_RUN_V1012_SI_PROFILE','port1-present'),('UNDERCOVER_RUN_V1009_SECOND_CALLBACK','1'),('UNDERCOVER_PREPARE_V1048_THIRD_ALARM','1'),('UNDERCOVER_RUN_V1051_THIRD_TRANSFER','2')):
            env=self.setup_env();env[key]=val
            for build in (False,True):self.assertEqual(self.plan(env,build).returncode,2,key)
        self.assertEqual(self.plan(self.setup_env(),True,'--prepare-si-handler-suffix').returncode,2)
        self.assertEqual(self.plan(self.setup_env(),False,'irq-si-alarm').returncode,2)
        env=self.setup_env();env['UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX']='1'
        self.assertEqual(self.plan(env,True).returncode,2)
if __name__=='__main__':unittest.main()
