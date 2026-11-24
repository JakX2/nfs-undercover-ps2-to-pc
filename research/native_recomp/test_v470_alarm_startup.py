import unittest
from unittest.mock import patch
from test_v468_exception_pack_geometry import fixture,digest,bl,put
from test_v466_exception_pack import HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe
from prepare_v466_exception_pack import patch_probe as pack_probe
from prepare_v470_alarm_startup import expectations,patch_probe,CALLS,ENDS
from test_v434_windows_startup_scope import OS_IPC,log
from audit_v457_exception_vector import STAGES as VECTOR,RESULT as VECTOR_RESULT
from audit_v466_exception_pack import STAGES as PACK,RESULT as PACK_RESULT
from audit_v470_alarm_startup import STAGES,RESULT,inspect

class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=bytearray(fixture())
        for site,target in CALLS:put(raw,site,bl(site,target))
        for end in ENDS:put(raw,end-4,0x4e800020)
        header,targets=expectations(raw,digest(raw))
        self.assertEqual(header.count('VectorEdge{'),5)
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        for site in [s for s,_ in CALLS]+[end-4 for end in ENDS]:
            bad=bytearray(raw);put(bad,site,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('alarm.begin(cpu)',new)
        self.assertIn('alarm.observe(addr,cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_gate(self):
        prefix=OS_IPC+[b'V457_VECTOR_BEGIN debug_needed=1',b'V457_VECTOR_PRELUDE n=1']+VECTOR+[VECTOR_RESULT]+PACK+[PACK_RESULT]
        good=prefix+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for i in range(len(STAGES)):
            self.assertFalse(inspect(log(prefix+STAGES[:i]+STAGES[i+1:]+[RESULT]),0)[1])
            self.assertFalse(inspect(log(prefix+STAGES[:i]+[STAGES[i]]+STAGES[i:]+[RESULT]),0)[1])
        for rows,rc in ((good,93),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(prefix[:-1]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(rows),rc)[1])
if __name__=='__main__':unittest.main()
