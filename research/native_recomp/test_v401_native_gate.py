#!/usr/bin/env python3
"""V401 owner gate validation of original-free 16-trial opcode categories."""
from pathlib import Path
import tempfile
import unittest
from audit_v401_native_gate import verify
from test_v400_native_gate import chain as chain400
from test_v400_nand_parent_resume_audit import E as E400,T as T400

E401=('V401_NAND_CALLSITE mapped=1 kind=1 direct_match=1 '
      'selected_site=1 blr_verified=0\n')
T401='V401_NAND_CALLSITE_TRIAL kind=1 completed=1\n'
def chain(entry:str=E401,trial:str=T401)->str:
    base=chain400()
    return base.replace(E400,E400+entry,1).replace(T400,T400+trial,1)
def run(data:str,rc:int=0):
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'owner-private.log'
        path.write_text(data,encoding='ascii')
        return verify(path,rc)
class Tests(unittest.TestCase):
    def test_clean_sixteen_original_guest_proofs(self):
        self.assertEqual(run(chain()*16),(True,1,0))
        for code in (1,124,134):
            self.assertEqual(run(chain()*16,code),(False,0,0))
        self.assertEqual(run(chain()*15),(False,0,0))
        self.assertEqual(run(chain()*17),(False,0,0))
    def test_other_instruction_class_remains_truthful(self):
        other=E401.replace('kind=1','kind=5').replace('direct_match=1','direct_match=0')
        trial=T401.replace('kind=1','kind=5')
        self.assertEqual(run(chain(other,trial)*16),(True,0,1))
    def test_false_positive_direct_targets_and_malformed_pairs_rejected(self):
        for case in (
            chain().replace('V401_NAND_CALLSITE_TRIAL kind=1',
                            'V401_NAND_CALLSITE_TRIAL kind=2'),
            chain().replace('direct_match=1','direct_match=2'),
            chain().replace('selected_site=1','selected_site=0'),
            chain().replace('mapped=1','mapped=0'),
            chain().replace('blr_verified=0','blr_verified=1'),
            chain().replace(T401,''),
            chain()+T401,
        ):
            with self.subTest(length=len(case)):
                self.assertFalse(run(chain()*15+case)[0])
    def test_code_words_never_exported(self):
        self.assertTrue(run(('PRIVATE INSTRUCTION 0x4e800421\n'+chain())*16)[0])
if __name__=='__main__':unittest.main()
