import unittest,subprocess
from tempfile import TemporaryDirectory
from pathlib import Path
from prepare_v1289_wake_fixture import WAKE,DISABLE,RESTORE,SELECT,BLR,EDGES,shape,merge,render
NOP=0x60000000
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
def fixture():
    ws=[NOP]*(0xf4//4);ws[-1]=BLR
    for a,b in EDGES:ws[(a-WAKE)//4]=bl(a,b)
    n={WAKE:tuple(ws),DISABLE:(NOP,BLR)}
    g={SELECT:(NOP,),RESTORE:(NOP,)}
    b={WAKE:(NOP,BLR),DISABLE:n[DISABLE],SELECT:(NOP,NOP,BLR),RESTORE:(NOP,BLR)}
    e=tuple((dst,pc+4,ws[(pc-WAKE)//4],NOP) for pc,dst in EDGES)
    return b,n,g,e
class WakeGeometry(unittest.TestCase):
    def test_shape(self):
        _,n,_,_=fixture()
        self.assertEqual(shape(n[WAKE]),EDGES)
        for i,w in ((0,0x44000002),(1,0x48000001),(6,NOP),(7,0x48001000),(60,NOP)):
            ws=list(n[WAKE]);ws[i]=w
            with self.assertRaises(ValueError):shape(ws)
    def test_merge(self):
        b,n,g,_=fixture();original=b.copy();out=merge(b,n,g)
        self.assertEqual(b,original);self.assertEqual(out[WAKE],n[WAKE])
        self.assertEqual({k:v for k,v in out.items() if k!=WAKE},{k:v for k,v in b.items() if k!=WAKE})
        for root in (WAKE,DISABLE,SELECT,RESTORE):
            bad={**b,root:(0,BLR)}
            with self.assertRaises(ValueError):merge(bad,n,g)
    def test_header(self):
        _,n,g,e=fixture()
        with TemporaryDirectory() as td:
            d=Path(td);(d/'wake.h').write_text(render((n,g,e)))
            (d/'main.cpp').write_text('#include "wake.h"\nstatic_assert(v1289::expected(1,2).thread==2);\n'
                'static_assert(v1289::words.size()==65);\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(Path(__file__).resolve().parent),
                '-fsyntax-only',str(d/'main.cpp')],check=True)
if __name__=='__main__':unittest.main()
