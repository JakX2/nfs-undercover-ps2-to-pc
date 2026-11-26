import unittest
from unittest.mock import patch
import audit_v1021_error_frontier as a
C=b'V995_CALLBACK_FRONTIER target_class=2 aligned=1 visits=71 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
T=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=44 handler_instruction_executed=0 boot_verified=0'
D=b'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match=1 callback_known=1 admitted=1 visits=15 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
class ErrorFrontier(unittest.TestCase):
    def test_exact_branches(self):
        with patch.object(a.error,'inspect',return_value=('verified=1 no_response=1',True,b'')):
            for tail,branch in (((a.INDIRECT,C),6),((T,a.DIRECT,D),4)):
                row,ok=a.inspect(b'\n'.join((a.error.RESULT,*tail)),0)
                self.assertTrue(ok);self.assertIn(f'branch={branch} admitted=1',row)
                self.assertFalse(a.inspect(b'\n'.join((a.error.RESULT,*tail)),126)[1])
            for rows in ((a.error.RESULT,a.INDIRECT),(a.error.RESULT,a.INDIRECT,C.replace(b'visits=71',b'visits=70')),
                         (a.error.RESULT,T,D,a.DIRECT),(a.error.RESULT,T,a.DIRECT,D.replace(b'queue_match=1',b'queue_match=0')),
                         (a.error.RESULT,a.INDIRECT,C,a.INDIRECT),(a.error.RESULT,a.INDIRECT,C,b'V958_ACK_INVALID'),
                         (a.INDIRECT,a.error.RESULT,a.INDIRECT,C),(a.error.RESULT,T,a.DIRECT,D.replace(b'visits=15',b'visits=77'))):
                self.assertFalse(a.inspect(b'\n'.join(rows),0)[1])
        with patch.object(a.error,'inspect',return_value=('verified=1 no_response=0',True,b'')):
            self.assertFalse(a.inspect(b'\n'.join((a.error.RESULT,a.INDIRECT,C)),0)[1])
if __name__=='__main__':unittest.main()
