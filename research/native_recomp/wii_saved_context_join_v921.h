#pragma once
#include "wii_external_return_v706.h"
namespace undercover::wii {
class SavedContextJoin {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool attach(C& c,ExternalReturnWitness& w,uint32_t base){
        if(stage_||error_||w.stage()!=1u||!w.saved_integer(c,base).ok())return fail(1);
        witness_=&w;cpu_=&c;base_=base;tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool returned(C& c,uint32_t base){
        if(stage_!=1u||error_||cpu_!=&c||base_!=base||c.inst_count<=tick_||
           !witness_||witness_->stage()!=1u||!witness_->saved_integer(c,base).ok())return fail(2);
        stage_=2;return true;
    }
    ExternalReturnWitness* captured()const{return stage_==2u&&!error_?witness_:nullptr;}
    uint32_t context()const{return base_;}
private:
    unsigned stage_=0,error_=0;ExternalReturnWitness* witness_=nullptr;
    const void* cpu_=nullptr;uint32_t base_=0;uint64_t tick_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
};
namespace v921 {inline thread_local SavedContextJoin join;}
}
