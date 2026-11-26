#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_dependency_fixture import merge,GUARD
class Fixture(unittest.TestCase):
    def test_merge(self):
        helper=0x80001000;root=0x80002000;caller=helper+52
        ws=(0x60000000,)*32+(0x4e800020,)
        old={helper:(0x60000000,)*13+(GUARD,),root:(ws[0],GUARD)}
        fields=(root,caller,0x60000000)
        got=merge(old,helper,fields,ws)
        self.assertEqual(got[helper],old[helper]);self.assertEqual(got[root],ws)
        for bad in ({**old,root:(ws[0],0)},{**old,helper:(0x60000000,)*12+(GUARD,)}):
            with self.assertRaises(ValueError):merge(bad,helper,fields,ws)
if __name__=='__main__':unittest.main(verbosity=2)
