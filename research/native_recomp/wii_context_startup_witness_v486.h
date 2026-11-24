#pragma once
#include "wii_exception_vector_witness_v457.h"
namespace undercover::wii {
struct ContextStartupExpectations {std::array<VectorEdge,4> edges;uint32_t frame_size;};
// Complete-image original context initializer, after IRQ return.
class ContextStartupWitness {
public:
    explicit ContextStartupWitness(const ContextStartupExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=Context||c.lr!=0x805208c0u||
           !matches(c,e_.edges[0])||e_.frame_size<8u||e_.frame_size>256u||(e_.frame_size&7u)||
           c.gpr[1]<0x80000200u||c.gpr[1]>0x817ffff8u||(c.msr&0x8000u)||
           !mapped(c,0x800000d4u,12)||!mapped(c,Dispatch,64))return fail(1);
        pre_=c.mmu.read32(0x800000d4u);post_=c.mmu.read32(0x800000dcu);
        guard_=c.mmu.read32(Dispatch+60u);
        for(unsigned i=0;i<15;++i){
            table_[i]=c.mmu.read32(Dispatch+4*i);
            if(table_[i]!=(i==4?IrqHandler:i==8?AlarmHandler:Default))return fail(2);
        }
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[14+i];
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>3||!c.is_running||c.pc!=addr||!matches(c,e_.edges[stage_])||
           c.inst_count<=last_||c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           c.gpr[1]!=(stage_==3?sp_:sp_-e_.frame_size)||
           !equal(c,0x800000d4u,pre_)||!equal(c,0x800000dcu,post_)||
           !equal(c,Dispatch+60u,guard_))return fail(3);
        for(unsigned i=0;i<15;++i)if(!equal(c,Dispatch+4*i,stage_>1&&i==7?Handler:table_[i]))return fail(4);
        if(stage_==1){
            if(addr!=Setter||c.gpr[3]!=7u||c.gpr[4]!=Handler)return fail(5);
        }else if(stage_==2){
            if(addr!=Debug)return fail(6);
        }else{
            if(addr!=Cache||!equal(c,0x800000d8u,0))return fail(7);
            for(unsigned i=0;i<18;++i)if(c.gpr[14+i]!=nv_[i])return fail(7);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Context=0x80522eb8u,Setter=0x80520e9cu,Debug=0x804e50b8u,
        Cache=0x80522540u,Handler=0x80522e34u,IrqHandler=0x80526ce0u,AlarmHandler=0x805217bcu,
        Default=0x80520f5cu,Dispatch=0x80003000u;
    ContextStartupExpectations e_;unsigned stage_=0,error_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,pre_=0,post_=0,guard_=0;uint64_t last_=0;
    std::array<uint32_t,15> table_{};std::array<uint32_t,18> nv_{};
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
