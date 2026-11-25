import unittest
from prepare_v831_callback_frontier import render,patch_prefix,patch_time,patch_ack
from pathlib import Path
HERE=Path(__file__).parent
class Installer(unittest.TestCase):
    def test_patches(self):
        p=patch_prefix((HERE/'wii_callback_prefix_binding_v807.h').read_text().replace(
            '#include "wii_callback_dispatch_device_v808.h"','#include "wii_callback_dispatch_device_v808.h"\n#include "wii_callback_time_binding_v813.h"'))
        self.assertIn('v831::capture(c);',p)
        self.assertLess(p.index('route.start_dispatch'),p.index('v831::capture(c);'))
        t=patch_time((HERE/'wii_callback_time_binding_v813.h').read_text())
        self.assertIn('if(v831::enabled()){v831::start(c,pc,w,route.stage()==5);return;}',t)
        a=patch_ack('    if(v813::active())return v813::poll(c);\nif(v813::observe(a,c))return;')
        self.assertEqual(a.count('if(v831::active())v831::reject(3);'),2)
        with self.assertRaises(ValueError):patch_ack(a.replace('if(v813::observe(a,c))return;',''))
    def test_render(self):
        s=render(0x80004000,0x80004004,{0x80004004:(0x80004000,0x60000000)},{0x80004004:(3,0x80006000),0x80004008:(5,0x80007000)})
        self.assertIn('CallbackFrontierWord{0x80004004u,0x60000000u}',s)
        self.assertIn('CallbackFrontierEdge{0x80004008u,0x80007000u,5u}',s)
        self.assertEqual(s.count('{'),s.count('}'))
if __name__=='__main__':unittest.main()
