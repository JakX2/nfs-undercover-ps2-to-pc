import struct
import tempfile
import unittest
from pathlib import Path
from prepare_v453_debug_leaf import DEBUG,SITES,VECTORS,NOP,BLR,classify,image,data_at,vector_geometry

def fixture(words,wrong=False,offsets=None):
    body=struct.pack('>'+str(len(words))+'I',*words)
    out=bytearray(image(body));base=min(SITES);code=bytearray(max(SITES)-base+4)
    for i,site in enumerate(SITES):
        dest=DEBUG+(4 if wrong and i==2 else 0)
        struct.pack_into('>I',code,site-base,0x48000001|((dest-site)&0x03fffffc))
    for h,v in ((0,len(out)),(0x48,base),(0x90,len(code))):struct.pack_into('>I',out,h+4,v)
    out.extend(code)
    table=struct.pack('>15I',*(offsets if offsets is not None else [0x100*i for i in range(1,16)]))
    for h,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,h,v)
    out.extend(table)
    return bytes(out)

class Tests(unittest.TestCase):
    def test_exact_leaf(self):
        for n in (1,2,32):
            words=[NOP]*(n-1)+[BLR];raw=fixture(words)
            kind,candidate,count=classify(raw,{DEBUG:4*n})
            self.assertEqual((kind,count),('leaf',n))
            self.assertEqual(candidate,image(struct.pack('>'+str(n)+'I',*words)))
    def test_nonleaf_never_substituted(self):
        for words,kind in (([0x38600001,BLR],'other'),([0x48000005,BLR],'linked'),([BLR,NOP],'other'),([NOP]*32+[BLR],'other')):
            self.assertEqual(classify(fixture(words),{DEBUG:4*len(words)}),(kind,None,len(words)))
        self.assertEqual(classify(fixture([BLR]),{}),('unbounded',None,0))
        with self.assertRaises(ValueError):classify(fixture([BLR],wrong=True),{DEBUG:4})
        with self.assertRaises(ValueError):classify(fixture([BLR]),{DEBUG:8})
    def test_vector_geometry(self):
        raw=fixture([BLR])
        self.assertEqual(vector_geometry(raw),(True,True))
        for offsets in ([0x100]*15,[0x101]+[0x100*i for i in range(2,16)],[0x3000]+[0x100*i for i in range(2,16)]):
            self.assertFalse(vector_geometry(fixture([BLR],offsets=offsets))[0])
        self.assertEqual(vector_geometry(fixture([BLR],offsets=[0x100*i for i in range(16,31)])),(True,False))
        with self.assertRaises(ValueError):data_at(raw,VECTORS,64)
if __name__=='__main__':unittest.main()
