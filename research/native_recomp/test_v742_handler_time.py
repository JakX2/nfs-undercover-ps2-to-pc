import unittest
from pathlib import Path
from prepare_v742_handler_time import patch_nested,patch_leaf,patch_ack,patch_handler,render
from prepare_v709_os_leaves import patch_nested as first_nested,patch_poll
from prepare_v726_handler_return import patch_ack as handler_patch
from prepare_v680_si_helper import patch_binding as first
from prepare_v688_si_second import patch_binding as second
from audit_v742_handler_time import inspect,STAGES,diagnostic
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
from test_v434_windows_startup_scope import OS_SI_DISPATCH
HOST=Path(__file__).parent
class TimeRoute(unittest.TestCase):
    def test_patches(self):
        read=lambda n:(HOST/n).read_text()
        sources=[first_nested(read('wii_si_nested_binding_v693.h')),read('wii_si_os_leaf_binding_v709.h'),handler_patch(patch_poll(second(first(read('wii_si_ack_binding_v672.h'))))),read('wii_si_handler_return_binding_v726.h')]
        for fn,s in zip((patch_nested,patch_leaf,patch_ack,patch_handler),sources):
            out=fn(s);self.assertIn('v742::',out)
            with self.assertRaises(ValueError):fn(out)
        self.assertIn('0x80004000u',render((0x80004000,0x80005000,0x80005064,0x48001001)))
    def test_order(self):
        first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,3)]
        base=OS_SI_DISPATCH+EVENTS[:1]+first+second+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT,STAGE,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',RETURN,END]
        end=b'V742_TIME_RESULT returned=1 abi=1 leaves=3 visits=25 total=45 handler_return=0 boot_verified=0'
        self.assertTrue(inspect(b'\n'.join(base+STAGES+[end]),0)[1])
        for tail in (STAGES[:-1]+[end],STAGES[::-1]+[end],STAGES+[end,end],STAGES+[end.replace(b'total=45',b'total=44')]):
            self.assertFalse(inspect(b'\n'.join(base+tail),0)[1])
        self.assertFalse(inspect(b'\n'.join(base+STAGES+[end]),126)[1])
        self.assertFalse(diagnostic(end+b' extra=1'))
if __name__=='__main__':unittest.main()
