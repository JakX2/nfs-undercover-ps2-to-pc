#!/usr/bin/env python3
import unittest
from guarded_continuation import extend_guarded,saved_mask,GUARD
R=0x80001000;T=0x80002000;N=0x60000000
def bl(a,z):return 0x48000001|((z-a)&0x03fffffc)
class Tests(unittest.TestCase):
    def setUp(self):
        self.old={R:(N,GUARD,GUARD,N)}
        self.rows=((R+4,N),(R+20,N),(R+16,bl(R+16,T)))
    def test_linear(self):
        out=extend_guarded({R:(N,GUARD)},R,R+4,((R+4,N),(R+8,bl(R+8,T))),T,N)
        self.assertEqual(out[R],(N,N,bl(R+8,T),GUARD))
        self.assertEqual(out[T],(N,GUARD))
    def test_guard_after_backward_edge(self):
        rows=((R+4,N),(R+24,N),(R+16,bl(R+16,T)))
        out=extend_guarded(self.old,R,R+4,rows,T,N)
        self.assertEqual(out[R][3],N);self.assertEqual(out[R][5],GUARD);self.assertEqual(out[R][6],N)
        self.assertEqual(self.old[R],(N,GUARD,GUARD,N))
    def test_return_overlap(self):
        with self.assertRaisesRegex(ValueError,'return guard'):
            extend_guarded(self.old,R,R+4,self.rows,T,N)
    def test_existing_instruction(self):
        with self.assertRaisesRegex(ValueError,'overlap'):
            extend_guarded(self.old,R,R+4,((R+4,N),(R+12,bl(R+12,T))),T,N)
    def test_duplicate(self):
        with self.assertRaisesRegex(ValueError,'labels'):
            extend_guarded(self.old,R,R+4,((R+4,N),(R+4,bl(R+4,T))),T,N)
    def test_existing_target(self):
        with self.assertRaisesRegex(ValueError,'ownership'):
            extend_guarded({**self.old,T:(N,GUARD)},R,R+4,((R+4,bl(R+4,T)),),T,N)
    def test_wrong_call(self):
        with self.assertRaisesRegex(ValueError,'final call'):
            extend_guarded(self.old,R,R+4,((R+4,N),),T,N)
    def test_mask(self):
        self.assertEqual(saved_mask(((4,32),(-4,31),(-8,14))),(1<<31)|(1<<14))
        for slots in (((0,13),),((0,14),(4,14))):
            with self.assertRaises(ValueError):saved_mask(slots)
if __name__=='__main__':unittest.main(verbosity=2)
