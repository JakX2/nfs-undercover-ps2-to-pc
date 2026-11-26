import unittest
from derive_ack_callback_paths_v1283 import path_lengths
from audit_v1182_ack_callback import is_result,RESULT,DIAG
from audit_second_irq_output_v1016 import public_line
H=0x80004000;NOP=0x60000000;CALL=0x4e800421
def bc(a,b):return 0x41820000|((b-a)&0xfffc)
def b(a,b):return 0x48000000|((b-a)&0x03fffffc)
def graph(words,goal):return [(H+i*4,w,H,H+i*4==goal) for i,w in enumerate(words)]
class Paths(unittest.TestCase):
    def test_branch_lengths(self):
        rows=graph([NOP,bc(H+4,H+16),NOP,NOP,CALL],H+16)
        self.assertEqual(path_lengths(rows,H,H,H+16),(2,4))
    def test_loop_and_cap(self):
        rows=graph([NOP,bc(H+4,H+4),CALL],H+8)
        self.assertEqual(path_lengths(rows,H,H,H+8,5),(2,3,4,5))
    def test_refused_edges(self):
        for w in (0x48000001,0x4e800020,0x44000002,0x7c600124,b(H,H-4)):
            with self.subTest(w=w),self.assertRaises(ValueError):
                path_lengths(graph([w,CALL],H+4),H,H,H+4)
        rows=graph([NOP,CALL],H+4)
        for rr in (rows+rows,[(H,NOP,H,True),rows[1]],[(H,NOP,H,False),(H+4,CALL,H,False)]):
            with self.assertRaises(ValueError):path_lengths(rr,H,H,H+4)
    def test_audit(self):
        self.assertTrue(is_result(RESULT))
        for n in (1,71,72,256):
            row=RESULT.replace(b'visits=71',f'visits={n} path_verified=1'.encode())
            self.assertTrue(is_result(row));self.assertTrue(public_line(row,(),(DIAG,)))
        for n in (0,257,999):
            self.assertFalse(is_result(RESULT.replace(b'visits=71',f'visits={n} path_verified=1'.encode())))
        self.assertFalse(is_result(RESULT.replace(b'visits=71',b'visits=72')))
        self.assertFalse(is_result(RESULT+b' path_verified=1'))
        nested=RESULT.replace(b'visits=71',b'visits=82 path_verified=1 nested_calls=4 nested_msr=2')
        self.assertTrue(is_result(nested));self.assertTrue(public_line(nested,(),(DIAG,)))
        self.assertFalse(is_result(nested.replace(b'nested_calls=4',b'nested_calls=5')))
        self.assertFalse(is_result(nested.replace(b' path_verified=1',b'')))
if __name__=='__main__':unittest.main()
