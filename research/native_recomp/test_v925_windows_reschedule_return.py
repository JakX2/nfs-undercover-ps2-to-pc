#!/usr/bin/env python3
"""Original-free Windows native no-switch scheduler return regressions."""
import unittest
from test_v924_windows_reschedule_entry import sample as earlier
from windows_reschedule_entry_v924 import RESULT as PREDECESSOR
from windows_reschedule_return_v925 import RESULT,inspect
from prepare_v925_windows_reschedule_return import private_header,patch_binding,patch_ack,patch_resume
from prepare_owner_scheduler_v722 import S
from windows_transfer_prefix_v751 import plan

def sample(changed=True):
    return earlier(changed).rstrip(b'\r\n')+b'\n'+RESULT+b'\n'

class WindowsRescheduleReturn(unittest.TestCase):
    def test_native_return_after_original_no_switch(self):
        for changed in (True,False):
            row,ok=inspect(sample(changed),0)
            self.assertTrue(ok,row)
            self.assertIn('reschedule_entry=1 reschedule_return=1 no_thread_switch=1',row)
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
    def test_exact_native_source(self):
        j=0x80526aa8
        branch=0x48000001|((S-(j+4))&0x03fffffc)
        header=private_header(j,branch,0x60000000,-44)
        self.assertIn('resched_hint_disp=-44',header)
        with self.assertRaises(ValueError):private_header(j,0x60000000,0x60000000,-44)
        base='''#include "v924_private_reschedule_entry.h"
template<class C>void resched_native(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V924_WINDOWS_RESCHEDULE_ENTRY original_handler_return=1 scheduler_return=1 original_reschedule_branch=1 native_entry_tick=1 reschedule_return=0 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''
        out=patch_binding(base)
        self.assertIn('if(resched_return_enabled()){resched_return_arm(c);return;}',out)
        self.assertIn('V925_WINDOWS_RESCHEDULE_RETURN',out)
        with self.assertRaises(ValueError):patch_binding(base.replace('reschedule_return=0','reschedule_return=1'))
        self.assertIn('resched_return_trace(a,c)',patch_ack('if(v868::resched_trace(a,c))return;'))
        with self.assertRaises(ValueError):patch_ack('other')
        src='''void fn_80526A3C(CPUContext& ctx) {
loc_80526AB0: ;
    // 0x80526AB0: 60000000
    ++ctx.inst_count;
    ctx.pc = 0x80526AB4;
}'''
        amended=patch_resume(src,0x80526ab0,0x60000000)
        self.assertEqual(amended.count('resched_return_native('),1)
        with self.assertRaises(ValueError):patch_resume(amended,0x80526ab0,0x60000000)
    def test_same_image_plan_legacy_disabled(self):
        p=plan('os-si-handler-time',False,False,False,handler_return=True)
        self.assertNotIn('UNDERCOVER_V925_RESCHEDULE_RETURN',p.env)
        self.assertEqual(p.observers[-1],('reschedule_return_observer','prepare_v925_windows_reschedule_return.py'))

if __name__=='__main__':unittest.main()
