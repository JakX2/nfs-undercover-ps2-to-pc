import unittest
from unittest.mock import patch
import audit_v967_post_ack as a
class PostAckAudit(unittest.TestCase):
    def test_order(self):
        p=b'V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits=80 reads=2 writes=1 boot_verified=0'
        r=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=11 handler_instruction_executed=0 boot_verified=0'
        rows=[p,r]
        with patch('audit_v958_second_ack.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[r],[r,*rows],rows+[b'V958_ACK_INVALID kind=1 stage=4 reason=2 call_reason=0 visits=12']):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
