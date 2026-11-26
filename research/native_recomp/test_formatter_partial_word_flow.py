import unittest
from audit_formatter_partial_word_flow import first_use,role
def d(op,rt,ra,imm=0):return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffff)
def x(xo,rt,ra,rb):return (31<<26)|(rt<<21)|(ra<<16)|(rb<<11)|(xo<<1)
class Tests(unittest.TestCase):
    def test_skip(self):
        self.assertEqual(first_use((d(14,7,0,1),d(36,3,1)),3,0xffff0000),(2,'store','read',0,0))
    def test_kill(self):
        self.assertEqual(first_use((d(14,3,0,1),),3,0xffff0000),(1,'arithmetic','killed',1,1))
    def test_address(self):
        self.assertEqual(first_use((d(32,7,3),),3,0xffff0000),(1,'load_address','read',0,0))
        self.assertEqual(first_use((x(23,7,0,3),),3,0xffff0000),(1,'load_address','read',0,0))
    def test_mask(self):
        self.assertEqual(first_use((d(29,3,3,0xff00),),3,0xffff0000),(1,'and_immediate','read',1,1))
    def test_compare(self):
        self.assertEqual(first_use((d(11,0,3),),3,0xffff0000),(1,'compare','read',0,0))
    def test_control(self):
        self.assertEqual(first_use((0x4e800420,),3,0xffff0000),(1,'control','unknown',0,0))
    def test_unknown(self):
        self.assertEqual(first_use((0,),3,0xffff0000),(1,'unsupported','unknown',0,0))
if __name__=='__main__':unittest.main(verbosity=2)
