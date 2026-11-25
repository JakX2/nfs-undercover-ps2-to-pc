#pragma once
#include "wii_postack_os_leaf_v703.h"
#include "v709_private_os_leaf_expectations.h"
#include "wii_si_completion_ack_v668.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v709 {
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V709_OS_LEAVES");return v&&v[0]=='1'&&v[1]=='\0';
}
inline thread_local std::array<PostAckOsLeaf,3> leaves{
    PostAckOsLeaf(expected_leaves[0]),PostAckOsLeaf(expected_leaves[1]),PostAckOsLeaf(expected_leaves[2])};
inline thread_local unsigned cursor=0;
inline thread_local bool active=false;
[[noreturn]]inline void reject(unsigned reason){
    std::cout<<"V709_OS_LEAF_INVALID reason="<<reason<<" ordinal="<<cursor+1
             <<" witness="<<(cursor<3?leaves[cursor].failure():0)<<" trace="<<si_completion_ack_trace.failure()<<std::endl;
    std::_Exit(126);
}
inline void event(unsigned stage){
    std::cout<<"V709_OS_LEAF_STAGE ordinal="<<cursor+1<<" n="<<stage<<std::endl;
}
inline bool eligible(uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    return enabled()&&si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::PostAck&&
        !active&&cursor<3&&ordinal==cursor+1&&kind==1&&
        pc==expected_leaves[cursor].site&&word==expected_leaves[cursor].branch;
}
template<class C>void start(C& c,uint32_t pc,uint32_t word){
    if(active||cursor>=3||!leaves[cursor].start(c,pc,word))reject(1);
    active=true;event(1);
}
template<class C>bool observe(uint32_t a,C& c){
    if(!active)return false;
    if(cursor>=3||!leaves[cursor].entry(a,c))reject(2);
    event(2);return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t word,unsigned ordinal){
    // These original OS roots are also called before this lane begins.
    if(!active)return;
    if(cursor>=3||ordinal!=cursor+1||!si_completion_ack_trace.auxiliary_before()||
       !leaves[cursor].before(c,pc,word))reject(3);
}
template<class C>void boundary(C& c,uint32_t pc){
    if(!active)return;
    if(cursor>=3||!leaves[cursor].returned(c,pc))reject(4);
    event(3);++cursor;active=false;
}
inline void complete(){
    if(enabled()&&si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::PostAck&&
       (active||cursor!=3))reject(5);
}
}
