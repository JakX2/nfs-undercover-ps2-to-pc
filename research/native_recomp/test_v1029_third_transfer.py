import unittest
from prepare_v1029_third_transfer import hook,SI,replace_body,include_once,verify_abi,replace_stage
P=0x80004000;W=0x48000101
L=f'loc_{P:X}: ;\n    // 0x{P:08X}: {W:08X}\n    ++ctx.inst_count;\n'+SI
CALL=f'undercover::wii::v958::before(ctx,0x{P:08x}u,0x{W:08x}u,'
LEGACY=f'    undercover::wii::v768::before(ctx,0x{P:08x}u,0x{W:08x}u);\n'
class Hooks(unittest.TestCase):
    def test_frontier(self):
        out=hook(L+'    '+CALL+'true);\n',P,W,'frontier')
        self.assertIn('SiBinding::handoff_second_transfer',out)
        self.assertLess(out.index('v958::before'),out.index('handoff_second_transfer'))
    def test_shared_and_legacy(self):
        for extra in ('','    '+CALL+'false);\n','    if(undercover::wii::v958::callback_active()) '+CALL+'false);\n'):
            out=hook(L+extra+LEGACY,P,W,'body')
            self.assertIn('if(!undercover::wii::v958::third_active()) '+LEGACY.lstrip(),out)
            self.assertEqual(out.count(SI),1)
            self.assertEqual(out.count('v958::before'),2 if 'callback_active' in extra else 1)
        out=hook(L+'    '+CALL+'true);\n',P,W,'resume')
        self.assertIn('third_active()) '+CALL+'false);',out)
        self.assertIn('else '+CALL+'true);',out)
    def test_unchanged_shared_leaf(self):
        body=L+'    '+CALL+'false);\n'
        self.assertEqual(hook(body,P,W,'body'),body)
        src='#include "runtime/cpu_context.h"\n'+body
        self.assertEqual(replace_body(src,body,body),src)
        with self.assertRaisesRegex(ValueError,'third body seam'):
            replace_body(src+body,body,body)
        inc='#include "undercover/wii_second_ack_live_v958.h"'
        once=include_once(src,inc)
        self.assertEqual(include_once(once,inc),once)
        with self.assertRaisesRegex(ValueError,'third include seam'):include_once(once+inc,inc)
        with self.assertRaisesRegex(ValueError,'third private seam'):replace_stage('a','b','c','third private seam')
    def test_original_abi_gate(self):
        self.assertEqual(verify_abi({P:[0x4e800020]},P,[]),1)
        # stw r9,0(r1) observes an unmodified incoming timing register.
        with self.assertRaisesRegex(ValueError,'third ABI proof'):
            verify_abi({P:[0x91210000,0x4e800020]},P,[])
        with self.assertRaisesRegex(ValueError,'third ABI proof'):
            verify_abi({P:[0,0x4e800020]},P,[])
    def test_refusals(self):
        for bad in (L,L+SI,L.replace(SI,''),L+'    '+CALL+'false);\n'):
            with self.assertRaises(ValueError):hook(bad,P,W,'frontier')
        with self.assertRaises(ValueError):hook(L+'    '+CALL+'true);\n',P,W,'body')
if __name__=='__main__':unittest.main()
