import unittest
from unittest.mock import patch
from pathlib import Path
from prepare_v778_transfer_suffix import patch_transfer,patch_handler,patch_ack
from prepare_v742_handler_time import patch_handler as time_handler
from prepare_v768_transfer_prefix import patch_handler as prefix_handler
from audit_v778_transfer_suffix import inspect
class Suffix(unittest.TestCase):
    def test_transfer(self):
        s=patch_transfer((Path(__file__).parent/'wii_transfer_return_binding_v777.h').read_text())
        self.assertIn('if(!continue_suffix())std::_Exit(0);',s)
        self.assertIn('si_transfer_device.after_return_at(c.inst_count)',s)
        with self.assertRaises(ValueError):patch_transfer(s)
    def test_handler(self):
        s=patch_handler(prefix_handler(time_handler((Path(__file__).parent/'wii_si_handler_return_binding_v726.h').read_text())))
        self.assertIn('si_transfer_device.held_now()',s)
        self.assertLess(s.index('V778_NEXT_BOUNDARY'),s.index('V747_NEXT_BOUNDARY'))
        self.assertIn('V778_HANDLER_BLR abi=1',s)
    def test_ack(self):
        s=patch_ack('    if(v768::active()){v768::handler_return(c,pc,word);return;}\n    if(v768::active())return v768::poll(c);')
        self.assertLess(s.index('witness.transfer_returned'),s.index('v726::before'))
    def test_audit(self):
        base=b'V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1 idle=1 irq_lane=1 reads=2 writes=3 follow=2 pending=1 total=80 handler_instruction_executed=0 boot_verified=0'
        a=b'V726_HANDLER_CONTROL ordinal=5 kind=1 opcode=18'
        b=b'V778_NEXT_BOUNDARY ordinal=5 kind=1 visits=40 polls=2 follow=3 executed=0'
        c=b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=40 polls=2'
        end=b'V778_HANDLER_BLR abi=1 visits=50 polls=2 follow=3 executed=0 boot_verified=0'
        with patch('audit_v778_transfer_suffix.transfer',return_value=('',True)):
            self.assertTrue(inspect(b'\n'.join((base,a,b,c)),126)[1])
            self.assertTrue(inspect(b'\n'.join((base,end)),0)[1])
            for bad in ((base,b,a,c),(base,a,b.replace(b'follow=3',b'follow=0'),c),(base,a,b,c,c),(base,a,b,c.replace(b'polls=2',b'polls=3'))):
                self.assertFalse(inspect(b'\n'.join(bad),126)[1])
if __name__=='__main__':unittest.main()
