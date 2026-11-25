import unittest
from pathlib import Path
from prepare_v831_callback_frontier import patch_prefix as earlier_prefix
from prepare_v847_wireless_wrapper import patch_frontier
from prepare_v850_callback_return import patch_label,patch_prefix,patch_wrapper,patch_ack,render
from prepare_v813_callback_time import verify_order

HERE=Path(__file__).parent
PC=0x80001000
W=0x60000000
LABEL='loc_80001000: ;\n    // 0x80001000: 60000000\n    ++ctx.inst_count;\n'
SI='    ctx.si_instruction_boundary();\n'
OLD='    undercover::wii::v768::restore_before(ctx,0x80001000u,0x60000000u);\n'
HANDLER='    undercover::wii::v672::before(ctx,0x80001000u,0x60000000u,0u,0u);\n'

class ReturnInstaller(unittest.TestCase):
    def test_callback(self):
        old=LABEL+SI+'    return;\n'
        new=patch_label(old,PC,W)
        verify_order(new,PC,W,'v850')
        for bad in (old+old,old.replace(SI,''),old.replace('60000000','60000001'),LABEL+'    ctx.gpr[1]=0;\n'+SI,new):
            with self.assertRaises(ValueError):patch_label(bad,PC,W)
    def test_restore(self):
        for old in (LABEL+OLD+SI,LABEL+SI+OLD):
            new=patch_label(old,PC,W,'restore')
            verify_order(new,PC,W,'v850')
            self.assertIn('if(!undercover::wii::v850::active()) '+OLD.lstrip(),new)
        with self.assertRaises(ValueError):patch_label(LABEL+OLD+SI+OLD,PC,W,'restore')
    def test_handler_resume(self):
        old=LABEL+SI+HANDLER+'    return;\n'
        new=patch_label(old,PC,W,'handler_resume')
        self.assertLess(new.index('v850::dispatch_resume'),new.index('++ctx.inst_count'))
        self.assertLess(new.index(SI),new.index('v850::handler_resume'))
        self.assertLess(new.index('v850::handler_resume'),new.index('v672::before'))
        for bad in (LABEL+SI,LABEL+HANDLER+SI):
            with self.assertRaises(ValueError):patch_label(bad,PC,W,'handler_resume')
    def test_binding(self):
        old=(HERE/'wii_callback_prefix_binding_v807.h').read_text().replace('#include "wii_callback_dispatch_device_v808.h"','#include "wii_callback_dispatch_device_v808.h"\n#include "wii_callback_time_binding_v813.h"')
        new=patch_prefix(earlier_prefix(old))
        self.assertIn('v831::capture(c);\n    v850::capture(c,pc,w,ordinal);',new)
        old=(HERE/'wii_wireless_wrapper_binding_v847.h').read_text()
        new=patch_wrapper(old)
        self.assertIn('route.stage()==2u&&route.ordinal()==3u&&!route.changed()',new)
        self.assertIn('finish(c,pc,0u);return true;',new)
        self.assertIn('finish(c,pc,w);',new)
        old='template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){\n    if(v847::active())v847::reject(3);\nif(v847::observe(a,c))return;'
        new=patch_ack(old)
        self.assertIn('if(v850::active())v850::reject(7);',new)
        self.assertIn('if(v850::active())return v850::poll(c);',new)
        self.assertIn('if(v850::observe(a,c))return;if(v847::observe(a,c))return;',new)
        for fn,s in ((patch_ack,new),(patch_wrapper,'bad'),(patch_prefix,'bad')):
            if fn==patch_ack:continue
            with self.assertRaises(ValueError):fn(s)
    def test_render(self):
        h=render(0x80001000,0x80001004,{0x80001004:W,0x80001008:0x4e800421,0x8000100c:0x48000001},
            {0x80001008:(4,2,None),0x8000100c:(13,1,0x80002000)},0x80002000,
            [W]*6+[0x4e800020],[W]*3+[0x4e800020],
            [(0x80003000,0x4e800421,6,W),(0x80003010,0x4e800421,11,W)])
        self.assertEqual(h.count('CallbackReturnExpectation{'),2)
        self.assertEqual(h.count('CallbackSuffixEdge{'),2)
        self.assertEqual(h.count('CallbackSuffixWord{'),3)

if __name__=='__main__':unittest.main()
