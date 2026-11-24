#pragma once
#include "wii_irq_bank_binding_v481.h"
#include "wii_irq_bootstrap_v475.h"
namespace undercover::wii {
// Verify the genuine cold seven-bank SetInterruptMask call sequence.
// Only completed backend operations are recorded, not predicted accesses.
class IrqMaskIo {
public:
    bool begin(unsigned bank)noexcept{
        if(active_||bad_||bank!=done_||bank>=7){bad_=true;return false;}
        bank_=bank;events_=0;read_=0;active_=true;return true;
    }
    void record(bool write,uint32_t address,unsigned width,uint32_t value,bool native)noexcept{
        if(!active_)return;
        constexpr std::array<uint32_t,7> addr{0x0c00401cu,0x0c00500au,0x0d006c00u,
            0x0d006800u,0x0d006814u,0x0d006828u,0x0c003004u};
        constexpr std::array<uint32_t,7> masks{0u,0xfffffe07u,0xffffffd3u,
            0xffffd3f0u,0xfffff3f0u,0xfffffff0u,0u};
        const bool reads=bank_!=0&&bank_!=6;
        const bool native_expected=bank_!=1&&bank_!=6;
        const unsigned expected_width=bank_<2?16u:32u;
        if(bad_||(address&0x3fffffffu)!=addr[bank_]||width!=expected_width||
           native!=native_expected||events_>=unsigned(reads)+1u||
           (width==16u&&value>0xffffu)){bad_=true;return;}
        if(reads&&events_==0){
            if(write){bad_=true;return;}
            read_=value;
        }else{
            const uint32_t expected=bank_==0?0u:bank_==6?0xf0u:read_&masks[bank_];
            if(!write||value!=expected){bad_=true;return;}
        }
        ++events_;
    }
    bool finish()noexcept{
        const bool ok=active_&&!bad_&&events_==(bank_==0||bank_==6?1u:2u);
        active_=false;if(ok)++done_;else bad_=true;return ok;
    }
    unsigned done()const noexcept{return done_;}
private:
    unsigned bank_=0,events_=0,done_=0;uint32_t read_=0;bool active_=false,bad_=false;
};
inline thread_local IrqMaskIo irq_mask_io{};
struct IrqReturnExpectations {std::array<VectorEdge,5> edges;};
class IrqReturnWitness {
public:
    explicit IrqReturnWitness(const IrqReturnExpectations& e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||!matches(c,e_.edges[0])||
           c.pc!=Disable||c.lr!=0x80526678u||!IrqBankBinding::active()||
           !mapped(c,0x800000c0u,16)||!mapped(c,0x80003000u,196)||
           c.gpr[1]<0x80000100u||c.gpr[1]>0x817ffff8u)return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        pre_=c.mmu.read32(0x800000c0u);post_=c.mmu.read32(0x800000ccu);
        for(unsigned i=0;i<15;++i)dispatch_[i]=c.mmu.read32(0x80003000u+i*4u);
        for(unsigned i=0;i<15;++i)if(!dispatch_[i])return fail(1);
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>10||!c.is_running||c.pc!=addr||
           c.inst_count<=last_||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           c.msr!=(msr_&~0x8000u)||!equal(c,0x800000c0u,pre_)||
           !equal(c,0x800000c4u,0xfffffff0u)||!equal(c,0x800000c8u,0u)||
           !equal(c,0x800000ccu,post_)||!equal(c,r13_-3408u,0x80003040u))return fail(2);
        for(unsigned i=0;i<32;++i)if(!equal(c,0x80003040u+4u*i,0))return fail(3);
        for(unsigned i=0;i<15;++i)if(!equal(c,0x80003000u+i*4u,
              stage_==10&&i==4?Handler:dispatch_[i]))return fail(3);
        if(stage_<=7){
            constexpr std::array<uint32_t,7> masks{0xfffffff0u,0x07fffff0u,0x00fffff0u,
                0x007ffff0u,0x000ffff0u,0x0001fff0u,0x00007ff0u};
            if(addr!=SetMask||!matches(c,e_.edges[1])||c.gpr[1]!=sp_||
               c.gpr[3]!=masks[stage_-1]||c.gpr[4]!=0xfffffff0u)return fail(4);
            if(stage_>1&&!irq_mask_io.finish())return fail(5);
            if(!irq_mask_io.begin(stage_-1))return fail(5);
        }else if(stage_==8){
            if(addr!=Restore||!matches(c,e_.edges[2])||c.gpr[1]!=sp_||
               c.gpr[3]!=((msr_>>15)&1u)||!irq_mask_io.finish()||
               irq_mask_io.done()!=7)return fail(6);
            // Readback of the actual mask banks after the final write.
            if(c.mmu.read16(0xcc00401cu)!=0||
               (c.mmu.read16(0xcc00500au)&0x150u)||
               (c.mmu.read32(0xcd006c00u)&4u)||
               (c.mmu.read32(0xcd006800u)&0x405u)||
               (c.mmu.read32(0xcd006814u)&0x405u)||
               (c.mmu.read32(0xcd006828u)&5u)||
               c.mmu.read32(0xcc003004u)!=0xf0u||
               c.mmu.read32(0xcd000034u)!=0x40000000u)return fail(7);
        }else if(stage_==9){
            if(addr!=Setter||!matches(c,e_.edges[3])||c.gpr[1]!=sp_||
               c.gpr[3]!=4u||c.gpr[4]!=Handler||c.msr!=msr_)return fail(8);
        }else{
            if(addr!=Context||!matches(c,e_.edges[4])||c.gpr[1]!=sp_+32u||
               c.gpr[3]!=dispatch_[4]||c.msr!=msr_)return fail(9);
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Disable=0x805265acu,SetMask=0x805266e0u,Restore=0x805265d4u,
        Setter=0x80520e9cu,Context=0x80522eb8u,Handler=0x80526ce0u;
    IrqReturnExpectations e_;unsigned stage_=0,error_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,pre_=0,post_=0;uint64_t last_=0;
    std::array<uint32_t,15> dispatch_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
};
}
