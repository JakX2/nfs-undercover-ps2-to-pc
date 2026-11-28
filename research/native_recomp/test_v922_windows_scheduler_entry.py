#!/usr/bin/env python3
"""Original-free regressions for native Windows scheduler handoff."""
import unittest
from audit_v920_handler_return import RETURN as HANDLER_RETURN
from test_v763_windows_handler_return import sample as handler_sample
from windows_scheduler_entry_v922 import RESULT,inspect,diagnostic
from prepare_v922_windows_scheduler_entry import patch_binding,patch_scheduler,patch_post_handler_observers
from windows_transfer_prefix_v751 import plan

def sample(changed=True):
    return handler_sample(changed).rstrip(b'\r\n')+b'\n'+RESULT+b'\n'

class WindowsSchedulerEntry(unittest.TestCase):
    def test_handler_to_native_scheduler(self):
        for changed in (True,False):
            with self.subTest(changed=changed):
                row,ok=inspect(sample(changed),0)
                self.assertTrue(ok,row)
                self.assertIn('handler_return=1 scheduler_entry=1 native_tick=1',row)

    def test_missing_duplicate_reordered_and_trailing_marker_refused(self):
        for raw in (handler_sample(),handler_sample()+b'unknown data\n',
                    sample()+b'unknown\n',sample()+RESULT+b'\n',
                    handler_sample().replace(HANDLER_RETURN,b'invalid')+RESULT+b'\n',
                    RESULT+b'\n'+handler_sample()):
            with self.subTest(tail=raw[-70:]):
                self.assertFalse(inspect(raw,0)[1])

    def test_fail_closed_errors(self):
        for rc,timeout in ((1,False),(126,False),(0,True),(-1073741819,False)):
            self.assertFalse(inspect(sample(),rc,timeout)[1])
        for args in ((b'abc',True,False),('text',0,False),(b'abc',0,1),(b'x'*(8*1024*1024+1),0,False)):
            with self.assertRaises(ValueError):inspect(*args)

    def test_bounded_original_scheduler_refusal_diagnostics(self):
        for i in range(1,18):
            self.assertTrue(diagnostic(f'V922_WINDOWS_SCHEDULER_INVALID reason={i}'.encode()))
        for invalid in (b'V922_WINDOWS_SCHEDULER_INVALID reason=0',
                        b'V922_WINDOWS_SCHEDULER_INVALID reason=18',
                        b'V922_WINDOWS_SCHEDULER_INVALID reason=1 address=0x80000000',
                        b'V922_WINDOWS_SCHEDULER_INVALID reason=-1',
                        b'V922_WINDOWS_SCHEDULER_INVALID reason=0001',
                        b'V922_WINDOWS_SCHEDULER_INVALID reason=foo'):
            self.assertFalse(diagnostic(invalid))
        self.assertFalse(diagnostic('V922_WINDOWS_SCHEDULER_INVALID reason=1'))

    def test_failure_retains_authenticated_predecessor(self):
        for rc in (1,126,-1073741819):
            row,ok=inspect(sample(),rc)
            self.assertFalse(ok)
            self.assertIn('handler_return=1',row)
        row,ok=inspect(sample(),0,True)
        self.assertFalse(ok)
        self.assertIn('handler_return=0',row)

    def test_binding_does_not_change_default_handler_stop(self):
        a='''#include "v920_private_handler_resume.h"
template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''
        out=patch_binding(a)
        self.assertIn('if(scheduler_enabled()){scheduler_start(c,pc,w);return;}',out)
        self.assertIn('V922_SCHEDULER_ENTRY',out)
        with self.assertRaises(ValueError):patch_binding(a.replace('original_blr=1','original_blr=0'))
        self.assertIn('scheduler_trace(uint32_t addr,C& c)',out)
        self.assertIn('V922_WINDOWS_SCHEDULER_INVALID reason=',out)
        self.assertEqual(out.count('scheduler_refusal('),18)
        self.assertIn('std::_Exit(126);',out)


    def test_completed_handler_observers_are_scoped_at_scheduler_call(self):
        from pathlib import Path
        from prepare_v919_handler_epilogue import patch_binding as epilogue
        from prepare_v920_handler_return import patch_binding as handler_return
        source=(Path(__file__).parent/'wii_handler_suffix_binding_v868.h').read_text(encoding='utf-8')
        out=patch_post_handler_observers(patch_binding(handler_return(epilogue(source))))
        self.assertEqual(out.count('inline thread_local bool scheduler_handoff=false;'),1)
        self.assertEqual(out.count('scheduler_handoff=true;'),1)
        self.assertIn('scheduler_pending=true;scheduler_handoff=true;',out)
        self.assertIn('if(scheduler_enabled()){scheduler_start(c,pc,w);return;}',out)
        self.assertIn('if(v726::witness.stage()!=5u||!v850::held(c))reject(6);',out)
        self.assertIn('if(v726::witness.stage()!=5u||!v850::held(c))reject(5);',out)
        self.assertEqual(out.count('if(scheduler_handoff){'),2)
        self.assertIn('if(!restore_enabled()||restore.stage()!=1u',out)
        self.assertIn('if(!v850::held(c)||!v726::witness.poll(c,true))reject(5);',out)
        self.assertLess(out.index('if(scheduler_pending||scheduler_traced)scheduler_refusal(1);'),
                        out.index('scheduler_handoff=true;'))
        with self.assertRaises(ValueError):
            patch_post_handler_observers(out)
        with self.assertRaises(ValueError):
            patch_post_handler_observers(out.replace('scheduler_handoff=true;', 'scheduler_handoff=false;'))
        with self.assertRaises(ValueError):
            patch_post_handler_observers(out.replace('if(scheduler_handoff){','if(true){',1))

    def test_native_first_instruction_hook_and_opt_in_plan(self):
        p=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertNotIn('UNDERCOVER_V922_SCHEDULER_ENTRY',p.env)
        self.assertNotIn('UNDERCOVER_V923_SCHEDULER_RETURN',p.env)
        self.assertEqual(p.observers[-3][1],'prepare_v923_windows_scheduler_return.py')
        self.assertEqual(p.observers[-2][1],'prepare_v924_windows_reschedule_entry.py')
        self.assertEqual(p.observers[-1][1],'prepare_v925_windows_reschedule_return.py')
        src='''void fn_80529434(CPUContext& ctx) {
loc_80529434: ;
    // 0x80529434: 60000000
    ++ctx.inst_count;
    ctx.pc = 0x80529438;
}'''
        out=patch_scheduler(src,0x80529434,0x60000000)
        self.assertEqual(out.count('scheduler_native('),1)
        self.assertEqual(out.count('scheduler_trace('),1)
        self.assertLess(out.index('scheduler_trace('),out.index('++ctx.inst_count;'))
        self.assertLess(out.index('++ctx.inst_count;'),out.index('scheduler_native('))
        with self.assertRaises(ValueError):patch_scheduler(out,0x80529434,0x60000000)

if __name__=='__main__':unittest.main()
