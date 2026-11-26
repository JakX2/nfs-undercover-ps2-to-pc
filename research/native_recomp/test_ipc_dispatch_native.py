#!/usr/bin/env python3
"""Source-only helper opcode shape regressions."""
import unittest
from prepare_ipc_dispatch_native import helper_shape
N=0x60000000
RET=0x4e800020
ST=0x90830000
LD=0x80630000
STX=(31<<26)|(151<<1)
LDX=(31<<26)|(23<<1)
class Shape(unittest.TestCase):
    def test_exact(self):
        for w,wr in ((ST,True),(LD,False),(STX,True),(LDX,False)):
            self.assertEqual(helper_shape((N,w,RET),wr),1)
    def test_refusals(self):
        for words,wr in (((N,RET),True),((LD,RET),True),((ST,ST,RET),True),
                        ((ST,0x48000001,RET),True),((ST,0x44000002,RET),True),
                        ((ST,37<<26,RET),True),((ST,N),True),((N,)*16+(RET,),False)):
            with self.subTest(words=words),self.assertRaises(ValueError):helper_shape(words,wr)

class HookInstaller(unittest.TestCase):
    def fixture(self):
        from prepare_ipc_dispatch_native import SUBMIT
        s=SUBMIT;w=0x80020000;r=0x80030000
        start=s+0x100
        calls=[(start+4,w),(start+16,r),(start+24,w)]
        stop=calls[-1][0]+4
        def bl(pc,dst):return 0x48000001|((dst-pc)&0x03fffffc)
        edges=tuple((pc,dst,bl(pc,dst)) for pc,dst in calls)
        words={pc:(s,N) for pc in range(start,stop+4,4)}
        for pc,dst,word in edges:words[pc]=(s,word)
        words.update({w:(w,ST),w+4:(w,RET),r:(r,LD),r+4:(r,RET)})
        def label(pc,word,body='',prior=False):
            return (f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n    ++ctx.inst_count;\n'
                    +(f'    v1344_before(ctx,0x{pc:08x}u,0x{word:08x}u);\n' if prior else '')+body)
        body=''
        for pc in range(start,stop+4,4):
            edge=next((x for x in edges if x[0]==pc),None)
            call=(f'    ctx.pc = 0x{edge[1]:X}; func_{edge[1]:X}(ctx);\n'
                  f'    if (ctx.pc != 0x{pc+4:X}) return;\n') if edge else ''
            body+=label(pc,words[pc][1],call,True)
        source='#include "runtime/cpu_context.h"\n'+f'void func_{s:X}(CPUContext& ctx) {{\n'+body+'}\n'
        for target,word in ((w,ST),(r,LD)):
            source+=(f'void func_{target:X}(CPUContext& ctx) {{\n'
                     f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{target:X}) nwii::runtime::trace_call(0x{target:X}, ctx);\n'
                     +label(target,word)+label(target+4,RET,'    ctx.pc = ctx.lr; return;\n')+'}\n')
        main='\n'.join(f'case 0x{x:X}: func_{x:X}(ctx); break;' for x in (s,w,r))+'\n'
        p=(start,stop,words,edges,(0x80010000,80,16),(0x80010100,4),
           ((0x80010200,4),(0x80010204,4),(0x80010300,128),(0x80010400,128)))
        return source,main,p
    def run_install(self,src,main,p,accepted):
        import contextlib
        import io
        import tempfile
        from pathlib import Path
        from prepare_ipc_dispatch_native import install
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);shard=root/'output_0.cpp';shard.write_text(src)
            (root/'main_output.cpp').write_text(main)
            if accepted:
                with contextlib.redirect_stdout(io.StringIO()) as capture:install(root,p)
                self.assertIn('helper_labels=4 edges=3 returns=3',capture.getvalue())
                out=shard.read_text()
                self.assertEqual(out.count('    ipc_dispatch_before('),4)
                self.assertEqual(out.count('    ipc_dispatch_return('),3)
                for call,_,_ in p[3]:
                    self.assertIn(f'ipc_dispatch_return(ctx,0x{call+4:08x}u);\n    ++ctx.inst_count;',out)
                self.assertEqual(out.count('    v1344_before('),8)
                with self.assertRaises(ValueError):install(root,p)
                self.assertEqual(shard.read_text(),out)
            else:
                with self.assertRaises(ValueError):install(root,p)
                self.assertEqual(shard.read_text(),src)
    def test_install(self):
        self.run_install(*self.fixture(),True)
    def test_installer_refusals(self):
        src,main,p=self.fixture()
        call,helper,word=p[3][0];ret=call+4
        cases=[
            (src.replace(f'loc_{ret:X}: ;',f'loc_{ret:X}: ;\nloc_{ret:X}: ;'),main),
            (src.replace(f'    v1344_before(ctx,0x{p[0]:08x}u,0x{N:08x}u);\n',''),main),
            (src.replace(f'ctx.pc != 0x{ret:X}',f'ctx.pc != 0x{ret+4:X}'),main),
            (src.replace(f'// 0x{call:08X}: {word:08X}',f'// 0x{call:08X}: 00000000'),main),
            (src.replace(f'loc_{helper+4:X}: ;',f'loc_{helper+8:X}: ;'),main),
            (src,main.replace(f'case 0x{helper:X}:','case 0x1234:')),
        ]
        for i,(s,m) in enumerate(cases):
            with self.subTest(i=i):self.run_install(s,m,p,False)
    def test_render(self):
        from prepare_ipc_dispatch_native import render
        _,_,p=self.fixture();h=render(p)
        self.assertEqual(h.count('IpcDispatchWord{'),12)
        self.assertEqual(h.count('IpcDispatchEdge{'),3)
        self.assertEqual(h.count('AllocatorRange{'),6)

if __name__=='__main__':unittest.main(verbosity=2)
