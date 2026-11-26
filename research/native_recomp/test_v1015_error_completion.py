import unittest
from unittest.mock import patch
import audit_v1015_error_completion as a
POST=b'V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits=130 handler_instruction_executed=0 boot_verified=0'
class ErrorAudit(unittest.TestCase):
    def test_exact_error_lane(self):
        with patch.object(a.shared.old,'inspect',return_value=('',True)):
            self.assertTrue(a.inspect(POST+b'\n'+a.RESULT,0)[1])
            for raw in (a.RESULT,POST.replace(b'130',b'129')+b'\n'+a.RESULT,
                        POST+b'\n'+a.RESULT+b'\n'+a.RESULT,
                        POST+b'\n'+a.RESULT.replace(b'entries=6',b'entries=5'),
                        POST+b'\n'+a.RESULT+b'\nV958_ACK_INVALID',
                        b'V989_SHARED_TIME_RESULT\n'+POST+b'\n'+a.RESULT):
                self.assertFalse(a.inspect(raw,0)[1])
            self.assertFalse(a.inspect(POST+b'\n'+a.RESULT,126)[1])
        with patch.object(a.shared.old,'inspect',return_value=('',False)):
            self.assertFalse(a.inspect(POST+b'\n'+a.RESULT,0)[1])
    def test_success_lane_preserved(self):
        with patch.object(a.shared,'inspect',return_value=('',True)):
            self.assertEqual(a.inspect(b'',0)[0],'V1015_COMPLETION_CENSUS verified=1 no_response=0 shared_time=1 boot_verified=0')
        with patch.object(a.shared,'inspect',return_value=('',False)):
            self.assertFalse(a.inspect(b'',0)[1])
if __name__=='__main__':unittest.main()
