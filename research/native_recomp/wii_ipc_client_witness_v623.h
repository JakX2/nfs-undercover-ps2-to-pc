#pragma once
#include "wii_native_ios_binding.h"
#include "wii_exception_vector_witness_v457.h"
#include <array>
#include <cstdint>
#include <vector>

namespace undercover::wii {
struct IpcClientExpectations {
    // Exact ordered call edges, derived privately from DOL and ELF.
    std::array<VectorEdge,17> edges;
    uint32_t handler,handler_word,return_word;
};
// Cold IPC client only. The guest creates its own heap and installs its own
// IRQ handler. This observer neither writes guest RAM nor pumps IOS.
class IpcClientWitness {
public:
    static constexpr uint32_t Call=0x80520948u,Return=Call+4u,Root=0x805194c4u;
    static constexpr uint32_t Stack=0x80751cb8u-88u,Sda=0x8070e8e0u;
    static constexpr uint32_t Table=0x80003040u,MaskA=0x800000c4u,MaskB=0x800000c8u;
    static constexpr uint32_t Lo=0x80003130u,Hi=0x80003134u,HeapLimit=0x10000u;
    static constexpr uint32_t IrqGlobal=Sda-3408u;
    explicit IpcClientWitness(const IpcClientExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    uint32_t heap_size()const noexcept{return size_;}
    uint32_t entry_refusal()const noexcept{return refusal_;}
    template<class Cpu>bool begin(Cpu& c){
        auto snap=NativeIosBinding::cold_snapshot();
        refusal_=0;
        if(stage_||error_){refusal_|=1u;return fail(1);}
        if(!c.is_running||c.pc!=Call||c.lr!=Call||!(c.msr&0x8000u)||c.dispatch_saved_ctx)refusal_|=2u;
        if(c.gpr[3]!=0)refusal_|=4u;
        if(c.gpr[1]!=Stack||c.gpr[13]!=Sda)refusal_|=8u;
        if(!snap||!idle(*snap))refusal_|=16u;
        if(!snap||snap->control!=0||snap->steps!=0)refusal_|=32u;
        if(e_.edges[0].pc!=Root||e_.edges[0].lr!=Return||
           !equal(c,Call,e_.edges[0].branch_word)||!equal(c,Root,e_.edges[0].entry_word))refusal_|=64u;
        if(!equal(c,MaskA,0xf7fff7f0u)||!equal(c,MaskB,0))refusal_|=128u;
        if(!mapped(c,Lo,8)||!mapped(c,Table,128))refusal_|=256u;
        if(!equal(c,IrqGlobal,Table))refusal_|=512u;
        if(e_.handler<0x80519094u||e_.handler>=Root||(e_.handler&3u)||
           !equal(c,e_.handler,e_.handler_word))refusal_|=1024u;
        if(refusal_)return fail(1);
        lo_=c.mmu.read32(Lo);hi_=c.mmu.read32(Hi);
        if(lo_<0x90000020u||(lo_&31u)||hi_>0x94000000u||uint64_t(lo_)+HeapLimit>=hi_)refusal_|=2048u;
        if(!equal(c,Sda-16336u,lo_)||!equal(c,Sda-3352u,hi_))refusal_|=4096u;
        if(lo_==0u||!mapped(c,lo_-1u,HeapLimit+2u))refusal_|=8192u;
        if(refusal_)return fail(2);
        heap_.resize(HeapLimit+2u);
        for(unsigned i=0;i<heap_.size();++i)heap_[i]=c.mmu.read8(lo_-1u+i);
        for(unsigned i=0;i<32;++i)irqs_[i]=c.mmu.read32(Table+4*i);
        if(irqs_[27]){refusal_|=16384u;return fail(2);}
        regs_=c.gpr;msr_=c.msr;start_=last_=c.inst_count;before_=*snap;ctx_=&c;
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        auto snap=NativeIosBinding::cold_snapshot();
        if(error_||stage_<1||stage_>18||ctx_!=&c||!c.is_running||c.pc!=addr||
           c.dispatch_saved_ctx||c.inst_count<=last_||c.inst_count-start_>2000000u||
           c.gpr[1]>regs_[1]||regs_[1]-c.gpr[1]>1024u||
           c.gpr[2]!=regs_[2]||c.gpr[13]!=regs_[13]||
           !snap||!idle(*snap)||snap->steps!=before_.steps||
           snap->ppc!=before_.ppc||snap->arm!=before_.arm||
           !equal(c,Lo,lo_)||!equal(c,Hi,hi_)||!equal(c,IrqGlobal,Table)||
           !equal(c,Sda-16336u,lo_)||!equal(c,Sda-3352u,hi_))return fail(3);
        if(stage_==18){
            if(addr!=Return||c.lr!=Return||c.gpr[1]!=regs_[1]||c.gpr[3]!=0||
               c.msr!=msr_||!equal(c,Return,e_.return_word)||
               !equal(c,MaskA,0xf7fff7e0u)||!equal(c,MaskB,0)||
               snap->control!=(control_&0x39u)||snap->irq_mask!=HollywoodIrq::IPC_PPC||
               !(snap->pi_mask&HollywoodIrq::PI_HOLLYWOOD)||
               !heap_valid(c))return fail(7);
            for(unsigned i=14;i<32;++i)if(c.gpr[i]!=regs_[i])return fail(7);
            for(unsigned i=0;i<32;++i)if(!equal(c,Table+4*i,i==27?e_.handler:irqs_[i]))return fail(7);
            ++stage_;return true;
        }
        const unsigned i=stage_-1;
        const auto& e=e_.edges[i];
        if(addr!=e.pc||c.lr!=e.lr||!equal(c,addr,e.entry_word)||!equal(c,c.lr-4u,e.branch_word))
            return fail(4);
        const bool disabled=i==8||i==13||i==14;
        if(c.msr!=(disabled?(msr_&~0x8000u):msr_))return fail(5);
        if(i<=15&&snap->control!=0)return fail(5);
        switch(i){
        case 0:if(c.gpr[1]!=regs_[1]||c.gpr[3]!=0)return fail(5);break;
        case 5:if(c.gpr[3]!=lo_)return fail(5);break;
        case 6:
            if(c.gpr[3]!=lo_||c.gpr[4]<32u||c.gpr[4]>=HeapLimit||(c.gpr[4]&31u))return fail(5);
            size_=c.gpr[4];break;
        case 8:case 14:if(c.gpr[3]!=1u)return fail(5);break;
        case 9:if(c.gpr[3]!=lo_+size_||!heap_valid(c))return fail(6);break;
        case 10:
            if(c.gpr[3]!=27u||c.gpr[4]!=e_.handler||!equal(c,Table+108u,0)||
               !equal(c,e_.handler,e_.handler_word))return fail(5);
            break;
        case 11:
            if(c.gpr[3]!=0x10u||!equal(c,Table+108u,e_.handler))return fail(5);
            break;
        case 13:if(c.gpr[3]!=0x10u)return fail(5);break;
        case 15:
            if(c.gpr[3]!=1u||!(c.gpr[4]&0x30u)||(c.gpr[4]&~0x3fu)||(c.gpr[4]&1u)||
               !(snap->pi_mask&HollywoodIrq::PI_HOLLYWOOD)||snap->irq_mask!=HollywoodIrq::IPC_PPC||
               !NativeIosBinding::begin_cold_control(c.gpr[4]))return fail(6);
            control_=c.gpr[4];break;
        case 16:if(!NativeIosBinding::finish_cold_control())return fail(6);break;
        default:break;
        }
        last_=c.inst_count;++stage_;return true;
    }
private:
    IpcClientExpectations e_;
    const void* ctx_=nullptr;
    unsigned stage_=0,error_=0;
    uint32_t refusal_=0;
    uint32_t lo_=0,hi_=0,size_=0,msr_=0,control_=0;
    uint64_t start_=0,last_=0;
    std::array<uint32_t,32> regs_{},irqs_{};
    std::vector<uint8_t> heap_;
    ColdIpcSnapshot before_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool idle(const ColdIpcSnapshot& s){
        using M=IpcMailbox;
        return !s.queued&&!s.replies&&!s.event&&!(s.control&(M::X1|M::Y1|M::Y2))&&
            !(s.flags&HollywoodIrq::IPC_PPC)&&!(s.pi_cause&s.pi_mask);
    }
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        if(!n)return false;
        const uint64_t end=uint64_t(a)+n;
        if(!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>bool heap_valid(Cpu& c)const{
        if(!size_||!mapped(c,lo_-1u,HeapLimit+2u)||c.mmu.read8(lo_-1u)!=heap_.front()||
           c.mmu.read8(lo_+HeapLimit)!=heap_.back())return false;
        bool changed=false;
        for(unsigned i=0;i<32;++i)changed|=c.mmu.read8(lo_+i)!=heap_[i+1];
        if(!changed)return false;
        for(unsigned i=size_;i<HeapLimit;++i)if(c.mmu.read8(lo_+i)!=heap_[i+1])return false;
        return true;
    }
};
}
