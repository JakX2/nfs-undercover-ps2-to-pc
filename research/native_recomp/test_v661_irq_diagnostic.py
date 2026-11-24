import unittest
from irq_diagnostic_v661 import diagnostic
class Tests(unittest.TestCase):
    def test_bounded(self):
        f=b'V616_IRQ_INVALID reason=1 stage=0\n'
        d=b'V661_IRQ_BEGIN refusal=32 pending=256'
        self.assertEqual(diagnostic(f+d,119),d.decode())
        for raw in (d,f+d+b'\n'+d,f+b'\n'+d,f+d.replace(b'256',b'0'),f+d.replace(b'32',b'2048'),f+d+b' extra'):
            self.assertIsNone(diagnostic(raw,119))
        self.assertIsNone(diagnostic(f+d,0))
        self.assertIsNotNone(diagnostic(f+b'V661_IRQ_BEGIN refusal=128 pending=0',119))
        self.assertIsNotNone(diagnostic(f+b'V661_IRQ_BEGIN refusal=1024 pending=256',119))
if __name__=='__main__':unittest.main()
