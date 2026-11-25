#pragma once
#include "wii_si_handler_return_v725.h"
#include "v726_private_handler_return_expectations.h"
#include "wii_si_completion_ack_v668.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v726 {
inline thread_local SiHandlerReturnWitness witness(expected);
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V726_HANDLER_RETURN");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return witness.stage()>=2;}
inline bool held(){return si_completion_ack_trace.postack_held();}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<"V726_HANDLER_INVALID kind="<<kind<<" witness="<<witness.failure()<<" stage="<<witness.stage()
             <<" visits="<<witness.visits()<<" polls="<<witness.polls()<<std::endl;std::_Exit(126);
}
template<class C>void capture(C& c){if(enabled()&&!witness.capture(c))reject(1);}
template<class C>bool start(C& c,uint32_t pc){
    if(!enabled())return false;
    if(!witness.start(c,pc,held()))reject(2);
    std::cout<<"V726_HANDLER_STAGE n=2"<<std::endl;return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    if(!active())return;
    if(!witness.before(c,pc,w,held())){
        if(witness.failure()==4)std::cout<<"V726_HANDLER_CONTROL ordinal="<<ordinal<<" kind="<<kind<<" opcode="<<(w>>26)<<std::endl;
        reject(3);
    }
    if(witness.stage()==3)std::cout<<"V726_HANDLER_STAGE n=3"<<std::endl;
}
template<class C>bool poll(C& c){
    if(!witness.poll(c,witness.stage()==2?si_completion_ack_trace.native_branch_poll(c.pc):held()))reject(4);
    if(witness.stage()==4)std::cout<<"V726_HANDLER_STAGE n=4"<<std::endl;
    return false;
}
template<class C>void resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!witness.resumed(c,pc,w,held()))reject(5);
    std::cout<<"V726_HANDLER_STAGE n=5"<<std::endl;
    std::cout<<"V726_HANDLER_RESULT returned=1 abi=1 dispatch_resume=1 visits="<<witness.visits()<<" polls="<<witness.polls()<<" rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
}
