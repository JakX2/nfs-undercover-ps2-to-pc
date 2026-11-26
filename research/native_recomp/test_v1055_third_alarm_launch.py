import unittest
from pathlib import Path
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
            if not build:
                self.assertIn('UNDERCOVER_V1118_POSTALARM_WIRELESS=1',p.stdout)
                self.assertIn('V1196_SRAM_PLAN selected=wireless-zero unchanged_setter=1 synthetic=1',p.stdout)
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
            self.assertNotIn('V1196_SRAM_PLAN',p.stdout)
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


class HeldDispatchLaunch(unittest.TestCase):
    def setUp(self):
        base=HeldEpilogueLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1163_HELD_DISPATCH='1',UNDERCOVER_PREPARE_V1161_HELD_DISPATCH='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1163_HELD_DISPATCH_BUILD_PLAN links=1 private_installer=1 vector_predecessor=1' if build else 'audit=audit_v1163_held_dispatch.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1158_HELD_DISPATCH=1',p.stdout)
    def test_refusals(self):
        for key in self.env:
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                for build in (False,True):
                    env=self.env.copy();env.pop(key)
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key in ('UNDERCOVER_RUN_V1163_HELD_DISPATCH','UNDERCOVER_PREPARE_V1161_HELD_DISPATCH'):
            for val in ('','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_epilogue_only_unchanged(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1163_HELD_DISPATCH_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1158_HELD_DISPATCH=1',p.stdout)
            self.assertIn('V1156_HELD_EPILOGUE_BUILD_PLAN' if build else 'audit=audit_v1156_held_epilogue.py',p.stdout)


class ThirdAckLaunch(unittest.TestCase):
    def setUp(self):
        base=HeldDispatchLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1171_THIRD_ACK='1',UNDERCOVER_PREPARE_V1169_THIRD_ACK='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1171_THIRD_ACK_BUILD_PLAN links=1 private_installer=1 dispatch_predecessor=1' if build else 'audit=audit_v1171_third_ack.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1167_THIRD_ACK=1',p.stdout)
    def test_refusals(self):
        for key in self.env:
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                for build in (False,True):
                    env=self.env.copy();env.pop(key)
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key in ('UNDERCOVER_RUN_V1171_THIRD_ACK','UNDERCOVER_PREPARE_V1169_THIRD_ACK'):
            for val in ('','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_dispatch_only_unchanged(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1171_THIRD_ACK_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1167_THIRD_ACK=1',p.stdout)
            self.assertIn('V1163_HELD_DISPATCH_BUILD_PLAN' if build else 'audit=audit_v1163_held_dispatch.py',p.stdout)


class AckHelperLaunch(unittest.TestCase):
    def setUp(self):
        base=ThirdAckLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1177_ACK_HELPER='1',UNDERCOVER_PREPARE_V1176_ACK_HELPER='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1177_ACK_HELPER_BUILD_PLAN links=1 private_installer=1 ack_predecessor=1' if build else 'audit=audit_v1177_ack_helper.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1175_ACK_HELPER=1',p.stdout)
    def test_refusals(self):
        for key in self.env:
            if key.startswith(('UNDERCOVER_RUN_V11','UNDERCOVER_PREPARE_V11','UNDERCOVER_RUN_V1055','UNDERCOVER_PREPARE_V1048','UNDERCOVER_PREPARE_V1097')):
                for build in (False,True):
                    env=self.env.copy();env.pop(key)
                    with self.subTest(key=key,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
        for key in ('UNDERCOVER_RUN_V1177_ACK_HELPER','UNDERCOVER_PREPARE_V1176_ACK_HELPER'):
            for val in ('','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_ack_only_unchanged(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertNotIn('V1177_ACK_HELPER_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1175_ACK_HELPER=1',p.stdout)
            self.assertIn('V1171_THIRD_ACK_BUILD_PLAN' if build else 'audit=audit_v1171_third_ack.py',p.stdout)

class AckCallbackLaunch(unittest.TestCase):
    def setUp(self):
        base=AckHelperLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1182_ACK_CALLBACK='1',UNDERCOVER_PREPARE_V1182_ACK_CALLBACK='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1182_ACK_CALLBACK_BUILD_PLAN links=1 private_installer=1 helper_predecessor=1' if build else 'audit=audit_v1182_ack_callback.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1180_ACK_CALLBACK=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1182_ACK_CALLBACK','UNDERCOVER_PREPARE_V1182_ACK_CALLBACK','UNDERCOVER_RUN_V1177_ACK_HELPER','UNDERCOVER_PREPARE_V1176_ACK_HELPER'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_helper_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1182_ACK_CALLBACK_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1180_ACK_CALLBACK=1',p.stdout)
            self.assertIn('V1177_ACK_HELPER_BUILD_PLAN' if build else 'audit=audit_v1177_ack_helper.py',p.stdout)
class AckPrefixLaunch(unittest.TestCase):
    def setUp(self):
        base=AckCallbackLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1187_ACK_PREFIX='1',UNDERCOVER_PREPARE_V1186_ACK_PREFIX='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1187_ACK_PREFIX_BUILD_PLAN links=1 private_installer=1 callback_predecessor=1' if build else 'audit=audit_v1187_ack_prefix.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1184_ACK_PREFIX=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1187_ACK_PREFIX','UNDERCOVER_PREPARE_V1186_ACK_PREFIX','UNDERCOVER_RUN_V1182_ACK_CALLBACK','UNDERCOVER_PREPARE_V1182_ACK_CALLBACK'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_callback_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1187_ACK_PREFIX_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1184_ACK_PREFIX=1',p.stdout)
            self.assertIn('V1182_ACK_CALLBACK_BUILD_PLAN' if build else 'audit=audit_v1182_ack_callback.py',p.stdout)
class AckTimeLaunch(unittest.TestCase):
    def setUp(self):
        base=AckPrefixLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1191_ACK_TIME='1',UNDERCOVER_PREPARE_V1190_ACK_TIME='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1191_ACK_TIME_BUILD_PLAN links=1 private_installer=1 prefix_predecessor=1' if build else 'audit=audit_v1191_ack_time.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1189_ACK_TIME=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1191_ACK_TIME','UNDERCOVER_PREPARE_V1190_ACK_TIME','UNDERCOVER_RUN_V1187_ACK_PREFIX','UNDERCOVER_PREPARE_V1186_ACK_PREFIX'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_prefix_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1191_ACK_TIME_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1189_ACK_TIME=1',p.stdout)
            self.assertIn('V1187_ACK_PREFIX_BUILD_PLAN' if build else 'audit=audit_v1187_ack_prefix.py',p.stdout)
class AckFrontierLaunch(unittest.TestCase):
    def setUp(self):
        base=AckTimeLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1194_ACK_FRONTIER='1',UNDERCOVER_PREPARE_V1194_ACK_FRONTIER='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1194_ACK_FRONTIER_BUILD_PLAN links=1 private_installer=1 time_predecessor=1' if build else 'audit=audit_v1194_ack_frontier.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1193_ACK_FRONTIER=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1194_ACK_FRONTIER','UNDERCOVER_PREPARE_V1194_ACK_FRONTIER','UNDERCOVER_RUN_V1191_ACK_TIME','UNDERCOVER_PREPARE_V1190_ACK_TIME'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_time_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1194_ACK_FRONTIER_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1193_ACK_FRONTIER=1',p.stdout)
            self.assertIn('V1191_ACK_TIME_BUILD_PLAN' if build else 'audit=audit_v1191_ack_time.py',p.stdout)
class AckWirelessLaunch(unittest.TestCase):
    def setUp(self):
        base=AckFrontierLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1198_ACK_WIRELESS='1',UNDERCOVER_PREPARE_V1198_ACK_WIRELESS='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1198_ACK_WIRELESS_BUILD_PLAN links=1 private_installer=1 frontier_predecessor=1' if build else 'audit=audit_v1198_ack_wireless.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1197_ACK_WIRELESS=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1198_ACK_WIRELESS','UNDERCOVER_PREPARE_V1198_ACK_WIRELESS','UNDERCOVER_RUN_V1194_ACK_FRONTIER','UNDERCOVER_PREPARE_V1194_ACK_FRONTIER'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_frontier_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1198_ACK_WIRELESS_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1197_ACK_WIRELESS=1',p.stdout)
            self.assertIn('V1194_ACK_FRONTIER_BUILD_PLAN' if build else 'audit=audit_v1194_ack_frontier.py',p.stdout)
class AckSuffixLaunch(unittest.TestCase):
    def setUp(self):
        base=AckWirelessLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1203_ACK_SUFFIX='1',UNDERCOVER_PREPARE_V1203_ACK_SUFFIX='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1203_ACK_SUFFIX_BUILD_PLAN links=1 private_installer=1 wireless_predecessor=1' if build else 'audit=audit_v1203_ack_suffix.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1201_ACK_SUFFIX=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1203_ACK_SUFFIX','UNDERCOVER_PREPARE_V1203_ACK_SUFFIX','UNDERCOVER_RUN_V1198_ACK_WIRELESS','UNDERCOVER_PREPARE_V1198_ACK_WIRELESS'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_wireless_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1203_ACK_SUFFIX_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1201_ACK_SUFFIX=1',p.stdout)
            self.assertIn('V1198_ACK_WIRELESS_BUILD_PLAN' if build else 'audit=audit_v1198_ack_wireless.py',p.stdout)
class AckReturnLaunch(unittest.TestCase):
    def setUp(self):
        base=AckSuffixLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1207_ACK_RETURN='1',UNDERCOVER_PREPARE_V1207_ACK_RETURN='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1207_ACK_RETURN_BUILD_PLAN links=1 private_installer=1 suffix_predecessor=1' if build else 'audit=audit_v1207_ack_return.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1205_ACK_RETURN=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1207_ACK_RETURN','UNDERCOVER_PREPARE_V1207_ACK_RETURN','UNDERCOVER_RUN_V1203_ACK_SUFFIX','UNDERCOVER_PREPARE_V1203_ACK_SUFFIX'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_suffix_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1207_ACK_RETURN_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1205_ACK_RETURN=1',p.stdout)
            self.assertIn('V1203_ACK_SUFFIX_BUILD_PLAN' if build else 'audit=audit_v1203_ack_suffix.py',p.stdout)
class AckHandlerLaunch(unittest.TestCase):
    def setUp(self):
        base=AckReturnLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1211_ACK_HANDLER='1',UNDERCOVER_PREPARE_V1211_ACK_HANDLER='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1211_ACK_HANDLER_BUILD_PLAN links=1 private_installer=1 return_predecessor=1' if build else 'audit=audit_v1211_ack_handler.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1210_ACK_HANDLER=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1211_ACK_HANDLER','UNDERCOVER_PREPARE_V1211_ACK_HANDLER','UNDERCOVER_RUN_V1207_ACK_RETURN','UNDERCOVER_PREPARE_V1207_ACK_RETURN'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_return_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1211_ACK_HANDLER_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1210_ACK_HANDLER=1',p.stdout)
            self.assertIn('V1207_ACK_RETURN_BUILD_PLAN' if build else 'audit=audit_v1207_ack_return.py',p.stdout)
class AckHandlerReturnLaunch(unittest.TestCase):
    def setUp(self):
        base=AckHandlerLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1215_ACK_HANDLER_RETURN='1',UNDERCOVER_PREPARE_V1215_ACK_HANDLER_RETURN='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1215_ACK_HANDLER_RETURN_BUILD_PLAN links=1 private_installer=1 handler_predecessor=1' if build else 'audit=audit_v1215_ack_handler_return.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1214_ACK_HANDLER_RETURN=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1215_ACK_HANDLER_RETURN','UNDERCOVER_PREPARE_V1215_ACK_HANDLER_RETURN','UNDERCOVER_RUN_V1211_ACK_HANDLER','UNDERCOVER_PREPARE_V1211_ACK_HANDLER'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_handler_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1215_ACK_HANDLER_RETURN_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1214_ACK_HANDLER_RETURN=1',p.stdout)
            self.assertIn('V1211_ACK_HANDLER_BUILD_PLAN' if build else 'audit=audit_v1211_ack_handler.py',p.stdout)
class AckFinalLaunch(unittest.TestCase):
    def setUp(self):
        base=AckHandlerReturnLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1218_ACK_FINAL='1',UNDERCOVER_PREPARE_V1218_ACK_FINAL='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1218_ACK_FINAL_BUILD_PLAN links=1 private_installer=1 handler_return_predecessor=1' if build else 'audit=audit_v1218_ack_final.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1217_ACK_FINAL=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1218_ACK_FINAL','UNDERCOVER_PREPARE_V1218_ACK_FINAL','UNDERCOVER_RUN_V1215_ACK_HANDLER_RETURN','UNDERCOVER_PREPARE_V1215_ACK_HANDLER_RETURN'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_handler_return_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1218_ACK_FINAL_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1217_ACK_FINAL=1',p.stdout)
            self.assertIn('V1215_ACK_HANDLER_RETURN_BUILD_PLAN' if build else 'audit=audit_v1215_ack_handler_return.py',p.stdout)
class AckResumeLaunch(unittest.TestCase):
    def setUp(self):
        base=AckFinalLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1221_ACK_RESUME='1',UNDERCOVER_PREPARE_V1221_ACK_RESUME='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1221_ACK_RESUME_BUILD_PLAN links=1 private_installer=1 final_predecessor=1' if build else 'audit=audit_v1221_ack_resume.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1220_ACK_RESUME=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1221_ACK_RESUME','UNDERCOVER_PREPARE_V1221_ACK_RESUME','UNDERCOVER_RUN_V1218_ACK_FINAL','UNDERCOVER_PREPARE_V1218_ACK_FINAL'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_final_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1221_ACK_RESUME_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1220_ACK_RESUME=1',p.stdout)
            self.assertIn('V1218_ACK_FINAL_BUILD_PLAN' if build else 'audit=audit_v1218_ack_final.py',p.stdout)
class ExactSramObserverLaunch(unittest.TestCase):
    def test_profile_bound_to_observer(self):
        script=(Path(__file__).parent/'run_v575_dsp_sc_launch.sh').read_text()
        self.assertEqual(script.count('"UNDERCOVER_V1224_SRAM_EXPECT=$sram_profile"'),1)
        self.assertEqual(script.count('--profile "$sram_profile"'),1)
        self.assertIn('V1224_SRAM_EXPECT_PLAN selected=wireless-zero exact_dma=1',script)
class ColdFailureDiagnostic(unittest.TestCase):
    def test_bounded_summary(self):
        from cold_launch_diagnostic_v1225 import diagnostic,SRAM,DISC
        raw=b'\n'.join((DISC, b'V534_SRAM_STAGE n=1',b'V534_SRAM_STAGE n=2',
                        b'V534_SRAM_INVALID reason=2 stage=2 completed=0',b'private payload 12345678'))
        self.assertEqual(diagnostic(raw,108,1), 'V1225_COLD_FAILURE rc=108 audit=1 discovery=1 sram=0 sram_stages=2 sram_reason=2 sram_completed=0 dsp=0 mi=0 report=0 arena=0')
        self.assertNotIn('12345678',diagnostic(raw,108,1))
        self.assertIn('sram=1',diagnostic(raw+ b'\n'+SRAM,108,1))
        for extra in (b'V534_SRAM_INVALID reason=2 stage=2 completed=0', b'V534_SRAM_INVALID reason=2 stage=2 completed=999'):
            self.assertIn('sram_reason=0',diagnostic(raw+b'\n'+extra,108,1))
        self.assertIn('sram_reason=0',diagnostic(raw,126,1))
        self.assertIsNone(diagnostic(raw,0,0))
    def test_geometry(self):
        from cold_launch_diagnostic_v1225 import diagnostic,MAX_LOG
        for raw,rc,audit in ((b'x'*(MAX_LOG+1),1,1),(b'',-1,1),(b'',256,1),(b'',1,-1),(b'',1,256)):
            with self.assertRaises(ValueError):diagnostic(raw,rc,audit)
class AckLeafLaunch(unittest.TestCase):
    def setUp(self):
        base=AckResumeLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1228_ACK_LEAF='1',UNDERCOVER_PREPARE_V1228_ACK_LEAF='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1228_ACK_LEAF_BUILD_PLAN links=1 private_installer=1 resume_predecessor=1' if build else 'audit=audit_v1228_ack_leaf.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1227_ACK_LEAF=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1228_ACK_LEAF','UNDERCOVER_PREPARE_V1228_ACK_LEAF','UNDERCOVER_RUN_V1221_ACK_RESUME','UNDERCOVER_PREPARE_V1221_ACK_RESUME'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_resume_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1228_ACK_LEAF_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1227_ACK_LEAF=1',p.stdout)
            self.assertIn('V1221_ACK_RESUME_BUILD_PLAN' if build else 'audit=audit_v1221_ack_resume.py',p.stdout)
class AckIpcLaunch(unittest.TestCase):
    def setUp(self):
        base=AckLeafLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1230_ACK_IPC='1',UNDERCOVER_PREPARE_V1230_ACK_IPC='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1230_ACK_IPC_BUILD_PLAN links=1 private_installer=1 leaf_predecessor=1' if build else 'audit=audit_v1230_ack_ipc.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1230_ACK_IPC=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1230_ACK_IPC','UNDERCOVER_PREPARE_V1230_ACK_IPC','UNDERCOVER_RUN_V1228_ACK_LEAF','UNDERCOVER_PREPARE_V1228_ACK_LEAF'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_leaf_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1230_ACK_IPC_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1230_ACK_IPC=1',p.stdout)
            self.assertIn('V1228_ACK_LEAF_BUILD_PLAN' if build else 'audit=audit_v1228_ack_leaf.py',p.stdout)
class AckIpcPrivatePreflight(unittest.TestCase):
    def setUp(self):
        base=AckIpcLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.prior.copy();self.env=base.env.copy()
    def test_enabled(self):
        env=dict(self.env,UNDERCOVER_PREPARE_V1232_ONLY='1')
        p=self.launch.plan(env,True)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        self.assertIn('V1232_PRIVATE_PREFLIGHT_PLAN translation=1 syntax=1 link=0 execution=0',p.stdout)
        self.assertEqual(self.launch.plan(env,False).returncode,0)
        import subprocess
        from test_v1051_third_launch import HERE
        p=subprocess.run(['bash',str(HERE/'run_v575_dsp_sc_launch.sh'),'missing','missing','missing','irq-si-handler-suffix'],env=env,capture_output=True,timeout=5)
        self.assertEqual(p.returncode,2,p.stderr+p.stdout)
    def test_invalid(self):
        for val in ('','2','true'):
            env=dict(self.env,UNDERCOVER_PREPARE_V1232_ONLY=val)
            for build in (False,True):
                self.assertEqual(self.launch.plan(env,build).returncode,2)
        env=dict(self.prior,UNDERCOVER_PREPARE_V1232_ONLY='1')
        for build in (False,True):
            self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_default(self):
        p=self.launch.plan(self.env,True)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        self.assertNotIn('V1232_PRIVATE_PREFLIGHT_PLAN',p.stdout)
class AckIpcCompleteLaunch(unittest.TestCase):
    def setUp(self):
        base=AckIpcLaunch();base.setUp()
        self.launch=base.launch;self.prior=base.env.copy();self.env=self.prior.copy()
        self.env.update(UNDERCOVER_RUN_V1235_ACK_IPC_COMPLETE='1',UNDERCOVER_PREPARE_V1235_ACK_IPC_COMPLETE='1')
    def test_enabled(self):
        for build in (False,True):
            p=self.launch.plan(self.env,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertIn('V1235_ACK_IPC_COMPLETE_BUILD_PLAN links=1 private_installer=1 ipc_predecessor=1' if build else 'audit=audit_v1235_ack_ipc_complete.py',p.stdout)
            if not build:self.assertIn('UNDERCOVER_V1235_ACK_IPC_COMPLETE=1',p.stdout)
    def test_refusals(self):
        for key in ('UNDERCOVER_RUN_V1235_ACK_IPC_COMPLETE','UNDERCOVER_PREPARE_V1235_ACK_IPC_COMPLETE','UNDERCOVER_RUN_V1230_ACK_IPC','UNDERCOVER_PREPARE_V1230_ACK_IPC'):
            for val in ('','0','2','true'):
                for build in (False,True):
                    env=self.env.copy();env[key]=val
                    with self.subTest(key=key,val=val,build=build):self.assertEqual(self.launch.plan(env,build).returncode,2)
    def test_ipc_entry_only(self):
        for build in (False,True):
            p=self.launch.plan(self.prior,build)
            self.assertEqual(p.returncode,0,p.stderr+p.stdout)
            self.assertNotIn('V1235_ACK_IPC_COMPLETE_BUILD_PLAN',p.stdout)
            self.assertNotIn('UNDERCOVER_V1235_ACK_IPC_COMPLETE=1',p.stdout)
            self.assertIn('V1230_ACK_IPC_BUILD_PLAN' if build else 'audit=audit_v1230_ack_ipc.py',p.stdout)
if __name__=='__main__':unittest.main()
