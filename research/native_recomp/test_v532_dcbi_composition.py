import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from apply_data_cache_invalidate_v532 import CONTEXT,EMITTER,ORDER_CTX,ORDER_EMIT,OLD_CTX,NEW_CTX,EMIT_NEW,rewrite,apply
class Tests(unittest.TestCase):
    def test_rewrite(self):
        c=OLD_CTX+'\n'+ORDER_CTX;e=ORDER_EMIT
        nc,ne,changed=rewrite(c,e)
        self.assertTrue(changed);self.assertEqual(nc,NEW_CTX+'\n'+ORDER_CTX);self.assertEqual(ne,EMIT_NEW)
        self.assertEqual(rewrite(nc,ne),(nc,ne,False))
        self.assertEqual(ne.count('xo == 470'),1)
        for a,b in ((OLD_CTX,e),(nc,e),(c,ne),(c+OLD_CTX,e),(c,e+e),(c,'ctx.guest_dcbi('+e)):
            with self.assertRaises(ValueError):rewrite(a,b)
    def test_install(self):
        with TemporaryDirectory() as td:
            root=Path(td);cp=root/CONTEXT;ep=root/EMITTER
            cp.parent.mkdir(parents=True);ep.parent.mkdir(parents=True)
            cp.write_text(OLD_CTX+'\n'+ORDER_CTX);ep.write_text(ORDER_EMIT)
            self.assertTrue(apply(root));self.assertFalse(apply(root))
            ep.write_text(ORDER_EMIT);before=cp.read_text()
            with self.assertRaises(ValueError):apply(root)
            self.assertEqual(cp.read_text(),before);self.assertEqual(ep.read_text(),ORDER_EMIT)
if __name__=='__main__':unittest.main()
