#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only census of completed MMIO accesses, not an interrupt source.
class SiDispatchPiReads {
public:
    bool begin(uint32_t cause,uint32_t mask)noexcept{
        if(active_||bad_||done_||(cause&mask)!=8u)return fail();
        cause_=cause;mask_=mask;active_=true;return true;
    }
    void record(bool write,uint32_t address,unsigned width,uint32_t value,bool native)noexcept{
        if(!active_)return;
        auto p=address&0x3fffffffu;
        if(p!=0x0c003000u&&p!=0x0c003004u)return;
        if(write||width!=32||native||value!=(p==0x0c003000u?cause_:mask_)){fail();return;}
        auto& count=p==0x0c003000u?cause_reads_:mask_reads_;
        if(++count>16u)fail();
    }
    bool good()const noexcept{return active_&&!bad_;}
    bool finish()noexcept{
        if(!good()||!cause_reads_||!mask_reads_)return fail();
        active_=false;done_=true;return true;
    }
private:
    bool active_=false,bad_=false,done_=false;
    uint32_t cause_=0,mask_=0;unsigned cause_reads_=0,mask_reads_=0;
    bool fail()noexcept{bad_=true;return false;}
};
inline thread_local SiDispatchPiReads si_dispatch_pi_reads{};
struct SiDispatchEdge{uint32_t pc,lr,branch_word,entry_word;};
struct SiDispatchExpectations{
    std::array<SiDispatchEdge,4> edges;
    uint32_t indirect_pc,indirect_word,handler_word,dispatcher_word;
};
class SiDispatchWitness{
public:
    static constexpr uint32_t Thread=0x806f5318u,Dispatcher=0x80526a3cu,Handler=0x80531b34u;
    explicit SiDispatchWitness(const SiDispatchExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class C>bool begin(C& c,uint32_t cause,uint32_t mask,uint32_t control,uint32_t status){
        if(stage_||error_||!valid(c)||c.pc!=Dispatcher||c.gpr[3]!=4||c.gpr[4]!=Thread||
           (cause&mask)!=8u||control!=0xe0010300u||status!=0x08000000u||
           !word(c,c.pc,e_.dispatcher_word)||!word(c,0x80003090u,Handler)||
           !word(c,0x800000d4u,Thread)||!word(c,0x800000e4u,Thread)||
           !mapped(c,Thread+408u)||!mapped(c,Thread+412u)||
           !si_dispatch_pi_reads.begin(cause,mask))return fail(1);
        resume_=c.mmu.read32(Thread+408u);saved_msr_=c.mmu.read32(Thread+412u);
        if(resume_<0x805265c4u||resume_>0x805265d0u||(resume_&3u)||!(saved_msr_&0x8000u))return fail(1);
        cause_=cause;mask_=mask;last_=c.inst_count;ctx_=&c;stage_=1;return true;
    }
    template<class C>bool poll(C& c,uint32_t cause,uint32_t mask){
        if(!common(c,cause,mask))return fail(2);
        return true; // only the masked source is permitted before handler entry
    }
    template<class C>bool observe(uint32_t addr,C& c,uint32_t cause,uint32_t mask,uint32_t control,uint32_t status){
        if(!common(c,cause,mask)||c.pc!=addr||c.inst_count<=last_||
           c.inst_count-last_>8192u||control!=0xe0010300u||status!=0x08000000u)return fail(3);
        if(stage_<=4){
            const auto& e=e_.edges[stage_-1];
            if(addr!=e.pc||c.lr!=e.lr||!word(c,addr,e.entry_word)||!word(c,e.lr-4u,e.branch_word))return fail(4);
        }else{
            if(addr!=Handler||c.gpr[3]!=20u||c.gpr[4]!=Thread||c.ctr!=Handler||
               c.lr!=e_.indirect_pc+4u||!word(c,Handler,e_.handler_word)||
               !word(c,e_.indirect_pc,e_.indirect_word)||!word(c,0x80003090u,Handler)||
               !word(c,Thread+408u,resume_)||!word(c,Thread+412u,saved_msr_)||
               !si_dispatch_pi_reads.finish())return fail(5);
        }
        last_=c.inst_count;++stage_;return true;
    }
private:
    SiDispatchExpectations e_;const void* ctx_=nullptr;
    unsigned stage_=0,error_=0;uint32_t cause_=0,mask_=0,resume_=0,saved_msr_=0;uint64_t last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool valid(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,uint32_t cause,uint32_t mask)const{
        return !error_&&stage_>=1&&stage_<=5&&ctx_==&c&&valid(c)&&cause==cause_&&mask==mask_&&
            si_dispatch_pi_reads.good();
    }
    template<class C>static bool mapped(C& c,uint32_t a){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return mapped(c,a)&&c.mmu.read32(a)==w;}
};
}
