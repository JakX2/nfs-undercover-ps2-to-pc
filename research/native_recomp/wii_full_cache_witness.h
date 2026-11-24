#pragma once
#include "wii_full_hardware_witness.h"

namespace undercover::wii {
struct CacheEdge {uint32_t pc,lr,branch_word,entry_word;};
struct CacheExpectations {
    std::array<CacheEdge,26> cache;
    std::array<CacheEdge,2> error;
    CacheEdge data;
};
class FullCacheWitness {
public:
    explicit FullCacheWitness(const CacheExpectations& e):e_(e){}
    unsigned stage() const noexcept{return stage_;}
    unsigned calls() const noexcept{return calls_;}
    unsigned failure() const noexcept{return failure_;}
    unsigned reads() const noexcept{return reads_;}
    unsigned writes() const noexcept{return writes_;}
    template<class Cpu> bool begin(Cpu& c){
        if(begun_||!c.is_running||c.pc!=0x80522540u||c.l2cr_busy_polls)return false;
        begun_=true;sp_=c.gpr[1];msr_=c.msr;hid_=c.hid0;l2_=c.l2cr;last_=c.inst_count;return true;
    }
    template<class Cpu> FullStartResult observe(uint32_t pc,Cpu& c){
        if(!begun_||failure_||stage_==4u||!c.is_running||c.pc!=pc||c.inst_count<=last_)return invalid(1);
        if(++calls_>128u)return invalid(2);
        last_=c.inst_count;
        if(pc==e_.data.pc){
            if(!matches(c,e_.data)||stage_!=3u||!cache_state(c)||!handler_state(c)||c.gpr[1]!=sp_-8u||c.msr!=msr_||
               !mapped(c,sp_-8u)||!mapped(c,sp_-4u)||c.mmu.read32(sp_-8u)!=0xffffffffu||c.mmu.read32(sp_-4u)!=0xffffffffu)return invalid(3);
            stage_=4;return FullStartResult::Complete;
        }
        if(stage_==1u||stage_==2u){
            const auto& edge=e_.error[stage_-1u];
            if(!matches(c,edge))return invalid(4);
            if(stage_==1u){if(c.mmu.read32(Table)!=old_||c.msr!=msr_)return invalid(5);}
            else if(!handler_state(c)||(c.msr&0x8000u))return invalid(5);
            ++stage_;return FullStartResult::Accepted;
        }
        bool found=false;for(const auto& edge:e_.cache)if(matches(c,edge)){found=true;break;}
        if(!found)return invalid(4);
        if(pc==0x805223bcu)++ice_;
        if(pc==0x80522280u)++dce_;
        if(pc==0x804b7930u)++reads_;
        if(pc==0x804b7938u)++writes_;
        if(pc==0x805230b8u){
            if(stage_||!cache_state(c)||c.gpr[3]!=1u||!mapped(c,c.gpr[4])||c.gpr[4]<0x80004000u||c.gpr[4]>=0x81800000u||
               !mapped(c,Table-4u)||!mapped(c,Table)||!mapped(c,Table+4u))return invalid(5);
            handler_=c.gpr[4];old_=c.mmu.read32(Table);left_=c.mmu.read32(Table-4u);right_=c.mmu.read32(Table+4u);stage_=1;
        }
        return FullStartResult::Accepted;
    }
private:
    static constexpr uint32_t Table=0x806f4f74u;
    CacheExpectations e_;
    unsigned stage_=0,calls_=0,failure_=0,ice_=0,dce_=0,reads_=0,writes_=0;
    bool begun_=false;uint32_t sp_=0,msr_=0,hid_=0,l2_=0,handler_=0,old_=0,left_=0,right_=0;uint64_t last_=0;
    FullStartResult invalid(unsigned reason){failure_=reason;return FullStartResult::Invalid;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a){return a>=0x80000000u&&a<=0x817ffffcu&&!(a&3u)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class Cpu> static bool matches(Cpu& c,const CacheEdge& e){return c.pc==e.pc&&c.lr==e.lr&&e.lr>=4u&&mapped(c,e.pc)&&mapped(c,e.lr-4u)&&c.mmu.read32(e.pc)==e.entry_word&&c.mmu.read32(e.lr-4u)==e.branch_word;}
    template<class Cpu> bool cache_state(Cpu& c) const{
        const bool l2on=(l2_&0x80000000u)!=0;
        return c.hid0==(hid_|0xc000u)&&ice_==unsigned(!(hid_&0x8000u))&&dce_==unsigned(!(hid_&0x4000u))&&
               reads_>0u&&(l2on?writes_==0u:writes_>=5u)&&!c.l2cr_busy_polls&&(c.l2cr&0x80200001u)==0x80000000u&&
               (c.l2cr&0xff00u)==(l2_&0xff00u)&&c.msr==msr_;
    }
    template<class Cpu> bool handler_state(Cpu& c) const{return mapped(c,Table-4u)&&mapped(c,Table)&&mapped(c,Table+4u)&&c.mmu.read32(Table)==handler_&&c.mmu.read32(Table-4u)==left_&&c.mmu.read32(Table+4u)==right_;}
};
}
