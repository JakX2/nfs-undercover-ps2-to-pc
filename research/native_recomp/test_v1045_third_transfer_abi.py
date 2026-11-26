import unittest
from unittest.mock import patch
import audit_v1045_third_transfer_abi as a
from test_v1041_transfer_abi import D,H,T,A
class ThirdAudit(unittest.TestCase):
    def test_admission_and_return_required(self):
        prior=b'\n'.join((D,H,T,A))
        with patch.object(a.abi.old,'inspect',return_value=('verified=1 branch=4 admitted=0',True)):
            raw=prior+b'\n'+a.third.RESULT
            row,ok=a.inspect(raw,0);self.assertTrue(ok);self.assertIn('admission=2 transfer_return=1',row)
            for data in (prior,raw+b'\n'+a.third.RESULT,raw+b'\nV958_ACK_INVALID',
                         raw.replace(b'visits=105',b'visits=21'),raw.replace(b'token=3',b'token=2'),
                         raw.replace(b'entries=5',b'entries=4'),raw.replace(b'pending=0',b'pending=1'),
                         raw.replace(b'admission=2',b'admission=0'),raw.replace(b'changed=0',b'changed=128')):
                self.assertFalse(a.inspect(data,0)[1])
            self.assertFalse(a.inspect(raw,126)[1])
            exact=b'\n'.join((D.replace(b'128',b'0'),H.replace(b'128',b'0'),
                             T.replace(b'queue_match=0',b'queue_match=1').replace(b'admitted=0',b'admitted=1'),
                             A.replace(b'admission=2 timing_only=1',b'admission=1 timing_only=0'),a.third.RESULT))
            self.assertTrue(a.inspect(exact,0)[1])
    def test_refused_boundary_cannot_pass(self):
        with patch.object(a.abi,'inspect',return_value=('V1041_ABI_CENSUS verified=1 admission=0 original_transfer_executed=0 boot_verified=0',True)):
            self.assertFalse(a.inspect(b'prior',0)[1])
            self.assertFalse(a.inspect(b'prior\n'+a.third.RESULT,0)[1])
if __name__=='__main__':unittest.main()
