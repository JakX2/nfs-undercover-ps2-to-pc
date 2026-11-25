import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v768_transfer_prefix import patch_handler,patch_leaf,patch_ack
from prepare_v742_handler_time import patch_handler as time_handler,patch_leaf as time_leaf
from audit_v768_transfer_prefix import inspect
class Prefix(unittest.TestCase):
    def test_hooks(self):
        host=Path(__file__).parent
        s=patch_handler(time_handler((host/'wii_si_handler_return_binding_v726.h').read_text()))
        self.assertIn('witness.before_authenticated(c,pc,w,held(),4)',s)
        self.assertIn('v768::start(c,pc,w);return;',s)
        with self.assertRaises(ValueError):patch_handler(s)
        s=patch_leaf(time_leaf((host/'wii_si_os_leaf_binding_v709.h').read_text()))
        self.assertLess(s.index('if(v768::active())'),s.index('if(v742::route.active())'))
        s=patch_ack('    if(v742::route.active())return v742::poll(c);\nif(v742::observe(a,c))return;')
        self.assertIn('if(v768::observe(a,c))return;',s)
    def test_audit(self):
        base=[b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=43 handler_return=0 boot_verified=0']
        a=b'V768_TRANSFER_ENTRY channel=1 type=1 idle=1'
        b=b'V768_TRANSFER_RESULT original_entry=1 save=1 disable=1 boundary=1 visits=24 mmio_executed=0 boot_verified=0'
        with patch('audit_v768_transfer_prefix.time',return_value=('',True)):
            self.assertTrue(inspect(b'\n'.join(base+[a,b]),0)[1])
            for bad in ([a]+base+[b],base+[b,a],base+[a,b,b],base+[a,b.replace(b'save=1',b'save=0')]):
                self.assertFalse(inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(inspect(b'\n'.join(base+[a,b]),126)[1])
if __name__=='__main__':unittest.main()
