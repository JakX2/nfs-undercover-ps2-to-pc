#!/usr/bin/env python3
"""Original-free Windows scheduler completion with original disables/restores."""
import unittest
from windows_scheduler_entry_v922 import RESULT as ENTRY
from windows_scheduler_return_v923 import RESULT,inspect,diagnostic
from test_v922_windows_scheduler_entry import sample as earlier
from prepare_v923_windows_scheduler_return import (
    private_header,patch_binding,patch_dependency,patch_dispatcher)
from prepare_owner_scheduler_v722 import E,S
from windows_transfer_prefix_v751 import plan

def sample(changed=True):
    return earlier(changed).rstrip(b'\r\n')+b'\n'+RESULT+b'\n'

class WindowsSchedulerReturn(unittest.TestCase):
    def test_strict_changed_and_unchanged_original_routes(self):
        for changed in (True,False):
            row,ok=inspect(sample(changed),0)
            self.assertTrue(ok,row)
            self.assertIn('scheduler_entry=1 scheduler_return=1 disable_restore=1',row)
    def test_unverified_predecessor_and_duplicate_terminal_refused(self):
        for raw in (earlier(),sample()+b'trailing\n',sample()+RESULT+b'\n',
                    earlier().replace(ENTRY,b'not original')+RESULT+b'\n',
                    RESULT+b'\n'+earlier(),earlier().rstrip(b'\n')+b'\n' +RESULT+b'\nwrong\n'):
            self.assertFalse(inspect(raw,0)[1])
    def test_exceptions_timeout_and_contract_refused(self):
        for rc,timeout in ((1,False),(126,False),(0,True),(-1073741819,False)):
            self.assertFalse(inspect(sample(),rc,timeout)[1])
        for args in ((b'abc',True,False),('text',0,False),(b'abc',0,1),(b'x'*(8*1024*1024+1),0,False)):
            with self.assertRaises(ValueError):inspect(*args)
    def test_strict_stage_refusal_diagnostics(self):
        for reason in range(1,8):
            self.assertTrue(diagnostic(f'V923_WINDOWS_SCHEDULER_RETURN_INVALID reason={reason}'.encode()))
        for suffix in ('reason=0','reason=8','reason=-1','reason=01',
                       'reason=foo','reason=1 pc=0x80000000'):
            self.assertFalse(diagnostic(f'V923_WINDOWS_SCHEDULER_RETURN_INVALID {suffix}'.encode()))
        self.assertFalse(diagnostic('V923_WINDOWS_SCHEDULER_RETURN_INVALID reason=1'))

    def test_failure_retains_authenticated_predecessor(self):
        for rc in (1,126,-1073741819):
            row,ok=inspect(sample(),rc)
            self.assertFalse(ok)
            self.assertIn('scheduler_entry=1',row)
        row,ok=inspect(sample(),0,True)
        self.assertFalse(ok)
        self.assertIn('scheduler_entry=0',row)

    def test_exact_private_original_call_contract(self):
        j=0x80526ca8
        d,r=0x805265ac,0x805265d4
        # Synthetic direct BL word, not original private executable bytes.
        branch=0x48000001|((S-(j+4))&0x03fffffc)
        calls=[(E+0x10,d),(E+0x20,r)]
        header=private_header(j,branch,d,r,calls,-32)
        self.assertIn('scheduler_counter_disp=-32',header)
        self.assertIn('scheduler_restore_lr=',header)
        with self.assertRaises(ValueError):
            private_header(j,0x60000000,d,r,calls,-32)
        with self.assertRaises(ValueError):
            private_header(j,branch,d,r,[(E+0x10,r),(E+0x20,d)],-32)
    def test_default_disabled_source_hooks(self):
        p=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertNotIn('UNDERCOVER_V923_SCHEDULER_RETURN',p.env)
        self.assertEqual(p.observers[-3][1],'prepare_v923_windows_scheduler_return.py')
        self.assertEqual(p.observers[-2][1],'prepare_v924_windows_reschedule_entry.py')
        self.assertEqual(p.observers[-1][1],'prepare_v925_windows_reschedule_return.py')
        base='''#include "v922_private_scheduler_entry.h"
template<class C>void scheduler_native(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V922_SCHEDULER_ENTRY original_handler_return=1 original_dispatcher_branch=1 original_scheduler_entry=1 native_tick=1 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''
        out=patch_binding(base)
        self.assertIn('if(scheduler_return_enabled()){scheduler_return_arm(c);return;}',out)
        self.assertIn('V923_WINDOWS_SCHEDULER_RETURN_INVALID reason=',out)
        self.assertIn('V923_WINDOWS_SCHEDULER_RETURN',out)
        self.assertIn('c.msr!=scheduler_msr||c.gpr[1]!=scheduler_frame_stack||',out)
        self.assertIn('c.gpr[1]!=scheduler_stack||c.gpr[2]!=scheduler_r2||',out)
        with self.assertRaises(ValueError):patch_binding(base.replace('original_scheduler_entry=1','original_scheduler_entry=0'))
        dep='''void fn_805265AC(CPUContext& ctx) {
loc_805265AC: ;
    // 0x805265AC: 60000000
    ++ctx.inst_count;
    ctx.pc = 0x805265B0;
}'''
        bound=patch_dependency(dep,0x805265ac,0x60000000)
        self.assertLess(bound.index('scheduler_return_trace('),bound.index('++ctx.inst_count;'))
        with self.assertRaises(ValueError):patch_dependency(bound,0x805265ac,0x60000000)
        src='''void fn_80526A3C(CPUContext& ctx) {
loc_80526AAC: ;
    // 0x80526AAC: 60000000
    ++ctx.inst_count;
    ctx.pc = 0x80526AB0;
}'''
        changed=patch_dispatcher(src,0x80526aac,0x60000000)
        self.assertEqual(changed.count('scheduler_return(ctx'),1)
        with self.assertRaises(ValueError):patch_dispatcher(changed,0x80526aac,0x60000000)

if __name__=='__main__':unittest.main()
