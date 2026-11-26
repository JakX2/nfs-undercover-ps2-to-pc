import unittest
from prepare_v1097_after_alarm import ACTIVE,SI
from prepare_v1134_postalarm_return import patch_return_label
from prepare_v1141_postalarm_handler import patch_handler,render
from prepare_v958_second_ack import patch_label as second
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
LEG=f'    undercover::wii::v672::before({A},0u,0u);\n'

class HeldHandlerHooks(unittest.TestCase):
    def test_reuse(self):
        body=L+f'    undercover::wii::v850::dispatch_resume({A});\n'+T+SI+f'    undercover::wii::v850::handler_resume({A});\n'+LEG
        prior=patch_return_label(body,H,W,True)
        self.assertEqual(patch_handler(prior,H,W,0,0,H),prior)
        for bad in (prior.replace('postalarm_dispatch_resume','bad_resume'),prior+LEG,
                    prior.replace('0u,0u);','1u,1u);')):
            with self.assertRaises(ValueError):patch_handler(bad,H,W,0,0,H)
    def test_old_owner(self):
        body=L+T+SI+LEG
        for old in (body,second(body,H,W,'v672',True),second(body,H,W,'v672',False)):
            new=patch_handler(old,H,W,0,0,H-4)
            self.assertEqual(new.count(T),1)
            self.assertIn(A+',false);',new)
            self.assertIn(A+',0u,0u);',new)
            self.assertEqual(patch_handler(new,H,W,0,0,H-4),new)
    def test_refusals(self):
        base=L+T+SI+LEG
        for bad in (base+LEG,base.replace(SI,''),base.replace(T,T+T),
                    base.replace('0u,0u);','1u,1u);'),base.replace(LEG,''),
                    base+f'    undercover::wii::v850::dispatch_resume({A});\n',
                    base+f'    if({ACTIVE}) unrelated();\n'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):patch_handler(bad,H,W,0,0,H-4)
    def test_metadata(self):
        rows={H:(W,0,0),H+4:(0x80830038,0,0)}
        text=render(rows,H+4,H+8,(H,[W]*14,(H+100,H+104,H+108,H+112),20,H+64))
        self.assertIn('std::array<HandlerSuffixLabel,2> rows',text)
        self.assertIn('rd=0x80004004u,wr=0x80004008u;',text)
        self.assertIn('HandlerIndexBranchExpectation index',text)

if __name__=='__main__':unittest.main()
