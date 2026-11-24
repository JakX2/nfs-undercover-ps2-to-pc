import unittest
from apply_native_stop_v463 import PAIRS,rewrite
class Tests(unittest.TestCase):
    def test_roundtrip(self):
        old='\n'.join(a for a,b,n in PAIRS for _ in range(n))
        new='\n'.join(b for a,b,n in PAIRS for _ in range(n))
        self.assertEqual(rewrite(old),new);self.assertEqual(rewrite(new),new)
        self.assertIn('\n    out << "        if (!ctx.is_running) break;\\n";',new)
        self.assertNotIn('\\n    out',new)
    def test_reject(self):
        old='\n'.join(a for a,b,n in PAIRS for _ in range(n))
        for a,b,n in PAIRS:
            for bad in (old.replace(a,b,1),old.replace(a,'',1),old+'\n'+a):
                with self.assertRaises(ValueError):rewrite(bad)
if __name__=='__main__':unittest.main()
