import unittest
from test_v1051_third_launch import Launch

class AlarmLaunch(unittest.TestCase):
    def setUp(self):
        self.launch=Launch()
        self.env=self.launch.setup_env()
        self.env['UNDERCOVER_RUN_V1055_THIRD_ALARM']='1'
        self.env['UNDERCOVER_PREPARE_V1048_THIRD_ALARM']='1'
    def check(self,env,rc):
        for build in (False,True):
            with self.subTest(build=build):
                p=self.launch.plan(env,build)
                self.assertEqual(p.returncode,rc,p.stderr+p.stdout)
                if rc==0:
                    self.assertIn('alarm=1' if build else 'audit=audit_v1054_third_alarm.py',p.stdout)
                    if not build:
                        self.assertIn('UNDERCOVER_V1028_THIRD_TRANSFER=1',p.stdout)
                        self.assertIn('UNDERCOVER_V1048_THIRD_ALARM=1',p.stdout)
    def test_enabled(self):
        self.check(self.env,0)
    def test_required(self):
        for key in ('UNDERCOVER_RUN_V1051_THIRD_TRANSFER','UNDERCOVER_PREPARE_V1048_THIRD_ALARM',
                    'UNDERCOVER_PREPARE_V1029_THIRD_TRANSFER','UNDERCOVER_RUN_V1040_SIX_ARGS',
                    'UNDERCOVER_RUN_V1034_QUEUE_DETAIL','UNDERCOVER_RUN_V1021_ERROR_FRONTIER'):
            with self.subTest(key=key):
                env=self.env.copy();env.pop(key)
                self.check(env,2)
    def test_conflicts(self):
        for key,value in (('UNDERCOVER_RUN_V1055_THIRD_ALARM','2'),
                          ('UNDERCOVER_PREPARE_V1048_THIRD_ALARM','2'),
                          ('UNDERCOVER_RUN_V1012_SI_PROFILE','port1-present'),
                          ('UNDERCOVER_RUN_V1009_SECOND_CALLBACK','1')):
            with self.subTest(key=key):
                env=self.env.copy();env[key]=value
                self.check(env,2)
        self.assertEqual(self.launch.plan(self.env,True,'--prepare-si-handler-suffix').returncode,2)
        self.assertEqual(self.launch.plan(self.env,False,'irq-si-alarm').returncode,2)
        env=self.env.copy();env['UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX']='1'
        self.assertEqual(self.launch.plan(env,True).returncode,2)
    def test_transfer_only_unchanged(self):
        env=self.env.copy();env.pop('UNDERCOVER_RUN_V1055_THIRD_ALARM');env.pop('UNDERCOVER_PREPARE_V1048_THIRD_ALARM')
        for build in (False,True):
            p=self.launch.plan(env,build)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('alarm=0' if build else 'audit=audit_v1045_third_transfer_abi.py',p.stdout)
            self.assertNotIn('UNDERCOVER_V1048_THIRD_ALARM=1',p.stdout)

if __name__=='__main__':unittest.main()
