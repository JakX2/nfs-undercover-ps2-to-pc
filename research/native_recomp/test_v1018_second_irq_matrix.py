import os,subprocess,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class Matrix(unittest.TestCase):
    def test_isolated_plans(self):
        env=os.environ.copy()
        env['UNDERCOVER_RUN_V1014_SECOND_CALLBACK_TIME']='1'
        env['UNDERCOVER_RUN_V1015_ERROR_COMPLETION']='1'
        env['UNDERCOVER_RUN_V1012_SI_PROFILE']='invalid'
        p=subprocess.run(['bash',str(HERE/'run_v1018_second_irq_matrix.sh'),'--describe-mode'],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        rows=p.stdout.splitlines()
        plans=[l for l in rows if l.startswith('V875_LAUNCH_PLAN ')]
        self.assertEqual(len(plans),3)
        for plan in plans:
            self.assertIn('UNDERCOVER_V958_SECOND_ACK=1',plan)
            self.assertIn('UNDERCOVER_V989_SHARED_COMPLETION=1',plan)
        self.assertIn('audit=audit_v1015_error_completion.py',plans[0])
        self.assertIn('UNDERCOVER_V1015_ERROR_COMPLETION=1',plans[0])
        self.assertNotIn('UNDERCOVER_V975_SECOND_TIME=1',plans[0])
        self.assertIn('audit=audit_v1009_second_callback.py',plans[1])
        self.assertNotIn('UNDERCOVER_V1014_SECOND_CALLBACK_TIME=1',plans[1])
        self.assertIn('audit=audit_v1014_second_callback_time.py',plans[2])
        self.assertIn('UNDERCOVER_V1014_SECOND_CALLBACK_TIME=1',plans[2])
        self.assertEqual(sum(l.startswith('V1012_SI_PROFILE ') for l in rows),2)
        self.assertEqual(rows[-1],'V1018_MATRIX_RESULT attempted=3 failed=0 describe=1 boot_verified=0')
    def test_extended_matrix(self):
        env=os.environ.copy();env['UNDERCOVER_RUN_V1023_ERROR_TIME_MATRIX']='1'
        p=subprocess.run(['bash',str(HERE/'run_v1018_second_irq_matrix.sh'),'--describe-mode'],env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        rows=p.stdout.splitlines();plans=[l for l in rows if l.startswith('V875_LAUNCH_PLAN ')]
        self.assertEqual(len(plans),4)
        self.assertIn('audit=audit_v1023_error_callback_time.py',plans[-1])
        self.assertIn('UNDERCOVER_V1021_ERROR_FRONTIER=1',plans[-1])
        self.assertIn('UNDERCOVER_V1014_SECOND_CALLBACK_TIME=1',plans[-1])
        self.assertEqual(sum(l.startswith('V1012_SI_PROFILE ') for l in rows),2)
        self.assertEqual(rows[-1],'V1018_MATRIX_RESULT attempted=4 failed=0 describe=1 boot_verified=0')
    def test_build_gate(self):
        env={k:v for k,v in os.environ.items() if not k.startswith('UNDERCOVER_RUN_')}
        env['UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX']='1'
        cmd=['bash',str(HERE/'run_v572_full_sc_translation.sh'),'--describe-mode','--run-si-handler-suffix']
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=5)
        self.assertEqual(p.returncode,2)
        for name in ('V1014_SECOND_CALLBACK_TIME','V1009_SECOND_CALLBACK','V995_SUCCESS_FRONTIER','V981_SECOND_FRONTIER','V975_SECOND_TIME','V989_SHARED_COMPLETION','V967_POST_ACK','V958_SECOND_ACK'):
            env['UNDERCOVER_RUN_'+name]='1'
        p=subprocess.run(cmd,env=env,capture_output=True,text=True,timeout=5)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('V1018_BUILD_PLAN links=1 isolated_launches=3 callback_time_installed=1',p.stdout)
        for bad in ('--run-dsp-return','--prepare-si-handler-suffix'):
            self.assertEqual(subprocess.run(cmd[:-1]+[bad],env=env,capture_output=True,timeout=5).returncode,2)
        env['UNDERCOVER_RUN_V1015_ERROR_COMPLETION']='1'
        self.assertEqual(subprocess.run(cmd,env=env,capture_output=True,timeout=5).returncode,2)
if __name__=='__main__':unittest.main()
