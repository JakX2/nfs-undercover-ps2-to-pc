#!/usr/bin/env python3
import tempfile
from pathlib import Path
import unittest
from apply_dol_loader_v431 import FILE,DEST,HEADER,START,NEXT,NEW,blob,rewrite,apply
SOURCE=HEADER+'\n'+START+'\n    return false;\n}\n\n'+NEXT+'const std::string& path, uint32_t base, uint32_t bss){return false;}\n'
class Tests(unittest.TestCase):
    def test_exact_seam(self):
        out=rewrite(SOURCE,blob(SOURCE));self.assertIn(NEW,out);self.assertEqual(rewrite(out),out)
        self.assertTrue(out.endswith(SOURCE[SOURCE.index(NEXT):]));self.assertNotIn('    return false;\n}',out)
        for bad in (SOURCE+'\n',SOURCE.replace(START,'missing'),SOURCE+SOURCE):
            with self.assertRaises(ValueError):rewrite(bad,blob(SOURCE))
        with self.assertRaises(ValueError):rewrite(out.replace(NEW,NEW+NEW))
    def test_install(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);src=root/FILE;dest=root/DEST
            src.parent.mkdir(parents=True);dest.parent.parent.mkdir(parents=True);src.write_text(SOURCE)
            with self.assertRaises(ValueError):apply(root)
            self.assertFalse(dest.exists());self.assertEqual(src.read_text(),SOURCE)
            self.assertTrue(apply(root,blob(SOURCE)));self.assertFalse(apply(root,blob(SOURCE)))
            self.assertIn(NEW,src.read_text());dest.write_text('broken')
            with self.assertRaises(ValueError):apply(root,blob(SOURCE))
if __name__=='__main__':unittest.main()
