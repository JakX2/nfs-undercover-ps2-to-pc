#pragma once
#include "wii_si_helper_binding_v680.h"
#include "v693_private_si_nested_expectations.h"
namespace undercover::wii::v693 {
inline thread_local SiFirstHelper nested(expected_nested);
[[noreturn]]inline void reject(){
    std::cout<<"V693_SI_NESTED_INVALID reason="<<nested.failure()<<" stage="<<nested.stage()<<" trace="<<si_completion_ack_trace.failure()<<std::endl;
    std::_Exit(126);
}
inline bool eligible(uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    return ordinal==1&&kind==1&&nested.stage()==0&&pc==expected_nested.site&&word==expected_nested.branch;
}
template<class C>void start(C& c,uint32_t pc,uint32_t word){
    if(!nested.start(c,pc,word)||!si_completion_ack_trace.allow_nested(expected_nested.root,expected_nested.end))reject();
    std::cout<<"V693_SI_NESTED_STAGE n=1"<<std::endl;
}
template<class C>bool observe(uint32_t a,C& c){
    if(nested.stage()!=1)return false;
    if(!nested.entry(a,c))reject();
    std::cout<<"V693_SI_NESTED_STAGE n=2"<<std::endl;return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Idle)return;
    if(!nested.instruction(c,pc,word,si_completion_ack_trace,true)){
        if(nested.failure()==4&&ordinal&&ordinal<=32&&kind>=1&&kind<=2)
            std::cout<<"V693_SI_NESTED_CALL ordinal="<<ordinal<<" kind="<<kind<<std::endl;
        reject();
    }
    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Complete){
        std::cout<<"V693_SI_NESTED_ACK n=1"<<std::endl;
        std::cout<<"V672_SI_ACK_STAGE n=2"<<std::endl;
        std::cout<<"V672_SI_ACK_RESULT guest_store=1 tc_w1c=1 pi_deasserted=1 mask_preserved=1 next_label=1 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
template<class C>void boundary(C& c,uint32_t pc){
    if(nested.stage()>=1&&nested.stage()<=3){
        if(!nested.returned(c,pc))reject();
        std::cout<<"V693_SI_NESTED_STAGE n=3"<<std::endl;
    }
}
}
