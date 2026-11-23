#!/usr/bin/env python3
"""Synthetic original-free V406 bounded abort checkpoint analyzer."""
import tempfile
import unittest
from pathlib import Path
from analyze_v406_nand_abort_frontier import inspect
def event(call:int,origin:int=2,selected:int=1,parent:int=1)->str:
    return (f'V406_NAND_CHECKPOINT call={call} origin={origin} '
            f'selected={selected} parent={parent}\n')
def run(data:str,rc:int=0)->str:
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'private.log'
        path.write_text(data,encoding='ascii')
        return inspect(path,rc)

class Tests(unittest.TestCase):
    def test_abort_after_original_guest_call_63(self):
        raw='PRIVATE GUEST INSTRUCTION 0x4e800421\n'
        raw+=''.join(event(i,i%4+1) for i in range(49,64))
        s=run(raw,134)
        self.assertIn('rc=134 kind=signal',s)
        self.assertIn('seen=15 first=49 last=63',s)
        self.assertIn('mask=15 selected_any=1 parent_any=1',s)
        self.assertIn('contiguous=1 boundary96=0 boot_verified=0',s)
        self.assertNotIn('PRIVATE GUEST',s)
    def test_complete_96_call_candidate_bounded_first_trial(self):
        s=run(''.join(event(i) for i in range(49,97)))
        self.assertIn('seen=48 first=49 last=96',s)
        self.assertIn('contiguous=1 boundary96=1 boot_verified=0',s)
    def test_no_post48_guest_call_is_not_a_success(self):
        s=run('native abort\n',134)
        self.assertIn('seen=0 first=0 last=0 mask=0',s)
        self.assertIn('contiguous=0 boundary96=0 boot_verified=0',s)
    def test_bad_order_duplicate_missing_and_malformed(self):
        for item in (
            event(50),event(49)+event(49),
            event(49)+event(51),
            ''.join(event(i) for i in range(49,97))+event(96),
            event(49).replace('origin=2','origin=5'),
            event(49,selected=0,parent=1),
        ):
            with self.subTest(size=len(item)):
                out=run(item)
                # Malformed-only logs are not proof, duplicates and gaps fail
                self.assertIn('contiguous=0',out)
                self.assertIn('boundary96=0',out)
if __name__=='__main__':
    unittest.main()
