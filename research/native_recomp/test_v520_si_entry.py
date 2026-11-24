import unittest
import struct
from unittest.mock import patch
from test_v510_exi_absent import fixture as absent_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,patch_probe as absent_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v520_si_entry import expectations,patch_probe,patch_label,CALLS,TAIL,EDGES
from audit_v510_exi_absent import STAGES as ABSENT_STAGES,RESULT as ABSENT_RESULT
from audit_v520_si_entry import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_ID,log
def fixture():
    data=bytearray(absent_fixture())
    for site,target in (*CALLS,*EDGES):put(data,site,bl(site,target))
    put(data,TAIL,bl(TAIL,0x80522f00)&~1)
    for slot in range(11):
        if struct.unpack_from('>I',data,0xac+4*slot)[0]==0:break
    else:raise ValueError('data slot')
    for h,v in ((0x1c,len(data)),(0x64,0x8070aa70),(0xac,4)):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(struct.pack('>I',0x80611000))
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets,w=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}))
        self.assertEqual(header.count('VectorEdge{'),4)
        for pc in {s for s,_ in (*CALLS,*EDGES)}|{TAIL}:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        line=f'loc_{TAIL:X}: ;\n    // 0x{TAIL:08X}: {w:08X}\n'
        self.assertIn('V520 original version tail',patch_label(line,w))
        with self.assertRaises(ValueError):patch_label(line+line,w)
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        with self.assertRaises(ValueError):patch_probe(new)
    def test_gate(self):
        prior=OS_EXI_ID+ABSENT_STAGES+[ABSENT_RESULT];good=prior+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,104),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (prior[:-1]+STAGES+[RESULT],0),(prior+STAGES[1:]+[RESULT],0),(prior+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
