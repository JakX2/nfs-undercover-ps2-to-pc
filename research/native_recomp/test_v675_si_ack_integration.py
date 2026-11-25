import os,re,shutil,subprocess,tempfile,unittest
from pathlib import Path
from prepare_v672_si_ack_route import patch_si
from prepare_v524_si_sampling import patch_si as sample_patch
from prepare_v529_si_discovery import patch_si as discovery_patch
from audit_v672_si_ack_route import EVENTS,RESULT
HOST=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
    def test_composed_mmio_seams(self):
        original=(HOST/'wii_si_binding_v512.h').read_text()
        prior=discovery_patch(sample_patch(original))
        after=patch_si(prior)
        self.assertEqual(after.count('si_completion_ack_trace.write(active_->controller_,*off,value);'),1)
        self.assertEqual(after.count('si_discovery_trace.mmio('),2)
        self.assertEqual(after.count('si_sampling_trace.si('),2)
        self.assertIn('arm_completion_ack',after)
        self.assertNotIn('active_->controller_.write(*off,value);',after)
    @unittest.skipIf(os.name=='nt','GCC sanitizer fixture is a Linux test; MSVC owner build verifies the native headers')
    def test_compiled_binding(self):
        cc=shutil.which('g++')
        if not cc:self.skipTest('GCC unavailable')
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for n in ('wii_si_controller_v511.h','wii_si_completion_ack_v668.h','wii_si_ack_binding_v672.h','wii_si_type_scheduler_v514.h','test_si_ack_integration_v675.cpp'):
                shutil.copyfile(HOST/n,root/n)
            (root/'wii_si_binding_v512.h').write_text(patch_si((HOST/'wii_si_binding_v512.h').read_text()))
            (root/'v672_private_si_ack_expectations.h').write_text('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v672 {inline constexpr uint32_t handler_first=0x80004000u,handler_end=0x80004020u;}\n')
            hw=root/'runtime/hw/hw.h';hw.parent.mkdir(parents=True)
            hw.write_text('#pragma once\n#include <atomic>\n#include <cstdint>\nnamespace nwii::runtime::hw {inline std::atomic<uint32_t> pi_intsr{0},pi_intmr{0};}\n')
            exe=root/'probe'
            subprocess.run([cc,'-std=c++20','-O1','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),str(root/'test_si_ack_integration_v675.cpp'),'-o',str(exe)],check=True,capture_output=True)
            expected={mode:(0,EVENTS+[RESULT]) for mode in ('native','mirror')}
            expected.update({
                'idle':(0,[b'V675_IDLE passed=1']),
                'stale':(0,EVENTS[:1]+[b'V675_STALE passed=1']),
                'masked':(126,[b'V672_SI_ACK_INVALID reason=1 trace=0']),
                'tamper':(126,EVENTS[:1]+[b'V672_SI_ACK_INVALID reason=2 trace=0']),
                'gap':(126,EVENTS[:1]+[b'V672_SI_ACK_INVALID reason=3 trace=3']),
                'wrong-next':(126,EVENTS[:1]+[b'V672_SI_ACK_INVALID reason=3 trace=3']),
                'direct':(126,EVENTS[:1]+[b'V673_SI_ACK_CALL ordinal=1 kind=1',b'V672_SI_ACK_INVALID reason=6 trace=0']),
                'indirect':(126,EVENTS[:1]+[b'V673_SI_ACK_CALL ordinal=1 kind=2',b'V672_SI_ACK_INVALID reason=6 trace=0']),
                'unknown':(126,EVENTS[:1]+[b'V673_SI_ACK_CALL ordinal=0 kind=0',b'V672_SI_ACK_INVALID reason=6 trace=0'])})
            for mode,(rc,rows) in expected.items():
                with self.subTest(mode=mode):
                    got=subprocess.run([str(exe),mode],capture_output=True,timeout=10)
                    self.assertEqual(got.returncode,rc,got.stderr.decode(errors='replace'))
                    self.assertEqual(got.stdout.splitlines(),rows)
                    self.assertEqual(got.stderr,b'')
            print('V675_SI_ACK_BINDING synthetic=1 cases=11 actual_mmio=1 original_execution=0')
if __name__=='__main__':unittest.main()
