#!/usr/bin/env python3
"""Original-free Windows scheduler completion with original disables/restores."""
import unittest
from windows_scheduler_entry_v922 import RESULT as ENTRY
from windows_scheduler_return_v923 import RESULT,inspect
from test_v922_windows_scheduler_entry import sample as earlier
from prepare_v923_windows_scheduler_return import (
    private_header,patch_binding,patch_ack,patch_dispatcher)
from prepare_owner_scheduler_v722 import E,S,D,R

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
    def test_exact_private_original_call_contract(self):
        j=0x80526ca8
        # The synthetic roots here contain only test words, never owner code.
        for calls in ([(j+0x40,D),(j+0x50,R)],):
            header=private_header(j,0x48000001,S if False else D,R,calls,-32) if False else None
        with self.assertRaises(ValueError):
            private_header(j,0x60000000,D,R,[(j+0x40,D),(j+0x50,R)],-32)
        with self.assertRaises(ValueError):
            private_header(j,0x48000001,D,R,[(j+0x40,R),(j+0x50,D)],-32)
    def test_default_disabled_source_hooks(self):
        base='''#include "v922_private_scheduler_entry.h"
template<class C>void scheduler_native(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V922_SCHEDULER_ENTRY original_handler_return=1 original_dispatcher_branch=1 original_scheduler_entry=1 native_tick=1 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''
        out=patch_binding(base)
        self.assertIn('if(scheduler_return_enabled()){scheduler_return_arm(c);return;}',out)
        self.assertIn('V923_WINDOWS_SCHEDULER_RETURN',out)
        with self.assertRaises(ValueError):patch_binding(base.replace('original_scheduler_entry=1','original_scheduler_entry=0'))
        self.assertIn('scheduler_return_trace(a,c)',patch_ack('if(v868::scheduler_trace(a,c))return;'))
        with self.assertRaises(ValueError):patch_ack('wrong')
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
