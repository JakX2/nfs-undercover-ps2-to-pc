import unittest
from test_v559_dsp_stage import (HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe,audio_probe,patch_probe as dsp_probe,log)
from prepare_v574_dsp_sc import patch_probe as sc_probe
from prepare_v581_dsp_return import patch_probe,patch_context,patch_return,CTX_INCLUDE,TICK
from test_v575_dsp_sc_frontier import GOOD
from audit_v581_dsp_return import STAGES,RESULT,inspect
class Tests(unittest.TestCase):
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe,audio_probe,dsp_probe,sc_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('DspBootSession',new);self.assertIn('dsp_return.observe',new)
        with self.assertRaises(ValueError):patch_probe(new)
        ctx=CTX_INCLUDE+'\n'+TICK
        self.assertIn('DspBootSession::advance',patch_context(ctx))
        with self.assertRaises(ValueError):patch_context(ctx+ctx)
        label='loc_805208D8: ;\n    // 0x805208D8: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('trace_call(0x805208D8, ctx)',patch_return(label,0x60000000))
        for bad in (label+label,patch_return(label,0x60000000),label.replace('60000000','44000002')):
            with self.assertRaises(ValueError):patch_return(bad,0x60000000)
    def test_gate(self):
        good=GOOD+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,114),(good[:-1],0),(good+[RESULT],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(good+[b'V581_DSP_PROFILE_INVALID rejected=1'],0),(GOOD+STAGES[::-1]+[RESULT],0),(GOOD[:-1]+STAGES+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
