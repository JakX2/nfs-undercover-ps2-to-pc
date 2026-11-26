import unittest
from benchmark_formatter_plan_cache import compare
from private_plan_cache import memoized_plan

class Tests(unittest.TestCase):
    def test_equal(self):
        calls=[]
        @memoized_plan
        def child(d,e):
            calls.append(1)
            return [d,e]
        def derive(d,e,second=False):
            return child(d,e),child(d,e)
        times=iter((0,10000000,12000000))
        self.assertEqual(compare(b'd',b'e',derive,lambda:next(times)),(10,2))
        self.assertEqual(len(calls),3)
    def test_mismatch(self):
        seq=iter((1,2))
        with self.assertRaisesRegex(ValueError,'cache plan mismatch'):
            compare(b'd',b'e',lambda *a,**kw:next(seq))
    def test_clock(self):
        seq=iter((2,1,3))
        with self.assertRaisesRegex(ValueError,'clock'):
            compare(b'd',b'e',lambda *a,**kw:1,lambda:next(seq))
if __name__=='__main__':unittest.main(verbosity=2)
