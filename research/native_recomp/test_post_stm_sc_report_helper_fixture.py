#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_helper_fixture import merge,GUARD
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Fixture(unittest.TestCase):
    def test_merge(self):
        root=0x80001000;dst=0x80002000;words=(0x60000000,)*12+(bl(root+48,dst),)
        old={root:(words[0],GUARD)}
        got=merge(old,root,words,dst,0x60000000)
        self.assertEqual(got[root],words+(GUARD,));self.assertEqual(got[dst],(0x60000000,GUARD))
        for bad in ({**old,dst:(GUARD,)},{root:(words[0],0)}):
            with self.assertRaises(ValueError):merge(bad,root,words,dst,0)
if __name__=='__main__':unittest.main(verbosity=2)
