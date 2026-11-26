#pragma once
#include "wii_open_sc_route_v637.h"
#include "open_cache_range_trace_v649.h"
#include <algorithm>
#include <span>
namespace undercover::wii {
struct IoctlFirstFlushExpectation {
    uint32_t entry_word,input_resume_word,output_resume_word;
    std::span<const uint32_t> polls;
};
// Continue the actual native DCFlushRange body. All translated labels and
// the two exact caller return edges are authenticated by the private installer.
class IoctlFirstFlushWitness {
public:
    using R=OpenScRoute;
    IoctlFirstFlushWitness(IoctlFirstFlushExpectation e,const std::array<uint8_t,28>& bytes,unsigned first,unsigned kind)
        :e_(e),caller_(kind==1?R::EventInputCaller:R::EventOutputCaller),route_(bytes,caller_,first,R::Mode::DeferredStm){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned lines()const{return lines_;} unsigned polls()const{return polls_;}
    unsigned zero()const{return empty_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!c.is_running||c.in_callback||c.dispatch_saved_ctx||(c.msr&0x8000u)||
           c.pc!=0x805222c0u||c.lr!=caller_||c.mmu.read32(c.pc)!=e_.entry_word||
           c.mmu.read32(caller_)!=return_word()||c.gpr[4]>4096u||
           c.open_cache_range.phase()!=OpenCacheRangeTrace::Phase::Done)return fail(1);
        empty_=c.gpr[4]==0u;
        // The zero-length variant must not generate a cache-line access.
        // Unaligned zero-size arguments are not assumed to be harmless.
        if(empty_&&(c.gpr[3]&31u))return fail(1);
        if(!c.open_cache_range.rearm(c)||
           !(empty_?c.open_cache_range.begin_empty(c):c.open_cache_range.begin(c,c.gpr[3],c.gpr[4])))return fail(1);
        cpu_=&c;sp_=c.gpr[1];msr_=c.msr;start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool trace(C& c,uint32_t pc,bool held){
        if(stage_==2u&&pc==R::Vector){
            try{return route_.vector_trace(pc,c)||fail(2);}catch(const std::exception&){return fail(2);}
        }
        if(!live(c,held))return fail(2);
        if(stage_==1u&&pc==R::Call&&c.pc==pc&&c.lr==caller_&&c.inst_count>start_){
            if(!c.open_cache_range.ready_sc(c))return fail(3);
            lines_=c.open_cache_range.lines();
            try{route_.arm(pc,c);}catch(const std::exception&){return fail(3);}
            stage_=2;return true;
        }
        if(stage_==3u&&pc==caller_&&c.pc==pc&&c.mmu.read32(pc)==return_word()&&
           route_.returned(c)&&c.open_cache_range.finish(c)){
            stage_=4;return true;
        }
        return fail(2);
    }
    template<class C,class Native,class Verify>bool dispatch(C& c,bool held,Native native,Verify verify){
        if(stage_!=2u||!live(c,held))return fail(4);
        try{if(!route_.dispatch(c,native,verify))return fail(4);}
        catch(const std::exception&){return fail(4);}
        stage_=3;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||++polls_>256u)return fail(5);
        if(stage_==1u&&std::find(e_.polls.begin(),e_.polls.end(),c.pc)!=e_.polls.end())return true;
        if(stage_==3u&&c.pc==R::Resume&&!resume_poll_){resume_poll_=true;return true;}
        return fail(5);
    }
    template<class C>bool returned(C& c,bool held)const{
        return stage_==4u&&live(c,held)&&route_.returned(c)&&
               c.open_cache_range.phase()==OpenCacheRangeTrace::Phase::Done;
    }
private:
    IoctlFirstFlushExpectation e_;uint32_t caller_;R route_;
    const void* cpu_=nullptr;uint32_t sp_=0,msr_=0;uint64_t start_=0;
    unsigned stage_=0,error_=0,lines_=0,polls_=0;bool empty_=false,resume_poll_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    uint32_t return_word()const{return caller_==R::EventInputCaller?e_.input_resume_word:e_.output_resume_word;}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
           c.gpr[1]==sp_&&c.msr==msr_&&c.inst_count>=start_&&c.inst_count-start_<=4096u;
    }
};
}
