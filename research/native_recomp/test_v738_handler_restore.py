import unittest
from pathlib import Path
from prepare_v738_handler_restore import patch_binding,patch_ack,render,patch_alias
from prepare_v726_handler_return import patch_ack as handler_patch
from prepare_v709_os_leaves import patch_poll
from prepare_v680_si_helper import patch_binding as first
from prepare_v688_si_second import patch_binding as second
from audit_v738_handler_restore import inspect,EVENTS as RESTORE,diagnostic
from audit_v726_handler_return import STAGES
from audit_v699_si_postack import STAGE,END,NESTED,RETURN
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
from test_v434_windows_startup_scope import OS_SI_DISPATCH
HOST=Path(__file__).parent
class RestoreRoute(unittest.TestCase):
    def test_bindings(self):
        source=(HOST/'wii_si_handler_return_binding_v726.h').read_text()
        out=patch_binding(source)
        self.assertIn('restore.start(c,pc,w,witness.entry_gprs())',out)
        self.assertIn('witness.restore_returned',out)
        self.assertIn("v[1]=='\\0'",out)
        with self.assertRaises(ValueError):patch_binding(out)
        ack=handler_patch(patch_poll(second(first((HOST/'wii_si_ack_binding_v672.h').read_text()))))
        self.assertIn('v726::restore_observe(a,c)',patch_ack(ack))
        self.assertIn('restore_ordinal=12u',render(0x80004000,0x80005000,0x48001001,17,11,-60))
    def test_alias(self):
        source='#include "runtime/cpu_context.h"\nvoid func_80005000(CPUContext& ctx) {\nloc_80005000: ;\n    // 0x80005000: 4E800020\n    ++ctx.inst_count;\n}\n'
        self.assertIn('v726::restore_before(ctx,0x80005000u,0x4e800020u)',patch_alias(source,0x80005000,[0x4e800020]))
        with self.assertRaises(ValueError):patch_alias(source,0x80005000,[0x60000000])
    def test_order(self):
        first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
        second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,3)]
        base=OS_SI_DISPATCH+EVENTS[:1]+first+second+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT,STAGE,*NESTED[:2],*LEAVES,NESTED[2],b'V719_POSTACK_LOOP_POLL n=1',RETURN,END]
        end=b'V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits=6 polls=0 rfi_return=0 boot_verified=0'
        rows=base+STAGES[:1]+RESTORE+STAGES[1:]+[end]
        self.assertTrue(inspect(b'\n'.join(rows),0)[1])
        for bad in (base+STAGES+[end],base+RESTORE+STAGES+[end],rows+[RESTORE[0]],base+STAGES[:1]+RESTORE[::-1]+STAGES[1:]+[end]):
            self.assertFalse(inspect(b'\n'.join(bad),0)[1])
        self.assertFalse(diagnostic(RESTORE[0]+b' private=1'))
if __name__=='__main__':unittest.main()
