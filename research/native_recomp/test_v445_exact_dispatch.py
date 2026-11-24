import tempfile
import unittest
from pathlib import Path
from apply_exact_dispatch_v445 import FILE,PAIRS,rewrite,apply
SOURCE='\n'.join(a for a,b in PAIRS)*2
class Tests(unittest.TestCase):
    def test_rewrite(self):
        out=rewrite(SOURCE)
        for a,b in PAIRS:
            self.assertEqual(out.count(b),2);self.assertNotIn(a,out)
        self.assertEqual(rewrite(out),out)
    def test_reject(self):
        out=rewrite(SOURCE)
        for a,b in PAIRS:
            with self.assertRaises(ValueError):rewrite(SOURCE.replace(a,'',1))
            with self.assertRaises(ValueError):rewrite(SOURCE+a)
            with self.assertRaises(ValueError):rewrite(out.replace(b,a,1))
    def test_install(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);p=root/FILE;p.parent.mkdir(parents=True)
            p.write_text(SOURCE);self.assertTrue(apply(root));self.assertFalse(apply(root))
            p.write_text(SOURCE+SOURCE)
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(p.read_text(),SOURCE+SOURCE)
if __name__=='__main__':unittest.main()
