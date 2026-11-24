import unittest
from pathlib import Path
from windows_startup_scope_v434 import contract
HOST=Path(__file__).parent
class Tests(unittest.TestCase):
    def test_ticks_before_translation(self):
        src=(HOST/'windows_full_build_v426.py').read_text(encoding='utf-8')
        a="run_stage('native_tick_labels'"
        self.assertEqual(src.count(a),1)
        self.assertIn("if not legacy_ticks:\n        "+a,src)
        self.assertLess(src.index(a),src.index("run_stage('translator_config'"))
        self.assertLess(src.index("run_stage('translator_config'"),src.index("run_stage('translation'"))
        self.assertIn("a.owner_scope,a.legacy_loader,a.legacy_ticks)",src)
        self.assertIn('apply_native_tick_v438.py',src)
    def test_os_time_scope(self):
        self.assertEqual(contract('os-time')[1],'prepare_v435_full_os_time.py')
        self.assertEqual(contract('os-time')[2],'audit_v435_full_os_time')
        with self.assertRaises(ValueError):contract('os-time',True)
if __name__=='__main__':unittest.main()
