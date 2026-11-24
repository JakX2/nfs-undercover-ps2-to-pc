#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
struct OsTimeEdge {uint32_t pc,lr,branch_word,entry_word;};
struct OsTimeExpectations {std::array<OsTimeEdge,6> edges;};
// Observe the unmodified cold OSInit prologue and original time helper chain.
// The endpoint is the next interrupt-disable entry, before its body executes.
class FullOsTimeWitness {
public:
    explicit FullOsTimeWitness(OsTimeExpectations e):e_(e){}
    unsigned stage() const noexcept{return stage_;}
    unsigned failure() const noexcept{return failure_;}
    bool active() const noexcept{return begun_;}
    template<class Cpu> bool begin(Cpu& c){
        if(begun_||failure_||!c.is_running||c.pc!=0x80520670u||c.lr!=0x80004160u||!equal(c,Flag,0))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        if(sp_<0x80000050u||sp_>0x817ffff8u||!mapped(c,sp_-80u)||!mapped(c,sp_+4u))return fail(1);
        for(unsigned i=0;i<12;++i)saved_[i]=c.gpr[20+i];
        begun_=true;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(!begun_||failure_||stage_>=6||!c.is_running||c.pc!=addr||c.inst_count<=last_)return fail(2);
        const auto& edge=e_.edges[stage_];
        if(addr!=edge.pc||c.lr!=edge.lr||edge.lr<4u||!equal(c,addr,edge.entry_word)||!equal(c,edge.lr-4u,edge.branch_word))return fail(3);
        if(c.gpr[2]!=r2_||c.gpr[13]!=r13_)return fail(4);
        switch(stage_){
        case 0:
            if(!frame(c)||c.gpr[11]!=sp_||c.msr!=msr_)return fail(4);
            break;
        case 1:
            if(!frame(c)||!spills(c)||!equal(c,Flag,1)||c.msr!=msr_)return fail(5);
            break;
        case 2:
            if(c.msr!=msr_)return fail(6);
            break;
        case 3:
            if(c.msr!=(msr_&~0x8000u)||!mapped(c,Offset)||!mapped(c,Offset+4u))return fail(6);
            lower_=c.read_timebase();offset_=pair(c,Offset);
            break;
        case 4:
            if(c.msr!=(msr_&~0x8000u)||c.gpr[3]!=unsigned((msr_&0x8000u)!=0))return fail(6);
            upper_=c.read_timebase();
            // An enormous time window is not evidence of a valid time read.
            if(upper_-lower_>1000000u)return fail(7);
            break;
        case 5: {
            if(!frame(c)||!spills(c)||!equal(c,Flag,1)||c.msr!=msr_)return fail(5);
            if(!mapped(c,Offset)||!mapped(c,Offset+4u)||pair(c,Offset)!=offset_)return fail(7);
            const uint64_t result=(uint64_t(c.gpr[3])<<32)|c.gpr[4];
            if(result-offset_-lower_>upper_-lower_)return fail(7);
            if(!equal(c,Stamp,c.gpr[3])||!equal(c,Stamp+4u,c.gpr[4]))return fail(8);
            break;
        }
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Flag=0x8070dafcu,Offset=0x800030d8u,Stamp=0x8070db30u;
    OsTimeExpectations e_;bool begun_=false;unsigned stage_=0,failure_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0,lower_=0,upper_=0,offset_=0;
    std::array<uint32_t,12> saved_{};
    bool fail(unsigned why){if(!failure_)failure_=why;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a){return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t v){return mapped(c,a)&&c.mmu.read32(a)==v;}
    template<class Cpu> static uint64_t pair(Cpu& c,uint32_t a){return (uint64_t(c.mmu.read32(a))<<32)|c.mmu.read32(a+4u);}
    template<class Cpu> bool frame(Cpu& c) const{return c.gpr[1]==sp_-80u&&equal(c,sp_-80u,sp_)&&equal(c,sp_+4u,0x80004160u);}
    template<class Cpu> bool spills(Cpu& c) const{for(unsigned i=0;i<12;++i)if(!equal(c,sp_-48u+4u*i,saved_[i]))return false;return true;}
};
}
