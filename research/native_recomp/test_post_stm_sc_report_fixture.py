#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_fixture import merge,REPORT,GUARD
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Fixture(unittest.TestCase):
    def test_merge(self):
        dst=REPORT+0x1000;site=REPORT+12
        rows={REPORT:0x60000000,REPORT+4:0x48000008,REPORT+8:0x60000000,site:bl(site,dst)}
        path=(REPORT,REPORT+4,site)
        old={REPORT:(rows[REPORT],GUARD)}
        got=merge(old,rows,path,dst,0x60000000)
        self.assertEqual(got[REPORT],(rows[REPORT],rows[REPORT+4],GUARD,rows[site],GUARD))
        self.assertEqual(got[dst],(0x60000000,GUARD))
        for bad in ({**old,dst:(GUARD,)},{REPORT:(rows[REPORT],0)}):
            with self.assertRaises(ValueError):merge(bad,rows,path,dst,0)
if __name__=='__main__':unittest.main(verbosity=2)
