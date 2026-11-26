import unittest
from prepare_v1152_held_epilogue import patch_label,render,NEW,ACK
from prepare_v922_irq_return import patch_label as ep
from prepare_v939_second_vector import patch_label as vector
from prepare_v975_second_time import shared_label
from prepare_v667_si_dispatch import DISABLE,RESTORE
from prepare_v1097_after_alarm import SI
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
class HeldEpilogueHooks(unittest.TestCase):
    def test_original_hooks(self):
        for vector_mode,prior in ((False,ep),(True,vector)):
            body=prior(L+T+SI,H,W)
            out=patch_label(body,H,W,vector_mode)
            self.assertEqual(out.count(T),1)
            self.assertEqual(out.count('v958::before(ctx,'),1)
            self.assertIn(f'if({NEW}) undercover::wii::v958::before({A},false);',out)
            self.assertIn('else undercover::wii::v922::',out)
            for bad in (body.replace(T,T+T),body.replace(SI,''),body.replace('v922::','bad::'),
                        body+f'    undercover::wii::v958::before({A},false);\n',out):
                with self.assertRaises(ValueError):patch_label(bad,H,W,vector_mode)
    def test_shared_hooks(self):
        for root in (DISABLE,RESTORE):
            body=ep(L+T+SI,H,W)
            shared=shared_label(body,H,W,root,False)
            self.assertEqual(patch_label(shared,H,W,False,True),shared)
            for bad in (body,shared.replace('false);','true);'),shared.replace(f'if(!{ACK}) ',''),
                        shared+f'    undercover::wii::v922::before({A});\n'):
                with self.assertRaises(ValueError):patch_label(bad,H,W,False,True)
    def test_metadata(self):
        h=render()
        self.assertIn('epilogue=v922::expected;',h)
        self.assertIn('vector=v922::second_expected;',h)
        self.assertIn('image=v663::expected.vector;',h)
if __name__=='__main__':unittest.main()
