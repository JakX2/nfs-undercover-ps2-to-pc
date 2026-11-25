import unittest
from audit_v747_time_suffix import inspect,diagnostic
from audit_v742_handler_time import STAGES
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
from test_v434_windows_startup_scope import OS_SI_DISPATCH
class Suffix(unittest.TestCase):
    def test_boundary(self):
        first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,3)]
        base=OS_SI_DISPATCH+EVENTS[:1]+first+second+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT,STAGE,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',RETURN,END]
        base+=STAGES+[b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=45 handler_return=0 boot_verified=0']
        tail=[b'V726_HANDLER_CONTROL ordinal=4 kind=1 opcode=18',b'V747_NEXT_BOUNDARY ordinal=4 kind=1 visits=32 polls=0 executed=0',b'V726_HANDLER_INVALID kind=3 witness=4 stage=2 visits=32 polls=0']
        raw=b'\n'.join(base+tail)
        self.assertTrue(inspect(raw,126)[1])
        for v in (raw.replace(b'ordinal=4 kind=1 visits',b'ordinal=5 kind=1 visits'),raw.replace(b'executed=0',b'executed=1'),raw.replace(b'visits=32 polls=0 executed',b'visits=33 polls=0 executed'),raw.replace(b'opcode=18',b'opcode=19')):
            self.assertFalse(inspect(v,126)[1])
        self.assertFalse(inspect(raw,0)[1])
        self.assertFalse(diagnostic(tail[1]+b' raw=1'))
if __name__=='__main__':unittest.main()
