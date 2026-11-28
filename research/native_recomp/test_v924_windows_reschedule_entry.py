#!/usr/bin/env python3
"""Original-free Windows reschedule entry, admission and exact-source tests."""
import unittest
from test_v923_windows_scheduler_return import sample as earlier
from windows_scheduler_return_v923 import RESULT as PREDECESSOR
from windows_reschedule_entry_v924 import RESULT,inspect,diagnostic
from prepare_v924_windows_reschedule_entry import private_header,patch_binding,patch_native
from prepare_owner_scheduler_v722 import S
from windows_transfer_prefix_v751 import plan

def sample(changed=True):
    return earlier(changed).rstrip(b'\r\n')+b'\n'+RESULT+b'\n'

class WindowsRescheduleEntry(unittest.TestCase):
    def test_native_entry_after_original_return(self):
        for changed in (True,False):
            row,ok=inspect(sample(changed),0)
            self.assertTrue(ok,row)
            self.assertIn('scheduler_return=1 reschedule_entry=1 native_tick=1',row)
    def test_missing_duplicate_trailing_and_reordered_fail(self):
        for raw in (earlier(),sample()+b'trailing\n',sample()+RESULT+b'\n',
                    earlier().replace(PREDECESSOR,b'fake')+RESULT+b'\n',
                    RESULT+b'\n'+earlier(),earlier().rstrip(b'\n')+b'\n'+RESULT+b'\ninvalid\n'):
            self.assertFalse(inspect(raw,0)[1])
    def test_timeout_and_process_failure(self):
        for rc,timeout in ((1,False),(126,False),(0,True),(-1073741819,False)):
            self.assertFalse(inspect(sample(),rc,timeout)[1])
        for bad in ((b'abc',True,False),('text',0,False),(b'abc',0,1),
                    (b'x'*(8*1024*1024+1),0,False)):
            with self.assertRaises(ValueError):inspect(*bad)
    def test_strict_stage_refusal_diagnostics(self):
        for reason in range(1,4):
            self.assertTrue(diagnostic(f'V924_WINDOWS_RESCHEDULE_ENTRY_INVALID reason={reason}'.encode()))
        for suffix in ('reason=0','reason=4','reason=-1','reason=01',
                       'reason=foo','reason=1 pc=0x80000000'):
            self.assertFalse(diagnostic(f'V924_WINDOWS_RESCHEDULE_ENTRY_INVALID {suffix}'.encode()))
        self.assertFalse(diagnostic('V924_WINDOWS_RESCHEDULE_ENTRY_INVALID reason=1'))

    def test_failure_retains_authenticated_predecessor(self):
        for rc in (1,126,-1073741819):
            row,ok=inspect(sample(),rc)
            self.assertFalse(ok)
            self.assertIn('scheduler_return=1',row)
        row,ok=inspect(sample(),0,True)
        self.assertFalse(ok)
        self.assertIn('scheduler_return=0',row)

    def test_exact_native_source(self):
        j=0x80526aa8
        branch=0x48000001|((S-(j+4))&0x03fffffc)
        header=private_header(j,branch,0x60000000)
        self.assertIn('reschedule_branch_word=',header)
        with self.assertRaises(ValueError):private_header(j,0x60000000,0x60000000)
        base='''#include "v923_private_scheduler_return.h"
template<class C>void scheduler_return(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V923_WINDOWS_SCHEDULER_RETURN original_handler_return=1 original_enable=1 disable=1 restore=1 counter=1 abi=1 reschedule_executed=0 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''
        out=patch_binding(base)
        self.assertIn('if(resched_enabled()){resched_arm(c,pc,w);return;}',out)
        self.assertIn('V924_WINDOWS_RESCHEDULE_ENTRY_INVALID reason=',out)
        self.assertIn('V924_WINDOWS_RESCHEDULE_ENTRY',out)
        with self.assertRaises(ValueError):patch_binding(base.replace('original_enable=1','original_enable=0'))
        self.assertIn('resched_trace(uint32_t addr,C& c)',out)
        src='''void fn_80529940(CPUContext& ctx) {
loc_80529940: ;
    // 0x80529940: 60000000
    ++ctx.inst_count;
    ctx.pc = 0x80529944;
}'''
        amended=patch_native(src,S,0x60000000)
        self.assertEqual(amended.count('resched_native('),1)
        self.assertLess(amended.index('resched_trace('),amended.index('++ctx.inst_count;'))
        self.assertLess(amended.index('++ctx.inst_count;'),amended.index('resched_native('))
        with self.assertRaises(ValueError):patch_native(amended,S,0x60000000)
    def test_same_image_plan_legacy_disabled(self):
        p=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertNotIn('UNDERCOVER_V924_RESCHEDULE_ENTRY',p.env)
        self.assertEqual(p.observers[-2],('reschedule_entry_observer','prepare_v924_windows_reschedule_entry.py'))
        self.assertEqual(p.observers[-1],('reschedule_return_observer','prepare_v925_windows_reschedule_return.py'))

if __name__=='__main__':unittest.main()
