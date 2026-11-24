import unittest
from pathlib import Path
from windows_full_build_v426 import translator_project
from windows_startup_scope_v434 import contract
HOST=Path(__file__).parent
class Tests(unittest.TestCase):
    def test_project_has_independent_loader_target(self):
        project=translator_project(HOST,HOST/'upstream fixture')
        self.assertIn('add_executable(dol_equivalence ',project)
        self.assertIn('check_wii_dol_equivalence_v436.cpp',project)
        self.assertEqual(project.count('nWiiRuntime/src/core/loader.cpp'),2)
        self.assertIn('target_include_directories(dol_equivalence PRIVATE ',project)
    def test_loader_order(self):
        source=(HOST/'windows_full_build_v426.py').read_text(encoding='utf-8')
        for seam in ("run_stage('dol_equivalence'", "run_stage('translation'", "run_stage('startup_observer'", "run_stage('strict_runtime_loader'", "run_stage('native_config'"):
            self.assertEqual(source.count(seam),1)
        order=[source.index(s) for s in ("run_stage('dol_equivalence'", "run_stage('translation'", "run_stage('startup_observer'", "run_stage('strict_runtime_loader'", "run_stage('native_config'")]
        self.assertEqual(order,sorted(order))
        self.assertIn("if not legacy_loader:\n        run_stage('strict_runtime_loader'",source)
        self.assertIn("if not legacy_loader:\n        run_stage('dol_equivalence'",source)
        self.assertEqual(contract('os-time')[1],'prepare_v435_full_os_time.py')
if __name__=='__main__':unittest.main()
