#pragma once
#include "wii_native_ios_binding.h"
#include <array>
#include <cstdint>
#include <stdexcept>
namespace undercover::wii {
// Isolated first IOS_Open cache-flush syscall route. Unlike the early boot
// routes this permits EE=1, but only on a stable, idle native IPC transport.
// No IOS service or general exception dispatch is authorized here.
class OpenScRoute {
public:
    static constexpr uint32_t Call=0x805222e8u, Resume=Call+4u,
        Caller=0x80519a1cu, SubmitCaller=0x8051963cu, Source=0x805290a8u, Vector=0x80000c00u;
    enum class Phase { Idle, Armed, Executing, Returned, Failed };
    explicit OpenScRoute(const std::array<uint8_t,28>& expected,uint32_t caller=Caller):bytes_(expected),caller_(caller){
        if(caller_!=Caller&&caller_!=SubmitCaller)fail();
        for(unsigned i=0;i<bytes_.size();i+=4){
            const uint32_t w=(uint32_t(bytes_[i])<<24)|(uint32_t(bytes_[i+1])<<16)|
                (uint32_t(bytes_[i+2])<<8)|bytes_[i+3];
            if(w==0x4c00012cu)++isyncs_;
            if(w>>26==31&&((w>>1)&1023u)==598u)++syncs_;
        }
    }
    Phase phase()const noexcept{return phase_;}
    template<class Cpu>void arm(uint32_t addr,Cpu& c){
        const auto s=NativeIosBinding::cold_snapshot();
        if(phase_!=Phase::Idle||addr!=Call||c.pc!=Call||c.lr!=caller_||!c.is_running||
           !(c.msr&0x8000u)||c.dispatch_saved_ctx||!s||!quiet(*s))
            fail();
        context_=&c;sp_=c.gpr[1];msr_=c.msr;tick_=c.inst_count;snapshot_=*s;
        phase_=Phase::Armed;
    }
    template<class Cpu>bool vector_trace(uint32_t addr,Cpu& c){
        if(phase_!=Phase::Executing)return false;
        if(addr!=Vector||c.pc!=Vector||context_!=&c||entries_++||
           c.srr0!=Resume||c.srr1!=msr_||c.msr!=(msr_&~0x0000ef33u)||!stable())fail();
        return true;
    }
    // False means "unrelated call: use the preexisting IOS handler".
    // True means native RFI has returned synchronously to the next label.
    // An armed mismatch or an unarmed call at this precise startup edge
    // is an error, never an invitation to substitute the HLE handler.
    template<class Cpu,class Native,class Verify>
    bool dispatch(Cpu& c,Native native,Verify verify){
        const bool target=c.pc==Call&&c.lr==caller_;
        if(phase_!=Phase::Armed){
            if(phase_==Phase::Executing||target)fail();
            return false;
        }
        if(!target||context_!=&c||!c.is_running||c.gpr[1]!=sp_||
           c.msr!=msr_||!(c.msr&0x8000u)||c.dispatch_saved_ctx||!stable()||
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
            c.srr0=Resume;c.srr1=msr_;c.msr=msr_&~0x0000ef33u;c.pc=Vector;
            native(c);
            if(entries_!=1||!c.is_running||c.pc!=Resume||c.srr0!=Resume||
               c.msr!=msr_||c.srr1!=msr_||c.dispatch_saved_ctx||!stable()||
               c.lr!=lr||c.ctr!=ctr||c.hid0!=hid||
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
               c.pc==caller_&&c.lr==caller_&&c.msr==msr_&&c.gpr[1]==sp_&&
               !c.dispatch_saved_ctx&&stable();
    }
private:
    std::array<uint8_t,28> bytes_;
    uint32_t caller_;
    Phase phase_=Phase::Idle;
    const void* context_=nullptr;
    uint32_t sp_=0,msr_=0;
    uint64_t tick_=0;
    unsigned entries_=0,syncs_=0,isyncs_=0;
    ColdIpcSnapshot snapshot_{};
    static bool quiet(const ColdIpcSnapshot& s){
        using M=IpcMailbox;using H=HollywoodIrq;
        return !s.queued&&!s.replies&&!s.event&&!s.steps&&
            (s.control&(M::IY1|M::IY2))&&!(s.control&(M::X1|M::Y1|M::Y2))&&
            !(s.flags&H::IPC_PPC)&&s.irq_mask==H::IPC_PPC&&
            (s.pi_mask&H::PI_HOLLYWOOD)&&!(s.pi_cause&s.pi_mask);
    }
    bool stable()const{
        const auto s=NativeIosBinding::cold_snapshot();const auto& b=snapshot_;
        return s&&quiet(*s)&&s->control==b.control&&s->ppc==b.ppc&&s->arm==b.arm&&
            s->flags==b.flags&&s->irq_mask==b.irq_mask&&s->pi_cause==b.pi_cause&&
            s->pi_mask==b.pi_mask&&s->steps==b.steps;
    }
    [[noreturn]]void fail(){phase_=Phase::Failed;throw std::runtime_error("V637 open SC route rejected");}
};
}
