import unittest
from pathlib import Path
from unittest.mock import patch
from prepare_v767_live_epilogue import patch_entry,patch_handler,patch_label
from prepare_v751_cold_capture import patch as cap
from prepare_v667_si_dispatch import patch_binding
from prepare_v756_combined_handler import combine
from audit_v767_live_epilogue import inspect,STAGES
class Epilogue(unittest.TestCase):
    def test_hooks(self):
        host=Path(__file__).parent
        e=patch_entry(patch_binding(cap((host/'wii_external_entry_binding_v663.h').read_text())))
        self.assertLess(e.index('if(v767::active())return'),e.index('if(v667::route.stage())return'))
        self.assertIn('v767::attach(capture.witness());',e)
        h=patch_handler(combine((host/'wii_si_handler_return_binding_v726.h').read_text()))
        self.assertIn('if(v767::begin(c,pc,w))return;',h)
        with self.assertRaises(ValueError):patch_handler(h)
    def test_label(self):
        src='loc_80004000: ;\n    // 0x80004000: 60000000\n    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80004000, ctx); // V616 native IRQ resume\n    ++ctx.inst_count;\n'
        s=patch_label(src,0x80004000,0x60000000,True)
        self.assertTrue(s.endswith('    undercover::wii::v767::resume(ctx,0x80004000u,0x60000000u);\n'))
        with self.assertRaises(ValueError):patch_label(src,0x80004000,0x60000000,False)
    def test_audit(self):
        base=[b'V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits=32 polls=0 rfi_return=0 boot_verified=0']
        end=b'V767_EPILOGUE_RESULT live_context=1 scheduler=1 native_rfi=1 original_resume=1 visits=70 resumed_instruction_executed=0 boot_verified=0'
        with patch('audit_v767_live_epilogue.captured',return_value=('','',True)):
            self.assertTrue(inspect(b'\n'.join(base+STAGES+[end]),0)[1])
            for rows in (base+STAGES[:-1]+[end],STAGES+base+[end],base+STAGES+[end,end],base+STAGES+[end.replace(b'visits=70',b'visits=0')]):
                self.assertFalse(inspect(b'\n'.join(rows),0)[1])
            self.assertFalse(inspect(b'\n'.join(base+STAGES+[end]),126)[1])
if __name__=='__main__':unittest.main()
