#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from apply_native_ios_mmio_v418 import PAIRS,HEADERS,rewrite,apply
from apply_hollywood_mmio_v62 import OLD,NEW
SOURCE='\n'.join(old for old,_ in PAIRS)
class Tests(unittest.TestCase):
    def test_reversible_idempotent(self):
        out=rewrite(SOURCE)
        self.assertEqual(rewrite(out),out)
        for old,new in reversed(PAIRS):out=out.replace(new,old,1)
        self.assertEqual(out,SOURCE)
    def test_bad_geometry(self):
        for old,_ in PAIRS:
            for bad in (SOURCE.replace(old,'missing',1),SOURCE+'\n'+old):
                with self.assertRaises(ValueError):rewrite(bad)
        with self.assertRaises(ValueError):rewrite(SOURCE.replace(*PAIRS[0]))
    def test_install_atomic_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ctx=root/'nWiiRuntime/include/runtime/cpu_context.h';mmio=root/'nWiiRuntime/src/core/os_hle_stubs.cpp';dest=root/'nWiiRuntime/include/undercover'
            ctx.parent.mkdir(parents=True);mmio.parent.mkdir(parents=True)
            ctx.write_text(OLD);mmio.write_text(SOURCE)
            host=Path(__file__).parent
            dest.mkdir();bad=dest/HEADERS[0];bad.write_text('conflict')
            with self.assertRaises(ValueError):apply(root,host)
            self.assertEqual(ctx.read_text(),OLD);self.assertEqual(mmio.read_text(),SOURCE)
            bad.unlink();apply(root,host)
            self.assertEqual(ctx.read_text(),NEW);self.assertEqual(mmio.read_text(),rewrite(SOURCE))
            self.assertTrue(all((dest/n).read_bytes()==(host/n).read_bytes() for n in HEADERS))
            apply(root,host)
if __name__=='__main__':unittest.main()
