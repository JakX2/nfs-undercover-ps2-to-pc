import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v928_leaf_finish import patch_binding,patch_one
from prepare_owner_irq_finish_v927 import extract_shape
import audit_v928_leaf_finish as a
HERE=Path(__file__).parent
class LeafFinish(unittest.TestCase):
    def test_shape(self):
        word=(21<<26)|(4<<21)|(3<<16)|(17<<11)|(31<<6)|(31<<1)
        self.assertTrue(extract_shape(word))
        for bit in (0,1,6,11,16,26):
            self.assertFalse(extract_shape(word^(1<<bit)))
    def test_binding(self):
        s=patch_binding((HERE/'wii_live_irq_return_binding_v922.h').read_text())
        self.assertIn('finish.start(c,*captured,false',s)
        self.assertIn('finish.poll(c,true)',s)
        self.assertIn('finish.dispatch(c,pc,true)',s)
        with self.assertRaises(ValueError):patch_binding(s)
    def test_label(self):
        pc=0x80004000;w=0x4e800020
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n'
        tick='    ++ctx.inst_count;\n';si='    ctx.si_instruction_boundary();\n'
        trace=f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx); // V616 native IRQ resume\n'
        self.assertIn('v922::leaf_blr',patch_one(label+tick+si,pc,w))
        self.assertIn('v922::caller_resume',patch_one(label+trace+tick+si,pc,w,True))
        for bad in (label+tick, label+tick+si+si,label+tick+'    ctx.gpr[0]=0;\n'+si):
            with self.assertRaises(ValueError):patch_one(bad,pc,w)
    def test_audit(self):
        res=b'V922_IRQ_RETURN_RESULT original_context=1 scheduler=1 native_rfi=1 original_resume=1 visits=85 device_held=1 resumed_instruction_executed=0 boot_verified=0'
        rows=[res,a.BEGIN,a.BLR,a.POLL,a.RETURN]
        with patch('audit_v922_irq_return.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[a.RETURN],rows+[b'V928_fault'],[a.BEGIN,*rows]):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
