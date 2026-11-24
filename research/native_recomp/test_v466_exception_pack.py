import unittest
from test_v434_windows_startup_scope import OS_IPC,log
from audit_v457_exception_vector import STAGES as VECTOR,RESULT as VECTOR_RESULT
from audit_v466_exception_pack import STAGES,RESULT,inspect
from test_v457_exception_vector import HOST
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v435_full_os_time import patch_probe as time_probe
from prepare_v439_full_os_hardware import patch_probe as hw_probe
from prepare_v444_full_os_arena import patch_probe as arena_probe
from prepare_v446_full_os_ipc import patch_probe as ipc_probe
from prepare_v457_exception_vector import patch_probe as vector_probe
from prepare_v466_exception_pack import patch_probe
class Tests(unittest.TestCase):
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('pack.first_copy(cpu)',new)
        self.assertIn('pack.first_vector_event(addr,cpu,first_vector.stage())',new)
        self.assertIn('pack.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_gate(self):
        prefix=OS_IPC+[b'V457_VECTOR_BEGIN debug_needed=1',b'V457_VECTOR_PRELUDE n=1']+VECTOR+[VECTOR_RESULT]
        good=prefix+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for i in range(len(STAGES)):
            self.assertFalse(inspect(log(prefix+STAGES[:i]+STAGES[i+1:]+[RESULT]),0)[1])
            self.assertFalse(inspect(log(prefix+STAGES[:i]+[STAGES[i]]+STAGES[i:]+[RESULT]),0)[1])
        for rows,rc in ((good,92),(good[:-1],0),(good+[RESULT],0),
                         (good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(prefix[:-1]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(rows),rc)[1])
        self.assertIn('reason=17',inspect(log(prefix+STAGES[:15]+[b'V466_PACK_INVALID reason=17 phase=3']),92)[0])
if __name__=='__main__':unittest.main()
