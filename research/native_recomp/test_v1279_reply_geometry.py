import unittest,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from prepare_v1279_reply_geometry import REPLY,READ,WRITE,CACHE,WAKE,WAKE_LR,BLR,shape,render
NOP=0x60000000
def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
def synthetic():
    body=[NOP]*(0x258//4);body[-1]=BLR
    for pc,dst in ((0x805190e4,READ),(0x805190f8,READ),(0x80519108,WRITE),
                   (REPLY+0x60,CACHE),(WAKE_LR-4,WAKE)):
        body[(pc-REPLY)//4]=bl(pc,dst)
    # synthetic loop and invalidation, not original cache instructions
    cache=[(31<<26)|(3<<16)|(4<<11)|(470<<1),BLR]
    return body,cache
class Geometry(unittest.TestCase):
    def test_shape(self):
        b,c=synthetic();edges,guards,dcbi=shape(b,c)
        self.assertEqual(len(edges),5);self.assertEqual(guards,(WAKE_LR-4,))
        self.assertEqual(dcbi,(CACHE,))
    def test_refusals(self):
        for lane in range(8):
            b,c=synthetic()
            if lane==0:b.pop()
            if lane==1:b[0]=bl(REPLY,REPLY-0x40)
            if lane==2:b[0]=0x48000003
            if lane==3:b[(WAKE_LR-4-REPLY)//4]=NOP
            if lane==4:b[0]=bl(REPLY,WAKE)
            if lane==5:c[0]=NOP
            if lane==6:c[0]=0x44000002
            if lane==7:c[0]=bl(CACHE,READ)
            with self.assertRaises(ValueError):shape(b,c)
    def test_header(self):
        b,c=synthetic();edges,guards,dcbi=shape(b,c)
        rows=tuple((dst,site+4,b[(site-REPLY)//4],NOP) for site,dst in edges)
        p=({REPLY:tuple(b),CACHE:tuple(c)},{WAKE:(NOP,)},rows,guards,dcbi)
        text=render(p);self.assertEqual(text,render(p))
        with TemporaryDirectory() as td:
            d=Path(td);(d/'reply.h').write_text(text)
            (d/'main.cpp').write_text('#include "reply.h"\nstatic_assert(v1279::edges.size()==5);\n'
                'static_assert(v1279::dcbi_sites.size()==1);\nstatic_assert(v1279::guard_sites.size()==1);\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',
                '-I'+str(Path(__file__).resolve().parent),'-fsyntax-only',str(d/'main.cpp')],check=True)
if __name__=='__main__':unittest.main()
