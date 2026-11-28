#!/usr/bin/env python3
"""Original-free regressions for native Windows scheduler handoff."""
import unittest
from audit_v920_handler_return import RETURN as HANDLER_RETURN
from test_v763_windows_handler_return import sample as handler_sample
from windows_scheduler_entry_v922 import RESULT,inspect
from prepare_v922_windows_scheduler_entry import patch_binding,patch_ack,patch_scheduler
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
        self.assertIn('scheduler_trace(a,c)',patch_ack('if(v868::active()){v868::observe(a,c);return;}'))
        with self.assertRaises(ValueError):patch_ack('invalid')

    def test_native_first_instruction_hook_and_opt_in_plan(self):
        p=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertNotIn('UNDERCOVER_V922_SCHEDULER_ENTRY',p.env)
        self.assertNotIn('UNDERCOVER_V923_SCHEDULER_RETURN',p.env)
        self.assertEqual(p.observers[-1][1],'prepare_v923_windows_scheduler_return.py')
        src='''void fn_80529434(CPUContext& ctx) {
loc_80529434: ;
    // 0x80529434: 60000000
    ++ctx.inst_count;
    ctx.pc = 0x80529438;
}'''
        out=patch_scheduler(src,0x80529434,0x60000000)
        self.assertEqual(out.count('scheduler_native('),1)
        with self.assertRaises(ValueError):patch_scheduler(out,0x80529434,0x60000000)

if __name__=='__main__':unittest.main()
