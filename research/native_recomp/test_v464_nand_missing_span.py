import unittest
from repair_v464_nand_missing_span import restore_missing
from test_v414_nand_resumed_coverage import dol,BODY,A,NOP
from make_osinit_execparams_v28 import text_at
class Tests(unittest.TestCase):
    def test_missing_tail(self):
        owner=dol(BODY*3);pc=A+16;sizes={pc:16}
        for prefix in (b'',BODY[:4],NOP,BODY[:8],BODY[:4]+NOP):
            fixture=dol(BODY+prefix)
            w,candidate,present=restore_missing(owner,fixture,sizes,pc)
            self.assertEqual(w.length,16);self.assertEqual(present,len(prefix))
            self.assertEqual(text_at(candidate,pc,16),BODY)
            self.assertEqual(text_at(candidate,A,16),BODY)
    def test_reject(self):
        owner=dol(BODY*3);pc=A+16
        for fixture in (owner,dol(BODY+bytes.fromhex('12345678')),dol(BODY+NOP*4)):
            with self.assertRaises(ValueError):restore_missing(owner,fixture,{pc:16},pc)
        with self.assertRaises(ValueError):restore_missing(owner,dol(BODY),{pc:8196},pc)
if __name__=='__main__':unittest.main()
