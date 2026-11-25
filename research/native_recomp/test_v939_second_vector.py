import unittest
from unittest.mock import patch
from pathlib import Path
from prepare_v939_second_vector import patch_binding,patch_label
import audit_v939_second_vector as a
HERE=Path(__file__).parent
class SecondVector(unittest.TestCase):
    def test_seams(self):
        out=patch_binding((HERE/'wii_live_irq_return_binding_v922.h').read_text())
        self.assertIn('second.begin(c,reentry',out);self.assertIn('second.poll(c,cause()',out)
        self.assertIn('             <<route.visits()<<" device_held=1 resumed_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);',out)
        self.assertEqual(out.count('if(!second_enabled())std::_Exit(0);'),1)
        with self.assertRaises(ValueError):patch_binding(out)
        label='loc_80000500: ;\n    // 0x80000500: 60000000\n    ++ctx.inst_count;\n'
        si='    ctx.si_instruction_boundary();\n'
        self.assertIn('v922::second_before',patch_label(label+si,0x80000500,0x60000000))
        for bad in (label,label+si+si,label+'    ctx.gpr[3]=0;\n'+si):
            with self.assertRaises(ValueError):patch_label(bad,0x80000500,0x60000000)
    def test_audit(self):
        first=b'V932_REENTRY_RESULT native_rfi=1 second_exception=1 vector_entry=1 restored_context=1 visits=85 device_held=1 resumed_instruction_executed=0 boot_verified=0'
        result=b'V939_SECOND_RESULT original_vector=1 original_trampoline=1 saved_fields=38 vector_visits=31 trampoline_visits=20 second_dispatcher_entry=1 device_held=1 dispatcher_instruction_executed=0 boot_verified=0'
        rows=[first,a.TRAMP,result]
        with patch('audit_v932_pending_rfi.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[::-1],rows[:-1],rows+[result],[a.TRAMP,*rows],rows[:-1]+[result.replace(b'visits=31',b'visits=129')]):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
