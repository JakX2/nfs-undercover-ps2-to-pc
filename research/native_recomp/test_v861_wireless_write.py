import unittest
from pathlib import Path
from prepare_v861_wireless_write import patch_label,patch_wrapper,patch_ack,render
HERE=Path(__file__).parent
PC=0x80001000
W=0x60000000
L='loc_80001000: ;\n    // 0x80001000: 60000000\n    ++ctx.inst_count;\n'
SI='    ctx.si_instruction_boundary();\n'
EXI='    ctx.exi_instruction_boundary();\n'
OLD='    undercover::wii::v768::restore_before(ctx,0x80001000u,0x60000000u);\n'
class LiveWrite(unittest.TestCase):
    def test_hooks(self):
        for old in (L+EXI+SI,L+OLD+EXI+SI,L+EXI+SI+OLD):
            new=patch_label(old,PC,W)
            self.assertEqual(new.count('v847::before'),1)
            self.assertLess(new.index(SI),new.index('v847::before'))
            if OLD in old:self.assertIn('if(!undercover::wii::v847::active()) { '+OLD.strip()+' }',new)
        for old in (L+EXI,L+SI+SI,L+'    ctx.gpr[1]=0;\n'+SI,L+SI+'    undercover::wii::unknown::before(ctx,0,0);\n'):
            with self.assertRaises(ValueError):patch_label(old,PC,W)
    def test_binding(self):
        old=(HERE/'wii_wireless_wrapper_binding_v847.h').read_text()
        new=patch_wrapper(old)
        self.assertIn('v861::start(c,route);',new)
        self.assertIn('route.continue_write(c,v861::extension',new)
        self.assertLess(new.index('v861::device.observe'),new.index('route.before(c,pc,w'))
        self.assertLess(new.index('route.before(c,pc,w'),new.index('v861::after(c,old,route)'))
        self.assertIn('route.poll(c,si_transfer_device.held_now())',patch_ack('    if(v847::active())v847::reject(3);'))
        with self.assertRaises(ValueError):patch_wrapper(new)
    def test_render(self):
        h=render({PC:[W,0x4e800020]},[(PC,1,1,-4)],0xcd006024,PC,PC,PC)
        self.assertIn('WirelessCode{0x80001000u,words_0}',h)
        self.assertIn('WirelessRestoreRule{0x80001000u,1u,1u,-4}',h)
if __name__=='__main__':unittest.main()
