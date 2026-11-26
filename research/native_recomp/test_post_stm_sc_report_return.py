#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_return import epilogue
def ins(op,rs,ra,n):return (op<<26)|(rs<<21)|(ra<<16)|(n&0xffff)
class Return(unittest.TestCase):
    def test_return(self):
        regs=[('reg',r) for r in range(32)];regs[1]=('stack',-128)
        slots={4:('lr',0)}
        ws=(ins(32,0,1,132),0x7c0803a6,ins(14,1,1,128),0x4e800020)
        self.assertEqual(epilogue(ws,128,regs,slots),(4,1,1))
        self.assertEqual(epilogue((ws[2],ins(32,0,1,4),ws[1],ws[3]),128,regs,slots),(4,1,1))
        for bad in ((ins(32,0,1,128),*ws[1:]),(ws[0],0x7c0903a6,*ws[2:]),
                    (*ws[:2],ins(14,1,1,124),ws[3]),ws[:-1],(*ws[:2],ws[3],ws[3])):
            with self.subTest(bad=bad),self.assertRaises(ValueError):epilogue(bad,128,regs,slots)
        regs[31]=('stack',-64);slots[-4]=('reg',31)
        restored=(ws[0],ins(32,31,1,124),*ws[1:])
        self.assertEqual(epilogue(restored,128,regs,slots),(5,2,1))
        for bad in (ws,(ws[0],ins(32,30,1,124),*ws[1:]),(ws[0],ins(32,31,1,120),*ws[1:])):
            with self.subTest(bad=bad),self.assertRaises(ValueError):epilogue(bad,128,regs,slots)
if __name__=='__main__':unittest.main(verbosity=2)
