#pragma once
#include "wii_si_first_helper_v680.h"
#include "wii_postack_os_leaf_v703.h"
namespace undercover::wii {
// Separate second invocation of the same authenticated system-time root.
// The original 25-word helper is linear except for its three direct calls.
class SiHandlerTime{
public:
    SiHandlerTime(SiHelperExpectation e,std::array<PostAckLeafExpectation,3> leaves)
        :e_(e),expected_(leaves),helper_(e),leaves_{PostAckOsLeaf(leaves[0]),PostAckOsLeaf(leaves[1]),PostAckOsLeaf(leaves[2])}{}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned cursor()const{return cursor_;}
    unsigned visits()const{return visits_;}
    unsigned total()const{return total_;}
    unsigned leaf_failure()const{return cursor_<3?leaves_[cursor_].failure():0;}
    unsigned leaf_stage()const{return cursor_<3?leaves_[cursor_].stage():0;}
    bool active()const{return stage_>=1&&stage_<=3;}
    bool leaf_active()const{return leaf_active_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack){
        if(stage_||error_||!ack.postack_held()||!helper_.start(c,pc,w)||
           !c.is_running||c.in_callback||c.dispatch_saved_ctx||(c.msr&0x8000u)||
           e_.end<=e_.root||e_.end-e_.root>128u||c.inst_count>UINT64_MAX-128u)return fail(1);
        tick_=c.inst_count;next_=e_.root;stage_=1;return true;
    }
    template<class C>bool entry(uint32_t pc,C& c,SiCompletionAckTrace& ack){
        if(!ack.postack_held())return fail(2);
        if(leaf_active_){
            if(cursor_>=3||!leaves_[cursor_].entry(pc,c))return fail(2);
            return true;
        }
        if(stage_!=1||c.inst_count!=tick_||!helper_.entry(pc,c))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind,SiCompletionAckTrace& ack){
        if(stage_!=2||pc!=next_||!ack.postack_held()||c.inst_count-tick_>128u)return fail(3);
        if(leaf_active_){
            if(cursor_>=3||!leaves_[cursor_].returned(c,pc))return fail(4);
            ++cursor_;leaf_active_=false;
        }
        const bool allow=cursor_<3&&ordinal==cursor_+1&&kind==1&&
            pc==expected_[cursor_].site&&w==expected_[cursor_].branch;
        const auto op=w>>26;
        if((op==16u||op==18u)&&!allow)return fail(5);
        if((ordinal||kind)&&!allow)return fail(5);
        if(!helper_.instruction(c,pc,w,ack,false,allow))return fail(5);
        if(++visits_>(e_.end-e_.root)/4u)return fail(5);
        next_=pc+4u;
        if(allow){
            if(!leaves_[cursor_].start(c,pc,w))return fail(4);
            leaf_active_=true;return true;
        }
        if(w==0x4e800020u){
            if(cursor_!=3||next_!=e_.end||visits_!=(e_.end-e_.root)/4u)return fail(5);
            last_=c.inst_count;stage_=3;
        }
        return true;
    }
    template<class C>bool leaf_before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,SiCompletionAckTrace& ack){
        if(stage_!=2||!leaf_active_||cursor_>=3||ordinal!=cursor_+1||
           !ack.auxiliary_before()||!leaves_[cursor_].before(c,pc,w))return fail(6);
        return true;
    }
    template<class C>bool poll(C& c,SiCompletionAckTrace& ack){
        if(stage_!=2||!leaf_active_||cursor_!=1||!ack.auxiliary_poll()||!leaves_[cursor_].poll(c))return fail(7);
        return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,SiCompletionAckTrace& ack){
        if(stage_!=3||leaf_active_||cursor_!=3||!ack.postack_held()||
           c.inst_count-last_!=1u||c.inst_count-tick_>129u||!helper_.returned(c,pc))return fail(8);
        total_=unsigned(c.inst_count-tick_-1u);
        if(total_!=visits_+leaves_[0].visits()+leaves_[1].visits()+leaves_[2].visits())return fail(8);
        stage_=4;return true;
    }
private:
    SiHelperExpectation e_;std::array<PostAckLeafExpectation,3> expected_;
    SiFirstHelper helper_;std::array<PostAckOsLeaf,3> leaves_;
    unsigned stage_=0,error_=0,cursor_=0,visits_=0,total_=0;
    uint32_t next_=0;uint64_t tick_=0,last_=0;bool leaf_active_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
};
}
