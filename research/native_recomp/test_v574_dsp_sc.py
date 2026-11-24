import unittest
from test_v559_dsp_stage import (HOST,cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe,audio_probe,patch_probe as dsp_probe,OS_EXI_ID,A,AR,E,ER,S,SR,D,DR,R,RR,T,TR,O,OR,STAGES as DSP,RESULT as DRSP,log)
from prepare_v574_dsp_sc import patch_probe,patch_ios,patch_return,HEADER,HOOK,diagnostic
from audit_v574_dsp_sc import STAGES,RESULT,inspect
class Tests(unittest.TestCase):
    def test_composition(self):
        old=(HOST/'wii_full_hardware_probe_v425.h').read_text()
        for f in (cache_probe,data_probe,os_probe,time_probe,hw_probe,arena_probe,ipc_probe,vector_probe,pack_probe,alarm_probe,irq_probe,mmio_probe,return_probe,context_probe,reuse_probe,poll_probe,handler_probe,id_probe,absent_probe,entry_probe,sample_probe,discovery_probe,sram_probe,thread_probe,audio_probe,dsp_probe):old=f(old)
        new=patch_probe(old)
        self.assertEqual(new.count('std::_Exit(0)'),1)
        self.assertIn('v574::arm(addr,cpu)',new)
        self.assertIn('v574::route.returned(cpu)',new)
        with self.assertRaises(ValueError):patch_probe(new)
        source=HEADER+'\n#include <algorithm>\n\n#include "runtime/cpu_context.h"\n\n'+HOOK+'\n  uint32_t syscall_id = ctx.gpr[0];\n}'
        out=patch_ios(source)
        self.assertIn('try_sc(ctx)) return false;',out)
        self.assertEqual(out.count('#include "runtime/cpu_context.h"'),2)
        self.assertEqual(out.count('#include "undercover/wii_boot_sc_binding_v574.h"'),1)
        self.assertEqual(out.replace('\n#include "undercover/wii_boot_sc_binding_v574.h"','',1).replace('\n  if (undercover::wii::v574::try_sc(ctx)) return false;','',1),source)
        self.assertIn('uint32_t syscall_id = ctx.gpr[0];',out)
        for bad in (out,source+source,source.replace(HOOK,'')):
            with self.assertRaises(ValueError):patch_ios(bad)
        label='loc_80522044: ;\n    // 0x80522044: 60000000\n    ++ctx.inst_count;\n'
        self.assertIn('trace_call(0x80522044, ctx)',patch_return(label,0x60000000))
        for bad in (label+label,patch_return(label,0x60000000),label.replace('++ctx.inst_count','ctx.inst_count++')):
            with self.assertRaises(ValueError):patch_return(bad,0x60000000)
    def test_diagnostic(self):
        try:patch_ios('private bytes and paths must not be printed')
        except ValueError as e:
            row=diagnostic(e)
            self.assertIn('file=prepare_v419_full_start.py',row)
            self.assertIn('reason=source_seam',row)
            self.assertIn('caller=prepare_v574_dsp_sc.py',row)
            self.assertNotIn('private',row)
        try:raise ValueError('private unknown text 0x1234')
        except ValueError as e:
            row=diagnostic(e)
            self.assertIn('reason=other',row)
            self.assertNotIn('0x1234',row)
    def test_exact_history(self):
        prior=OS_EXI_ID+A+[AR]+E+[ER]+S+[SR]+D+[DR]+R+[RR]+T+[TR]+O+[OR]+DSP+[DRSP]
        good=prior+STAGES+[RESULT]
        self.assertTrue(inspect(log(good),0)[1])
        for bad,rc in ((good,113),(good[:-1],0),(good+[RESULT],0),(good+[b'V572_SC_DIRECT_ONLY rejected=1'],0),(good+[b'V425_HARDWARE_FALLBACK hit=1'],0),(prior[:-1]+STAGES+[RESULT],0),(prior+STAGES[::-1]+[RESULT],0),(prior+STAGES[1:]+[RESULT],0)):
            self.assertFalse(inspect(log(bad),rc)[1])
if __name__=='__main__':unittest.main()
