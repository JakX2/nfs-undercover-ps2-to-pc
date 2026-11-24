import unittest
from audit_v524_si_sampling import diagnostic
class Tests(unittest.TestCase):
    def test_strict(self):
        def row(reason,stage,detail):
            return f'V524_SI_SAMPLE_INVALID reason={reason} stage={stage} detail={detail}\n'.encode()
        for i in (1,2,4,8,16,32,64,128,255):
            self.assertEqual(diagnostic(row(6,5,i),106),f'V543_SI_SAMPLE_DIAG reason=6 stage=5 detail={i} boot_verified=0')
        self.assertIsNotNone(diagnostic(row(7,5,0),106))
        for x in (row(6,5,0),row(6,5,256),row(6,4,1),row(7,5,1),row(6,5,1)*2,row(6,5,1).rstrip()+b' private\n',b'private'):
            self.assertIsNone(diagnostic(x,106))
        self.assertIsNone(diagnostic(row(6,5,1),0))
if __name__=='__main__':unittest.main()
