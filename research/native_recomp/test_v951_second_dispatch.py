import unittest
from unittest.mock import patch
from pathlib import Path
from prepare_v939_second_vector import patch_binding as old_patch
from prepare_v951_second_dispatch import patch_binding,patch_label,patch_trace
from prepare_v667_si_dispatch import TIME,DISABLE,DISPATCH
import audit_v951_second_dispatch as a
HERE=Path(__file__).parent
class SecondDispatch(unittest.TestCase):
    def test_binding(self):
        old=old_patch((HERE/'wii_live_irq_return_binding_v922.h').read_text())
        new=patch_binding(old)
        self.assertIn('second_dispatch_mmio=&second_dispatch',new)
        self.assertIn('if(second_dispatch_active_now()){second_dispatch_before',new)
        self.assertIn('if(!second_dispatch_enabled())std::_Exit(0);',new)
        with self.assertRaises(ValueError):patch_binding(new)
    def test_labels(self):
        for root in (TIME,DISABLE,DISPATCH):
            pc=root;w=0x60000000
            s=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n    ctx.si_instruction_boundary();\n'
            if root==TIME:s+=f'    undercover::wii::v709::before(ctx,0x{pc:08x}u,0x{w:08x}u,2u);\n'
            if root==DISABLE:s+=f'    undercover::wii::v922::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
            new=patch_label(s,pc,w,root,False)
            if root==DISABLE:self.assertEqual(s,new)
            else:self.assertIn('v922::second_dispatch_before',new)
            if root==TIME:self.assertIn('if(!undercover::wii::v922::second_dispatch_active_now())',new)
            with self.assertRaises(ValueError):patch_label(s.replace('    ctx.si_instruction_boundary();\n',''),pc,w,root,False)
    def test_trace(self):
        s='#include "wii_si_dispatch_v667.h"\n        si_dispatch_pi_reads.record(write,address,width,value,native);\n'
        out=patch_trace(s);self.assertIn('record_second_dispatch_pi',out)
        with self.assertRaises(ValueError):patch_trace(out)
    def test_audit(self):
        first=b'V939_SECOND_RESULT original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=34 trampoline_visits=20 second_dispatcher_entry=1 device_held=1 dispatcher_instruction_executed=0 boot_verified=0'
        result=b'V951_DISPATCH_RESULT original_dispatcher=1 original_leaves=4 pi_reads=1 handler_entry=1 saved_fields=38 visits=150 device_held=1 handler_instruction_executed=0 boot_verified=0'
        rows=[first,a.BEGIN,*a.EDGES,result]
        with patch('audit_v939_second_vector.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[result],[a.BEGIN,*rows],rows[:-2]+[result]):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
