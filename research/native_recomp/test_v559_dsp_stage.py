import struct
import unittest
from unittest.mock import patch
from test_v556_audio_reset import fixture as audio_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe,patch_probe as audio_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v559_dsp_stage import expectations,patch_probe,patch_label,EDGES,GETHI,SC,MICROCODE
from audit_v510_exi_absent import STAGES as A,RESULT as AR
from audit_v520_si_entry import STAGES as E,RESULT as ER
from audit_v524_si_sampling import STAGES as S,RESULT as SR
from audit_v529_si_discovery import STAGES as D,RESULT as DR
from audit_v534_sram_read import STAGES as R,RESULT as RR
from audit_v549_thread_init import STAGES as T,RESULT as TR
from audit_v556_audio_reset import STAGES as O,RESULT as OR
from audit_v559_dsp_stage import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_ID,log
def fixture():
    data=bytearray(audio_fixture())
    for site,target in EDGES:put(data,site,bl(site,target))
    put(data,GETHI+4,0x4e800020);put(data,SC,0x44000002);put(data,SC+4,0x4e800020)
    for slot in range(11):
        if struct.unpack_from('>I',data,0xac+4*slot)[0]==0:break
    else:raise ValueError('data slot')
    for h,v in ((0x1c,len(data)),(0x64,MICROCODE),(0xac,128)):struct.pack_into('>I',data,h+4*slot,v)
    data.extend(bytes((i*17+9)&255 for i in range(128)))
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets=expectations(raw,digest(raw))
        self.assertEqual(header.count('VectorEdge{'),4)
        self.assertEqual(targets,sorted({pc for _,pc in EDGES}))
        for pc in {s for s,_ in EDGES}|{GETHI+4,SC,SC+4}:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
        with self.assertRaises(ValueError):expectations(raw[:-1],digest(raw[:-1]))
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe,audio_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        with self.assertRaises(ValueError):patch_probe(new)
        label='loc_805222E8: ;\n    // 0x805222E8: 44000002\n'
        self.assertIn('trace_call(0x805222E8, ctx)',patch_label(label))
        for bad in (label+label,patch_label(label),label.replace('44000002','60000000')):
            with self.assertRaises(ValueError):patch_label(bad)
    def test_gate(self):
        prior=OS_EXI_ID+A+[AR]+E+[ER]+S+[SR]+D+[DR]+R+[RR]+T+[TR]+O+[OR];good=prior+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,112),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (prior[:-1]+STAGES+[RESULT],0),(prior+STAGES[1:]+[RESULT],0),(prior+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
