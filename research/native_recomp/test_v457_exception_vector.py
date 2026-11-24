import unittest
from pathlib import Path
from test_v446_full_os_ipc import PREFIX,TIME,TIME_RESULT,HW,HW_RESULT,ARENA,ARENA_RESULT,STAGES as IPC,RESULT as IPC_RESULT,log
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v435_full_os_time import patch_probe as time_probe
from prepare_v439_full_os_hardware import patch_probe as hw_probe
from prepare_v444_full_os_arena import patch_probe as arena_probe
from prepare_v446_full_os_ipc import patch_probe as ipc_probe
from prepare_v457_exception_vector import patch_probe,return_seam
from audit_v457_exception_vector import STAGES,RESULT,inspect
HOST=Path(__file__).parent
class Tests(unittest.TestCase):
    def test_composed_probe(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for transform in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe):old=transform(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('first_vector.begin(cpu)',new)
        self.assertIn('first_vector.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_original_return_seam(self):
        source='loc_80520DB8: ;\n    // 0x80520DB8: 12345678\n    ++ctx.inst_count;\n'
        updated=return_seam(source,0x12345678)
        self.assertIn('trace_call(0x80520DB8, ctx)',updated)
        with self.assertRaises(ValueError):return_seam(updated,0x12345678)
        with self.assertRaises(ValueError):return_seam(source,0x12345679)
        with self.assertRaises(ValueError):return_seam(source*2,0x12345678)
    def test_gate(self):
        prefix=PREFIX+TIME+[TIME_RESULT,b'V439_HW_BEGIN copy=0']+HW+[HW_RESULT,b'V444_ARENA_BEGIN boot_path=1 direct_low=0']+ARENA+[ARENA_RESULT,b'V446_IPC_BEGIN clamp=0']+IPC+[IPC_RESULT]
        for debug in (0,1):
            begin=f'V457_VECTOR_BEGIN debug_needed={debug}'.encode()
            prelude=[f'V457_VECTOR_PRELUDE n={i}'.encode() for i in range(1,3+debug)]
            good=prefix+[begin]+prelude+STAGES+[RESULT]
            self.assertTrue(inspect(log(good),0)[1])
            for bad,rc in ((good,91),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
                    (prefix+[begin]+STAGES+[RESULT],0),(prefix+[begin]+prelude[1:]+STAGES+[RESULT],0),
                    (prefix[:-1]+[begin]+prelude+STAGES+[RESULT],0)):
                self.assertFalse(inspect(log(bad),rc)[1])
            self.assertIn('reason=10',inspect(log(prefix+[begin]+prelude+[b'V457_VECTOR_INVALID reason=10 stage=0']),91)[0])
if __name__=='__main__':unittest.main()
