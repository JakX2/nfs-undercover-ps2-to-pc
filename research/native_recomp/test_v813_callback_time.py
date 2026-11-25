import unittest
from pathlib import Path
from prepare_v813_callback_time import patch_prefix,patch_callback_label,verify_order,patch_shared

class TimeRoute(unittest.TestCase):
    def test_prefix(self):
        s=(Path(__file__).parent/'wii_callback_prefix_binding_v807.h').read_text()
        q=patch_prefix(s)
        self.assertIn('v813::start(c,pc,w,route.stage()==6)',q)
        self.assertEqual(q.count('si_transfer_device.after_return_at(c.inst_count)'),1)
        with self.assertRaises(ValueError):patch_prefix(q)
    def test_order(self):
        base='loc_80004000: ;\n    // 0x80004000: 60000000\n    ++ctx.inst_count;\n'
        hook='    undercover::wii::v693::before(ctx,0x80004000u,0x60000000u,0,0);\n'
        si='    ctx.si_instruction_boundary();\n'
        verify_order(base+si+hook,0x80004000,0x60000000,'v693')
        with self.assertRaises(ValueError):verify_order(base+hook+si,0x80004000,0x60000000,'v693')
        q=patch_callback_label(base+si,0x80004000,0x60000000)
        self.assertIn('v813::before',q);self.assertNotIn('v807::before',q)
    def test_shared(self):
        s='#include "wii_alarm_return_binding_v786.h"\n    if(v786::active()){v786::before(c,pc,word);return;}\n'
        q=patch_shared(s)
        self.assertLess(q.index('v813::active'),q.index('v786::active'))
        with self.assertRaises(ValueError):patch_shared(q)
if __name__=='__main__':unittest.main()
