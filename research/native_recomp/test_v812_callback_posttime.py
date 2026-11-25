import unittest
from audit_callback_posttime_v812 import shared,SDK
from prepare_v667_si_dispatch import DISABLE,RESTORE
from prepare_owner_leaf_v714 import bl

class Dependencies(unittest.TestCase):
    def test_shared(self):
        a,b,c=0x80530000,0x80530100,0x80531000
        aw=[0x60000000]*39;bw=[0x60000000]*30
        for i,d in enumerate((DISABLE,RESTORE,c,c)):aw[i]=bl(a+4*i,d)
        for i,d in enumerate((DISABLE,RESTORE,c)):bw[i]=bl(b+4*i,d)
        aw[-1]=bw[-1]=0x4e800020
        self.assertEqual(shared(a,aw,b,bw),c)
        for i,d in ((0,RESTORE),(1,DISABLE),(3,c+4)):
            bad=aw[:];bad[i]=bl(a+4*i,d)
            with self.assertRaises(ValueError):shared(a,bad,b,bw)
        with self.assertRaises(ValueError):shared(a,aw[:-1],b,bw)
    def test_allowlist(self):
        self.assertIn('OSGetWirelessID',SDK)
        self.assertIn('OSSetWirelessID',SDK)
        self.assertIn('EXIImm',SDK)
        self.assertEqual(len(set(SDK)),len(SDK))
if __name__=='__main__':unittest.main()
