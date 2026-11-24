#pragma once
#include "wii_full_cache_witness.h"
#include <algorithm>
#include <cstddef>

namespace undercover::wii {
struct DataRange {uint32_t start,size;};
struct DataExpectations {
    std::array<uint32_t,44> table;
    std::array<DataRange,3> zero;
    CacheEdge set,fill;
    uint32_t return_word;
};
// Observe original in-place data relocation and BSS initialization. No guest
// state is seeded or changed, including the bytes outside each BSS span.
class FullDataWitness {
public:
    explicit FullDataWitness(const DataExpectations& e):e_(e){}
    unsigned stage() const noexcept{return calls_;}
    unsigned failure() const noexcept{return failure_;}
    uint32_t before_nonzero() const noexcept{return nonzero_;}
    template<class Cpu> bool begin(Cpu& c){
        if(begun_||failure_||!c.is_running||c.pc!=0x80004238u||c.lr!=Return||!table(c))return fail(1);
        sp_=c.gpr[1];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<19;++i)preserved_[i]=c.gpr[13+i];
        uint64_t total=0;
        for(unsigned i=0;i<e_.zero.size();++i){
            const auto [addr,size]=e_.zero[i];
            if(!size||size>1024*1024u||addr<=0x80000000u||uint64_t(addr)+size>=0x81800000u||!mapped(c,addr-1u,size+2u))return fail(2);
            if(i&&uint64_t(e_.zero[i-1].start)+e_.zero[i-1].size>=addr)return fail(2);
            total+=size;
            const auto* p=c.mmu.get_ptr(addr);
            for(uint32_t j=0;j<size;++j)nonzero_+=unsigned(p[j]!=0);
            left_[i]=c.mmu.read8(addr-1u);right_[i]=c.mmu.read8(addr+size);
        }
        if(total!=963456u)return fail(2);
        begun_=true;return true;
    }
    template<class Cpu> bool observe(uint32_t pc,Cpu& c){
        if(!begun_||failure_||calls_>=6||!c.is_running||pc!=c.pc||c.inst_count<=last_)return fail(3);
        const auto& edge=calls_%2==0?e_.set:e_.fill;
        const auto& range=e_.zero[calls_/2];
        if(pc!=edge.pc||c.lr!=edge.lr||!mapped(c,pc,4)||!mapped(c,edge.lr-4u,4)||c.mmu.read32(pc)!=edge.entry_word||c.mmu.read32(edge.lr-4u)!=edge.branch_word)return fail(4);
        if(c.gpr[3]!=range.start||c.gpr[4]!=0u||c.gpr[5]!=range.size)return fail(5);
        // By the following memset entry the preceding fill must have returned.
        if(calls_&&calls_%2==0&&!cleared(c,calls_/2-1u))return fail(6);
        ++calls_;last_=c.inst_count;return true;
    }
    template<class Cpu> bool finish(Cpu& c){
        if(!begun_||failure_||complete_||calls_!=6||!c.is_running||c.pc!=Return||c.lr!=Return||c.gpr[1]!=sp_||c.msr!=msr_||c.inst_count<=last_||!mapped(c,Return,4)||c.mmu.read32(Return)!=e_.return_word||!table(c))return fail(7);
        for(unsigned i=0;i<19;++i)if(preserved_[i]!=c.gpr[13+i])return fail(8);
        for(unsigned i=0;i<3;++i)if(!cleared(c,i))return fail(6);
        if(!mapped(c,sp_,8)||c.mmu.read32(sp_)!=0xffffffffu||c.mmu.read32(sp_+4u)!=Return)return fail(9);
        complete_=true;return true;
    }
private:
    static constexpr uint32_t Table=0x80006420u,Return=0x80004058u;
    DataExpectations e_;bool begun_=false,complete_=false;
    unsigned calls_=0,failure_=0;uint32_t sp_=0,msr_=0,nonzero_=0;uint64_t last_=0;
    std::array<uint8_t,3> left_{},right_{};std::array<uint32_t,19> preserved_{};
    bool fail(unsigned why){failure_=why;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,uint32_t n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000u&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> bool table(Cpu& c) const{
        if(!mapped(c,Table,176u))return false;
        for(unsigned i=0;i<e_.table.size();++i)if(c.mmu.read32(Table+4u*i)!=e_.table[i])return false;
        return true;
    }
    template<class Cpu> bool cleared(Cpu& c,unsigned i) const{
        const auto [addr,size]=e_.zero[i];
        if(!mapped(c,addr-1u,size+2u)||c.mmu.read8(addr-1u)!=left_[i]||c.mmu.read8(addr+size)!=right_[i])return false;
        const auto* p=c.mmu.get_ptr(addr);return std::all_of(p,p+size,[](uint8_t v){return v==0;});
    }
};
}
