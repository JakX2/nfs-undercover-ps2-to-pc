import unittest
from private_plan_cache import memoized_plan,plan_cache_scope

class Tests(unittest.TestCase):
    def setUp(self):
        self.calls=0
        @memoized_plan
        def plan(d,e,*,details=False):
            self.calls+=1
            if d==b'bad':raise ValueError('bad')
            return {'rows':[d,e,details]}
        self.plan=plan
    def test_scoped(self):
        self.plan(b'd',b'e');self.plan(b'd',b'e')
        self.assertEqual(self.calls,2)
        with plan_cache_scope():
            r=self.plan(b'd',b'e');r['rows'].clear()
            self.assertEqual(self.plan(b'd',b'e')['rows'],[b'd',b'e',False])
            self.plan(b'd',b'e',details=True)
            with plan_cache_scope():self.plan(b'd',b'e')
            self.assertEqual(self.calls,4)
        self.plan(b'd',b'e');self.assertEqual(self.calls,5)
    def test_identity(self):
        with plan_cache_scope():
            for d,e in ((b'a',b'b'),(b'b',b'a'),(b'a',b'c'),(b'a',b'b')):
                self.assertEqual(self.plan(d,e)['rows'][:2],[d,e])
            self.assertEqual(self.calls,3)
    def test_failure(self):
        with plan_cache_scope():
            for _ in range(2):
                with self.assertRaises(ValueError):self.plan(b'bad',b'e')
            self.assertEqual(self.calls,2)
    def test_mutable(self):
        d=bytearray(b'a')
        with plan_cache_scope():
            self.plan(d,b'e');d[0]=98
            self.assertEqual(self.plan(d,b'e')['rows'][0],b'b')
            self.assertEqual(self.calls,2)
    def test_limit(self):
        with plan_cache_scope(limit=1):
            self.plan(b'a',b'e')
            self.plan(b'b',b'e');self.plan(b'b',b'e');self.plan(b'a',b'e')
            self.assertEqual(self.calls,3)
        with self.assertRaises(ValueError):
            with plan_cache_scope(limit=129):pass
    def test_exception_cleanup(self):
        with self.assertRaises(RuntimeError):
            with plan_cache_scope():
                self.plan(b'a',b'e')
                raise RuntimeError('test')
        with plan_cache_scope():self.plan(b'a',b'e')
        self.assertEqual(self.calls,2)
if __name__=='__main__':unittest.main(verbosity=2)
