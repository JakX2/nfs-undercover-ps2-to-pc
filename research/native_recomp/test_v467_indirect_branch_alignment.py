import unittest
from apply_indirect_branch_alignment_v467 import PAIRS,rewrite
class Tests(unittest.TestCase):
    def test_roundtrip(self):
        a='\n'.join(x for x,y,n in PAIRS for _ in range(n))
        b='\n'.join(y for x,y,n in PAIRS for _ in range(n))
        self.assertEqual(rewrite(a),b);self.assertEqual(rewrite(b),b)
    def test_reject(self):
        a='\n'.join(x for x,y,n in PAIRS for _ in range(n))
        for x,y,n in PAIRS:
            for bad in (a.replace(x,y,1),a.replace(x,'',1),a+'\n'+x):
                with self.assertRaises(ValueError):rewrite(bad)
if __name__=='__main__':unittest.main()
