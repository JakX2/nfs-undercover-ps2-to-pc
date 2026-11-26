import unittest
from prepare_v1161_held_dispatch import patch_label,render,DISPATCH_ACTIVE
from prepare_v951_second_dispatch import patch_label as prior
from prepare_v922_irq_return import patch_label as ep
from prepare_v975_second_time import shared_label
from prepare_v1097_after_alarm import patch_label as post
from prepare_v667_si_dispatch import DISPATCH,SCHED,TIME,DISABLE,RESTORE
from prepare_v1097_after_alarm import SI
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
class HeldDispatchHooks(unittest.TestCase):
    def test_unshared(self):
        for root in (DISPATCH,SCHED):
            for guard in (False,True):
                body=prior(L+T+SI,H,W,root,guard)
                out=patch_label(body,H,W,root,guard)
                self.assertIn(f'if({DISPATCH_ACTIVE}) undercover::wii::v958::before({A},{str(guard).lower()});',out)
                self.assertEqual(out.count(T),1);self.assertEqual(out.count(SI),1)
                self.assertIn('else undercover::wii::v922::second_dispatch_before',out)
                for bad in (body.replace(T,T+T),body.replace(SI,''),body.replace('v922::','bad::'),out):
                    with self.assertRaises(ValueError):patch_label(bad,H,W,root,guard)
    def test_shared(self):
        for root in (DISABLE,RESTORE,TIME):
            if root==TIME:
                body=prior(L+T+SI+f'    undercover::wii::v709::before({A},2u);\n',H,W,root,False)
            else:body=ep(L+T+SI,H,W)
            body=post(shared_label(body,H,W,root,False),H,W)
            self.assertEqual(patch_label(body,H,W,root,False),body)
            for bad in (body.replace('v922::','bad::'),body.replace('v958::before','wrong::before'),body.replace(SI,''),body+T):
                with self.assertRaises(ValueError):patch_label(bad,H,W,root,False)
            with self.assertRaises(ValueError):patch_label(body,H,W,root,True)
    def test_metadata(self):
        self.assertIn('expected=v667::expected;',render())
if __name__=='__main__':unittest.main()
