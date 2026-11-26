#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
// Cooperative OSSaveContext is not an external-exception capture.
// Observe only ABI-preserved registers and the saved continuation;
// volatile registers other than the setjmp-style result are not compared.
// This observer never writes guest memory or synthesizes an RFI.
class CooperativeContextWitness {
public:
    struct Geometry {
        uint32_t context,save,save_return,loader,rfi,active,physical,current;
        uint32_t saved_msr_mask;
    };
    explicit CooperativeContextWitness(Geometry e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool capture(C& c,bool held){
        if(stage_||error_||!safe(c,held)||c.pc!=e_.save||c.lr!=e_.save_return||
           c.gpr[3]!=e_.context||!aligned(e_.context)||!mapped(c,e_.context,0x2c8u)||
           !equal(c,e_.active,e_.context)||!equal(c,e_.physical,e_.context&0x3fffffffu)||
           !equal(c,e_.current,e_.context)||(c.msr&0x8000u)||!e_.saved_msr_mask||
           !c.gpr[1]||(c.gpr[1]&7u)||!mapped(c,c.gpr[1],8u))return fail(1);
        cpu_=&c;gp_=c.gpr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        msr_=c.msr&e_.saved_msr_mask;tick_=c.inst_count;stage_=1;return true;
    }
    // Call after the original save helper returns zero, before switching
    // to idle. A snapshot taken only after wake cannot prove provenance.
    template<class C>bool saved(C& c,bool held){
        if(stage_!=1u||!live(c,held)||c.inst_count<=tick_||
           c.pc!=e_.save_return||c.lr!=lr_||c.gpr[3]!=0u||
           !equal(c,e_.active,e_.context)||!equal(c,e_.current,e_.context)||
           !live_abi(c)||!mapped(c,e_.context,0x2c8u)||!stored(c))return fail(2);
        for(unsigned i=0;i<image_.size();++i){
            const auto addr=e_.context+4u*i;
            if(!mapped(c,addr,4u))return fail(2);
            image_[i]=c.mmu.read32(addr);
        }
        stage_=2;return true;
    }
    template<class C>bool preserved(C& c,bool held)const{
        if(stage_!=2u||!live(c,held)||!mapped(c,e_.context,0x2c8u))return false;
        for(unsigned i=0;i<image_.size();++i)if(!equal(c,e_.context+4u*i,image_[i]))return false;
        return true;
    }
    // The scheduler itself must already have installed the selected thread.
    template<class C>bool loader_entry(C& c,bool held){
        if(!preserved(c,held)||c.pc!=e_.loader||c.gpr[3]!=e_.context||
           (c.msr&0x8000u)||!selected(c)||c.inst_count<=tick_)return fail(3);
        load_tick_=c.inst_count;stage_=3;return true;
    }
    template<class C>bool before_rfi(C& c,uint32_t pc,uint32_t word,bool held){
        if(stage_!=3u||!live(c,held)||!selected(c)||pc!=e_.rfi||
           word!=0x4c000064u||!equal(c,pc,word)||c.inst_count<=load_tick_||
           c.srr0!=e_.save_return||c.srr1!=msr_||!restored_regs(c)||
           (c.msr&0x8000u))return fail(4);
        rfi_tick_=c.inst_count;stage_=4;return true;
    }
    template<class C>bool returned(C& c,bool held){
        if(stage_!=4u||!live(c,held)||!selected(c)||c.inst_count!=rfi_tick_||
           c.pc!=e_.save_return||c.msr!=msr_||!restored_regs(c))return fail(5);
        stage_=5;return true;
    }
    template<class C>bool resumed_at(C& c,bool held)const{
        return stage_==5u&&live(c,held)&&selected(c)&&c.inst_count==rfi_tick_&&
               c.pc==e_.save_return&&c.msr==msr_&&restored_regs(c);
    }
private:
    Geometry e_;const void* cpu_=nullptr;std::array<uint32_t,32> gp_{};
    std::array<uint32_t,0x2c8u/4u> image_{};
    uint32_t cr_=0,lr_=0,ctr_=0,xer_=0,msr_=0;
    uint64_t tick_=0,load_tick_=0,rfi_tick_=0;unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool aligned(uint32_t a){return a&&!(a&3u);}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        return n&&a>=0x80000000u&&end<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class C>static bool equal(C& c,uint32_t a,uint32_t v){
        return aligned(a)&&mapped(c,a,4u)&&c.mmu.read32(a)==v;
    }
    template<class C>static bool safe(C& c,bool held){
        return held&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;
    }
    template<class C>bool live(C& c,bool held)const{
        return !error_&&cpu_==&c&&safe(c,held)&&c.inst_count>=tick_&&c.inst_count-tick_<=32768u;
    }
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
    }
    template<class C>bool live_abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||(pack(c)&0x00fff000u)!=(cr_&0x00fff000u))return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>bool stored(C& c)const{
        const auto a=e_.context;
        if(!equal(c,a+4u,gp_[1])||!equal(c,a+8u,gp_[2])||!equal(c,a+12u,1u)||
           !equal(c,a+128u,cr_)||!equal(c,a+132u,lr_)||!equal(c,a+136u,ctr_)||
           !equal(c,a+140u,xer_)||!equal(c,a+408u,lr_)||!equal(c,a+412u,msr_)||
           (c.mmu.read16(a+0x1a2u)&2u))return false;
        for(unsigned i=13;i<32;++i)if(!equal(c,a+4u*i,gp_[i]))return false;
        return true;
    }
    template<class C>bool selected(C& c)const{
        return equal(c,e_.active,e_.context)&&equal(c,e_.physical,e_.context&0x3fffffffu)&&
               equal(c,e_.current,e_.context)&&mapped(c,e_.context+0x2c8u,2u)&&c.mmu.read16(e_.context+0x2c8u)==2u;
    }
    template<class C>bool restored_regs(C& c)const{
        return live_abi(c)&&pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_&&c.gpr[3]==1u;
    }
};
}
