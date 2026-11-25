import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v919_handler_epilogue import patch_binding as prior_patch
from prepare_v920_handler_return import patch_binding,patch_label
from audit_v920_handler_return import inspect,POLL,RETURN
from audit_v919_handler_epilogue import MARKERS
from audit_v870_handler_suffix import STATUS,STORE
from test_v870_handler_suffix_audit import prefix,markers,P
HERE=Path(__file__).parent
class HandlerReturn(unittest.TestCase):
    def test_patch(self):
        s=patch_binding(prior_patch((HERE/'wii_handler_suffix_binding_v868.h').read_text()))
        self.assertIn('if(!return_enabled())std::_Exit(0);',s)
        self.assertIn('v726::witness.resumed(c,pc,w,true)',s)
        self.assertIn('observe_completed_callback_dispatch',s)
        with self.assertRaises(ValueError):patch_binding(s)
    def test_label(self):
        h=0x80004000;w=0x60000000
        s=f'loc_{h:X}: ;\n    // 0x{h:08X}: {w:08X}\n    ++ctx.inst_count;\n    undercover::wii::v726::resume(ctx,0x{h:08x}u,0x{w:08x}u);\n    ctx.si_instruction_boundary();\n'
        t=patch_label(s,h,w)
        self.assertLess(t.index('v868::dispatch_resume'),t.index('++ctx.inst_count'))
        self.assertLess(t.index('ctx.si_instruction_boundary'),t.index('v868::dispatcher_resume'))
        self.assertIn('if(!undercover::wii::v868::return_active()) undercover::wii::v726::resume',t)
        with self.assertRaises(ValueError):patch_label(t,h,w)
    def test_audit(self):
        j,s=markers(6,12,1,20)
        rows=(*prefix(P,6),j,STATUS,STORE,b'V911_HANDLER_INDEX_BRANCH original_load=1 compare=1 branch_taken=1 successor=1',s,*MARKERS)
        with patch('audit_v809_callback_prefix.alarm',return_value=('',True)):
            self.assertTrue(inspect(b'\n'.join((*rows,POLL,RETURN)),0)[1])
            for tail in ((),(POLL,),(RETURN,POLL),(POLL,RETURN,RETURN),(POLL,b'V920_unknown',RETURN)):
                self.assertFalse(inspect(b'\n'.join((*rows,*tail)),0)[1])
            self.assertFalse(inspect(b'\n'.join((*rows,POLL,RETURN)),126)[1])
if __name__=='__main__':unittest.main()
