import unittest,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from prepare_v1292_nested_wake import WAKE,SELECT,GET,RESTORE,BLR,render,verify_hooks,expected_labels
NOP=0x60000000
def make():
    return ({WAKE:(NOP,BLR),SELECT:(NOP,BLR),GET:(BLR,),RESTORE:(BLR,)},
        (GET,SELECT+4,0x48000001,BLR),(RESTORE,WAKE+4,0x48000001,BLR),-8)
def code(pc,owner,w):
    name='v1289_before' if owner==WAKE else 'v1270_before'
    return f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n    {name}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
class Tests(unittest.TestCase):
    def test_hooks(self):
        labels=expected_labels(make())
        sources=[code(pc,a,w) for pc,(a,w) in labels.items()]
        verify_hooks(sources,labels)
        for bad in (sources[1:],sources+sources[:1],[s.replace('v1289_before','v1270_before') for s in sources]):
            with self.assertRaises(ValueError):verify_hooks(bad,labels)
    def test_header(self):
        with TemporaryDirectory() as td:
            d=Path(td);(d/'nested.h').write_text(render(make()))
            (d/'main.cpp').write_text('#include "nested.h"\nstatic_assert(v1292::words.size()==6);\n'
                'static_assert(v1292::expected(1,2).counter==2);\nstatic_assert(v1292::counter_disp==-8);\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(Path(__file__).resolve().parent),
                '-fsyntax-only',str(d/'main.cpp')],check=True)
if __name__=='__main__':unittest.main()
