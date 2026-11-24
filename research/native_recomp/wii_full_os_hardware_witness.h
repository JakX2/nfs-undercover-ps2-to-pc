#pragma once
#include <array>
#include <cstdint>
#include "wii_full_os_time_witness.h"

namespace undercover::wii {
struct OsHardwareExpectations {std::array<OsTimeEdge,12> edges;uint32_t copy_entry,copy_branch,stop_word;};
class FullOsHardwareWitness {
public:
    explicit FullOsHardwareWitness(OsHardwareExpectations e):e_(e){}
    bool active() const noexcept{return active_;}
    unsigned stage() const noexcept{return stage_;}
    unsigned failure() const noexcept{return failure_;}
    bool copied() const noexcept{return copied_;}
    bool copy_seen() const noexcept{return copy_seen_;}
    template<class Cpu> bool begin(Cpu& c){
        if(active_||failure_||!c.is_running||c.pc!=0x805265acu||c.lr!=0x805206b8u)return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr&~0x8000u;last_=c.inst_count;
        hid0_=c.hid0;hid2_=c.hid2;l2_=c.l2cr;fpscr_=c.fpscr;
        if(!mapped(c,Stamp,8)||!mapped(c,Pointer,4)||!mapped(c,Dest-1,30))return fail(1);
        time_={c.mmu.read32(Stamp),c.mmu.read32(Stamp+4)};
        ptr_=c.mmu.read32(Pointer);copied_=ptr_>=0x80000000u;
        if(copied_&&!mapped(c,ptr_,28))return fail(2);
        for(unsigned i=0;i<30;++i)dest_[i]=c.mmu.read8(Dest-1+i);
        for(unsigned i=0;i<28;++i)expected_[i]=copied_?c.mmu.read8(ptr_+i):(i<4?0:dest_[i+1]);
        active_=true;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(!active_||failure_||stage_>12||!c.is_running||c.pc!=addr||c.inst_count<=last_)return fail(3);
        if(c.msr!=msr_||c.gpr[2]!=r2_||c.gpr[13]!=r13_||!equal(c,Stamp,time_[0])||!equal(c,Stamp+4,time_[1])||c.hid2!=hid2_||c.l2cr!=l2_)return fail(4);
        if(addr==Copy){
            if(stage_!=1||!copied_||copy_seen_||c.lr!=0x805206c0u||c.gpr[3]!=Dest||c.gpr[4]!=ptr_||c.gpr[5]!=28||c.gpr[1]!=sp_||!equal(c,Copy,e_.copy_entry)||!equal(c,0x80523b30u,e_.copy_branch))return fail(5);
            copy_seen_=true;last_=c.inst_count;return true;
        }
        if(stage_==12){
            if(addr!=0x80520700u||c.lr!=addr||c.gpr[1]!=sp_||!equal(c,addr,e_.stop_word)||c.fpscr!=(fpscr_|4u)||c.hid4!=0x83900000u||c.hid0!=(hid0_|0x200u)||!perf_clear(c,6)||!params(c))return fail(8);
            ++stage_;active_=false;return true;
        }
        const auto& edge=e_.edges[stage_];
        if(addr!=edge.pc||c.lr!=edge.lr||!equal(c,addr,edge.entry_word)||!equal(c,edge.lr-4u,edge.branch_word))return fail(6);
        if(stage_!=9&&stage_!=10&&c.gpr[1]!=sp_)return fail(4);
        if(stage_==0){if(c.gpr[3]!=Dest||!equal(c,Pointer,ptr_))return fail(5);}
        else if(stage_<=6){if(c.gpr[3]!=0||!perf_clear(c,stage_-1)||!params(c))return fail(7);}
        else if(stage_==7){if(c.gpr[3]!=0x83900000u||!perf_clear(c,6))return fail(7);}
        else if(stage_==8){if(c.hid4!=0x83900000u||c.hid0!=hid0_)return fail(8);}
        else if(stage_==9){if(c.hid0!=hid0_)return fail(8);}
        else if(stage_==10){if(c.gpr[3]!=(hid0_|0x200u))return fail(8);}
        else if(stage_==11){if(c.hid0!=(hid0_|0x200u)||c.fpscr!=fpscr_)return fail(8);}
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Dest=0x806f4f00u,Pointer=0x800030f0u,Stamp=0x8070db30u,Copy=0x80004338u;
    OsHardwareExpectations e_;bool active_=false,copied_=false,copy_seen_=false;unsigned stage_=0,failure_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,hid0_=0,hid2_=0,l2_=0,fpscr_=0,ptr_=0;uint64_t last_=0;
    std::array<uint32_t,2> time_{};std::array<uint8_t,30> dest_{};std::array<uint8_t,28> expected_{};
    bool fail(unsigned why){if(!failure_)failure_=why;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        return n&&((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull))&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t v){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==v;}
    template<class Cpu> bool params(Cpu& c) const{
        if(copied_!=copy_seen_||!mapped(c,Dest-1,30)||c.mmu.read8(Dest-1)!=dest_[0]||c.mmu.read8(Dest+28)!=dest_[29])return false;
        for(unsigned i=0;i<28;++i)if(c.mmu.read8(Dest+i)!=expected_[i])return false;
        return true;
    }
    template<class Cpu> static bool perf_clear(Cpu& c,unsigned n){
        const std::array<uint32_t,6> regs{c.mmcr0,c.mmcr1,c.pmc[0],c.pmc[1],c.pmc[2],c.pmc[3]};
        for(unsigned i=0;i<n;++i)if(regs[i])return false;
        return true;
    }
};
}
