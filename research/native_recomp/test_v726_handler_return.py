import unittest
from audit_v726_handler_return import inspect,STAGES,diagnostic
from prepare_v726_handler_return import patch_ack,patch_second,verify_resume_dispatch,render
from prepare_v709_os_leaves import patch_poll,patch_second_poll
from prepare_v680_si_helper import patch_binding as first
from prepare_v688_si_second import patch_binding as second
from prepare_v693_si_nested import patch_second as nested
from pathlib import Path
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
from test_v434_windows_startup_scope import OS_SI_DISPATCH
HOST=Path(__file__).parent
class HandlerReturn(unittest.TestCase):
    def test_patches(self):
        a=patch_poll(second(first((HOST/'wii_si_ack_binding_v672.h').read_text())))
        b=patch_second_poll(nested((HOST/'wii_si_second_binding_v688.h').read_text()))
        for patch,source in ((patch_ack,a),(patch_second,b)):
            out=patch(source);self.assertIn('v726::',out)
            with self.assertRaises(ValueError):patch(out)
        verify_resume_dispatch(' case 0x80004004: func_80004000(ctx); break;',0x80004000,0x80004004)
        with self.assertRaises(ValueError):verify_resume_dispatch(' case 0x80004004: func_80004004(ctx); break;',0x80004000,0x80004004)
        self.assertIn('0x80004000u',render(0x80004000,0x80004020,0x80004008,0x80005000,0x60000000))
    def test_order(self):
        first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,3)]
        base=OS_SI_DISPATCH+EVENTS[:1]+first+second+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT,STAGE,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',RETURN,END]
        end=b'V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits=6 polls=0 rfi_return=0 boot_verified=0'
        rows=base+STAGES+[end]
        self.assertTrue(inspect(b'\n'.join(rows),0)[1])
        for bad in (rows[:-1],base+STAGES[::-1]+[end],rows+[STAGES[0]],base+[STAGES[0]]+STAGES+[end]):
            self.assertFalse(inspect(b'\n'.join(bad),0)[1])
        self.assertFalse(inspect(b'\n'.join(rows),126)[1])
        self.assertTrue(diagnostic(end));self.assertFalse(diagnostic(end+b' private=1'))
if __name__=='__main__':unittest.main()
