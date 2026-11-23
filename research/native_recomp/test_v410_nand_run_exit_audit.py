#!/usr/bin/env python3
"""Synthetic original-free host V390 exit classification, no game code."""
import tempfile
import unittest
from pathlib import Path
from analyze_v410_nand_run_exit import inspect

E=('V410_NAND_GUEST_RUN_EXIT calls=50 kind=0 running=0 '
   'mapped=1 matched_stop=0 v390=0\n')
def run(data:str,rc:int=134)->str:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(data,encoding='ascii')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_unexpected_guest_exit_before_old_harness_assertion(self):
        result=run('SECRET private original PPC\n'+E)
        self.assertIn('rc=134 kind=signal',result)
        self.assertIn('entries=1 max_calls=50 last_calls=50',result)
        self.assertIn('guest_stop_trials=0 running_trials=0 mapped_trials=1',result)
        self.assertIn('v390_trials=0 classified=1 boot_verified=0',result)
        self.assertNotIn('SECRET private',result)
    def test_synthetic_successful_observer_stop_is_distinguished(self):
        good=E.replace('calls=50 kind=0','calls=96 kind=2').replace(
            'matched_stop=0 v390=0','matched_stop=1 v390=1')
        out=run(good*16,0)
        self.assertIn('entries=16 max_calls=96',out)
        self.assertIn('guest_stop_trials=16',out)
        self.assertIn('v390_trials=16 classified=1',out)
    def test_no_traces_does_not_claim_success(self):
        s=run('',134)
        self.assertIn('entries=0 max_calls=0',s)
        self.assertIn('boot_verified=0',s)
    def test_overflow_and_incoherent_classifications_fail_closed(self):
        for bad in (E*17,E.replace('calls=50','calls=100'),
                    E.replace('kind=0','kind=2').replace('matched_stop=0','matched_stop=2'),
                    E.replace('kind=0','kind=0').replace('matched_stop=0','matched_stop=1'),
                    E.replace('kind=0','kind=0').replace('v390=0','v390=1')):
            with self.subTest(size=len(bad)):
                self.assertIn('classified=0',run(bad))
if __name__=='__main__':unittest.main()
