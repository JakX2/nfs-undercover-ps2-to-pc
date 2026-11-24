import unittest
from pathlib import Path
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v435_full_os_time import patch_probe as time_probe
from prepare_v439_full_os_hardware import patch_probe as hw_probe
from prepare_v444_full_os_arena import patch_probe,return_seam
from audit_v435_full_os_time import STAGES as TIME,RESULT as TIME_RESULT
from test_v435_full_os_time_audit import PREFIX
from audit_v439_full_os_hardware import STAGES as HW,RESULT as HW_RESULT,COPY
from audit_v444_full_os_arena import STAGES,RESULT,inspect
HOST=Path(__file__).parent
def log(lines):return b'\n'.join(lines)+b'\n'
class Tests(unittest.TestCase):
    def test_probe(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for transform in (cache_probe,data_probe,os_probe,time_probe,hw_probe):old=transform(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('os_arena.begin(cpu)',new);self.assertIn('os_arena.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
        seam='loc_80520818: ;\n    // 0x80520818: 60000000\n'
        self.assertIn('trace_call(0x80520818, ctx)',return_seam(seam,0x60000000))
        for bad in (seam+seam,seam.replace('60000000','4E800020'),return_seam(seam,0x60000000)):
            with self.assertRaises(ValueError):return_seam(bad,0x60000000)
    def test_gate(self):
        for copy in (0,1):
            prior=PREFIX+TIME+[TIME_RESULT,f'V439_HW_BEGIN copy={copy}'.encode()]+HW[:1]+([COPY] if copy else [])+HW[1:]+[HW_RESULT]
            for boot in (0,1,2):
                for direct in (0,1):
                    begin=f'V444_ARENA_BEGIN boot_path={boot} direct_low={direct}'.encode()
                    good=prior+[begin]+STAGES+[RESULT]
                    self.assertTrue(inspect(log(good),0)[1])
                    for bad,rc in ((good,89),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(prior+[begin,STAGES[1],STAGES[2],RESULT],0)):
                        self.assertFalse(inspect(log(bad),rc)[1])
                    self.assertIn('reason=7',inspect(log(prior+[begin,b'V444_ARENA_INVALID reason=7 stage=1']),89)[0])
if __name__=='__main__':unittest.main()
