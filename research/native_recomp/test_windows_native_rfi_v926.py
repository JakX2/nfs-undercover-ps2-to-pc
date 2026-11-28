#!/usr/bin/env python3
"""Original-free Windows native RFI adapter: fail-closed routing seams."""
import unittest
from pathlib import Path
from prepare_windows_native_rfi_v926 import patch_return,patch_entry,patch_label
from prepare_windows_rfi_context_bridge import patch_handler,patch_external
from prepare_v667_si_dispatch import patch_binding as patch_dispatcher
from prepare_v922_windows_scheduler_entry import patch_binding as patch_scheduler_entry
from prepare_v923_windows_scheduler_return import patch_binding as patch_scheduler_return
from prepare_v924_windows_reschedule_entry import patch_binding as patch_reschedule_entry
from prepare_v925_windows_reschedule_return import patch_binding as patch_reschedule_return

HERE=Path(__file__).resolve().parent
BASE='''#include "v920_private_handler_resume.h"
template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''

class WindowsNativeRfi(unittest.TestCase):
    def binding(self):
        # Actual installer composition order from full-image Windows runner.
        s=patch_scheduler_entry(BASE)
        s=patch_scheduler_return(s)
        s=patch_reschedule_entry(s)
        s=patch_reschedule_return(s)
        s=patch_handler(s)
        return s

    def test_handler_join_before_original_rfi_route(self):
        s=patch_return(self.binding())
        self.assertIn('UNDERCOVER_V926_WINDOWS_RFI',s)
        self.assertIn('if(windows_context_bridge_enabled())',s)
        self.assertIn('!v921::join.captured()',s)
        self.assertIn('v922::begin(c,pc,w);',s)
        self.assertLess(s.index('WINDOWS_RFI_CONTEXT_JOIN'),s.index('if(windows_rfi_enabled()){'))
        self.assertLess(s.index('if(windows_rfi_enabled()){'),
                        s.index('if(scheduler_enabled()){scheduler_start(c,pc,w);return;}'))
        self.assertEqual(s.count('#include "wii_live_irq_return_binding_v922.h"'),1)
        with self.assertRaises(ValueError):patch_return(s)

    def test_unjoined_or_unverified_windows_binding_refused(self):
        s=self.binding()
        for bad in (s.replace('WINDOWS_RFI_CONTEXT_JOIN','FORGED_CONTEXT_JOIN'),
                    s.replace('if(scheduler_enabled()){scheduler_start(c,pc,w);return;}',''),
                    s.replace('#include "wii_saved_context_join_v921.h"',''),
                    s.replace('template<class C>void dispatcher_resume','template<class C>void wrong')):
            with self.subTest(bad=bad[-80:]),self.assertRaises(ValueError):
                patch_return(bad)

    def test_original_external_poll_and_dispatch_entry_precedence(self):
        old=(HERE/'wii_external_entry_binding_v663.h').read_text(encoding='utf-8')
        current=patch_external(patch_dispatcher(old))
        new=patch_entry(current)
        self.assertLess(new.index('v922::poll(c)'),new.index('v667::poll(c)'))
        self.assertLess(new.index('v922::observe(a,c)'),new.index('v667::observe(a,c)'))
        self.assertIn('v921::join.attach(c,capture.witness()',new)
        self.assertEqual(new.count('wii_live_irq_return_binding_v922.h'),1)
        with self.assertRaises(ValueError):patch_entry(new)

    def test_authenticated_guest_label_never_skips_original_instruction(self):
        pc=0x80010000;word=0x60000000
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n    ++ctx.inst_count;\n'
        si='    ctx.si_instruction_boundary();\n'
        result=patch_label(label+si,pc,word)
        self.assertLess(result.index('++ctx.inst_count;'),result.index(si))
        self.assertLess(result.index(si),result.index('v922::before('))
        self.assertEqual(result.count('v922::before('),1)
        with self.assertRaises(ValueError):patch_label(label,pc,word)

if __name__=='__main__':unittest.main()
