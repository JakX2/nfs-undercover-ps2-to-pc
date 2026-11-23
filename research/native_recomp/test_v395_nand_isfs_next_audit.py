#!/usr/bin/env python3
"""V395 audit: strict original guest pairs, no proprietary traces."""
import tempfile
import unittest
from pathlib import Path
from analyze_v395_nand_isfs_next import inspect
from diagnose_v299_native_log import WINDOW
E='V395_NAND_ISFS_NEXT guest=1 clear=1 masked=1 registered=1 mapped=1 selected=1 userdata=1 nand=1\n'
T='V395_NAND_ISFS_TRIAL isfs=1 next=1 completed=1\n'
def run(raw,rc=0):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(raw,encoding='utf-8')
        return inspect(p,rc)
class Tests(unittest.TestCase):
    def test_authentic_nested_nand_callback_and_private_redaction(self):
        s=run('private PPCCONTEXT data\n'+E+T)
        self.assertIn('entries=1 trials=1 mapped_any=1 selected_any=1',s)
        self.assertIn('userdata_any=1 nand_any=1 next_verified=1',s)
        self.assertNotIn('private PPC',s)
    def test_unknown_original_guest_callee_not_fabricated(self):
        e=E.replace('nand=1','nand=0').replace('selected=1','selected=0')
        self.assertIn('nand_any=0 next_verified=1',run(e+T))
    def test_bad_unpaired_or_inconsistent_fails(self):
        for raw in ('',E,T,T+E+T,E+E+T,E+T+T,
                    E.replace('guest=1','guest=0')+T,
                    E.replace('clear=1','clear=0')+T,
                    E+T+E+T.replace('completed=1','completed=0')):
            self.assertIn('next_verified=0',run(raw),raw)
    def test_bitfield_census_identifies_exact_first_bad_trial_without_private_bytes(self):
        raw=E+T+E.replace('selected=1','selected=0')+T.replace('completed=1','completed=0')
        s=run('PRIVATE-NAND-ADDRESS 0xDEADBEEF\n'+raw)
        self.assertIn('entries=2 trials=2',s)
        self.assertIn('next_verified=0',s)
        self.assertIn('V395_NAND_FIELD_CENSUS entries=2 trials=2',s)
        self.assertIn('entry_any_mask=FF entry_all_mask=DF',s)
        self.assertIn('trial_any_mask=7 trial_all_mask=3',s)
        self.assertIn('first_bad=2',s)
        self.assertNotIn('PRIVATE-NAND-ADDRESS',s)
        self.assertNotIn('DEADBEEF',s)
    def test_unexpected_optional_callback_target_does_not_count_as_failure(self):
        unknown=E.replace('mapped=1','mapped=0').replace('selected=1','selected=0').replace('userdata=1','userdata=0').replace('nand=1','nand=0')
        report=run(unknown+T)
        self.assertIn('next_verified=1',report)
        self.assertIn('entry_all_mask=0F',report)
        self.assertIn('first_bad=0',report)
    def test_empty_census_masks_report_zero(self):
        result=run('')
        self.assertIn('entry_any_mask=00 entry_all_mask=00',result)
        self.assertIn('trial_any_mask=0 trial_all_mask=0',result)
    def test_chain_cascade_census_exposes_only_failure_stage(self):
        earlier=(
            'V392_NAND_POST_CACHE_TRIAL kind=1 stopped=1 completed=0\n'
            'V393_NAND_NEXT_TRIAL first=1 next=1 completed=0\n'
            'V394_NAND_ISFS_TRIAL context=1 isfs=1 completed=0\n'
        )
        report=run('PRIVATE ORIGINAL NAND FUNCTION ADDRESS\n'+earlier+E+T.replace('completed=1','completed=0'))
        self.assertIn('V395_NAND_CHAIN_CENSUS',report)
        self.assertIn('v392_trials=1 v393_trials=1 v394_trials=1 v395_trials=1',report)
        self.assertIn('v392_first_failed=1 v393_first_failed=1 v394_first_failed=1 v395_first_failed=1',report)
        self.assertNotIn('PRIVATE ORIGINAL',report)
    def test_stages_with_no_evidence_have_zero_failure_masks(self):
        report=run('')
        self.assertIn('v392_trials=0 v393_trials=0 v394_trials=0 v395_trials=0',report)
        self.assertIn('v392_all_mask=0 v393_all_mask=0 v394_all_mask=0 v395_all_mask=0',report)
    def test_full_private_log_middle_evidence_is_not_lost(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'private-owner.log'
            with p.open('wb') as f:
                f.write(b'ORIGINAL-PRIVATE-OUTPUT\n')
                f.write(b'x'*(WINDOW+128))
                f.write(b'\n'+E.encode('ascii')+T.encode('ascii'))
                f.write(b'PRIVATE-CODE-STREAM\n')
                f.write(b'y'*(WINDOW+128))
                f.write(b'\n')
            report=inspect(p,0)
            self.assertIn('entries=1 trials=1',report)
            self.assertIn('next_verified=1',report)
            self.assertIn('V395_NAND_FIELD_CENSUS entries=1 trials=1',report)
            self.assertNotIn('ORIGINAL-PRIVATE',report)
            self.assertNotIn('PRIVATE-CODE-STREAM',report)
    def test_more_than_sixteen_private_marker_pairs_fail_closed(self):
        report=run((E+T)*17)
        self.assertIn('next_verified=0',report)
        self.assertIn('V395_NAND_FIELD_CENSUS',report)
    def test_large_private_log_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'owner-private.log'
            with p.open('wb') as f:
                f.write((E+T).encode('ascii'))
                f.seek(WINDOW+80)
                f.write(b'\n')
            self.assertIn('sample_complete=0',inspect(p,124))
if __name__=="__main__":unittest.main()
