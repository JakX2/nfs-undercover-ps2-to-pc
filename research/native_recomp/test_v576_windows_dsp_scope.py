import unittest
from pathlib import Path
from windows_full_build_v426 import translator_project
from windows_startup_scope_v434 import requires_sc_overlay,requires_sram_profile,launch_flags,SCOPES,EXTERNAL_SCOPES
HOST=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_translator_opt_in(self):
        control=translator_project(HOST,HOST)
        overlay=translator_project(HOST,HOST,True)
        self.assertNotIn('UNDERCOVER_NATIVE_SC_OVERLAY',control)
        self.assertEqual(overlay.count('UNDERCOVER_NATIVE_SC_OVERLAY'),1)
        self.assertEqual(overlay.replace(' UNDERCOVER_NATIVE_SC_OVERLAY',''),control)
        for scope in SCOPES:self.assertEqual(requires_sc_overlay(scope),scope in ('os-dsp-sc','os-dsp-return','os-report','os-arena-clear',*EXTERNAL_SCOPES))
    def test_profile_flags(self):
        for scope in SCOPES:
            self.assertEqual(requires_sram_profile(scope),scope in ('os-sram','os-thread','os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return','os-report','os-arena-clear',*EXTERNAL_SCOPES))
            flags=launch_flags(scope)
            self.assertEqual('UNDERCOVER_V581_DSP' in flags,scope in ('os-dsp-return','os-report','os-arena-clear',*EXTERNAL_SCOPES))
            self.assertEqual('UNDERCOVER_V574_SC' in flags,scope in ('os-dsp-sc','os-dsp-return','os-report','os-arena-clear',*EXTERNAL_SCOPES))
            self.assertEqual('UNDERCOVER_V537_ACR' in flags,scope in ('os-audio','os-dsp-stage','os-dsp-sc','os-dsp-return','os-report','os-arena-clear',*EXTERNAL_SCOPES))
        build=(HOST/'windows_full_build_v426.py').read_text()
        self.assertIn("sram_fixture() if requires_sram_profile(scope)",build)
        self.assertIn("*(['--native-sc-overlay'] if sc_overlay else [])",build)
    def test_default(self):
        wf=(HOST.parent.parent/'.github/workflows/wii-native-windows-full.yml').read_text()
        self.assertIn('default: os-si-os-leaves',wf)
        self.assertIn("inputs.owner_scope || 'os-si-os-leaves'",wf)
        self.assertIn('os-dsp-stage, os-dsp-sc, os-dsp-return, os-report, os-arena-clear, os-external-entry, os-si-dispatch, os-si-ack, os-si-os-leaves, os-si-handler-time]',wf)
if __name__=='__main__':unittest.main()
