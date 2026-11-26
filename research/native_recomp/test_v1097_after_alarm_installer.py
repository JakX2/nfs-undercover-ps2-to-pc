import unittest
from prepare_v1097_after_alarm import patch_label,ACTIVE,OLD_ACTIVE,OLD_THIRD,CALLBACK,OLD_SUPPRESS,NEW_SUPPRESS,SI,suffix_line
P=0x80004000;W=0x60000000
L=f'loc_{P:X}: ;\n    // 0x{P:08X}: {W:08X}\n    ++ctx.inst_count;\n'+SI
B=f'undercover::wii::v958::before(ctx,0x{P:08x}u,0x{W:08x}u,'
CURRENT='    '+B+'false);\n'
GUARD='    '+B+'true);\n'
LEGACY=f'undercover::wii::v786::before(ctx,0x{P:08x}u,0x{W:08x}u);'
def conditional(p):return '    if('+p+') '+CURRENT.lstrip()
class Hooks(unittest.TestCase):
    def test_exact_existing_shapes(self):
        for old,expected in (
            ('',conditional(ACTIVE)),
            (CURRENT,CURRENT),
            (GUARD,conditional(ACTIVE)+'    else '+GUARD.lstrip()),
            (conditional(CALLBACK),conditional(CALLBACK+'||'+ACTIVE)),
            (conditional(OLD_ACTIVE),conditional(OLD_ACTIVE+'||'+ACTIVE)),
            (conditional(OLD_ACTIVE+'||'+CALLBACK),conditional(OLD_ACTIVE+'||'+CALLBACK+'||'+ACTIVE)),
            (conditional(OLD_ACTIVE)+'    else '+GUARD.lstrip(),conditional(OLD_ACTIVE+'||'+ACTIVE)+'    else '+GUARD.lstrip())):
            with self.subTest(shape=old):
                self.assertEqual(patch_label(L+old,P,W),L+expected)
    def test_legacy_order(self):
        old=OLD_SUPPRESS+LEGACY+' }\n'
        got=patch_label(L+old+conditional(OLD_ACTIVE)+old,P,W)
        self.assertEqual(got,L+NEW_SUPPRESS+LEGACY+' }\n'+conditional(OLD_ACTIVE+'||'+ACTIVE)+NEW_SUPPRESS+LEGACY+' }\n')
        for extra in ('    '+LEGACY+'\n','    if(!'+CALLBACK+') '+LEGACY+'\n'):
            self.assertIn('    if(!'+ACTIVE+') { '+extra.strip()+' }\n',patch_label(L+CURRENT+extra,P,W))
    def test_refusals(self):
        for bad in (L+SI,L.replace(SI,''),L+CURRENT+CURRENT,L+conditional('untrusted()'),
                    L+conditional(OLD_ACTIVE)+'    unrelated();\n    else '+GUARD.lstrip(),
                    L+conditional(OLD_THIRD),L+conditional(ACTIVE),
                    L.replace(SI,CURRENT+SI),L.replace('++ctx.inst_count;',''),
                    L.replace('60000000','60000001')):
            with self.subTest(shape=bad):
                with self.assertRaises(ValueError):patch_label(bad,P,W)
    def test_metadata(self):
        rows={P+4:(0x4e800421,6,2),P:(W,0,0)}
        self.assertEqual(suffix_line('third_postalarm_suffix',rows),
            'inline constexpr std::array<HandlerSuffixLabel,2> third_postalarm_suffix{{HandlerSuffixLabel{0x80004000u,0x60000000u,0u,0u},HandlerSuffixLabel{0x80004004u,0x4e800421u,6u,2u}}};\n')
if __name__=='__main__':unittest.main()
