import unittest,subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from prepare_v1299_reply_return import IPC,REPLY,READ,WRITE,BLR,labels,render,verify_hooks,verify_resume
NOP=0x60000000
def plan():
    return ({IPC:(NOP,BLR),REPLY:(NOP,BLR),READ:(BLR,),WRITE:(BLR,)},((WRITE,REPLY+4,0x48000001,BLR),))
def code(pc,owner,w):
    hook='v1266_before' if owner==IPC else 'v1281_before'
    return f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n    {hook}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
class Tests(unittest.TestCase):
    def test_hook_identity(self):
        expected=labels(plan());s=[code(pc,a,w) for pc,(a,w) in expected.items()]
        verify_hooks(s,expected)
        for bad in (s[1:],s+s[:1],[x.replace('v1281_before','v1266_before') for x in s],
                    [x.replace('++ctx.inst_count;', '++ctx.inst_count;\n    extra(ctx);') for x in s]):
            with self.assertRaises(ValueError):verify_hooks(bad,expected)
    def test_resume(self):
        rows=((REPLY+4,REPLY),(IPC+4,IPC))
        s=''.join(f' case 0x{pc:X}: func_{a:08X}(ctx); break;\n' for pc,a in rows)
        verify_resume(s,rows)
        for bad in (s+s,s.replace(f'func_{REPLY:08X}',f'func_{IPC:08X}'),s.replace('break;','return;')):
            with self.assertRaises(ValueError):verify_resume(bad,rows)
    def test_ownership(self):
        with self.assertRaises(ValueError):labels(({REPLY:(NOP,BLR),REPLY+4:(BLR,)},()))
    def test_header(self):
        with TemporaryDirectory() as td:
            d=Path(td);(d/'return.h').write_text(render(plan()))
            (d/'main.cpp').write_text('#include "return.h"\nstatic_assert(v1299::words.size()==6);\n'
                'static_assert(v1299::expected(4).counter==4);\n')
            subprocess.run(['g++','-std=c++20','-Wall','-Wextra','-Werror','-I'+str(Path(__file__).resolve().parent),
                '-fsyntax-only',str(d/'main.cpp')],check=True)
if __name__=='__main__':unittest.main()
