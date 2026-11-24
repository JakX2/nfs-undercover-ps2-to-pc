#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
struct ArenaEdge {uint32_t pc,lr,branch_word,entry_word;};
struct OsArenaExpectations {std::array<ArenaEdge,2> edges;uint32_t stop_word;};
// Observe original boot-info handoff and MEM1 setters. No guest mutation.
class FullOsArenaWitness {
public:
    explicit FullOsArenaWitness(OsArenaExpectations e):e_(e){}
    bool active() const{return stage_>0&&stage_<4&&!failure_;}
    unsigned stage() const{return stage_;}
    unsigned failure() const{return failure_;}
    unsigned boot_path() const{return boot_?2u:legacy_?1u:0u;}
    bool direct_low() const{return hint_lo_!=0;}
    template<class Cpu> bool begin(Cpu& c){
        if(stage_||failure_||!c.is_running||c.pc!=0x80520700u||c.lr!=c.pc||c.gpr[13]!=Sda)return fail(1);
        if(!mapped(c,0x80000030u,8)||!mapped(c,0x800000f4u,4)||!mapped(c,0x800030e8u,2)||!mapped(c,0x8000310cu,8))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];msr_=c.msr;last_=c.inst_count;
        if(msr_&0x8000u)return fail(1);
        boot_=c.mmu.read32(0x800000f4u);legacy_=c.mmu.read32(0x80000034u);override_=c.mmu.read32(0x80000030u);
        hint_lo_=c.mmu.read32(0x8000310cu);hint_hi_=c.mmu.read32(0x80003110u);
        byte0_=c.mmu.read8(0x800030e8u);byte1_=c.mmu.read8(0x800030e9u);
        if(!mapped(c,Fallback,12)||!mapped(c,Field,4)||!mapped(c,Mode,4)||!mapped(c,Lo-4,8)||!mapped(c,Hi,8))return fail(1);
        fallback_=c.mmu.read32(Fallback);field_=c.mmu.read32(Field);guard_lo_=c.mmu.read32(Lo-4);guard_hi_=c.mmu.read32(Hi+4);old_hi_=c.mmu.read32(Hi);
        if(boot_){
            if((boot_&3u)||!mapped(c,boot_,40))return fail(2);
            boot0_=c.mmu.read32(boot_+12);boot1_=c.mmu.read32(boot_+36);
        }
        expected_hi_=hint_hi_?hint_hi_:legacy_?legacy_:0x81700000u;
        stage_=1;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(!active()||!c.is_running||c.pc!=addr||c.inst_count<=last_||c.gpr[1]!=sp_||c.gpr[2]!=r2_||c.gpr[13]!=Sda||c.msr!=msr_)return fail(3);
        if(!boot_ok(c))return fail(4);
        if(!equal(c,Lo-4,guard_lo_)||!equal(c,Hi+4,guard_hi_))return fail(5);
        if(stage_<3){
            const auto& edge=e_.edges[stage_-1];
            if(addr!=edge.pc||c.lr!=edge.lr||!equal(c,addr,edge.entry_word)||!equal(c,edge.lr-4,edge.branch_word))return fail(6);
            if(stage_==1){
                selected_lo_=c.gpr[3];
                // Direct hints are exact. Without a hint accept only the previously
                // verified original fallback candidates or explicit lowmem override.
                if(!arena(selected_lo_)||(hint_lo_?selected_lo_!=hint_lo_:
                   selected_lo_!=0x80751cc0u&&selected_lo_!=0x80753cc0u&&(!override_||selected_lo_!=override_)))return fail(7);
                if(!equal(c,Hi,old_hi_))return fail(5);
            }else if(c.gpr[3]!=expected_hi_||!arena(expected_hi_)||selected_lo_>=expected_hi_||!equal(c,Lo,selected_lo_)||!equal(c,Hi,old_hi_))return fail(8);
        }else if(addr!=0x80520818u||c.lr!=addr||!equal(c,addr,e_.stop_word)||c.gpr[3]!=expected_hi_||!equal(c,Lo,selected_lo_)||!equal(c,Hi,expected_hi_))return fail(9);
        last_=c.inst_count;++stage_;return true;
    }
private:
    static constexpr uint32_t Sda=0x8070e8e0u,Base=Sda-3512u,Record=Sda-3516u,Fallback=Sda-3520u,Field=Sda-3216u,Mode=Sda-16864u,Lo=Sda-16400u,Hi=Sda-3472u;
    OsArenaExpectations e_;unsigned stage_=0,failure_=0;uint64_t last_=0;
    uint32_t sp_=0,r2_=0,msr_=0,boot_=0,legacy_=0,override_=0,hint_lo_=0,hint_hi_=0,boot0_=0,boot1_=0,fallback_=0,field_=0,guard_lo_=0,guard_hi_=0,old_hi_=0,selected_lo_=0,expected_hi_=0;
    uint8_t byte0_=0,byte1_=0;
    bool fail(unsigned reason){if(!failure_)failure_=reason;return false;}
    static bool arena(uint32_t a){return a>=0x80000000u&&a<=0x81800000u;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){const uint64_t end=uint64_t(a)+n;return n&&((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull))&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1);}
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t v){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==v;}
    template<class Cpu> bool boot_ok(Cpu& c) const{
        if(!equal(c,Base,0x80000000u)||!equal(c,Mode,1)||!equal(c,0x800000f4u,boot_)||!equal(c,0x80000034u,legacy_)||!equal(c,0x80000030u,override_)||!equal(c,0x8000310cu,hint_lo_)||!equal(c,0x80003110u,hint_hi_))return false;
        if(boot_)return equal(c,Record,boot_+12)&&equal(c,Field,boot1_)&&equal(c,Fallback,fallback_)&&equal(c,boot_+12,boot0_)&&equal(c,boot_+36,boot1_)&&c.mmu.read8(0x800030e8u)==uint8_t(boot0_)&&c.mmu.read8(0x800030e9u)==uint8_t(boot1_);
        if(c.mmu.read8(0x800030e8u)!=byte0_||c.mmu.read8(0x800030e9u)!=byte1_)return false;
        return legacy_?equal(c,Record,Fallback)&&equal(c,Field,byte1_)&&equal(c,Fallback,byte0_):equal(c,Record,0)&&equal(c,Field,field_)&&equal(c,Fallback,fallback_);
    }
};
}
