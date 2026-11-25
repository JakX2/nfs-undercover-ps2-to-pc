import unittest
from prepare_v807_callback_prefix import patch_label,SI
from apply_si_roots_v669 import pairs,TEST_SPANS

class Prefix(unittest.TestCase):
    def test_scheduler_order(self):
        s='loc_80004000: ;\n    // 0x80004000: 60000000\n    ++ctx.inst_count;\n'
        h='    undercover::wii::v680::before(ctx,0x80004000u,0x60000000u);\n'
        for b in (s+SI,s+h+SI,s+SI+h):
            q=patch_label(b,0x80004000,0x60000000)
            self.assertGreater(q.index('v807::before'),q.index(SI))
            if h in b:self.assertIn('if(!undercover::wii::v807::active())',q)
        for b in (s,s+'    illegal();\n'+SI,s+h+SI+h):
            with self.assertRaises(ValueError):patch_label(b,0x80004000,0x60000000)
    def test_shared_alias(self):
        a=0x80009000
        self.assertEqual(pairs(TEST_SPANS,alias=a),pairs(TEST_SPANS,alias=a,callback_alias=a))
        self.assertNotEqual(pairs(TEST_SPANS),pairs(TEST_SPANS,callback_alias=a))
        with self.assertRaises(ValueError):pairs(TEST_SPANS,callback_alias=TEST_SPANS[0][0])
if __name__=='__main__':unittest.main()
