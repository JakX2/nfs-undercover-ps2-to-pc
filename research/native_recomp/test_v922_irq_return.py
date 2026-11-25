import unittest
from unittest.mock import patch
from pathlib import Path
from prepare_v922_irq_return import patch_label,patch_entry,patch_return
from prepare_v751_cold_capture import patch as capture
from prepare_v667_si_dispatch import patch_binding
from prepare_v919_handler_epilogue import patch_binding as epilogue
from prepare_v920_handler_return import patch_binding as returned
from prepare_v921_capture_join import patch_capture,patch_return as join
import audit_v922_irq_return as a
HERE=Path(__file__).parent
class IrqReturn(unittest.TestCase):
    def test_labels(self):
        h=0x80004000;w=0x60000000
        label=f'loc_{h:X}: ;\n    // 0x{h:08X}: {w:08X}\n';tick='    ++ctx.inst_count;\n';si='    ctx.si_instruction_boundary();\n'
        trace=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{h:X}, ctx); // V616 native IRQ resume\n'
        self.assertLess(patch_label(label+tick+si,h,w).index(si),patch_label(label+tick+si,h,w).index('v922::before'))
        self.assertIn('v922::resume',patch_label(label+trace+tick+si,h,w,True))
        for bad in (label+tick, label+tick+'    ctx.gpr[0]=0;\n'+si, label+tick+si+si):
            with self.assertRaises(ValueError):patch_label(bad,h,w)
        with self.assertRaises(ValueError):patch_label(label+tick+si,h,w,True)
    def test_shared_leaf(self):
        h=0x80004000;w=0x60000000
        label=f'loc_{h:X}: ;\n    // 0x{h:08X}: {w:08X}\n    ++ctx.inst_count;\n'
        si='    ctx.si_instruction_boundary();\n'
        for ordinal in (1,3):
            old=f'    undercover::wii::v709::before(ctx,0x{h:08x}u,0x{w:08x}u,{ordinal}u);\n'
            out=patch_label(label+si+old,h,w,shared=ordinal)
            self.assertIn('if(!undercover::wii::v922::active()) '+old.lstrip(),out)
            self.assertLess(out.index(si),out.index('v922::before'))
            for bad in (label+si,label+old+si,label+si+old+old):
                with self.assertRaises(ValueError):patch_label(bad,h,w,shared=ordinal)
            with self.assertRaises(ValueError):patch_label(label+si+old,h,w)
    def test_bindings(self):
        s=patch_entry(patch_capture(patch_binding(capture((HERE/'wii_external_entry_binding_v663.h').read_text()))))
        self.assertLess(s.index('v922::poll'),s.index('v667::poll'))
        self.assertLess(s.index('v922::observe'),s.index('v667::observe'))
        t=patch_return(join(returned(epilogue((HERE/'wii_handler_suffix_binding_v868.h').read_text()))))
        self.assertIn('v922::begin(c,pc,w)',t)
        with self.assertRaises(ValueError):patch_return(t)
    def test_audit(self):
        res=b'V922_IRQ_RETURN_RESULT original_context=1 scheduler=1 native_rfi=1 original_resume=1 visits=85 device_held=1 resumed_instruction_executed=0 boot_verified=0'
        base=[a.old.RETURN,*a.STAGES,res]
        with patch('audit_v921_capture_join.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(base),0)[1])
            for rows in (base[:-1],base[::-1],base+[res],base+[b'V922_fault'],[res,*base],base[:-1]+[res.replace(b'visits=85',b'visits=999')]):
                self.assertFalse(a.inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(base),126)[1])
if __name__=='__main__':unittest.main()
