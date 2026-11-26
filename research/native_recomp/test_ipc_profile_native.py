#!/usr/bin/env python3
"""Synthetic generated-C++ hook installer tests; no original binary data."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from prepare_ipc_profile_native import CALL, HELPER, SUBMIT, install, render

N=0x60000000
RET=0x4e800020
BL=0x48000001|((HELPER-CALL)&0x03fffffc)
RANGES=((0x80010000,4),(0x80010004,4),(0x80010100,128),(0x80010200,128))
PLAN=((N,RET),RANGES,(BL,N))

def label(pc,w,body=''):
    return f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {w:08X}\n    ++ctx.inst_count;\n'+body

def source():
    return ('#include "runtime/cpu_context.h"\n'
        f'void func_{HELPER:X}(CPUContext& ctx) {{\n'
        f'    if (nwii::runtime::g_trace_calls && ctx.pc == 0x{HELPER:X}) nwii::runtime::trace_call(0x{HELPER:X}, ctx);\n'
        +label(HELPER,N)+label(HELPER+4,RET,'    ctx.pc = ctx.lr; return;\n')+'}\n'
        f'void func_{SUBMIT:X}(CPUContext& ctx) {{\n'
        +label(CALL,BL,f'    ctx.pc = 0x{HELPER:X}; func_{HELPER:X}(ctx);\n'
                      f'    if (ctx.pc != 0x{CALL+4:X}) return;\n')
        +label(CALL+4,N)+'}\n')

def main_source():
    return '\n'.join(f'case 0x{x:X}: func_{x:X}(ctx); break;' for x in (HELPER,SUBMIT))+'\n'

class HookInstaller(unittest.TestCase):
    def run_install(self,src,main,accepted):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'output_0.cpp';p.write_text(src)
            (root/'main_output.cpp').write_text(main)
            if accepted:
                with contextlib.redirect_stdout(io.StringIO()) as capture:install(root,PLAN)
                self.assertIn('verified=1 labels=2 direct_edges=1 return_hooks=1',capture.getvalue())
                out=p.read_text()
                self.assertEqual(out.count('    ipc_profile_before('),2)
                self.assertEqual(out.count('    ipc_profile_return('),1)
                self.assertIn(f'ipc_profile_return(ctx,0x{CALL+4:08x}u);\n    ++ctx.inst_count;',out)
                self.assertNotIn('    v1344_before(',out)
                with self.assertRaises(ValueError):install(root,PLAN)
                self.assertEqual(p.read_text(),out)
            else:
                with self.assertRaises(ValueError):install(root,PLAN)
                self.assertEqual(p.read_text(),src)
    def test_exact(self):self.run_install(source(),main_source(),True)
    def test_refusals(self):
        s=source();m=main_source()
        cases=[
            (s.replace(f'loc_{HELPER+4:X}: ;','loc_ABC: ;'),m),
            (s.replace(f'0x{HELPER:08X}: {N:08X}',f'0x{HELPER:08X}: 00000000'),m),
            (s.replace('    ++ctx.inst_count;','    ++ctx.inst_count;\n    ++ctx.inst_count;',1),m),
            (s.replace('    if (nwii::runtime::g_trace_calls','    if (false'),m),
            (s.replace(f'ctx.pc != 0x{CALL+4:X}',f'ctx.pc != 0x{CALL+8:X}'),m),
            (s,m.replace(f'case 0x{HELPER:X}:', 'case 0xABC:')),
            (s.replace(f'loc_{CALL+4:X}: ;',f'loc_{CALL+4:X}: ;\nloc_{CALL+4:X}: ;'),m),
        ]
        for i,(src,main) in enumerate(cases):
            with self.subTest(i=i):self.run_install(src,main,False)
    def test_render(self):
        h=render(PLAN)
        self.assertIn('IpcProfileNativeWord,2>',h)
        self.assertEqual(h.count('IpcProfileNativeWord{'),2)
        self.assertEqual(h.count('AllocatorRange{'),4)
        self.assertIn(f'0x{CALL:08x}u,0x{BL:08x}u,0x{N:08x}u',h)
if __name__=='__main__':unittest.main(verbosity=2)
