#pragma once
#include "wii_si_dispatch_v667.h"
#include "wii_external_return_v706.h"
namespace undercover::wii {
// Independent second-dispatch census. Unlike the cold first dispatch,
// admission uses the already captured successor interrupt and its held
// transaction witness, not a fixed cold COMCSR/status value.
class SecondSiDispatchWitness {
public:
    explicit SecondSiDispatchWitness(SiDispatchExpectations e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool begin(C& c,ExternalReturnWitness& captured,uint32_t cause,uint32_t mask,bool held){
        if(stage_||error_||!safe(c)||!held||c.pc!=SiDispatchWitness::Dispatcher||
           c.gpr[3]!=4u||c.gpr[4]!=SiDispatchWitness::Thread||
           !captured.pending_source(c,cause,mask)||!captured.saved_integer(c,SiDispatchWitness::Thread).ok()||
           !word(c,c.pc,e_.dispatcher_word)||!tables(c)||!pi_.begin(cause,mask))return fail(1);
        cpu_=&c;captured_=&captured;cause_=cause;mask_=mask;start_=last_=c.inst_count;stage_=1;return true;
    }
    // Only called by a real completed MMIO-access observer in a live route.
    void record(bool write,uint32_t addr,unsigned width,uint32_t value,bool native){
        if(stage_>=1u&&stage_<=5u&&!error_)pi_.record(write,addr,width,value,native);
    }
    template<class C>bool poll(C& c,uint32_t cause,uint32_t mask,bool held){
        if(!common(c,cause,mask,held)||c.inst_count<last_||c.inst_count-start_>8192u)return fail(2);
        return true;
    }
    template<class C>bool observe(C& c,uint32_t pc,uint32_t cause,uint32_t mask,bool held){
        if(!common(c,cause,mask,held)||c.pc!=pc||c.inst_count<=last_||c.inst_count-start_>8192u)return fail(3);
        if(stage_<=4u){
            const auto& e=e_.edges[stage_-1u];
            if(pc!=e.pc||c.lr!=e.lr||!word(c,pc,e.entry_word)||!word(c,e.lr-4u,e.branch_word))return fail(4);
        }else{
            if(pc!=SiDispatchWitness::Handler||c.gpr[3]!=20u||c.gpr[4]!=SiDispatchWitness::Thread||
               c.ctr!=pc||c.lr!=e_.indirect_pc+4u||!word(c,pc,e_.handler_word)||
               !word(c,e_.indirect_pc,e_.indirect_word)||!pi_.finish())return fail(5);
        }
        last_=c.inst_count;++stage_;return true;
    }
private:
    SiDispatchExpectations e_;SiDispatchPiReads pi_;ExternalReturnWitness* captured_=nullptr;
    const void* cpu_=nullptr;unsigned stage_=0,error_=0;uint32_t cause_=0,mask_=0;uint64_t start_=0,last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>static bool word(C& c,uint32_t a,uint32_t v){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==v;
    }
    template<class C>static bool tables(C& c){
        return word(c,0x80003090u,SiDispatchWitness::Handler)&&word(c,0x800000d4u,SiDispatchWitness::Thread)&&word(c,0x800000e4u,SiDispatchWitness::Thread);
    }
    template<class C>bool common(C& c,uint32_t cause,uint32_t mask,bool held)const{
        return !error_&&stage_>=1u&&stage_<=5u&&held&&cpu_==&c&&safe(c)&&cause==cause_&&mask==mask_&&
               captured_&&captured_->pending_source(c,cause,mask)&&captured_->saved_integer(c,SiDispatchWitness::Thread).ok()&&tables(c)&&pi_.good();
    }
};
inline thread_local SecondSiDispatchWitness* second_dispatch_mmio=nullptr;
inline void record_second_dispatch_pi(bool write,uint32_t address,unsigned width,uint32_t value,bool native){
    if(second_dispatch_mmio)second_dispatch_mmio->record(write,address,width,value,native);
}
}
