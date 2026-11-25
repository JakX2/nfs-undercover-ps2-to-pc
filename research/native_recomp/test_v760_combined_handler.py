import unittest
from pathlib import Path
from prepare_v756_combined_handler import combine,after_restore
from prepare_v738_handler_restore import patch_binding

from audit_v760_combined_handler import inspect
from audit_v742_handler_time import STAGES as TIME
from audit_v738_handler_restore import EVENTS as RESTORE
from audit_v726_handler_return import STAGES
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
from test_v434_windows_startup_scope import OS_SI_DISPATCH
class Combined(unittest.TestCase):
    def test_binding(self):
        src=(Path(__file__).parent/'wii_si_handler_return_binding_v726.h').read_text()
        self.assertEqual(combine(src),after_restore(patch_binding(src)))
        with self.assertRaises(ValueError):after_restore(src)
        with self.assertRaises(ValueError):after_restore(combine(src))
    def test_audit(self):
        first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,3)]
        base=OS_SI_DISPATCH+EVENTS[:1]+first+second+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT,STAGE,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',RETURN,END]
        base+=TIME+[b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=45 handler_return=0 boot_verified=0']
        tail=RESTORE+STAGES[1:]+[b'V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits=32 polls=0 rfi_return=0 boot_verified=0']
        self.assertTrue(inspect(b'\n'.join(base+tail),0)[1])
        for bad in (tail[1:],RESTORE[::-1]+tail[3:],tail+[RESTORE[0]],tail[3:]):
            self.assertFalse(inspect(b'\n'.join(base+bad),0)[1])
        refusal=[b'V726_HANDLER_CONTROL ordinal=4 kind=1 opcode=18',b'V747_NEXT_BOUNDARY ordinal=4 kind=1 visits=32 polls=0 executed=0',b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=32 polls=0']
        self.assertTrue(inspect(b'\n'.join(base+refusal),126)[1])
        self.assertFalse(inspect(b'\n'.join(base+RESTORE+refusal),126)[1])
if __name__=='__main__':unittest.main()
