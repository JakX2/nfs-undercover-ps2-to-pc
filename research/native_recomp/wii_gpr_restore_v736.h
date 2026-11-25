#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Verifies a direct native compiler restore leaf. No register or memory writes.
struct GprRestoreExpectation{
    uint32_t site,root,branch;unsigned first,base;int32_t disp;
};
class GprRestoreWitness{
public:
    explicit GprRestoreWitness(GprRestoreExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,const std::array<uint32_t,32>& original){
        if(stage_||error_||!safe(c)||pc!=e_.site||w!=e_.branch||
           w>>26!=18u||(w&3u)!=1u||pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u)!=e_.root||
           e_.first<14||e_.first>31||(e_.base!=1&&e_.base!=11)||
           e_.disp>=0||e_.disp<-512||(e_.disp&3)||e_.disp+int32_t(31-e_.first)*4>=0||
           !mapped(c,pc)||c.mmu.read32(pc)!=w||e_.root<0x80000000u||
           uint64_t(e_.root)+4u*(33u-e_.first)>0x81800000u||
           c.inst_count>UINT64_MAX-32u)return fail(1);
        const int64_t frame=int64_t(c.gpr[e_.base])+e_.disp;
        if(frame<0x80000000ll||frame+4ll*(32u-e_.first)>0x81800000ll||(frame&3))return fail(1);
        address_=uint32_t(frame);initial_=c.gpr;expected_=original;cpu_=&c;tick_=c.inst_count;
        msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;ctr_=c.ctr;xer_=c.xer;cr_=pack_cr(c);
        if(!memory(c))return fail(2);
        stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc){
        if(stage_!=1||!common(c)||pc!=e_.root||c.pc!=pc||c.lr!=e_.site+4u||
           c.inst_count!=tick_||!registers(c,0))return fail(3);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w){
        const unsigned loads=32u-e_.first;
        if(stage_!=2||!common(c)||visits_>loads||pc!=e_.root+4u*visits_||
           c.inst_count-tick_!=visits_+1u||c.lr!=e_.site+4u||!mapped(c,pc)||
           c.mmu.read32(pc)!=w||!registers(c,visits_))return fail(4);
        const uint32_t expected=visits_==loads?0x4e800020u:
            (32u<<26)|((e_.first+visits_)<<21)|(e_.base<<16)|(uint32_t(e_.disp+int32_t(visits_)*4)&0xffffu);
        if(w!=expected)return fail(5);
        ++visits_;if(visits_==loads+1u)stage_=3;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc){
        if(stage_!=3||!common(c)||pc!=e_.site+4u||c.pc!=pc||c.lr!=pc||
           c.inst_count-tick_!=visits_+1u||!registers(c,32u-e_.first))return fail(6);
        stage_=4;return true;
    }
private:
    GprRestoreExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> initial_{},expected_{};
    unsigned stage_=0,error_=0,visits_=0;uint64_t tick_=0;
    uint32_t address_=0,msr_=0,srr0_=0,srr1_=0,ctr_=0,xer_=0,cr_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>static bool mapped(C& c,uint32_t a){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);
    }
    template<class C>static uint32_t pack_cr(C& c){
        uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return v;
    }
    template<class C>bool memory(C& c)const{
        for(unsigned i=e_.first;i<32;++i){
            const auto a=address_+4u*(i-e_.first);
            if(!mapped(c,a)||c.mmu.read32(a)!=expected_[i])return false;
        }
        return true;
    }
    template<class C>bool common(C& c)const{
        return !error_&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&
               c.ctr==ctr_&&c.xer==xer_&&pack_cr(c)==cr_&&memory(c);
    }
    template<class C>bool registers(C& c,unsigned n)const{
        for(unsigned i=0;i<32;++i)if(c.gpr[i]!=(i>=e_.first&&i<e_.first+n?expected_[i]:initial_[i]))return false;
        return true;
    }
};
}
