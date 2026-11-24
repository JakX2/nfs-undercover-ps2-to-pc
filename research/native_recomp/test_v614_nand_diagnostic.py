import unittest,struct
from unittest.mock import patch
from derive_v605_nand_selected_lifetime import authenticate,diagnostic
PC=0x80510000
LR=0x804f0f54
EW=0x60000000
LW=0x4e800421
class Tests(unittest.TestCase):
    def test_exact_original_callsite(self):
        def reader(blob,addr,n):
            return struct.pack('>I',blob[addr])
        owner={PC:EW,LR-4:LW};fixture=owner.copy()
        sizes={0x804f0e04:0x180,PC:60}
        with patch('derive_v605_nand_selected_lifetime.history',return_value=(PC,LR,EW,LW)),patch('derive_v605_nand_selected_lifetime.classify',return_value=('original',None)),patch('derive_v605_nand_selected_lifetime.aot_entry',return_value=(1,1)):
            self.assertEqual(authenticate(b'',owner,fixture,sizes,'',reader=reader),(PC,LR))
            with self.assertRaisesRegex(ValueError,'selected fixture word'):
                authenticate(b'',owner,{**fixture,LR-4:0},sizes,'',reader=reader)
            with self.assertRaisesRegex(ValueError,'selected owner word'):
                authenticate(b'',{**owner,PC:0},fixture,sizes,'',reader=reader)
            with self.assertRaisesRegex(ValueError,'ISFS extent'):
                authenticate(b'',owner,fixture,{0x804f0e04:4},'',reader=reader)
        for word in (0x4e800420,0x4e800020,0x48000001):
            data={PC:EW,LR-4:word}
            with patch('derive_v605_nand_selected_lifetime.history',return_value=(PC,LR,EW,word)),patch('derive_v605_nand_selected_lifetime.classify',return_value=('original',None)),patch('derive_v605_nand_selected_lifetime.aot_entry',return_value=(1,1)):
                with self.assertRaisesRegex(ValueError,'selected link'):authenticate(b'',data,data,sizes,'',reader=reader)
    def test_public_diagnostic(self):
        self.assertEqual(diagnostic(ValueError('selected owner word'),'selected_auth'),'V614_NAND_DERIVE phase=selected_auth reason=selected_owner_word')
        for e in (ValueError('private path and bytes'),OSError('private path'),KeyError('private bytes')):
            self.assertEqual(diagnostic(e,'source_chain'),'V614_NAND_DERIVE phase=source_chain reason=other')
if __name__=='__main__':unittest.main()
