#!/usr/bin/env python3
"""Original-free Windows scheduler completion with original disables/restores."""
import unittest
from windows_scheduler_entry_v922 import RESULT as ENTRY
from windows_scheduler_return_v923 import RESULT,inspect,diagnostic
from test_v922_windows_scheduler_entry import sample as earlier
from prepare_v923_windows_scheduler_return import (
    private_header,patch_binding,patch_dependency,patch_dispatcher,patch_device_tick,install)
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
    def test_device_completion_advances_only_on_real_guest_instruction(self):
        # The SI hardware scheduler tick alone does not update the separate
        # post-ACK completion witness. Authentic E/D/R/S labels must do so.
        import inspect as inspection
        source=inspection.getsource(install)
        self.assertIn('for owner in (E,disable,restore,S):',source)
        self.assertIn('for target in (E,disable,restore,S):',source)
        self.assertIn('if target==E and pc==E:',source)
        self.assertIn('owned=patch_device_tick(owned,pc,roots[target][(pc-target)//4])',source)
        pc=0x80004000
        word=0x60000000
        label=f'loc_{pc:X}: ;\n    // 0x{pc:08X}: {word:08X}\n'
        tick='    ++ctx.inst_count;\n'
        device='    undercover::wii::v868::scheduler_device_tick(ctx,0x80004000u,0x60000000u);\n'
        boundary='    ctx.si_instruction_boundary();\n'
        preceding='    undercover::wii::v709::before(ctx,0x80004000u,0x60000000u,1u);\n'
        for prior in ('',preceding):
            original=('void fn_80004000(CPUContext& ctx) {\n'+label+tick+
                      '    ctx.exi_instruction_boundary();\n'+prior+
                      boundary+'    ctx.pc=0x80004004u;\n}')
            changed=patch_device_tick(original,pc,word)
            self.assertEqual(changed.count(device),1)
            self.assertLess(changed.index(boundary),changed.index(device))
            self.assertLess(changed.index(device),changed.index('ctx.pc='))
            self.assertIn(tick,changed)
            with self.assertRaises(ValueError):patch_device_tick(changed,pc,word)
            with self.assertRaises(ValueError):patch_device_tick(
                original.replace(boundary,''),pc,word)
            with self.assertRaises(ValueError):patch_device_tick(
                original.replace(boundary,boundary+boundary),pc,word)
            with self.assertRaises(ValueError):patch_device_tick(
                original.replace(boundary,'    ctx.gpr[3]=0;\n'+boundary),pc,word)

    def test_rfi_composition_retains_tick_handoff_after_original_si_boundary(self):
        from prepare_windows_native_rfi_v926 import patch_label as rfi_patch
        pc=0x80004000
        word=0x60000000
        original=f'''loc_{pc:X}: ;
    // 0x{pc:08X}: {word:08X}
    ++ctx.inst_count;
    ctx.si_instruction_boundary();
    ctx.pc=0x80004004u;
'''
        with_tick=patch_device_tick(original,pc,word)
        with_entry=patch_dependency(with_tick,pc,word)
        final=rfi_patch(with_entry,pc,word,trace='scheduler_return_trace')
        self.assertLess(final.index('scheduler_return_trace('),final.index('++ctx.inst_count;'))
        self.assertLess(final.index('ctx.si_instruction_boundary();'),final.index('v922::before('))
        self.assertLess(final.index('v922::before('),final.index('scheduler_device_tick('))


    def test_complete_native_first_two_labels_preserve_pre_tick_identity(self):
        # The complete-image RFI adapter runs after both original scheduler
        # installers even for an incremental scheduler-entry process. Verify
        # that no later hook moves/removes the first pre-tick V922 gate.
        from prepare_v922_windows_scheduler_entry import patch_scheduler
        from prepare_windows_native_rfi_v926 import patch_label as rfi_patch
        first=0x80004000
        second=first+4
        word=0x9421fff0  # synthetic PPC stwu r1, -16(r1)
        next_word=0x60000000  # synthetic nop
        original=f'''void fn_{first:X}(CPUContext& ctx) {{
loc_{first:X}: ;
    // 0x{first:08X}: {word:08X}
    ++ctx.inst_count;
    ctx.exi_instruction_boundary();
    ctx.si_instruction_boundary();
    ctx.gpr[1]-=16;
loc_{second:X}: ;
    // 0x{second:08X}: {next_word:08X}
    ++ctx.inst_count;
    ctx.exi_instruction_boundary();
    ctx.si_instruction_boundary();
    ctx.pc=0;
}}'''
        with_entry=patch_scheduler(original,first,word)
        with_device=patch_device_tick(with_entry,second,next_word)
        with_rfi_first=rfi_patch(with_device,first,word,
                                 trace='scheduler_trace')
        final=rfi_patch(with_rfi_first,second,next_word)
        left=final.index(f'loc_{first:X}:')
        right=final.index(f'loc_{second:X}:')
        first_body=final[left:right]
        second_body=final[right:]
        self.assertEqual(first_body.count('scheduler_trace('),1)
        self.assertEqual(first_body.count('scheduler_native('),1)
        self.assertEqual(first_body.count('v922::before('),1)
        self.assertLess(first_body.index('scheduler_trace('),
                        first_body.index('++ctx.inst_count;'))
        self.assertLess(first_body.index('++ctx.inst_count;'),
                        first_body.index('scheduler_native('))
        self.assertLess(first_body.index('scheduler_native('),
                        first_body.index('ctx.si_instruction_boundary();'))
        self.assertLess(first_body.index('ctx.si_instruction_boundary();'),
                        first_body.index('v922::before('))
        self.assertEqual(second_body.count('scheduler_device_tick('),1)
        self.assertLess(second_body.index('ctx.si_instruction_boundary();'),
                        second_body.index('v922::before('))
        self.assertLess(second_body.index('v922::before('),
                        second_body.index('scheduler_device_tick('))
        self.assertEqual(final.count('++ctx.inst_count;'),2)

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
        self.assertIn('if(!scheduler_return_enabled()||!scheduler_handoff)return false;',out)
        self.assertIn('if(!scheduler_return_enabled()||!scheduler_handoff)return;',out)
        self.assertIn('!scheduler_pending||!scheduler_traced||',out)
        self.assertIn('c.mmu.read32(pc)!=w||!scheduler_held_after_tick(c))scheduler_return_refusal(6);',out)
        self.assertIn('!v850::held(c))scheduler_return_refusal(5);',out)
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
