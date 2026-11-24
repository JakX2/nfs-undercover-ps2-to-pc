import unittest
from unittest.mock import patch
from test_v549_thread_init import fixture as thread_fixture,HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,patch_probe as thread_probe
from test_v468_exception_pack_geometry import digest,bl,put
from prepare_v556_audio_reset import expectations,patch_probe,patch_acr,patch_label,EDGES,RANGES,AUDIO,STOP
from audit_v510_exi_absent import STAGES as A,RESULT as AR
from audit_v520_si_entry import STAGES as E,RESULT as ER
from audit_v524_si_sampling import STAGES as S,RESULT as SR
from audit_v529_si_discovery import STAGES as D,RESULT as DR
from audit_v534_sram_read import STAGES as R,RESULT as RR
from audit_v549_thread_init import STAGES as T,RESULT as TR
from audit_v556_audio_reset import STAGES,RESULT,inspect
from test_v434_windows_startup_scope import OS_EXI_ID,log
def fixture():
    data=bytearray(thread_fixture())
    for site,target in EDGES:put(data,site,bl(site,target))
    for lo,hi in RANGES:
        if lo!=AUDIO:put(data,hi-4,0x4e800020)
    put(data,STOP,0x60000000)
    return bytes(data)
class Tests(unittest.TestCase):
    @patch('prepare_v457_exception_vector.ipc_expectations',return_value='synthetic predecessor')
    def test_geometry(self,_):
        raw=fixture();header,targets,w=expectations(raw,digest(raw))
        self.assertEqual(targets,sorted({pc for _,pc in EDGES}))
        self.assertEqual(header.count('VectorEdge{'),12);self.assertEqual(w,0x60000000)
        for pc in {s for s,_ in EDGES}|{hi-4 for lo,hi in RANGES if lo!=AUDIO}|{STOP}:
            bad=bytearray(raw);put(bad,pc,0)
            with self.assertRaises(ValueError):expectations(bad,digest(bad))
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe):old=f(old)
        new=patch_probe(old);self.assertEqual(new.count('std::_Exit(0)'),1)
        with self.assertRaises(ValueError):patch_probe(new)
        acr=patch_acr((HOST/'wii_audio_acr_v537.h').read_text())
        self.assertEqual(acr.count('audio_reset_trace.record'),2)
        with self.assertRaises(ValueError):patch_acr(acr)
        label='loc_80522010: ;\n    // 0x80522010: 60000000\n'
        self.assertIn('trace_call(0x80522010, ctx)',patch_label(label,0x60000000))
        with self.assertRaises(ValueError):patch_label(label+label,0x60000000)
    def test_gate(self):
        prior=OS_EXI_ID+A+[AR]+E+[ER]+S+[SR]+D+[DR]+R+[RR]+T+[TR];good=prior+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,111),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),
            (prior[:-1]+STAGES+[RESULT],0),(prior+STAGES[1:]+[RESULT],0),(prior+STAGES[::-1]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
