#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_decision import merge,ROOT,RESTORE,GUARD
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Fixture(unittest.TestCase):
    def test_merge(self):
        start=ROOT+20
        old={ROOT:(0x60000000,)*5+(GUARD,),ROOT-0x100:(0x4e800020,)}
        rows={start+4*i:0x60000000 for i in (0,1,2,3,5,6,7,8)}
        calls={start+12:RESTORE,start+32:RESTORE}
        rows.update({pc:bl(pc,dst) for pc,dst in calls.items()})
        got=merge(old,rows,start,calls)
        self.assertEqual(got[ROOT][:5],old[ROOT][:5])
        self.assertEqual(got[ROOT][9],GUARD)
        self.assertEqual(got[ROOT][-1],GUARD)
        self.assertEqual(got[ROOT-0x100],old[ROOT-0x100])
        for pc,w in rows.items():self.assertEqual(got[ROOT][(pc-ROOT)//4],w)
        for bad in ({**rows,start+16:0x60000000},{**rows,start+12:0x60000000}):
            with self.assertRaises(ValueError):merge(old,bad,start,calls)
        with self.assertRaises(ValueError):merge({ROOT:old[ROOT][:-1]},rows,start,calls)
if __name__=='__main__':unittest.main(verbosity=2)
