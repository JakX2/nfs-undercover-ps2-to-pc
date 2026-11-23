#!/usr/bin/env python3
"""V403 privacy-safe strict owner gate, synthetic guest chain regression."""
import tempfile
import unittest
from pathlib import Path
from audit_v403_native_gate import verify
from test_v401_native_gate import chain as chain401,E401,T401
E403=('V403_NAND_CALL_PROVENANCE ctr=1 sp=1 lr=0 family=0 '
      'v401_kind=1 selected_site=1 blr_verified=0\n')
T403='V403_NAND_CALL_PROVENANCE_TRIAL family=0 complete=1\n'
def chain(e401:str=E401,t401:str=T401,e403:str=E403,t403:str=T403)->str:
    prev=chain401(e401,t401)
    return prev.replace(e401,e401+e403,1).replace(t401,t401+t403,1)
def run(data:str,rc:int=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner.log'
        p.write_text(data,encoding='ascii')
        return verify(p,rc)
class Tests(unittest.TestCase):
    def test_complete_16_trial_original_guest_provenance(self):
        self.assertEqual(run(chain()*16),(True,1,1,0))
        for rc in (1,124,134):
            self.assertEqual(run(chain()*16,rc),(False,0,0,0))
        self.assertEqual(run(chain()*15),(False,0,0,0))
        self.assertEqual(run(chain()*17),(False,0,0,0))
    def test_authenticated_v401_other_family_is_preserved(self):
        e401=E401.replace('kind=1','kind=5').replace('direct_match=1','direct_match=0')
        t401=T401.replace('kind=1','kind=5')
        e403=E403.replace('family=0','family=4').replace('v401_kind=1','v401_kind=5')
        t403=T403.replace('family=0','family=4')
        self.assertEqual(run(chain(e401,t401,e403,t403)*16),(True,1,1,0))
    def test_malformed_guest_chain_fails_closed(self):
        for event in (
            chain().replace('family=0','family=1'),
            chain().replace('v401_kind=1','v401_kind=5'),
            chain().replace('selected_site=1','selected_site=0'),
            chain().replace('sp=1','sp=2'),
            chain().replace('V403_NAND_CALL_PROVENANCE_TRIAL family=0',
                            'V403_NAND_CALL_PROVENANCE_TRIAL family=1'),
            chain().replace('V403_NAND_CALL_PROVENANCE_TRIAL family=0 complete=1',
                            'V403_NAND_CALL_PROVENANCE_TRIAL family=0 complete=0'),
            chain().replace(T403,''),
            chain()+T403,
        ):
            with self.subTest(size=len(event)):
                self.assertFalse(run(chain()*15+event)[0])
    def test_private_code_not_printed(self):
        self.assertTrue(run(('PRIVATE 0x12345678\n'+chain())*16)[0])
if __name__=='__main__':unittest.main()
