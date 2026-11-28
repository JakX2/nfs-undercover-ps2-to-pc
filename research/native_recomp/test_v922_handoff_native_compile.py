#!/usr/bin/env python3
"""Original-free C++ runtime check for authenticated Windows scheduler ownership.

Compile the *actual* V922 installer-produced C++ helpers against a synthetic
CPU. Earlier real OS scheduler calls must not arm/reject; once the original
SI handler has returned, incorrect handoffs must still fail closed. The
pinned emitter does not update ctx.pc at each sequential instruction label;
the positive continuation and independent 19/22-28 refusals check that fact.
"""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from prepare_v922_windows_scheduler_entry import patch_binding

START = '''#include "v920_private_handler_resume.h"
template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){
    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}'''

PRE = r'''
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string_view>
struct Mmu {
    uint8_t memory=0;
    bool unmapped_label=false,corrupt_label=false;
    uint8_t* get_ptr(uint32_t a) {
        if(unmapped_label&&(a==0x80004104u||a==0x80004107u))return nullptr;
        return a==0x80004000u||a==0x80004003u||
               a==0x80004100u||a==0x80004103u||
               a==0x80004104u||a==0x80004107u?&memory:nullptr;
    }
    uint32_t read32(uint32_t a) {
        return a==0x80004000u?0x48000101u:
               a==0x80004100u?0x9421fff0u:
               a==0x80004104u?(corrupt_label?0xDEADBEEFu:0x60000000u):0u;
    }
};
struct Cpu {
    std::array<uint32_t,32> gpr{};
    uint32_t pc=0x80004000u,lr=0x80004000u,msr=0x32u;
    uint64_t inst_count=100u;
    bool is_running=true,in_callback=false,dispatch_saved_ctx=false;
    bool device_held=true,device_advance=true;
    Mmu mmu;
    Cpu(){gpr[1]=0x80002000u;gpr[13]=0x80003000u;}
};
namespace undercover::wii {
namespace v850 {template<class C>bool held(C& c){return c.device_held;}}
namespace v726 {
    struct Witness{unsigned current=5u;unsigned stage()const{return current;}};
    inline Witness witness;
}
namespace v868 {
inline constexpr uint32_t scheduler_call_pc=0x80004000u;
inline constexpr uint32_t scheduler_call_word=0x48000101u;
inline constexpr uint32_t scheduler_entry_pc=0x80004100u;
inline constexpr uint32_t scheduler_entry_word=0x9421fff0u;
inline constexpr int32_t scheduler_frame_delta=-16;
inline thread_local bool scheduler_handoff=false;
inline thread_local bool dispatch_tick_seen=true;
template<class C>bool advance_restore(C& c){return c.device_advance;}
'''

POST = r'''
} // namespace v868
} // namespace undercover::wii
int main(int argc,char** argv){
    if(argc!=2)return 2;
    const std::string_view mode=argv[1];
    namespace v=undercover::wii::v868;
    Cpu c;
    if(mode=="early"||mode=="early-then-handoff"){
        if(v::scheduler_trace(v::scheduler_entry_pc,c))return 3;
        v::scheduler_device_tick(c,v::scheduler_entry_pc,v::scheduler_entry_word);
        v::scheduler_native(c,v::scheduler_entry_pc,v::scheduler_entry_word);
        if(v::scheduler_pending||v::scheduler_traced||v::scheduler_handoff)return 4;
        if(mode=="early"){std::cout<<"V922_EARLY_SCOPE valid=1\n";return 0;}
    }
    if(mode=="bad-handoff"||mode=="bad-trace"||mode=="bad-device-unarmed"){
        v::scheduler_handoff=true;
        if(mode=="bad-handoff")v::scheduler_native(c,v::scheduler_entry_pc,v::scheduler_entry_word);
        if(mode=="bad-trace")v::scheduler_trace(v::scheduler_entry_pc,c);
        if(mode=="bad-device-unarmed")v::scheduler_device_tick(c,v::scheduler_entry_pc,v::scheduler_entry_word);
        return 5;
    }
    if(mode=="valid-stale-pc"||mode=="bad-device-stage"||
       mode=="bad-device-tick"||mode=="bad-device-state"||
       mode=="bad-device-msr"||mode=="bad-device-map"||
       mode=="bad-device-opcode"||mode=="bad-device-held"){
        // Arm the actual V920 handoff and original-entry trace, then
        // exercise the next *sequential* guest label. The pinned emitter
        // leaves ctx.pc at the first branch target across linear PPC code.
        v::dispatcher_resume(c,v::scheduler_call_pc,v::scheduler_call_word);
        v::scheduler_handoff=true;
        c.pc=v::scheduler_entry_pc;
        c.lr=v::scheduler_call_pc+4u;
        if(!v::scheduler_trace(v::scheduler_entry_pc,c))return 11;
        ++c.inst_count;
        if(mode=="bad-device-stage")v::v726::witness.current=4u;
        if(mode=="bad-device-tick")--c.inst_count;
        if(mode=="bad-device-state")c.in_callback=true;
        if(mode=="bad-device-msr")c.msr|=0x8000u;
        if(mode=="bad-device-map")c.mmu.unmapped_label=true;
        if(mode=="bad-device-opcode")c.mmu.corrupt_label=true;
        if(mode=="bad-device-held"){c.device_held=false;c.device_advance=false;}
        v::scheduler_device_tick(c,0x80004104u,0x60000000u);
        if(mode=="valid-stale-pc"){
            if(c.pc!=v::scheduler_entry_pc)return 12;
            std::cout<<"V922_SEQUENTIAL_LABEL native=1 stale_pc_preserved=1\\n";
            return 0;
        }
        return 13;
    }
    if(mode=="early-then-handoff"||mode=="bad-post"){
        v::dispatcher_resume(c,v::scheduler_call_pc,v::scheduler_call_word);
        if(!v::scheduler_pending)return 6;
        v::scheduler_handoff=true; // authenticated V920 observer switch
        c.pc=v::scheduler_entry_pc;
        c.lr=v::scheduler_call_pc+4u;
        if(mode=="bad-post"){
            ++c.inst_count;
            v::scheduler_native(c,v::scheduler_entry_pc,v::scheduler_entry_word);
            return 7;
        }
        if(!v::scheduler_trace(v::scheduler_entry_pc,c))return 8;
        ++c.inst_count;
        v::scheduler_native(c,v::scheduler_entry_pc,v::scheduler_entry_word);
        return 9;
    }
    return 10;
}
'''

class SchedulerHandoffCompiled(unittest.TestCase):
    def test_native_injected_scoping_and_negative_reentry(self):
        cxx=shutil.which('g++')
        if not cxx:
            self.skipTest('GCC unavailable')
        emitted=patch_binding(START)
        for include in ('#include "v920_private_handler_resume.h"',
                        '#include "v922_private_scheduler_entry.h"'):
            self.assertEqual(emitted.count(include),1)
            emitted=emitted.replace(include,'')
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)
            src=p/'scope.cpp'
            exe=p/'scope'
            src.write_text(PRE+emitted+'\n'+POST,encoding='utf-8')
            subprocess.run([cxx,'-std=c++20','-O1','-Wall','-Wextra',
                            '-Werror',str(src),'-o',str(exe)],
                           capture_output=True,text=True,check=True)
            env=os.environ.copy()
            env['UNDERCOVER_V922_SCHEDULER_ENTRY']='1'
            expected={'early':(0,'V922_EARLY_SCOPE valid=1'),
                      'early-then-handoff':(0,'V922_SCHEDULER_ENTRY original_handler_return=1'),
                      'bad-handoff':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=12'),
                      'bad-trace':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=7'),
                      'bad-device-unarmed':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=22'),
                      'bad-device-stage':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=23'),
                      'bad-device-tick':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=24'),
                      'bad-device-state':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=25'),
                      'bad-device-msr':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=26'),
                      'bad-device-map':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=27'),
                      'bad-device-opcode':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=28'),
                      'bad-device-held':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=19'),
                      'valid-stale-pc':(0,'V922_SEQUENTIAL_LABEL native=1 stale_pc_preserved=1'),
                      'bad-post':(126,'V922_WINDOWS_SCHEDULER_INVALID reason=21')}
            for mode,(rc,marker) in expected.items():
                with self.subTest(mode=mode):
                    run=subprocess.run([str(exe),mode],env=env,
                                       capture_output=True,text=True,timeout=10)
                    self.assertEqual(run.returncode,rc,run.stdout+run.stderr)
                    self.assertIn(marker,run.stdout)

if __name__=='__main__':
    unittest.main()
