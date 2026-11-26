import unittest,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from prepare_v1270_ipc_epilogue import merge_blocks,analyzer,render,scope,DISPATCH,DISPATCH_RETURN,L,SELECT,E,S,DISABLE,RESTORE,BLR,ANALYZE_ROOT,READ,SCANNER
class Merge(unittest.TestCase):
    def setup(self):
        cut=(DISPATCH_RETURN-DISPATCH)//4
        prefix=(0x60000000,)*cut
        old=prefix+(BLR,)*(169-cut)
        g=({DISPATCH:old},)
        code=(0x48000001,0x48000001,0x60000000,0x48000001)
        added={L:(0x60000000,)*53+(0x4c000064,),E:(BLR,),S:(BLR,),DISABLE:(BLR,),RESTORE:(BLR,)}
        blocks={DISPATCH:prefix+(code[0],)+(BLR,)*(168-cut),L:(added[L][0],BLR),SELECT:(BLR,),DISABLE:(BLR,),RESTORE:(BLR,)}
        return blocks,g,added,DISPATCH_RETURN,code
    def test_exact_extension(self):
        b,g,a,j,c=self.setup();copy=b.copy();out=merge_blocks(b,g,a,j,c)
        i=(j-DISPATCH)//4
        self.assertEqual(b,copy)
        self.assertEqual(out[DISPATCH][:i],b[DISPATCH][:i])
        self.assertEqual(out[DISPATCH][i:i+4],c)
        self.assertEqual(out[DISPATCH][i+4:],b[DISPATCH][i+4:])
        self.assertEqual(out[L],a[L]);self.assertEqual(out[SELECT],b[SELECT])
    def test_refusals(self):
        for i in range(6):
            b,g,a,j,c=self.setup()
            if i==0:b[L]=(0,BLR)
            if i==1:del b[SELECT]
            if i==2:b[DISPATCH]=b[DISPATCH][:-1]
            if i==3:b[DISPATCH]=(0,)+b[DISPATCH][1:]
            if i==4:b[E]=(0,)
            if i==5:b[DISPATCH]=b[DISPATCH][:-1]+(0,)
            with self.assertRaises(ValueError):merge_blocks(b,g,a,j,c)
    def test_private_header(self):
        b,g,a,j,c=self.setup()
        p=(g,{}, {},a,j,c,30,255,-8,-4,DISABLE,RESTORE,SELECT,())
        text=render(p)
        self.assertIn('LiveEpilogueExpectation expected',text)
        self.assertIn('context,-8,-4,30u,255u};}',text)
        self.assertIn('Word{0x80522a88u,0x4c000064u}',text)
        self.assertEqual(text,render(p))
        # Compile the actual independently generated header against the
        # real public witness interface, not just a string comparison.
        with TemporaryDirectory() as td:
            d=Path(td)
            (d/'v1270_private_epilogue.h').write_text(text)
            (d/'test.cpp').write_text('#include "v1270_private_epilogue.h"\n'
                'static_assert(v1270::expected(7).context==7);\n'
                'static_assert(v1270::words.size()==62);\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror',
                '-I'+str(Path(__file__).resolve().parent),'-fsyntax-only',str(d/'test.cpp')],check=True)
        self.assertIn((L,216),scope(p,{SELECT:(BLR,)},{L:(a[L][0],)}))
    def test_ownership(self):
        s=ANALYZE_ROOT+'\n'+READ+'\n'+SCANNER
        spans=((DISPATCH,0x2a4),(L,216))
        out=analyzer(s,spans)
        self.assertIn('ipc_return_owner',out)
        self.assertIn('a<0x80522a8cu',out)
        self.assertEqual(analyzer(out,spans),out)
if __name__=='__main__':unittest.main()
