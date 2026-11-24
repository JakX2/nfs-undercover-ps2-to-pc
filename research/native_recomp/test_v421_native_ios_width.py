#!/usr/bin/env python3
import unittest
import tempfile
from pathlib import Path
from apply_native_ios_width_v421 import PAIRS,BIND,rewrite,apply
SOURCE='\n'.join(a for a,_ in PAIRS)+'\n(paddr >= 0x0D800000 && paddr < 0x0D810000);'
class Tests(unittest.TestCase):
    def test_reversible_idempotent(self):
        out=rewrite(SOURCE);self.assertEqual(rewrite(out),out)
        for a,b in reversed(PAIRS):out=out.replace(b,a,1)
        self.assertEqual(out,SOURCE)
    def test_refuses_ambiguous_and_partial(self):
        for a,b in PAIRS:
            for bad in (SOURCE.replace(a,'missing',1),SOURCE+'\n'+a,SOURCE.replace(a,b,1)):
                with self.assertRaises(ValueError):rewrite(bad)
        with self.assertRaises(ValueError):rewrite(SOURCE.replace('paddr >= 0x0D800000','missing'))
    def test_requires_active_seam(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ctx=root/'nWiiRuntime/include/runtime/cpu_context.h';stubs=root/'nWiiRuntime/src/core/os_hle_stubs.cpp';binding=root/'nWiiRuntime/include/undercover/wii_native_ios_binding.h'
            for p in (ctx,stubs,binding):p.parent.mkdir(parents=True,exist_ok=True)
            ctx.write_text(SOURCE);stubs.write_text('legacy');binding.write_text('static void check_cpu_access(')
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(ctx.read_text(),SOURCE)
            stubs.write_text(BIND+'::read32(addr)');apply(root);self.assertEqual(ctx.read_text(),rewrite(SOURCE));apply(root)
if __name__=='__main__':unittest.main()
