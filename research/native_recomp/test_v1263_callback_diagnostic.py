import unittest
from audit_second_irq_output_v1016 import public_line
from audit_v1182_ack_callback import REFUSAL
class CallbackDiagnostic(unittest.TestCase):
    def test_whitelist(self):
        for n in range(1,12):
            self.assertTrue(public_line(f'V1263_ACK_CALLBACK_REFUSAL kind={n} visits=71 expected=71 identity=2'.encode(),(),(REFUSAL,)))
        for row in (
            b'V1263_ACK_CALLBACK_REFUSAL kind=0 visits=71 expected=71 identity=0',
            b'V1263_ACK_CALLBACK_REFUSAL kind=12 visits=71 expected=71 identity=0',
            b'V1263_ACK_CALLBACK_REFUSAL kind=5 visits=12345 expected=71 identity=0',
            b'V1263_ACK_CALLBACK_REFUSAL kind=9 visits=71 expected=71 identity=5',
            b'V1263_ACK_CALLBACK_REFUSAL kind=9 visits=71 expected=71 identity=4 pc=80500000',
            b'V1263_ACK_CALLBACK_REFUSAL kind=5 visits=0x1234 expected=71 identity=0',
        ):
            self.assertFalse(public_line(row,(),(REFUSAL,)))
if __name__=='__main__':unittest.main()
