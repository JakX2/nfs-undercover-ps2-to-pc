import unittest
from unittest.mock import patch
import audit_v1054_third_alarm as a
from test_v1041_transfer_abi import D,H,T,A
R=b'V1048_THIRD_ALARM_RETURN original_return=1 queue=1 token=3 lane=0 timer=0 calls=3 visits=33 suffix_visits=17 status_reads=1 status_writes=1 token_held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0'
class Audit(unittest.TestCase):
    def test_order_and_exact_alarm(self):
        prior=b'\n'.join((D,H,T,A,a.third.third.RESULT))
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            self.assertTrue(a.inspect(prior+b'\n'+R,0)[1])
            for bad in (R.replace(b'token=3',b'token=2'),R.replace(b'visits=33',b'visits=32'),R.replace(b'calls=3',b'calls=1'),
                        R.replace(b'lane=0',b'lane=4'),R.replace(b'timer=0',b'timer=1'),R.replace(b'suffix_visits=17',b'suffix_visits=129'),
                        R.replace(b'status_reads=1',b'status_reads=0'),R+b'\n'+R,R+b'\nV958_ACK_INVALID',
                        R.replace(b'handler_instruction_executed=0',b'handler_instruction_executed=1')):
                self.assertFalse(a.inspect(prior+b'\n'+bad,0)[1])
            self.assertFalse(a.inspect(prior,0)[1])
            self.assertFalse(a.inspect(prior+b'\n'+R,126)[1])
            self.assertFalse(a.inspect(b'\n'.join((D,H,T,A,R)),0)[1])
            self.assertTrue(a.inspect(prior+b'\n'+R.replace(b'status_reads=1 status_writes=1',b'status_reads=0 status_writes=0'),0)[1])
if __name__=='__main__':unittest.main()
