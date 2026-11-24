#pragma once
#include "wii_arena_reset_v606.h"
#include "undercover/arena_cache_range_trace_v596.h"
#include <array>
#include <algorithm>
#include <cstdint>
namespace undercover::wii {
struct ArenaClearEdge {uint32_t pc,lr,branch,entry;};
struct ArenaClearExpectations {
    std::array<std::array<ArenaClearEdge,7>,2> edges;
    std::array<uint32_t,2> flush_resume_words;
    uint32_t begin_word,return_word;
};
// This observer is a bounded cold-start lane. Warm reset, alternate boot
// record branches and actual hardware cache behavior are not modeled.
class ArenaClearWitness {
public:
    static constexpr uint32_t Begin=0x80520908u,Return=0x80520944u,Sc=0x805222e8u;
    explicit ArenaClearWitness(const ArenaClearExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    uint64_t lines()const noexcept{return expected_lines_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=Begin||c.lr!=Begin||
           (c.msr&0x8000u)||c.gpr[13]!=0x8070e8e0u||
           !equal(c,Begin,e_.begin_word)||!equal(c,0x806f4f0cu,0)||
           !equal(c,c.gpr[13]-3400u,1)||c.arena_cache_range.lanes()!=0)return fail(1);
        ctx_=&c;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;start_=last_=c.inst_count;
        for(unsigned i=0;i<4;++i){
            if(!mapped(c,r13_-Offsets[i],4))return fail(1);
            bounds_[i]=c.mmu.read32(r13_-Offsets[i]);
        }
        for(unsigned i=0;i<2;++i){
            const uint32_t lo=bounds_[i*2],hi=bounds_[i*2+1];
            if(((lo|hi)&31u)||hi<=lo||hi-lo<ArenaCacheRangeTrace::Tail||
               (i==0?(lo<=0x80000000u||hi>=0x81800000u):(lo<=0x90000000u||hi>=0x94000000u))||
               !mapped(c,lo-1,hi-lo+2))return fail(1);
            expected_lines_+=(hi-lo)/32u;
        }
        stage_=1;return true;
    }
    template<class Cpu,class Pair>bool observe(uint32_t addr,Cpu& c,ArenaResetProfile& reset,Pair& pair){
        if(error_||stage_<1||stage_>19||ctx_!=&c||!c.is_running||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           c.inst_count<=last_||c.inst_count-start_>100000000u||!preserved(c))return fail(2);
        if(stage_==19){
            if(addr!=Return||c.pc!=addr||c.lr!=addr||c.gpr[1]!=sp_||
               !equal(c,addr,e_.return_word)||!reset.complete()||pair.completed()!=2||
               c.arena_cache_range.lanes()!=2||c.arena_cache_range.zeros()!=expected_lines_||
               c.arena_cache_range.flushes()!=2u*ArenaCacheRangeTrace::Tail/32u||
               !cleared(c,0)||!cleared(c,1))return fail(7);
            ++stage_;return true;
        }
        const unsigned lane=(stage_-1)/9,step=(stage_-1)%9;
        const uint32_t lo=bounds_[2*lane],hi=bounds_[2*lane+1];
        if(c.gpr[1]!=(step==0?sp_:sp_-16u))return fail(3);
        if(step<7){
            const auto& e=e_.edges[lane][step];
            if(addr!=e.pc||!matches(c,e))return fail(3);
            if(step==0){
                if(reset.reads()!=lane||pair.completed()!=lane||
                   c.arena_cache_range.lanes()!=lane||(lane&&!cleared(c,0)))return fail(4);
            }else if(step==1){
                if(!reset.arm(lane+1))return fail(4);
            }else if(step<5){
                if(reset.reads()!=lane+1||reset.armed())return fail(4);
            }else if(step==5){
                if(reset.reads()!=lane+1||c.gpr[3]!=lo||c.gpr[4]!=hi-lo)return fail(5);
                guards_[lane]={c.mmu.read8(lo-1),c.mmu.read8(hi)};
                if(!c.arena_cache_range.begin(c,lane+1,lo,hi))return fail(5);
            }else if(c.gpr[3]!=hi-ArenaCacheRangeTrace::Tail||c.gpr[4]!=ArenaCacheRangeTrace::Tail||
                     !c.arena_cache_range.begin_flush(c,c.gpr[3],c.gpr[4]))return fail(5);
        }else if(step==7){
            if(addr!=Sc||c.lr!=e_.edges[lane][6].lr||!equal(c,Sc,0x44000002u))return fail(6);
            try{pair.arm(addr,c,c.arena_cache_range);}catch(const std::exception&){return fail(6);}
        }else{
            if(addr!=e_.edges[lane][6].lr||c.pc!=addr||c.lr!=addr||
               !equal(c,addr,e_.flush_resume_words[lane]))return fail(6);
            try{if(!pair.finish(c))return fail(6);}catch(const std::exception&){return fail(6);}
            if(!cleared(c,lane))return fail(6);
        }
        last_=c.inst_count;++stage_;return true;
    }
private:
    static constexpr std::array<uint32_t,4> Offsets{16400,3472,16396,3468};
    ArenaClearExpectations e_;
    const void* ctx_=nullptr;unsigned stage_=0,error_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t start_=0,last_=0,expected_lines_=0;
    std::array<uint32_t,4> bounds_{};
    std::array<std::array<uint8_t,2>,2> guards_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,uint32_t n){
        const auto end=uint64_t(a)+n;
        return n&&((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull))&&
               c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const ArenaClearEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry)&&equal(c,e.lr-4u,e.branch);
    }
    template<class Cpu>bool preserved(Cpu& c)const{
        if(!equal(c,0x806f4f0cu,0)||!equal(c,r13_-3400u,1))return false;
        for(unsigned i=0;i<4;++i)if(!equal(c,r13_-Offsets[i],bounds_[i]))return false;
        return true;
    }
    template<class Cpu>bool cleared(Cpu& c,unsigned lane)const{
        const auto lo=bounds_[2*lane],hi=bounds_[2*lane+1];
        auto* p=c.mmu.get_ptr(lo);auto* end=c.mmu.get_ptr(hi);
        return p&&end&&reinterpret_cast<uintptr_t>(end)>=reinterpret_cast<uintptr_t>(p)&&
               reinterpret_cast<uintptr_t>(end)-reinterpret_cast<uintptr_t>(p)==hi-lo&&
               c.mmu.read8(lo-1)==guards_[lane][0]&&c.mmu.read8(hi)==guards_[lane][1]&&
               std::all_of(p,end,[](uint8_t v){return v==0;});
    }
};
}
