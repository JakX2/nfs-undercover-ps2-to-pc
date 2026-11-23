#!/usr/bin/env python3
"""V403 strict bounded guest provenance census, no proprietary game code."""
from pathlib import Path
import tempfile
import unittest
from analyze_v403_nand_call_provenance import inspect
from test_v401_nand_callsite_audit import E as E401,T as T401
E403=('V403_NAND_CALL_PROVENANCE ctr=1 sp=1 lr=0 family=0 '
      'v401_kind=1 selected_site=1 blr_verified=0\n')
T403='V403_NAND_CALL_PROVENANCE_TRIAL family=0 complete=1\n'
def run(raw:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'private.log'
        p.write_text(raw,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_complete_lk_guest_census_no_false_blr(self):
        result=run(('SECRET PPC 0x4e800421\n'+E401+E403+T403)*16)
        self.assertIn('entries=16 trials=16 family0=16',result)
        self.assertIn('ctr_trials=16 sp_trials=16 lr_trials=0',result)
        self.assertIn('classified=1 blr_verified=0',result)
        self.assertNotIn('SECRET',result)
    def test_nonlink_opcode_is_classified_without_claiming_return(self):
        e401=E401.replace('kind=1','kind=5').replace('direct_match=1','direct_match=0')
        e403=E403.replace('family=0','family=4').replace('v401_kind=1','v401_kind=5')
        t403=T403.replace('family=0','family=4')
        out=run((e401+e403+t403)*16)
        self.assertIn('family4=16',out)
        self.assertIn('ctr_trials=16',out)
        self.assertIn('classified=1 blr_verified=0',out)
    def test_malformed_or_unpaired_events_fail_closed(self):
        for bad in (
            '',E403,T403,E401+E403,E401+E403+T403+T403,
            E401+E403+E403+T403,
            E403+E401+T403,
            E401+E403.replace('family=0','family=1')+T403,
            E401+E403.replace('v401_kind=1','v401_kind=5')+T403,
            E401+E403.replace('selected_site=1','selected_site=0')+T403,
            E401+E403.replace('blr_verified=0','blr_verified=1')+T403,
            E401+E403+T403.replace('complete=1','complete=0'),
            (E401+E403+T403)*17,
        ):
            with self.subTest(size=len(bad)):
                self.assertIn('classified=0',run(bad))
if __name__=="__main__":
    unittest.main()
