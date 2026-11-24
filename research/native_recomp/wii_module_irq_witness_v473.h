#pragma once
#include "wii_exception_vector_witness_v457.h"
namespace undercover::wii {
struct ModuleIrqExpectations {
    std::array<VectorEdge,4> edges;
    uint32_t return_word;
};
// Original module init and IRQ table memset, stopping before hardware masks.
class ModuleIrqWitness {
public:
    explicit ModuleIrqWitness(const ModuleIrqExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu> bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||!matches(c,e_.edges[0])||
           c.pc!=Module||c.lr!=0x805208b8u||c.gpr[13]!=Sda||
           (c.msr&0x8000u)||c.gpr[1]<0x80000200u||c.gpr[1]>0x817ffff8u||
           !mapped(c,Table-4,132)||!mapped(c,Table+128,4)||!mapped(c,ModulePre,20)||
           !mapped(c,IrqGlobal,4))return fail(1);
        before_=c.mmu.read32(Table-4);after_=c.mmu.read32(Table+128);
        mod_pre_=c.mmu.read32(ModulePre);mod_post_=c.mmu.read32(ModulePost);
        sp_=c.gpr[1];r2_=c.gpr[2];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[14+i];
        stage_=1;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>4||!c.is_running||c.pc!=addr||c.inst_count<=last_||
           c.gpr[2]!=r2_||c.gpr[13]!=Sda||c.msr!=msr_)return fail(2);
        if(!module(c))return fail(3);
        if(stage_==1){
            if(addr!=Irq||c.lr!=0x805208bcu||!matches(c,e_.edges[1])||c.gpr[1]!=sp_)return fail(4);
            for(unsigned i=0;i<18;++i)if(c.gpr[14+i]!=nv_[i])return fail(4);
        }else if(stage_==2){
            if(addr!=Memset||c.lr!=Stop||!matches(c,e_.edges[2])||c.gpr[1]!=sp_-32||
               c.gpr[3]!=Table||c.gpr[4]!=0||c.gpr[5]!=128||!equal(c,IrqGlobal,Table))return fail(5);
        }else if(stage_==3){
            if(addr!=Fill||c.lr!=0x80004454u||!matches(c,e_.edges[3])||c.gpr[3]!=Table)return fail(6);
        }else{
            if(addr!=Stop||c.lr!=Stop||!equal(c,Stop,e_.return_word)||c.gpr[1]!=sp_-32||
               c.gpr[3]!=Table||!equal(c,IrqGlobal,Table)||!equal(c,Table-4,before_)||
               !equal(c,Table+128,after_))return fail(7);
            for(unsigned i=0;i<32;++i)if(!equal(c,Table+4*i,0))return fail(8);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Sda=0x8070e8e0u,Module=0x80526d30u,Irq=0x8052661cu,
        Memset=0x8000443cu,Fill=0x80004388u,Stop=0x8052664cu,Table=0x80003040u,
        IrqGlobal=Sda-3408u,ModulePre=0x800030c4u,ModulePost=0x800030d4u;
    ModuleIrqExpectations e_;unsigned stage_=0,error_=0;
    uint32_t before_=0,after_=0,mod_pre_=0,mod_post_=0,sp_=0,r2_=0,msr_=0;
    uint64_t last_=0;std::array<uint32_t,18> nv_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
    template<class Cpu> static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
    template<class Cpu> bool module(Cpu& c) const{
        return equal(c,ModulePre,mod_pre_)&&equal(c,ModulePost,mod_post_)&&
            equal(c,ModulePre+4,0)&&equal(c,ModulePre+8,0)&&equal(c,ModulePre+12,0);
    }
};
}
