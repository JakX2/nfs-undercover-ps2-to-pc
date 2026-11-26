import unittest
from prepare_v1146_postalarm_handler_return import patch_restore,patch_dispatch,render
from prepare_v919_handler_epilogue import patch_alias
from prepare_v920_handler_return import patch_label
from prepare_v1097_after_alarm import ACTIVE,SI
H=0x80004000;W=0x60000000
A=f'ctx,0x{H:08x}u,0x{W:08x}u'
L=f'loc_{H:X}: ;\n    // 0x{H:08X}: {W:08X}\n'
T='    ++ctx.inst_count;\n'
class HandlerReturnHooks(unittest.TestCase):
    def test_restore(self):
        for old in ('',f'    undercover::wii::v726::restore_before({A});\n'):
            body=patch_alias(L+T+old+SI,H,[W])
            new=patch_restore(body,H,W)
            self.assertIn(f'if(!{ACTIVE}) undercover::wii::v868::restore_before({A});',new)
            self.assertEqual(new.count(T),1)
            self.assertEqual(new.count('v958::before(ctx,'),1)
            for bad in (body.replace('v868::restore_before','other'),body+f'    undercover::wii::v868::restore_before({A});\n',
                        body.replace(T,T+T),body.replace(SI,'')):
                with self.assertRaises(ValueError):patch_restore(bad,H,W)
    def test_dispatch(self):
        old=patch_label(L+T+f'    undercover::wii::v726::resume({A});\n'+SI,H,W)
        new=patch_dispatch(old,H,W)
        self.assertLess(new.index('postalarm_handler_dispatch_resume'),new.index(T))
        self.assertLess(new.index(SI),new.index('v958::before(ctx,'))
        self.assertIn(f'if(!{ACTIVE}) undercover::wii::v868::dispatcher_resume({A});',new)
        self.assertEqual(new.count(T),1)
        for bad in (old.replace('v868::dispatch_resume','other'),old.replace('v868::dispatcher_resume','other'),
                    old.replace('v726::resume','other'),old+T,old.replace(SI,''),old.replace('0x60000000u','0x60000001u')):
            with self.assertRaises(ValueError):patch_dispatch(bad,H,W)
    def test_metadata(self):
        s=render(H,H+0x100,H+0x200,[W]*16,[W]*4,W)
        self.assertIn('HandlerReturnExpectation expected{0x80004000u,0x80004100u,0x80004200u',s)
if __name__=='__main__':unittest.main()
