import unittest
from unittest.mock import patch
from pathlib import Path
from prepare_v958_second_ack import patch_label,patch_binding,patch_si
from prepare_v939_second_vector import patch_binding as v939
from prepare_v951_second_dispatch import patch_binding as v951
from prepare_v777_transfer_return import patch_si as v777
import audit_v958_second_ack as a
HERE=Path(__file__).parent
class LiveAck(unittest.TestCase):
    def test_binding(self):
        old=v951(v939((HERE/'wii_live_irq_return_binding_v922.h').read_text()))
        s=patch_binding(old)
        self.assertIn('SiBinding::handoff_second_ack',s)
        self.assertIn('if(v958::active())return v958::poll(c);',s)
        self.assertIn('if(!v958::enabled())std::_Exit(0);',s)
        with self.assertRaises(ValueError):patch_binding(s)
    def test_mmio(self):
        s='#include "wii_si_completion_ack_v668.h"\n    static bool active()noexcept{return active_!=nullptr;}\n        try{return si_completion_ack_trace.read(active_->controller_,off);}\ntry{si_completion_ack_trace.write(active_->controller_,*off,value);}'
        s=v777(s);new=patch_si(s)
        self.assertIn('si_transfer_device.handoff_second_ack(v958::ack',new)
        self.assertIn('v958::ack.read(active_->controller_,off,value)',new)
        self.assertIn('v958::ack.write(active_->controller_,*off,value)',new)
        with self.assertRaises(ValueError):patch_si(new)
    def test_labels(self):
        pc=0x80004000;w=0x60000000
        for ns in ('v672','v680','v688','v693'):
            args='' if ns=='v680' else ',0u,0u'
            hook=f'    undercover::wii::{ns}::before(ctx,0x{pc:08x}u,0x{w:08x}u{args});\n'
            si='    ctx.si_instruction_boundary();\n'
            base=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'
            for text in (base+hook+si,base+si+hook):
                new=patch_label(text,pc,w,ns,True)
                self.assertIn('if(!undercover::wii::v958::active()) '+hook.lstrip(),new)
                self.assertIn('v958::before(ctx,0x80004000u,0x60000000u,true);',new)
                with self.assertRaises(ValueError):patch_label(text.replace(si,''),pc,w,ns,True)
                with self.assertRaises(ValueError):patch_label(new,pc,w,ns,True)
    def test_audit(self):
        p=b'V951_DISPATCH_RESULT original_dispatcher=1 original_leaves=4 pi_reads=1 handler_entry=1 saved_fields=38 visits=100 device_held=1 handler_instruction_executed=0 boot_verified=0'
        r=b'V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits=80 reads=2 writes=1 boot_verified=0'
        rows=[p,a.BEGIN,r]
        with patch('audit_v951_second_dispatch.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[r],[a.BEGIN,*rows],[p,r],rows+[b'V958_ACK_INVALID kind=1 stage=1 reason=2 call_reason=0 visits=2']):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
