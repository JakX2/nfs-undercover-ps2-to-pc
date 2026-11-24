import tempfile
import unittest
from pathlib import Path
from apply_function_root_v443 import *
A=MIN_DECL+MIN_UPDATE+ROOT_OLD
E=DISPATCH_OLD
class Tests(unittest.TestCase):
    def test_identity_and_dispatch(self):
        a,e=rewrite(A,E)
        self.assertIn(ROOT_NEW,a);self.assertNotIn(MIN_DECL,a);self.assertNotIn(MIN_UPDATE,a)
        self.assertIn('first_addr',e);self.assertNotIn('func.start_address',e)
        self.assertEqual(rewrite(a,e),(a,e))
    def test_fail_closed(self):
        a,e=rewrite(A,E)
        for x,y in ((A+a,E),(A,E+e),(a,E),(A,e),(A.replace(MIN_UPDATE,''),E)):
            with self.assertRaises(ValueError):rewrite(x,y)
    def test_no_partial_file_write(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);a=root/ANALYZER;e=root/EMITTER
            a.parent.mkdir(parents=True);e.parent.mkdir(parents=True)
            a.write_text(A);e.write_text(E+E)
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(a.read_text(),A);self.assertEqual(e.read_text(),E+E)
            e.write_text(E);self.assertTrue(apply(root));self.assertFalse(apply(root))
if __name__=='__main__':unittest.main()
