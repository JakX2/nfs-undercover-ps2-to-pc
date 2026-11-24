import struct
import unittest
from unittest.mock import patch
from test_v520_si_entry import fixture as entry_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,patch_probe as entry_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v524_si_sampling import expectations,patch_probe,patch_si,patch_vi,CALLS,RATE_END,XY_END,TV_END
from audit_v510_exi_absent import STAGES as A,RESULT as AR
from audit_v520_si_entry import STAGES as E,RESULT as ER
from audit_v524_si_sampling import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_ID,log
def fixture():
    data=bytearray(entry_fixture())
    for site,target in CALLS:put(data,site,bl(site,target))
    for end in (RATE_END,XY_END,TV_END):put(data,end-4,0x4e800020)
    for slot in range(11):
        if struct.unpack_from('>I',data,0xac+4*slot)[0]==0:break
    else:raise ValueError('data slot')
    for h,v in ((0x1c,len(data)),(0x64,0x80619a88),(0xac,4)):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(struct.pack('>I',0x000f0200))
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in CALLS}));self.assertEqual(header.count('VectorEdge{'),6)
        for pc in {s for s,_ in CALLS}|{RATE_END-4,XY_END-4,TV_END-4}:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        with self.assertRaises(ValueError):patch_probe(new)
        for name,fn in (('wii_si_binding_v512.h',patch_si),('wii_vi_clock_v522.h',patch_vi)):
            text=(HOST/name).read_text();new=fn(text);self.assertIn('si_sampling_trace',new)
            with self.assertRaises(ValueError):fn(new)
    def test_gate(self):
        prior=OS_EXI_ID+A+[AR]+E+[ER];good=prior+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,106),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (prior[:-1]+STAGES+[RESULT],0),(prior+STAGES[1:]+[RESULT],0),(prior+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
