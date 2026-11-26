#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_version_fixture import merge,verify_tail,ROOT,VERSION,REPORT,GUARD
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Fixture(unittest.TestCase):
    def test_merge(self):
        start=ROOT+20;old={ROOT:(0x60000000,)*5+(GUARD,)}
        rows={start:0x60000000,start+4:bl(start+4,VERSION)}
        body=(0x60000000,0x60000000,0x48000000)
        fields=(start,VERSION,REPORT,0x60000000,0,0)
        got=merge(old,rows,body,fields)
        self.assertEqual(got[ROOT],old[ROOT][:-1]+(rows[start],rows[start+4],GUARD))
        self.assertEqual(got[VERSION],body);self.assertEqual(got[REPORT],(0x60000000,GUARD))
        for bad in ({**old,VERSION:body},{**old,REPORT:body},{ROOT:old[ROOT][:-1]}):
            with self.assertRaises(ValueError):merge(bad,rows,body,fields)
    def test_tail(self):
        pc=VERSION+8
        good=f'loc_{pc:X}: ;\n    ctx.pc = 0x{REPORT:X}; return;\n'
        verify_tail(good,pc,REPORT)
        for bad in (good.replace('return;','break;'),good.replace(f'{REPORT:X}',f'{REPORT+4:X}'),good+good):
            with self.assertRaises(ValueError):verify_tail(bad,pc,REPORT)
if __name__=='__main__':unittest.main(verbosity=2)
