import unittest
from prepare_v1048_third_alarm import hook,SI,verify_alarm_identity
from prepare_v789_alarm_suffix import patch_private
P=0x80004000;W=0x48000101
L=f'loc_{P:X}: ;\n    // 0x{P:08X}: {W:08X}\n    ++ctx.inst_count;\n'+SI
B=f'undercover::wii::v958::before(ctx,0x{P:08x}u,0x{W:08x}u,'
OLD=f'    undercover::wii::v786::before(ctx,0x{P:08x}u,0x{W:08x}u);\n'
class Hooks(unittest.TestCase):
    def test_shared(self):
        self.assertEqual(hook(L+'    '+B+'false);\n',P,W),L+'    '+B+'false);\n')
        for extra in ('','    '+B+'true);\n','    if(undercover::wii::v958::callback_active()) '+B+'false);\n'):
            got=hook(L+extra+OLD,P,W)
            self.assertEqual(got.count(SI),1)
            self.assertIn('third_alarm_active()',got)
            self.assertIn('if(!undercover::wii::v958::third_alarm_active()) '+OLD.lstrip(),got)
            self.assertLess(got.index(SI),got.index('v958::before'))
        self.assertIn('else '+B+'true);',hook(L+'    '+B+'true);\n',P,W))
    def test_composed_alarm_identity(self):
        base='#pragma once\nnamespace undercover::wii::v786 {\ninline constexpr unsigned marker=1;\n}\n'
        callback=(0x80006000,(0x60000000,0x4e800020),(0x80004000,0x80004004))
        composed=patch_private(base,*callback)
        verify_alarm_identity(composed,base,callback)
        for bad in (base,composed.replace('marker=1','marker=2'),
                    composed.replace('0x80006000u','0x80006004u'),
                    composed.replace('0x60000000u','0x60000001u'),
                    composed.replace('0x80004004u','0x80004008u'),
                    composed+'// unexpected\n'):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,'third alarm identity'):
                    verify_alarm_identity(bad,base,callback)
    def test_refusals(self):
        for bad in (L+SI,L.replace(SI,''),L+'    '+B+'false);\n    '+B+'true);\n',
                    L+'    if(other()) '+B+'false);\n'):
            with self.assertRaises(ValueError):hook(bad,P,W)
if __name__=='__main__':unittest.main()
