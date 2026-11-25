import unittest
from audit_v761_captured_handler import inspect
from audit_v751_cold_capture import CAPTURE,EVENTS as EXT,RESULT as EXT_RESULT
from audit_v742_handler_time import STAGES as TIME
from audit_v738_handler_restore import EVENTS as RESTORE
from audit_v726_handler_return import STAGES
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
from test_v434_windows_startup_scope import OS_SI_DISPATCH
class Captured(unittest.TestCase):
    def test_same_run(self):
        first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,3)]
        base=OS_SI_DISPATCH+EVENTS[:1]+first+second+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT,STAGE,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',RETURN,END]
        base+=TIME+[b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=45 handler_return=0 boot_verified=0']
        tail=RESTORE+STAGES[1:]+[b'V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits=32 polls=0 rfi_return=0 boot_verified=0']
        rows=base+tail
        self.assertFalse(inspect(b'\n'.join(rows),0)[2])
        i=rows.index(EXT[2]);rows[i:i]=CAPTURE[:1]
        i=rows.index(EXT_RESULT);rows[i:i]=CAPTURE[1:]
        self.assertTrue(inspect(b'\n'.join(rows),0)[2])
        for bad in (rows+[CAPTURE[0]],[x for x in rows if x!=CAPTURE[1]],rows[:i]+[CAPTURE[0]]+rows[i:]):
            self.assertFalse(inspect(b'\n'.join(bad),0)[2])
        self.assertFalse(inspect(b'\n'.join(rows),126)[2])
if __name__=='__main__':unittest.main()
