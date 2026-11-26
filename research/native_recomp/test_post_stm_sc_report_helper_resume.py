#!/usr/bin/env python3
import unittest
from prepare_post_stm_sc_report_helper_resume import resume,formatter_args
B=0x80001000;T=0x80002000;U=0x80003000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
class Resume(unittest.TestCase):
    def test_paths(self):
        ws=(0x9421ffe0,bl(B+4,T),0x2c030000,0x4182000c,0x387f0000,bl(B+20,U),
            0x80010024,0x7c0803a6,0x38210020,0x4e800020)
        regs=[('reg',r) for r in range(32)];regs[31]=('const',0x80005000)
        gp,path,site,dst,kind=resume(B,ws,B+8,regs,1)
        self.assertEqual((len(path),site,dst,kind,gp[3]),(4,B+20,U,1,regs[31]))
        self.assertEqual(resume(B,ws,B+8,regs,0)[2:],(B+24,0,2))
        with self.assertRaises(ValueError):resume(B,(*ws[:2],0x2c040000,*ws[3:]),B+8,regs,1)
    def test_formatter_identity(self):
        args=(('const',0x80004000),('const',0x80005000),('const',0x80006000),('stack',-120))
        self.assertEqual(formatter_args(args,0x80005000,0x80006000,('stack',-120)),0x80004000)
        for i,v in enumerate((('const',3),('const',0),('const',0),('stack',-116))):
            bad=list(args);bad[i]=v
            with self.assertRaises(ValueError):formatter_args(tuple(bad),0x80005000,0x80006000,('stack',-120))
if __name__=='__main__':unittest.main(verbosity=2)
