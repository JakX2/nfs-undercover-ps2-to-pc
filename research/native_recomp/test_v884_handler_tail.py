import unittest
from prepare_v884_handler_tail import patch_label,patch_suffix,patch_ack
H=0x80004000;W=0x60000000
SI='    ctx.si_instruction_boundary();\n'
def label():
    return f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n    ++ctx.inst_count;\n'
class TailPatch(unittest.TestCase):
    def test_resume(self):
        old=f'    undercover::wii::v726::resume(ctx,0x{H:08x}u,0x{W:08x}u);\n'
        s=patch_label(label()+old+SI,H,W,'resume')
        self.assertLess(s.index('v884::dispatch_resume'),s.index('++ctx.inst_count'))
        self.assertLess(s.index(SI),s.index('v884::resume'))
        self.assertIn('if(!undercover::wii::v884::active()) '+old.lstrip(),s)
        for bad in (label()+SI,label()+old, label()+old+old+SI,label()+old+'    ctx.gpr[0] = 1;\n'+SI):
            with self.assertRaises(ValueError):patch_label(bad,H,W,'resume')
    def test_alias(self):
        old=f'    undercover::wii::v726::restore_before(ctx,0x{H:08x}u,0x{W:08x}u);\n'
        for body in (label()+SI,label()+old+SI):
            s=patch_label(body,H,W,'alias')
            self.assertLess(s.index(SI),s.index('v884::before_alias'))
            if old in body:self.assertIn('if(!undercover::wii::v884::active()) '+old.lstrip(),s)
            with self.assertRaises(ValueError):patch_label(s,H,W,'alias')
        gated='    if(!undercover::wii::v847::active()&&!undercover::wii::v850::active()) '+old.lstrip()
        out=patch_label(label()+gated+SI,H,W,'alias')
        self.assertIn('if(!undercover::wii::v884::active()) { '+gated.strip()+' }',out)
        with self.assertRaises(ValueError):patch_label(label()+'    ctx.gpr[1] = 0;\n'+SI,H,W,'alias')
    def test_binding(self):
        s='#include "wii_callback_return_binding_v850.h"\n    if(!v850::continue_handler()||x)return false;\n    if(kind){\n}\ntemplate<class C>bool poll(C& c){\n}'
        out=patch_suffix(s)
        self.assertIn('v884::handler_before',out);self.assertIn('v884::start',out);self.assertIn('v884::poll',out)
        with self.assertRaises(ValueError):patch_suffix(out)
        self.assertIn('v884::observe',patch_ack('    if(v868::active())v868::reject(6);'))
if __name__=='__main__':unittest.main()
