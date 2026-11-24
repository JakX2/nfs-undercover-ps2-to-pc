#pragma once
#include "wii_exception_vector_witness_v457.h"
namespace undercover::wii {
// Observe the actual cold controller's EXI CR reads, not a synthetic busy schedule.
class ExiColdPollTrace {
public:
    bool begin(bool bound)noexcept{
        if(!bound||active_||count_||bad_){bad_=true;return false;}
        active_=true;return true;
    }
    void record(bool write,unsigned offset,uint32_t value)noexcept{
        if(!active_)return;
        if(write||count_>=3||offset!=12u+20u*count_||value!=0u){bad_=true;return;}
        ++count_;
    }
    bool finish()noexcept{
        const bool ok=active_&&!bad_&&count_==3;
        active_=false;if(!ok)bad_=true;return ok;
    }
    unsigned count()const{return count_;}
private:
    unsigned count_=0;bool active_=false,bad_=false;
};
inline thread_local ExiColdPollTrace exi_cold_poll_trace{};
struct ExiColdPollExpectations{std::array<VectorEdge,2> edges;};
class ExiColdPollWitness {
public:
    explicit ExiColdPollWitness(const ExiColdPollExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c,bool controller){
        if(stage_||error_||!c.is_running||c.pc!=Exi||c.lr!=0x805208c8u||
           !matches(c,e_.edges[0])||(c.msr&0x8000u)||c.gpr[1]<0x80000200u||
           c.gpr[1]>0x817ffff8u||!mapped(c,0x800000c0u,16)||
           !equal(c,0x800000c4u,0xfffffff0u)||!equal(c,0x800000c8u,0)||
           !exi_cold_poll_trace.begin(controller))return fail(1);
        pre_=c.mmu.read32(0x800000c0u);post_=c.mmu.read32(0x800000ccu);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(stage_!=1||error_||!c.is_running||addr!=Mask||c.pc!=addr||
           c.lr!=0x804efa18u||!matches(c,e_.edges[1])||c.inst_count<=last_||
           c.gpr[1]!=sp_-32u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           c.gpr[3]!=0x007f8000u||!equal(c,sp_+4u,0x805208c8u)||
           !equal(c,0x800000c0u,pre_)||!equal(c,0x800000c4u,0xfffffff0u)||
           !equal(c,0x800000c8u,0)||!equal(c,0x800000ccu,post_))return fail(2);
        if(!exi_cold_poll_trace.finish())return fail(3);
        stage_=2;return true;
    }
private:
    static constexpr uint32_t Exi=0x804ef9bcu,Mask=0x8052693cu;
    ExiColdPollExpectations e_;unsigned stage_=0,error_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,pre_=0,post_=0;uint64_t last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
