import unittest
from unittest.mock import patch
import audit_v1021_error_frontier as a
C=b'V995_CALLBACK_FRONTIER target_class=2 aligned=1 visits=71 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
T=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=44 handler_instruction_executed=0 boot_verified=0'
D=b'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match=1 callback_known=1 admitted=1 visits=15 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
class ErrorFrontier(unittest.TestCase):
    def test_queue_detail(self):
        detail=b'V1034_QUEUE_DETAIL mismatch_mask=128 slot_kind=1 arg_time_zero=1 queue_time_zero=0'
        mismatch=D.replace(b'queue_match=1',b'queue_match=0').replace(b'admitted=1',b'admitted=0')
        with patch.object(a.error,'inspect',return_value=('verified=1 no_response=1',True,b'')):
            def inspect(*tail):return a.inspect(b'\n'.join((a.error.RESULT,T,a.DIRECT,*tail)),0)
            row,ok=inspect(detail,mismatch)
            self.assertTrue(ok);self.assertIn('branch=4 admitted=0',row)
            self.assertTrue(inspect(detail.replace(b'128',b'0'),D)[1])
            for tail in ((detail,D),(detail.replace(b'128',b'256'),mismatch),
                         (detail,detail,mismatch),(mismatch,detail),
                         (detail.replace(b'slot_kind=1',b'slot_kind=3'),mismatch),
                         (detail.replace(b'128',b'0'),mismatch)):
                self.assertFalse(inspect(*tail)[1])
    def test_queue_history(self):
        detail=b'V1034_QUEUE_DETAIL mismatch_mask=128 slot_kind=1 arg_time_zero=1 queue_time_zero=0'
        history=b'V1037_QUEUE_HISTORY initial_mismatch=128 current_mismatch=128 changed=0 initial_slot_kind=1 samples=256'
        mismatch=D.replace(b'queue_match=1',b'queue_match=0').replace(b'admitted=1',b'admitted=0')
        with patch.object(a.error,'inspect',return_value=('verified=1 no_response=1',True,b'')):
            def inspect(*tail):return a.inspect(b'\n'.join((a.error.RESULT,T,a.DIRECT,*tail)),0)
            self.assertTrue(inspect(detail,history,mismatch)[1])
            for bad in (history.replace(b'current_mismatch=128',b'current_mismatch=0'),
                        history.replace(b'initial_mismatch=128',b'initial_mismatch=0'),
                        history.replace(b'samples=256',b'samples=0'),
                        history.replace(b'changed=0',b'changed=256')):
                self.assertFalse(inspect(detail,bad,mismatch)[1])
            self.assertFalse(inspect(history,mismatch)[1])
            self.assertFalse(inspect(detail,history,history,mismatch)[1])
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
