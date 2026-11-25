#pragma once
#include "v777_private_transfer_return.h"
#include "wii_si_binding_v512.h"
#include "runtime/hw/hw.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v768 {
inline thread_local TransferReturnWitness route(expected);
inline bool active(){return route.stage()!=0;}
inline bool eligible(uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    const char* v=std::getenv("UNDERCOVER_V777_TRANSFER_RETURN");
    return v&&v[0]=='1'&&v[1]=='\0'&&!active()&&pc==expected.site&&w==expected.branch&&ordinal==4&&kind==1;
}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V777_TRANSFER_INVALID kind="<<kind<<" reason="<<route.failure()<<" stage="<<route.stage()
             <<" visits="<<route.visits()<<" device="<<si_transfer_device.failure()<<" follow="<<si_transfer_device.follow_failure()
             <<" trace="<<si_completion_ack_trace.failure()<<std::endl;std::_Exit(126);
}
template<class C>void start(C& c,uint32_t pc,uint32_t w){
    if(!route.start(c,pc,w,si_completion_ack_trace))reject(1);
    std::cout<<std::dec<<"V768_TRANSFER_ENTRY channel="<<route.channel()<<" type="<<unsigned(route.type())<<" idle="<<unsigned(route.idle())<<std::endl;
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    if(!route.entry(c,pc,si_completion_ack_trace,si_transfer_device))reject(2);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(active()&&!route.before(c,pc,w,si_completion_ack_trace,si_transfer_device))reject(3);
}
template<class C>void save_before(C& c,uint32_t pc,uint32_t w){
    if(active()&&!route.save_before(c,pc,w,si_completion_ack_trace,si_transfer_device))reject(4);
}
template<class C>void restore_before(C& c,uint32_t pc,uint32_t w){
    if(active()&&!route.restore_before(c,pc,w,si_completion_ack_trace,si_transfer_device))reject(4);
}
template<class C>void disable_before(C& c,uint32_t pc,uint32_t w,unsigned ordinal){
    if(!active())reject(5);
    if(ordinal==1){
        if(!route.disable_before(c,pc,w,si_completion_ack_trace,si_transfer_device))reject(5);
        if(route.handoff_due()){
            using namespace nwii::runtime::hw;
            if(!SiBinding::begin_transfer_device(pi_intsr,pi_intmr,c.inst_count,route.channel(),route.idle()))reject(5);
            std::cout<<"V777_TRANSFER_HANDOFF scheduler_tick=1 ack_identity=1"<<std::endl;
        }
    }else if(ordinal!=3||!route.irq_before(c,pc,w,si_completion_ack_trace,si_transfer_device))reject(5);
}
template<class C>bool poll(C& c){if(!route.poll(c,si_completion_ack_trace,si_transfer_device))reject(6);return false;}
template<class C>void handler_return(C& c,uint32_t pc,uint32_t w){
    if(!route.returned(c,pc,w,si_completion_ack_trace,si_transfer_device))reject(7);
    std::cout<<std::dec<<"V777_TRANSFER_RESULT original_return=1 abi=1 irq_restore=1 compiler_restore=1 idle="<<route.idle()
        <<" irq_lane="<<route.irq_lane()+1u<<" reads="<<si_transfer_device.reads()<<" writes="<<si_transfer_device.writes()
        <<" follow="<<si_transfer_device.follow_stage()<<" pending="<<si_transfer_device.pending()
        <<" total="<<route.total()<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
}
