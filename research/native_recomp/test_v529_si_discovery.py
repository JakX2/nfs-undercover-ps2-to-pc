import struct
import unittest
from unittest.mock import patch
from test_v524_si_sampling import fixture as sample_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,patch_probe as sample_probe,patch_si as sample_si
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v529_si_discovery import expectations,patch_probe,patch_si,patch_scheduler,CALLS,EDGES,RANGES
from audit_v510_exi_absent import STAGES as A,RESULT as AR
from audit_v520_si_entry import STAGES as E,RESULT as ER
from audit_v524_si_sampling import STAGES as S,RESULT as SR
from audit_v529_si_discovery import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_ID,log
def fixture():
    data=bytearray(sample_fixture())
    for site,target in (*CALLS,*EDGES):put(data,site,bl(site,target))
    for _,end in RANGES:put(data,end-4,0x4e800020)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}));self.assertEqual(header.count('VectorEdge{'),7)
        for pc in {s for s,_ in (*CALLS,*EDGES)}|{hi-4 for _,hi in RANGES}:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        with self.assertRaises(ValueError):patch_probe(new)
        old=sample_si((HOST/'wii_si_binding_v512.h').read_text());new=patch_si(old)
        self.assertEqual(new.count('si_discovery_trace.mmio'),2)
        with self.assertRaises(ValueError):patch_si(new)
        old=(HOST/'wii_si_type_scheduler_v514.h').read_text();new=patch_scheduler(old)
        self.assertEqual(new.count('si_discovery_trace.completion'),1)
        with self.assertRaises(ValueError):patch_scheduler(new)
    def test_gate(self):
        prior=OS_EXI_ID+A+[AR]+E+[ER]+S+[SR];good=prior+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,107),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (prior[:-1]+STAGES+[RESULT],0),(prior+STAGES[1:]+[RESULT],0),(prior+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
