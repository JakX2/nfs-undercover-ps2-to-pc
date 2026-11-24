import unittest
from apply_arena_reset_v606 import CTX,STUB
from apply_irq_bootstrap_v475 import rewrite
class Tests(unittest.TestCase):
    def test_exact(self):
        for pairs in (CTX,STUB):
            src='\n'.join(a for a,b in pairs);out=rewrite(src,pairs)
            self.assertEqual(rewrite(out,pairs),out)
            for bad in (src+src,src.replace(pairs[-1][0],'')):
                with self.assertRaises(ValueError):rewrite(bad,pairs)
        self.assertTrue(any('true,true' in b for a,b in CTX))
        self.assertTrue(any('false,false' in b for a,b in CTX))
if __name__=='__main__':unittest.main()
