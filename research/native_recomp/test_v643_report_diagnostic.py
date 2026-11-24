import unittest
from report_diagnostic_v643 import diagnostic
F=b'V603_REPORT_INVALID reason=8 stage=2 reports=3 getters=0'
D=b'V643_REPORT_DIAG mask=48 class=6 call_offset=128 format_offset=164'
class Tests(unittest.TestCase):
    def test_exact(self):
        self.assertEqual(diagnostic(b'\n'.join((F,D)),116),D.decode())
        for bad in (D,F,F+b'\n'+D+b'\n'+D,F+b'\n'+D.replace(b'48',b'128'),F+b'\n'+D.replace(b'class=6',b'class=37'),F+b'\n'+D.replace(b'offset=128',b'offset=129'),F+b'\nother\n'+D):
            self.assertIsNone(diagnostic(bad,116))
        self.assertIsNone(diagnostic(F+b'\n'+D,0))
if __name__=='__main__':unittest.main()
