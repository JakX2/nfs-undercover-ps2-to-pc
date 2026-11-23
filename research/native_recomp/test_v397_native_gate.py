#!/usr/bin/env python3
"""V397 owner gate synthetic event proof, no game-derived bytes."""
from pathlib import Path
import tempfile
import unittest
from audit_v397_native_gate import verify
from test_v396_native_gate import (
    ENTRY395,ENTRY396,T392,T393,T394,T395,T396
)
E397=('V397_NAND_ORIGINS mask=8 last=4 calls=24 selected_any=0 '
      'isfs_any=0 parent_any=0 other_any=1 same_lr_any=0\n')
T397='V397_NAND_ORIGINS_TRIAL completed=1 stopped=1\n'
EVENT=ENTRY395+ENTRY396+E397+T392+T393+T394+T395+T396+T397
def run(raw:str,rc:int=0)->bool:
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'owner-private.log'
        p.write_text(raw,encoding='ascii')
        return verify(p,rc)
class Tests(unittest.TestCase):
    def test_full_owner_original_lineage_requires_sixteen_trials(self):
        self.assertTrue(run(EVENT*16))
        for rc in (1,124,134):
            self.assertFalse(run(EVENT*16,rc))
        self.assertFalse(run(EVENT*15))
        self.assertFalse(run(EVENT*17))
        self.assertFalse(run(''))
    def test_invalid_lineage_and_stale_v396_gate_rejected(self):
        for altered in (
            EVENT.replace('mask=8','mask=4'),
            EVENT.replace('last=4','last=3'),
            EVENT.replace('completed=1 stopped=1','completed=0 stopped=1'),
            EVENT.replace('calls=24','calls=25'),
            EVENT.replace('same_lr_any=0','same_lr_any=2'),
            EVENT.replace('selected=1','selected=0'),
            EVENT.replace('userdata=1','userdata=0'),
            EVENT.replace('verified=1','verified=0'),
            EVENT.replace(T397,''),
            EVENT+T397,
        ):
            with self.subTest(size=len(altered)):
                self.assertFalse(run(EVENT*15+altered))
    def test_selected_origin_early_stop_is_not_claimed_as_return(self):
        selected=E397.replace('mask=8','mask=1').replace('last=4','last=1').replace(
            'calls=24','calls=7').replace('selected_any=0','selected_any=1').replace(
            'other_any=1','other_any=0')
        owned=ENTRY396.replace('kind=2','kind=1').replace('owned=0','owned=1').replace(
            'bounded=1','bounded=0')
        trial=T396.replace('kind=2','kind=1')
        event=ENTRY395+owned+selected+T392+T393+T394+T395+trial+T397
        self.assertTrue(run(event*16))
    def test_private_text_never_appears_in_gate_result(self):
        self.assertTrue(run(('private text 0xdeadbeef\n'+EVENT)*16))
if __name__=="__main__":
    unittest.main()
