#pragma once
#include "wii_exception_vector_witness_v457.h"
namespace undercover::wii {
// The complete image already ran the original cache initializer in __start.
// The second OSInit invocation must take the enabled-cache path, not fake
// hardware writes or repeat the L2 invalidation handshake.
struct OsCacheReuseExpectations {std::array<VectorEdge,9> edges;};
class OsCacheReuseWitness {
public:
    explicit OsCacheReuseWitness(const OsCacheReuseExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=Cache||c.lr!=0x805208c4u||
           !matches(c,e_.edges[0])||c.gpr[1]<0x80000200u||c.gpr[1]>0x817ffff8u||
           (c.msr&0x8000u)||(c.hid0&0xc000u)!=0xc000u||
           (c.l2cr&0x80200001u)!=0x80000000u||c.l2cr_busy_polls||
           !mapped(c,Table-4,12))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;
        hid_=c.hid0;l2_=c.l2cr;last_=c.inst_count;
        old_=c.mmu.read32(Table);left_=c.mmu.read32(Table-4);right_=c.mmu.read32(Table+4);
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[14+i];
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>8||!c.is_running||c.pc!=addr||
           c.inst_count<=last_||!matches(c,e_.edges[stage_])||c.gpr[2]!=r2_||
           c.gpr[13]!=r13_||c.msr!=msr_||c.hid0!=hid_||c.l2cr!=l2_||c.l2cr_busy_polls||
           !equal(c,Table-4,left_)||!equal(c,Table+4,right_))return fail(2);
        if(!equal(c,Table,stage_>=6?Handler:old_))return fail(3);
        if(stage_<=3){
            if(c.gpr[1]!=sp_-16u)return fail(4);
        }else if(stage_==4){
            if(addr!=Error||c.gpr[1]!=sp_-16u||c.gpr[3]!=1u||c.gpr[4]!=Handler)return fail(5);
        }else if(stage_==5||stage_==6){
            if(c.gpr[1]>=sp_-16u||c.gpr[1]<sp_-256u)return fail(6);
            if(stage_==5)error_sp_=c.gpr[1];
            else if(c.gpr[1]!=error_sp_||c.gpr[3]!=0)return fail(6);
        }else if(stage_==7){
            if(addr!=Debug||c.gpr[1]!=sp_-16u)return fail(7);
        }else{
            if(addr!=Exi||c.gpr[1]!=sp_)return fail(8);
            for(unsigned i=0;i<18;++i)if(c.gpr[14+i]!=nv_[i])return fail(8);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Cache=0x80522540u,Error=0x805230b8u,Debug=0x804e50b8u,
        Exi=0x804ef9bcu,Table=0x806f4f74u,Handler=0x805223f8u;
    OsCacheReuseExpectations e_;unsigned stage_=0,error_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,hid_=0,l2_=0,old_=0,left_=0,right_=0,error_sp_=0;
    uint64_t last_=0;std::array<uint32_t,18> nv_{};
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
