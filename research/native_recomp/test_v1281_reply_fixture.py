import unittest,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from prepare_v1281_reply_fixture import REPLY,IPC_READ,IPC_WRITE,CACHE,WAKE,WAKE_LR,BLR,merge,scope,render,symbols
NOP=0x60000000
G=0x8051b070
EXIST=0x8051ad3c
def fixture():
    native={REPLY:(NOP,NOP,BLR),IPC_READ:(NOP,BLR),IPC_WRITE:(NOP,BLR),CACHE:(NOP,BLR)}
    guards={WAKE:(NOP,),G:(NOP,),EXIST:(NOP,)}
    blocks={REPLY:(NOP,BLR),IPC_READ:native[IPC_READ],IPC_WRITE:native[IPC_WRITE],WAKE:(NOP,BLR),EXIST:(NOP,NOP,BLR)}
    edges=((WAKE,WAKE_LR,0x48000001,NOP),)
    return blocks,native,guards,edges
class Tests(unittest.TestCase):
    def test_merge(self):
        b,n,g,_=fixture();original=b.copy();out=merge(b,n,g)
        self.assertEqual(original,b);self.assertEqual(out[REPLY],n[REPLY]);self.assertEqual(out[CACHE],n[CACHE])
        self.assertEqual(out[EXIST],b[EXIST]);self.assertEqual(out[G],(NOP,BLR));self.assertEqual(out[WAKE],b[WAKE])
        spans=scope([(REPLY,8),(IPC_READ,8),(IPC_WRITE,8),(WAKE,8)],{pc:len(ws)*4 for pc,ws in out.items()},n,g)
        self.assertIn((REPLY,12),spans);self.assertIn((EXIST,12),spans)
    def test_refusals(self):
        for lane in range(7):
            b,n,g,_=fixture()
            if lane==0:b[REPLY]=(0,BLR)
            if lane==1:b[IPC_READ]=(0,BLR)
            if lane==2:b[WAKE]=(NOP,NOP)
            if lane==3:b[CACHE]=(NOP,BLR)
            if lane==4:b[EXIST]=(0,BLR)
            if lane==5:b[REPLY+8]=(NOP,)
            if lane==6:b.update({0x80010000+4*i:(NOP,) for i in range(48)})
            with self.assertRaises(ValueError):merge(b,n,g)
    def test_symbols(self):
        self.assertEqual(symbols('Name,Location,Size\nfunc_80010000,80010000,4\n'),{0x80010000:4})
        for s in ('bad','Name,Location,Size\nfunc_80010000,80010000,3','Name,Location,Size\nfunc_80010000,80010000,4\nfunc_80010000,80010000,4'):
            with self.assertRaises(ValueError):symbols(s)
    def test_header(self):
        _,n,g,e=fixture();h=render((n,g,e))
        with TemporaryDirectory() as td:
            d=Path(td);(d/'reply.h').write_text(h)
            (d/'main.cpp').write_text('#include "reply.h"\nstatic_assert(v1281::expected(1,2).thread==2);\n'
                'static_assert(v1281::words.size()==12);\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(Path(__file__).resolve().parent),
                '-fsyntax-only',str(d/'main.cpp')],check=True)
if __name__=='__main__':unittest.main()
