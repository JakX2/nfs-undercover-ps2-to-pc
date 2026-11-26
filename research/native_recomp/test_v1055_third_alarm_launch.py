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

class PostAlarmLaunch(unittest.TestCase):
    def setUp(self):
        self.launch=Launch()
        self.env=self.launch.setup_env()
        self.env.update(UNDERCOVER_RUN_V1055_THIRD_ALARM='1',UNDERCOVER_PREPARE_V1048_THIRD_ALARM='1',
                        UNDERCOVER_RUN_V1102_AFTER_ALARM='1',UNDERCOVER_PREPARE_V1097_AFTER_ALARM='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1102_POSTALARM_BUILD_PLAN links=1 private_installer=1 alarm_predecessor=1' if build else 'audit=audit_v1101_postalarm.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1095_AFTER_ALARM=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1102_AFTER_ALARM','UNDERCOVER_PREPARE_V1097_AFTER_ALARM',
                    'UNDERCOVER_RUN_V1055_THIRD_ALARM','UNDERCOVER_PREPARE_V1048_THIRD_ALARM',
                    'UNDERCOVER_RUN_V1051_THIRD_TRANSFER','UNDERCOVER_PREPARE_V1029_THIRD_TRANSFER',
                    'UNDERCOVER_RUN_V1040_SIX_ARGS','UNDERCOVER_RUN_V1034_QUEUE_DETAIL'):
            env=self.env.copy();env.pop(key)
            for build in (False,True):
                with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key,val in (('UNDERCOVER_RUN_V1102_AFTER_ALARM','2'),('UNDERCOVER_RUN_V1102_AFTER_ALARM',''),
                        ('UNDERCOVER_PREPARE_V1097_AFTER_ALARM','2'),('UNDERCOVER_PREPARE_V1097_AFTER_ALARM',''),
                        ('UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX','1'),('UNDERCOVER_RUN_V1012_SI_PROFILE','port1-present'),
                        ('UNDERCOVER_RUN_V1009_SECOND_CALLBACK','1')):
            env=self.env.copy();env[key]=val
            for build in (False,True):
                with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        self.assertEqual(self.launch.plan(self.env,True,'--prepare-si-handler-suffix').returncode,2)
        self.assertEqual(self.launch.plan(self.env,False,'irq-si-alarm').returncode,2)
    def test_alarm_only_unchanged(self):
        env=self.env.copy();env.pop('UNDERCOVER_RUN_V1102_AFTER_ALARM');env.pop('UNDERCOVER_PREPARE_V1097_AFTER_ALARM')
        for build in (False,True):
            p=self.launch.plan(env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1102_POSTALARM_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1095_AFTER_ALARM=1',p.stdout)
            self.assertIn('alarm=1' if build else 'audit=audit_v1054_third_alarm.py',p.stdout)

class PostAlarmTimeLaunch(unittest.TestCase):
    def setUp(self):
        self.launch=Launch()
        self.env=self.launch.setup_env()
        self.env.update(UNDERCOVER_RUN_V1055_THIRD_ALARM='1',UNDERCOVER_PREPARE_V1048_THIRD_ALARM='1',
                        UNDERCOVER_RUN_V1102_AFTER_ALARM='1',UNDERCOVER_PREPARE_V1097_AFTER_ALARM='1',
                        UNDERCOVER_RUN_V1107_POSTALARM_TIME='1',UNDERCOVER_PREPARE_V1106_POSTALARM_TIME='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1107_POSTALARM_TIME_BUILD_PLAN links=1 private_installer=1 prefix_predecessor=1' if build else 'audit=audit_v1107_postalarm_time.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1103_POSTALARM_TIME=1',p.stdout)
    def test_refusals(self):
        for key in tuple(self.env):
            if key.startswith(('UNDERCOVER_RUN_V110','UNDERCOVER_PREPARE_V110','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                env=self.env.copy();env.pop(key)
                for build in (False,True):
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key,val in (('UNDERCOVER_RUN_V1107_POSTALARM_TIME','2'),('UNDERCOVER_RUN_V1107_POSTALARM_TIME',''),
                        ('UNDERCOVER_PREPARE_V1106_POSTALARM_TIME','2'),('UNDERCOVER_PREPARE_V1106_POSTALARM_TIME',''),
                        ('UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX','1'),('UNDERCOVER_RUN_V1012_SI_PROFILE','port1-present')):
            env=self.env.copy();env[key]=val
            for build in (False,True):
                with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_prefix_only_unchanged(self):
        env=self.env.copy();env.pop('UNDERCOVER_RUN_V1107_POSTALARM_TIME');env.pop('UNDERCOVER_PREPARE_V1106_POSTALARM_TIME')
        for build in (False,True):
            p=self.launch.plan(env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1107_POSTALARM_TIME_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1103_POSTALARM_TIME=1',p.stdout)
            self.assertIn('V1102_POSTALARM_BUILD_PLAN' if build else 'audit=audit_v1101_postalarm.py',p.stdout)

class PostAlarmFrontierLaunch(unittest.TestCase):
    def setUp(self):
        self.launch=Launch()
        self.env=self.launch.setup_env()
        self.env.update(UNDERCOVER_RUN_V1055_THIRD_ALARM='1',UNDERCOVER_PREPARE_V1048_THIRD_ALARM='1',
                        UNDERCOVER_RUN_V1102_AFTER_ALARM='1',UNDERCOVER_PREPARE_V1097_AFTER_ALARM='1',
                        UNDERCOVER_RUN_V1107_POSTALARM_TIME='1',UNDERCOVER_PREPARE_V1106_POSTALARM_TIME='1',
                        UNDERCOVER_RUN_V1114_POSTALARM_FRONTIER='1',UNDERCOVER_PREPARE_V1113_POSTALARM_FRONTIER='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1114_POSTALARM_FRONTIER_BUILD_PLAN links=1 private_installer=1 time_predecessor=1' if build else 'audit=audit_v1114_postalarm_frontier.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1111_POSTALARM_FRONTIER=1',p.stdout)
    def test_refusals(self):
        for key in tuple(self.env):
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                env=self.env.copy();env.pop(key)
                for build in (False,True):
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key,val in (('UNDERCOVER_RUN_V1114_POSTALARM_FRONTIER','2'),('UNDERCOVER_RUN_V1114_POSTALARM_FRONTIER',''),
                        ('UNDERCOVER_PREPARE_V1113_POSTALARM_FRONTIER','2'),('UNDERCOVER_PREPARE_V1113_POSTALARM_FRONTIER',''),
                        ('UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX','1'),('UNDERCOVER_RUN_V1012_SI_PROFILE','port1-present')):
            env=self.env.copy();env[key]=val
            for build in (False,True):
                with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_time_only_unchanged(self):
        env=self.env.copy();env.pop('UNDERCOVER_RUN_V1114_POSTALARM_FRONTIER');env.pop('UNDERCOVER_PREPARE_V1113_POSTALARM_FRONTIER')
        for build in (False,True):
            p=self.launch.plan(env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1114_POSTALARM_FRONTIER_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1111_POSTALARM_FRONTIER=1',p.stdout)
            self.assertIn('V1107_POSTALARM_TIME_BUILD_PLAN' if build else 'audit=audit_v1107_postalarm_time.py',p.stdout)

class PostAlarmWirelessLaunch(unittest.TestCase):
    def setUp(self):
        self.launch=Launch()
        self.env=self.launch.setup_env()
        self.env.update(UNDERCOVER_RUN_V1055_THIRD_ALARM='1',UNDERCOVER_PREPARE_V1048_THIRD_ALARM='1',
                        UNDERCOVER_RUN_V1102_AFTER_ALARM='1',UNDERCOVER_PREPARE_V1097_AFTER_ALARM='1',
                        UNDERCOVER_RUN_V1107_POSTALARM_TIME='1',UNDERCOVER_PREPARE_V1106_POSTALARM_TIME='1',
                        UNDERCOVER_RUN_V1114_POSTALARM_FRONTIER='1',UNDERCOVER_PREPARE_V1113_POSTALARM_FRONTIER='1',
                        UNDERCOVER_RUN_V1121_POSTALARM_WIRELESS='1',UNDERCOVER_PREPARE_V1119_POSTALARM_WIRELESS='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1121_POSTALARM_WIRELESS_BUILD_PLAN links=1 private_installer=1 frontier_predecessor=1' if build else 'audit=audit_v1121_postalarm_wireless.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1118_POSTALARM_WIRELESS=1',p.stdout)
    def test_refusals(self):
        for key in tuple(self.env):
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_RUN_V112','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                env=self.env.copy();env.pop(key)
                for build in (False,True):
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key,val in (('UNDERCOVER_RUN_V1121_POSTALARM_WIRELESS','2'),('UNDERCOVER_RUN_V1121_POSTALARM_WIRELESS',''),
                        ('UNDERCOVER_PREPARE_V1119_POSTALARM_WIRELESS','2'),('UNDERCOVER_PREPARE_V1119_POSTALARM_WIRELESS',''),
                        ('UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX','1'),('UNDERCOVER_RUN_V1012_SI_PROFILE','port1-present')):
            env=self.env.copy();env[key]=val
            for build in (False,True):
                with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_frontier_only_unchanged(self):
        env=self.env.copy();env.pop('UNDERCOVER_RUN_V1121_POSTALARM_WIRELESS');env.pop('UNDERCOVER_PREPARE_V1119_POSTALARM_WIRELESS')
        for build in (False,True):
            p=self.launch.plan(env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1121_POSTALARM_WIRELESS_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1118_POSTALARM_WIRELESS=1',p.stdout)
            self.assertIn('V1114_POSTALARM_FRONTIER_BUILD_PLAN' if build else 'audit=audit_v1114_postalarm_frontier.py',p.stdout)

class PostAlarmSuffixLaunch(PostAlarmWirelessLaunch):
    def setUp(self):
        super().setUp()
        self.env.update(UNDERCOVER_RUN_V1127_POSTALARM_SUFFIX='1',UNDERCOVER_PREPARE_V1124_POSTALARM_SUFFIX='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1127_POSTALARM_SUFFIX_BUILD_PLAN links=1 private_installer=1 wireless_predecessor=1' if build else 'audit=audit_v1127_postalarm_suffix.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1123_POSTALARM_SUFFIX=1',p.stdout)
    def test_refusals(self):
        super().test_refusals()
        for key in ('UNDERCOVER_RUN_V1127_POSTALARM_SUFFIX','UNDERCOVER_PREPARE_V1124_POSTALARM_SUFFIX'):
            for val in ('','2','true'):
                env=self.env.copy();env[key]=val
                for build in (False,True):
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_frontier_only_unchanged(self):
        self.env.pop('UNDERCOVER_RUN_V1127_POSTALARM_SUFFIX');self.env.pop('UNDERCOVER_PREPARE_V1124_POSTALARM_SUFFIX')
        super().test_frontier_only_unchanged()
    def test_wireless_only_unchanged(self):
        env=self.env.copy();env.pop('UNDERCOVER_RUN_V1127_POSTALARM_SUFFIX');env.pop('UNDERCOVER_PREPARE_V1124_POSTALARM_SUFFIX')
        for build in (False,True):
            p=self.launch.plan(env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1127_POSTALARM_SUFFIX_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1123_POSTALARM_SUFFIX=1',p.stdout)
            self.assertIn('V1121_POSTALARM_WIRELESS_BUILD_PLAN' if build else 'audit=audit_v1121_postalarm_wireless.py',p.stdout)

class PostAlarmReturnLaunch(PostAlarmSuffixLaunch):
    def setUp(self):
        super().setUp()
        self.env.update(UNDERCOVER_RUN_V1135_POSTALARM_RETURN='1',UNDERCOVER_PREPARE_V1134_POSTALARM_RETURN='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1135_POSTALARM_RETURN_BUILD_PLAN links=1 private_installer=1 suffix_predecessor=1' if build else 'audit=audit_v1135_postalarm_return.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1132_POSTALARM_RETURN=1',p.stdout)
    def test_refusals(self):
        super().test_refusals()
        for key in ('UNDERCOVER_RUN_V1135_POSTALARM_RETURN','UNDERCOVER_PREPARE_V1134_POSTALARM_RETURN'):
            for val in ('','2','true'):
                env=self.env.copy();env[key]=val
                for build in (False,True):
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def without_return(self):
        self.env.pop('UNDERCOVER_RUN_V1135_POSTALARM_RETURN');self.env.pop('UNDERCOVER_PREPARE_V1134_POSTALARM_RETURN')
    def test_frontier_only_unchanged(self):
        self.without_return();super().test_frontier_only_unchanged()
    def test_wireless_only_unchanged(self):
        self.without_return();super().test_wireless_only_unchanged()
    def test_suffix_only_unchanged(self):
        self.without_return()
        for build in (False,True):
            p=self.launch.plan(self.env,build);self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1135_POSTALARM_RETURN_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1132_POSTALARM_RETURN=1',p.stdout)
            self.assertIn('V1127_POSTALARM_SUFFIX_BUILD_PLAN' if build else 'audit=audit_v1127_postalarm_suffix.py',p.stdout)


class PostAlarmHandlerLaunch(unittest.TestCase):
    def setUp(self):
        base=PostAlarmReturnLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1143_POSTALARM_HANDLER='1',UNDERCOVER_PREPARE_V1141_POSTALARM_HANDLER='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1143_POSTALARM_HANDLER_BUILD_PLAN links=1 private_installer=1 return_predecessor=1' if build else 'audit=audit_v1143_postalarm_handler.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1139_POSTALARM_HANDLER=1',p.stdout)
    def test_refusals(self):
        for key in self.env:
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                for build in (False,True):
                    env=self.env.copy();env.pop(key)
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key in ('UNDERCOVER_RUN_V1143_POSTALARM_HANDLER','UNDERCOVER_PREPARE_V1141_POSTALARM_HANDLER'):
            for val in ('','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_return_only_unchanged(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1143_POSTALARM_HANDLER_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1139_POSTALARM_HANDLER=1',p.stdout)
            self.assertIn('V1135_POSTALARM_RETURN_BUILD_PLAN' if build else 'audit=audit_v1135_postalarm_return.py',p.stdout)


class PostAlarmHandlerReturnLaunch(unittest.TestCase):
    def setUp(self):
        base=PostAlarmHandlerLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1148_POSTALARM_HANDLER_RETURN='1',UNDERCOVER_PREPARE_V1146_POSTALARM_HANDLER_RETURN='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1148_POSTALARM_HANDLER_RETURN_BUILD_PLAN links=1 private_installer=1 handler_predecessor=1' if build else 'audit=audit_v1148_postalarm_handler_return.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1145_POSTALARM_HANDLER_RETURN=1',p.stdout)
    def test_refusals(self):
        for key in self.env:
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                for build in (False,True):
                    env=self.env.copy();env.pop(key)
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key in ('UNDERCOVER_RUN_V1148_POSTALARM_HANDLER_RETURN','UNDERCOVER_PREPARE_V1146_POSTALARM_HANDLER_RETURN'):
            for val in ('','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_handler_only_unchanged(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1148_POSTALARM_HANDLER_RETURN_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1145_POSTALARM_HANDLER_RETURN=1',p.stdout)
            self.assertIn('V1143_POSTALARM_HANDLER_BUILD_PLAN' if build else 'audit=audit_v1143_postalarm_handler.py',p.stdout)


class HeldEpilogueLaunch(unittest.TestCase):
    def setUp(self):
        base=PostAlarmHandlerReturnLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1156_HELD_EPILOGUE='1',UNDERCOVER_PREPARE_V1152_HELD_EPILOGUE='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1156_HELD_EPILOGUE_BUILD_PLAN links=1 private_installer=1 handler_return_predecessor=1' if build else 'audit=audit_v1156_held_epilogue.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1151_HELD_EPILOGUE=1',p.stdout)
    def test_refusals(self):
        for key in self.env:
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                for build in (False,True):
                    env=self.env.copy();env.pop(key)
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key in ('UNDERCOVER_RUN_V1156_HELD_EPILOGUE','UNDERCOVER_PREPARE_V1152_HELD_EPILOGUE'):
            for val in ('','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_handler_return_only_unchanged(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1156_HELD_EPILOGUE_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1151_HELD_EPILOGUE=1',p.stdout)
            self.assertIn('V1148_POSTALARM_HANDLER_RETURN_BUILD_PLAN' if build else 'audit=audit_v1148_postalarm_handler_return.py',p.stdout)

if __name__=='__main__':unittest.main()
