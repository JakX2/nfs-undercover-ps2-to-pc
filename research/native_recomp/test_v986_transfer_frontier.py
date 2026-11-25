import unittest
from unittest.mock import patch
import audit_v986_transfer_frontier as a
class FrontierAudit(unittest.TestCase):
    def test_classifications(self):
        p=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=44 handler_instruction_executed=0 boot_verified=0'
        def row(t=1,i=1,q=1,c=1,d=1,v=15):
            return f'V981_TRANSFER_FRONTIER type={t} idle={i} queue_match={q} callback_known={c} admitted={d} visits={v} token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'.encode()
        with patch('audit_v975_second_time.inspect',return_value=('',True)):
            for r in (row(),row(q=0,d=0),row(t=0,d=0),row(i=0,d=0),row(c=0,d=0)):
                self.assertTrue(a.inspect(p+b'\n'+r,0)[1])
            for rs in ([p], [row(),p], [p,row(),row()], [p,row(d=0)], [p,row(q=0)], [p,row(v=0)], [p,row(v=8193)], [p,row(),b'V958_ACK_INVALID kind=11 stage=4 reason=0 call_reason=4 visits=8']):
                self.assertFalse(a.inspect(b'\n'.join(rs),0)[1])
            self.assertFalse(a.inspect(p+b'\n'+row(),126)[1])
    def test_requires_predecessor(self):
        p=b'V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits=44 handler_instruction_executed=0 boot_verified=0'
        r=b'V981_TRANSFER_FRONTIER type=1 idle=1 queue_match=1 callback_known=1 admitted=1 visits=15 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0'
        with patch('audit_v975_second_time.inspect',return_value=('',False)):
            self.assertFalse(a.inspect(p+b'\n'+r,0)[1])
if __name__=='__main__':unittest.main()
