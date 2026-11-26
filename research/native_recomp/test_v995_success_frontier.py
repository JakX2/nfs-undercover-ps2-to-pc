import unittest
from unittest.mock import patch
import audit_v995_success_frontier as a
class SuccessFrontier(unittest.TestCase):
    def test_branches(self):
        post=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=167 handler_instruction_executed=0 boot_verified=0'
        time=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=44 handler_instruction_executed=0 boot_verified=0'
        transfer=b'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match=1 callback_known=1 admitted=1 visits=15 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
        callback=b'V995_CALLBACK_FRONTIER target_class=2 aligned=1 visits=71 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
        with patch('audit_v989_shared_time.inspect',return_value=('',True)):
            for rows,branch in (([post,callback],6),([post,time,transfer],4),([post,callback.replace(b'aligned=1',b'aligned=0')],6),([post,time,transfer.replace(b'queue_match=1',b'queue_match=0').replace(b'admitted=1',b'admitted=0')],4)):
                result,ok=a.inspect(b'\n'.join(rows),0);self.assertTrue(ok);self.assertIn(f'branch={branch}',result)
            for rows in ([post],[callback,post],[post,callback,callback],[post,time,callback],[post,transfer],[post,time,transfer,callback],[post,time,transfer.replace(b'admitted=1',b'admitted=0')],[post,callback.replace(b'target_class=2',b'target_class=0')],[post,callback.replace(b'visits=71',b'visits=0')],[post,callback,b'V958_ACK_INVALID kind=13 stage=4 reason=0 call_reason=4 visits=123']):
                self.assertFalse(a.inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(a.inspect(b'\n'.join([post,callback]),126)[1])
        with patch('audit_v989_shared_time.inspect',return_value=('',False)):
            self.assertFalse(a.inspect(b'\n'.join([post,callback]),0)[1])
if __name__=='__main__':unittest.main()
