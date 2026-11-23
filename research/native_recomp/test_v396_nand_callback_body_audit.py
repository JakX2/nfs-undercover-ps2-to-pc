#!/usr/bin/env python3
"""V396 bounded original-free callback continuation census tests."""
import tempfile
import unittest
from pathlib import Path
from analyze_v396_nand_callback_body import inspect
E='V396_NAND_CB_BODY kind=1 verified=1 owned=1 clear=1 cache=0 context=0 nand=0 bounded=0\n'
T='V396_NAND_CB_TRIAL kind=1 stopped=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'private-owner.log'
        p.write_text(raw,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_real_dynamic_callback_guest_call(self):
        s=run('PRIVATE CODE NOT EXPORTED\n'+E+T)
        self.assertIn('entries=1 trials=1 owner_any=1 cap_any=0',s)
        self.assertIn('nand_any=0 next_verified=1',s)
        self.assertNotIn('PRIVATE CODE',s)
    def test_bounded_nonowner_does_not_claim_callback_completion(self):
        e=E.replace('kind=1','kind=2').replace('owned=1','owned=0').replace('bounded=0','bounded=1')
        t=T.replace('kind=1','kind=2')
        self.assertIn('owner_any=0 cap_any=1',run(e+t))
    def test_malformed_mixed_and_unpaired_not_verified(self):
        for raw in ('',E,T,E+E+T,T+E+T,E+T+T,
                    E.replace('clear=1','clear=0')+T,
                    E.replace('owned=1','owned=0')+T,
                    E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('next_verified=0',run(raw),raw)
    def test_more_than_sixteen_pairs_cannot_pass(self):
        self.assertIn('next_verified=0',run((E+T)*17))
if __name__=="__main__":unittest.main()
