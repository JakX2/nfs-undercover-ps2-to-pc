#pragma once
#include "wii_native_ios_binding.h"
#include "wii_exception_vector_witness_v457.h"
namespace undercover::wii {
// Capture successful backend writes only, on the guest CPU thread. Do
// not service IOS or manufacture an interrupt during cold IRQ setup.
class IrqBootTrace {
public:
    bool begin(bool bound) noexcept {
        if(active_||count_||failed_||!bound){failed_=true;return false;}
        active_=true;return true;
    }
    void record(uint32_t addr,uint32_t value,unsigned width,bool native) noexcept {
        if(!active_)return;
        addr&=0x3fffffffu;
        if(width!=32||count_>=2||
           (count_==0&&(addr!=IosBus::PI_MASK||value!=0xf0u||native))||
           (count_==1&&(addr!=IosBus::IPC+HollywoodIrq::PPC_MASK||value!=HollywoodIrq::IPC_PPC||!native))){
            failed_=true;return;
        }
        ++count_;
    }
    bool complete() noexcept{
        const bool ok=active_&&!failed_&&count_==2;
        active_=false;if(!ok)failed_=true;return ok;
    }
    unsigned count()const noexcept{return count_;}
private:
    unsigned count_=0;bool active_=false,failed_=false;
};
inline thread_local IrqBootTrace irq_boot_trace{};
class IrqMmioWitness {
public:
    IrqMmioWitness(uint32_t start_word,VectorEdge next):word_(start_word),edge_(next){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu> bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=Start||c.lr!=Start||
           !equal(c,Start,word_)||!mapped(c,0x800000c0u,16)||!NativeIosBinding::active()||
           !irq_boot_trace.begin(true))return fail(1);
        before_=c.mmu.read32(0x800000c0u);after_=c.mmu.read32(0x800000ccu);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        stage_=1;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(stage_!=1||error_||!c.is_running||addr!=Disable||c.pc!=addr||
           c.lr!=0x80526678u||edge_.pc!=addr||edge_.lr!=c.lr||
           !equal(c,addr,edge_.entry_word)||!equal(c,c.lr-4,edge_.branch_word)||
           c.gpr[1]!=sp_||c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           c.inst_count<=last_)return fail(2);
        if(c.gpr[3]!=0xcd000000u||c.gpr[4]!=0xcc000000u||c.gpr[5]!=0xf0u||
           c.gpr[6]!=0||c.gpr[0]!=0x40000000u||
           !equal(c,0x800000c0u,before_)||!equal(c,0x800000ccu,after_)||
           !equal(c,0x800000c4u,0)||!equal(c,0x800000c8u,0))return fail(3);
        if(!irq_boot_trace.complete()||!NativeIosBinding::active()||
           c.mmu.read32(0xcc003004u)!=0xf0u||c.mmu.read32(0xcd000034u)!=0x40000000u||
           c.mmu.read32(0xcd800034u)!=0x40000000u)return fail(4);
        stage_=2;return true;
    }
private:
    static constexpr uint32_t Start=0x8052664cu,Disable=0x805265acu;
    uint32_t word_;VectorEdge edge_;unsigned stage_=0,error_=0;
    uint32_t before_=0,after_=0,sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
};
}
