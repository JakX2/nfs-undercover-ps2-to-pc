import subprocess
import unittest
from pathlib import Path
from windows_startup_scope_v434 import contract,launch_flags
from write_sram_profile_v536 import sram_fixture,payload
HOST=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_syntax(self):
        for name in ('run_full_recomp_probe_ci.sh','run_private_full_start.sh'):
            subprocess.run(['bash','-n',str(HOST/name)],check=True)
    def test_scope_composition(self):
        build=(HOST/'run_full_recomp_probe_ci.sh').read_text()
        run=(HOST/'run_private_full_start.sh').read_text()
        patches,observer,auditor=contract('os-sram')
        self.assertIn(observer,build)
        self.assertIn(auditor+'.py',run)
        self.assertIn(patches[-1]+'.py',build)
        for source in (build,run):
            for line in source.splitlines():
                if '|| "$mode" == os-si-return ]]' in line:
                    self.fail('SRAM predecessor omitted')
        for flag,value in launch_flags('os-sram').items():
            self.assertIn(flag+'='+value,run)
        self.assertIn('write_sram_profile_v536.py',run)
        self.assertEqual(len(sram_fixture()),64)
        self.assertIn(b'sram='+sram_fixture().hex().encode(),payload())
    def test_auto_scope(self):
        workflow=(HOST.parent.parent/'.github/workflows/wii-full-recomp-probe.yml').read_text()
        self.assertIn('os_sram_requested: ',workflow)
        self.assertIn('os_sram_requested=$os_sram',workflow)
        self.assertIn("outputs.os_sram_requested == 'true' && 'os-sram'",workflow)
        self.assertIn('os-si-return, os-sram]',workflow)
if __name__=='__main__':unittest.main()
