import unittest
from unittest.mock import patch
import audit_v932_pending_rfi as a
class PendingAudit(unittest.TestCase):
    def test_order(self):
        result=b'V932_REENTRY_RESULT native_rfi=1 second_exception=1 vector_entry=1 restored_context=1 visits=85 device_held=1 resumed_instruction_executed=0 boot_verified=0'
        rows=[a.old.old.RETURN,a.SOURCE,*a.old.STAGES[:2],a.RFI,a.POLL,result]
        with patch('audit_v921_capture_join.inspect',return_value=('',True)):
            self.assertTrue(a.inspect(b'\n'.join(rows),0)[1])
            for bad in (rows[:-1],rows[::-1],rows+[result],rows+[a.POLL],[a.RFI,*rows],rows[:-2]+[result]):
                self.assertFalse(a.inspect(b'\n'.join(bad),0)[1])
            self.assertFalse(a.inspect(b'\n'.join(rows),126)[1])
if __name__=='__main__':unittest.main()
