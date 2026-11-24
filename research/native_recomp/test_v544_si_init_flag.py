import unittest
import struct
import hashlib
from audit_v544_si_init_flag import classify,SI,SI_END,FIRST,LAST,TYPE,FLAG
def make(stores):
    words=[0x60000000]*((SI_END-SI)//4)
    for pc in range(FIRST,LAST+1,8):words[(pc-SI)//4]=0x48000001|((TYPE-pc)&0x03fffffc)
    words[-1]=0x4e800020
    for pc in stores:words[(pc-SI)//4]=0x90000000|(3<<21)|(13<<16)|(FLAG&0xffff)
    header=bytearray(256)
    for off,val in ((0,256),(0x48,SI),(0x90,len(words)*4)):struct.pack_into('>I',header,off,val)
    return bytes(header)+struct.pack('>'+'I'*len(words),*words)
class Tests(unittest.TestCase):
    def test_relations(self):
        for stores,wanted in (([SI+8],('before',1)),([FIRST+4],('between',1)),([LAST+4],('after',1)),([],('ambiguous',0)),([SI+8,LAST+4],('ambiguous',2))):
            data=make(stores)
            self.assertEqual(classify(data,hashlib.sha256(data).hexdigest()),wanted)
    def test_identity_and_branch(self):
        data=make([SI+8])
        with self.assertRaises(ValueError):classify(data)
        bad=bytearray(data);struct.pack_into('>I',bad,256+FIRST-SI,0x60000000)
        with self.assertRaises(ValueError):classify(bad,hashlib.sha256(bad).hexdigest())
if __name__=='__main__':unittest.main()
