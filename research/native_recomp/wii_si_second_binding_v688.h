#pragma once
#include "wii_si_helper_binding_v680.h"
#include "v688_private_si_second_expectations.h"
namespace undercover::wii::v688 {
inline thread_local SiFirstHelper second(expected_second);
inline bool continue_after_ack(){
    const char* v=std::getenv("UNDERCOVER_V699_SI_POSTACK");return v&&v[0]=='1'&&v[1]=='\0';
}
[[noreturn]]inline void post_refuse(unsigned n){
    std::cout<<"V699_POSTACK_INVALID reason="<<n<<" trace="<<si_completion_ack_trace.failure()<<std::endl;
    std::_Exit(126);
}
[[noreturn]]inline void reject(){
    std::cout<<"V688_SI_SECOND_INVALID reason="<<second.failure()<<" stage="<<second.stage()<<" trace="<<si_completion_ack_trace.failure()<<std::endl;
    std::_Exit(126);
}
template<class C>bool start(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    if(ordinal!=2||kind!=1||second.stage()||v680::helper.stage()!=4)return false;
    if(!second.start(c,pc,word)||!si_completion_ack_trace.allow_helper(expected_second.root,expected_second.end))reject();
    std::cout<<"V688_SI_SECOND_STAGE n=1"<<std::endl;
    return true;
}
template<class C>bool observe(uint32_t a,C& c){
    if(second.stage()!=1)return false;
    if(!second.entry(a,c))reject();
    std::cout<<"V688_SI_SECOND_STAGE n=2"<<std::endl;return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Idle)return;
    if(!second.instruction(c,pc,word,si_completion_ack_trace,true)){
        if(second.failure()==4&&ordinal&&ordinal<=32&&kind>=1&&kind<=2)
            std::cout<<"V688_SI_SECOND_CALL ordinal="<<ordinal<<" kind="<<kind<<std::endl;
        reject();
    }
    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Complete){
        std::cout<<"V688_SI_SECOND_ACK n=1"<<std::endl;
        std::cout<<"V672_SI_ACK_STAGE n=2"<<std::endl;
        std::cout<<"V672_SI_ACK_RESULT guest_store=1 tc_w1c=1 pi_deasserted=1 mask_preserved=1 next_label=1 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        if(!continue_after_ack())std::_Exit(0);
        // Completion was at the immediate successor, not after executing
        // it. Do not bypass any branch/exception or ABI-return guard.
        const auto op=word>>26,xo=(word>>1)&1023u;
        if(op==16u||op==17u||op==18u||op==19u||(op==31u&&xo==146u))post_refuse(1);
        if(!si_completion_ack_trace.resume_after_ack(pc,word))post_refuse(2);
        std::cout<<"V699_POSTACK_STAGE n=1"<<std::endl;
    }
}
template<class C>void handler_boundary(C& c,uint32_t pc){
    if(second.stage()>=1&&second.stage()<=3){
        if(!second.returned(c,pc))reject();
        std::cout<<"V688_SI_SECOND_STAGE n=3"<<std::endl;
        if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::PostAck){
            std::cout<<"V699_POSTACK_RESULT second_return=1 abi=1 original_ack=1 rfi_return=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
    }
}
}
