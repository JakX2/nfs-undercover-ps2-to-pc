#pragma once
#include "native_sc_vector_v63.h"
#include <array>
#include <cstdint>
#include <stdexcept>
namespace undercover::wii {
// One-shot startup route, explicitly armed by an authenticated checkpoint.
// Not a replacement for IOS syscall dispatch or arbitrary guest exceptions.
class BootScRoute {
public:
    static constexpr uint32_t Call=0x805222e8u, Resume=Call+4u,
        Caller=0x80522044u, Source=0x805290a8u, Vector=0x80000c00u;
    enum class Phase { Idle, Armed, Executing, Returned, Failed };
    explicit BootScRoute(const std::array<uint8_t,28>& expected):bytes_(expected){
        for(unsigned i=0;i<bytes_.size();i+=4){
            const uint32_t w=(uint32_t(bytes_[i])<<24)|(uint32_t(bytes_[i+1])<<16)|
                (uint32_t(bytes_[i+2])<<8)|bytes_[i+3];
            if(w==0x4c00012cu)++isyncs_;
            if(w>>26==31&&((w>>1)&1023u)==598u)++syncs_;
        }
    }
    Phase phase()const noexcept{return phase_;}
    template<class Cpu>void arm(uint32_t addr,Cpu& c){
        if(phase_!=Phase::Idle||addr!=Call||c.lr!=Caller||!c.is_running)
            fail();
        context_=&c;sp_=c.gpr[1];msr_=c.msr;tick_=c.inst_count;
        phase_=Phase::Armed;
    }
    template<class Cpu>bool vector_trace(uint32_t addr,Cpu& c){
        if(phase_!=Phase::Executing)return false;
        if(addr!=Vector||c.pc!=Vector||context_!=&c||entries_++)fail();
        return true;
    }
    // False means "unrelated call: use the preexisting IOS handler".
    // True means native RFI has returned synchronously to the next label.
    // An armed mismatch or an unarmed call at this precise startup edge
    // is an error, never an invitation to substitute the HLE handler.
    template<class Cpu,class Native,class Verify>
    bool dispatch(Cpu& c,Native native,Verify verify){
        const bool target=c.pc==Call&&c.lr==Caller;
        if(phase_!=Phase::Armed){
            if(phase_==Phase::Executing||target)fail();
            return false;
        }
        if(!target||context_!=&c||!c.is_running||c.gpr[1]!=sp_||
           c.msr!=msr_||(c.msr&0x8000u)||c.dispatch_saved_ctx||
           c.inst_count<tick_||c.inst_count-tick_!=1u||
           c.mmu.read32(Call)!=0x44000002u||c.mmu.read32(Resume)!=0x4e800020u)
            fail();
        for(unsigned i=0;i<bytes_.size();++i)
            if(c.mmu.read8(Source+i)!=bytes_[i]||c.mmu.read8(Vector+i)!=bytes_[i])fail();
        const auto gp=c.gpr;
        const auto hid=c.hid0,lr=c.lr,ctr=c.ctr;
        const auto sy=c.guest_sync_count,isy=c.guest_isync_count;
        const auto before=c.inst_count;
        phase_=Phase::Executing;
        try{
            boot_native_sc(c,Vector,bytes_,native);
            if(entries_!=1||!c.is_running||c.pc!=Resume||c.srr0!=Resume||
               c.msr!=msr_||c.lr!=lr||c.ctr!=ctr||c.hid0!=hid||
               c.gpr[1]!=sp_||c.inst_count-before!=7u||
               c.guest_sync_count-sy!=syncs_||c.guest_isync_count-isy!=isyncs_||
               !verify(c,gp,hid))fail();
            for(unsigned i=0;i<bytes_.size();++i)
                if(c.mmu.read8(Source+i)!=bytes_[i]||c.mmu.read8(Vector+i)!=bytes_[i])fail();
            phase_=Phase::Returned;
        }catch(...){phase_=Phase::Failed;throw;}
        return true;
    }
    template<class Cpu>bool returned(const Cpu& c)const{
        return phase_==Phase::Returned&&context_==&c&&c.is_running&&
               c.pc==Caller&&c.lr==Caller&&c.msr==msr_&&c.gpr[1]==sp_;
    }
private:
    std::array<uint8_t,28> bytes_;
    Phase phase_=Phase::Idle;
    const void* context_=nullptr;
    uint32_t sp_=0,msr_=0;
    uint64_t tick_=0;
    unsigned entries_=0,syncs_=0,isyncs_=0;
    [[noreturn]]void fail(){phase_=Phase::Failed;throw std::runtime_error("V570 boot SC route rejected");}
};
}
