import unittest
from unittest.mock import patch
import audit_v1031_third_transfer as a
class Audit(unittest.TestCase):
    def test_direct_requires_original_return(self):
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=4 admitted=1',True)):
            self.assertTrue(a.inspect(b'prior\n'+a.RESULT,0)[1])
            for data in (b'prior',b'prior\n'+a.RESULT+b'\n'+a.RESULT,
                         b'prior\n'+a.RESULT.replace(b'visits=105',b'visits=104'),
                         b'prior\n'+a.RESULT.replace(b'token=3',b'token=2'),
                         b'prior\n'+a.RESULT.replace(b'pending=0',b'pending=1'),
                         b'prior\n'+a.RESULT.replace(b'returns=5',b'returns=4'),
                         b'prior\n'+a.RESULT+b'\nV958_ACK_INVALID',
                         b'prior\nV1028_UNRECOGNIZED\n'+a.RESULT):
                self.assertFalse(a.inspect(data,0)[1])
    def test_alternate_and_failed_prior(self):
        with patch.object(a.old,'inspect',return_value=('verified=1 branch=6 admitted=1',True)):
            row,ok=a.inspect(b'prior',0);self.assertTrue(ok);self.assertIn('transfer_return=0',row)
            self.assertFalse(a.inspect(b'prior\n'+a.RESULT,0)[1])
        with patch.object(a.old,'inspect',return_value=('verified=0 branch=0 admitted=0',False)):
            self.assertFalse(a.inspect(b'prior\n'+a.RESULT,126)[1])
    def test_bounds(self):
        for rc in (-1,256):
            with self.assertRaises(ValueError):a.inspect(b'',rc)
if __name__=='__main__':unittest.main()
