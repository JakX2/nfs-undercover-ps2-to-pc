import tempfile
import unittest
from pathlib import Path
from apply_cache_order_v456 import CONTEXT,EMITTER,CTX_OLD,CTX_NEW,EMIT_OLD,EMIT_NEW,rewrite,apply
class Tests(unittest.TestCase):
    def test_roundtrip(self):
        c,e,changed=rewrite(CTX_OLD,EMIT_OLD)
        self.assertEqual((c,e,changed),(CTX_NEW,EMIT_NEW,True))
        self.assertEqual(rewrite(c,e),(c,e,False))
    def test_reject(self):
        for c,e in ((CTX_NEW,EMIT_OLD),(CTX_OLD,EMIT_NEW),(CTX_OLD*2,EMIT_OLD),(CTX_OLD,EMIT_OLD*2),
                    ('guest_store_count\n'+CTX_OLD,EMIT_OLD),('',EMIT_OLD),(CTX_OLD,'')):
            with self.assertRaises(ValueError):rewrite(c,e)
    def test_install(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);cp,ep=root/CONTEXT,root/EMITTER
            cp.parent.mkdir(parents=True);ep.parent.mkdir(parents=True)
            cp.write_text(CTX_OLD);ep.write_text(EMIT_OLD)
            self.assertTrue(apply(root));self.assertFalse(apply(root))
            ep.write_text(EMIT_OLD)
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(cp.read_text(),CTX_NEW);self.assertEqual(ep.read_text(),EMIT_OLD)
if __name__=='__main__':unittest.main()
