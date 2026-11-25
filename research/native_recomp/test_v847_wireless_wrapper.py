#!/usr/bin/env python3
import unittest
from pathlib import Path
from prepare_v847_wireless_wrapper import patch_frontier,patch_ack,patch_leaf,patch_label,render
from prepare_v813_callback_time import verify_order

class WirelessInstaller(unittest.TestCase):
    def test_frontier(self):
        p=Path(__file__).with_name('wii_callback_frontier_binding_v831.h')
        old=p.read_text();new=patch_frontier(old)
        self.assertEqual(new.count('finish(c,pc,w);'),2)
        self.assertIn('if(v847::enabled()){v847::start(c,pc,w,route.stage()==2,route.ordinal());return;}',new)
        self.assertEqual(new.count('std::_Exit(0);'),1)
        with self.assertRaises(ValueError):patch_frontier(new)
    def test_ack(self):
        old='    if(v831::active())v831::reject(3);\n    if(v831::active())v831::reject(3);if(v813::observe(a,c))return;\n'
        new=patch_ack(old)
        self.assertIn('if(v847::active())v847::reject(3);',new)
        self.assertIn('if(v847::observe(a,c))return;if(v831::active())',new)
        with self.assertRaises(ValueError):patch_ack(old.replace('if(v813::observe(a,c))return;',''))
    def test_shared(self):
        old='#include "wii_callback_time_binding_v813.h"\n    if(v813::active()){v813::before(c,pc,word);return;}\n'
        new=patch_leaf(old)
        self.assertLess(new.index('if(v847::active())'),new.index('if(v813::active())'))
        self.assertEqual(new.count('v847::before(c,pc,word)'),1)
        with self.assertRaises(ValueError):patch_leaf('bad')
    def test_label(self):
        pc=0x80001000;w=0x60000000
        s='loc_80001000: ;\n    // 0x80001000: 60000000\n    ++ctx.inst_count;\n    ctx.si_instruction_boundary();\n    return;\n'
        new=patch_label(s,pc,w);verify_order(new,pc,w,'v847')
        for bad in (s.replace('60000000','60000001'),s.replace('    ctx.si_instruction_boundary();\n',''),s+s,s.replace('    ctx.si_instruction_boundary();','    ctx.gpr[0]=0;\n    ctx.si_instruction_boundary();'),new):
            with self.assertRaises(ValueError):patch_label(bad,pc,w)
    def test_render(self):
        roots={i:[0x60000000]*(i+1) for i in range(5)}
        new=render(roots,tuple(roots),[(4,8,12,3),(16,20,24,5)],28,32)
        self.assertEqual(new.count('WirelessCode{'),5)
        self.assertEqual(new.count('WirelessEdge{'),2)
        self.assertIn('namespace undercover::wii::v847',new)
if __name__=='__main__':unittest.main()
