#pragma once
#include <cstdint>

namespace undercover::wii {
struct OsEntryExpectations {uint32_t db_branch,db_entry,os_branch,os_entry;};
// Read-only boundary witness: no boot metadata or guest registers are seeded.
class FullOsEntryWitness {
public:
    explicit FullOsEntryWitness(OsEntryExpectations e):e_(e){}
    unsigned stage() const noexcept{return stage_;}
    unsigned failure() const noexcept{return failure_;}
    bool arena_hi_nonzero() const noexcept{return arena_;}
    bool boot_info_nonzero() const noexcept{return info_;}
    template<class Cpu> bool begin(Cpu& c){
        if(stage_||failure_||!c.is_running||c.pc!=0x80004058u||c.lr!=c.pc||!mapped(c,0x80000034u)||!mapped(c,0x800000f4u))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];last_=c.inst_count;
        arena_=c.mmu.read32(0x80000034u)!=0;info_=c.mmu.read32(0x800000f4u)!=0;
        stage_=1;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(failure_||stage_<1||stage_>2||!c.is_running||c.pc!=addr||c.inst_count<=last_)return fail(2);
        const bool db=stage_==1;
        const uint32_t pc=db?0x804e5020u:0x80520670u,lr=db?0x8000415cu:0x80004160u;
        if(addr!=pc)return fail(3);
        if(c.lr!=lr||!mapped(c,pc)||!mapped(c,lr-4u)||c.mmu.read32(pc)!=(db?e_.db_entry:e_.os_entry)||c.mmu.read32(lr-4u)!=(db?e_.db_branch:e_.os_branch))return fail(4);
        if(c.gpr[1]!=sp_||c.gpr[2]!=r2_||c.gpr[13]!=r13_)return fail(5);
        if(!db){
            if(!equal(c,0x80000044u,0)||!equal(c,0x80000048u,0x004e5090u)||!equal(c,0x8070d8a0u,0x80000040u)||!equal(c,0x8070d8a4u,1u))return fail(6);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    OsEntryExpectations e_;unsigned stage_=0,failure_=0;uint32_t sp_=0,r2_=0,r13_=0;uint64_t last_=0;bool arena_=false,info_=false;
    bool fail(unsigned code){if(!failure_)failure_=code;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a){return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t v){return mapped(c,a)&&c.mmu.read32(a)==v;}
};
}
