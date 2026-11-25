#pragma once
#include "wii_si_binding_v512.h"
#include "v672_private_si_ack_expectations.h"
#include "runtime/hw/hw.h"
#include <cstdlib>
#include <iostream>

namespace undercover::wii::v672 {
using Phase=SiCompletionAckTrace::Phase;
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V672_SI_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return si_completion_ack_trace.phase()!=Phase::Idle;}
[[noreturn]] inline void reject(unsigned reason){
    std::cout<<"V672_SI_ACK_INVALID reason="<<reason<<" trace="<<si_completion_ack_trace.failure()<<std::endl;
    std::_Exit(126);
}
template<class C>bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
template<class C>void begin(C& c){
    using namespace nwii::runtime::hw;
    if(!safe(c)||c.pc!=handler_first||!SiBinding::arm_completion_ack(pi_intsr,pi_intmr,c.inst_count,handler_first,handler_end))reject(1);
    std::cout<<"V672_SI_ACK_STAGE n=1"<<std::endl;
}
// Only authenticated handler labels may advance this witness. A call out
// of this first bounded lane is a new dependency, not a successful ACK.
template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    if(!active())return;
    if(!safe(c)||pc<handler_first||pc>=handler_end||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
       c.mmu.read32(pc)!=word)reject(2);
    if(!si_completion_ack_trace.before(pc,word))reject(3);
    if(si_completion_ack_trace.phase()==Phase::Complete){
        std::cout<<"V672_SI_ACK_STAGE n=2"<<std::endl;
        std::cout<<"V672_SI_ACK_RESULT guest_store=1 tc_w1c=1 pi_deasserted=1 mask_preserved=1 next_label=1 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
    // No unverified helper (including signature-hooked host code) can
    // run before ACK. Report only the position within the authenticated
    // call census, never private addresses, instructions or register data.
    const auto op=word>>26,xo=(word>>1)&1023u;
    const bool linked=(word&1u)&&(op==16u||op==18u||(op==19u&&(xo==16u||xo==528u)));
    if(ordinal||kind||linked){
        if(ordinal<=32u&&ordinal&&kind>=1u&&kind<=2u)
            std::cout<<"V673_SI_ACK_CALL ordinal="<<ordinal<<" kind="<<kind<<std::endl;
        else std::cout<<"V673_SI_ACK_CALL ordinal=0 kind=0"<<std::endl;
        reject(6);
    }
}
template<class C>bool poll(C& c){
    if(!safe(c)||c.pc<handler_first||c.pc>=handler_end||si_completion_ack_trace.phase()!=Phase::Armed)reject(4);
    return false;
}
template<class C>void observe(uint32_t,C&){reject(5);}
}
