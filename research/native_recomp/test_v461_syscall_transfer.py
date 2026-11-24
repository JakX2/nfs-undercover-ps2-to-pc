import tempfile
import unittest
from pathlib import Path
from apply_syscall_transfer_v461 import EMIT_OLD,EMIT_NEW,INTERP_OLD,INTERP_NEW,EMITTER,INTERPRETER,rewrite,apply
class Tests(unittest.TestCase):
    def test_rewrite(self):
        self.assertEqual(rewrite(EMIT_OLD,INTERP_OLD),(EMIT_NEW,INTERP_NEW,True))
        self.assertEqual(rewrite(EMIT_NEW,INTERP_NEW),(EMIT_NEW,INTERP_NEW,False))
    def test_reject(self):
        for e,i in ((EMIT_NEW,INTERP_OLD),(EMIT_OLD,INTERP_NEW),(EMIT_OLD*2,INTERP_OLD),
                    (EMIT_OLD,INTERP_OLD*2),('',INTERP_OLD),(EMIT_OLD,'')):
            with self.assertRaises(ValueError):rewrite(e,i)
    def test_install(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);ep,ip=root/EMITTER,root/INTERPRETER
            ep.parent.mkdir(parents=True);ip.parent.mkdir(parents=True)
            ep.write_text(EMIT_OLD);ip.write_text(INTERP_OLD)
            self.assertTrue(apply(root));self.assertFalse(apply(root))
            ip.write_text(INTERP_OLD)
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(ep.read_text(),EMIT_NEW);self.assertEqual(ip.read_text(),INTERP_OLD)
if __name__=='__main__':unittest.main()
