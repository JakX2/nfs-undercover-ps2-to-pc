import unittest
from prepare_v1048_third_alarm import hook,SI
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
    def test_refusals(self):
        for bad in (L+SI,L.replace(SI,''),L+'    '+B+'false);\n    '+B+'true);\n',
                    L+'    if(other()) '+B+'false);\n'):
            with self.assertRaises(ValueError):hook(bad,P,W)
if __name__=='__main__':unittest.main()
