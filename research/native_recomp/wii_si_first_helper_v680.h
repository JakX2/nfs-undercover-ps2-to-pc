#pragma once
#include "wii_si_completion_ack_v668.h"
#include <array>
#include <cstdint>
namespace undercover::wii {
struct SiHelperExpectation {uint32_t site,root,end,branch;};
class SiFirstHelper {
public:
    explicit SiFirstHelper(SiHelperExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w){
        if(stage_||error_||pc!=e_.site||w!=e_.branch||e_.root>=e_.end||
           e_.end-e_.root>4096u||((e_.root|e_.end|e_.site)&3u))return fail(1);
        ctx_=&c;gp_=c.gpr;msr_=c.msr;stage_=1;return true;
    }
    template<class C>bool entry(uint32_t a,C& c){
        if(!same(c)||stage_!=1||a!=e_.root||c.pc!=a||c.lr!=e_.site+4u)return fail(2);
        stage_=2;return true;
    }
    template<class C>bool instruction(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack){
        if(!same(c)||stage_!=2||pc<e_.root||pc>=e_.end||(pc&3u)||
           !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w||
           !ack.auxiliary_before())return fail(3);
        const auto op=w>>26,xo=(w>>1)&1023u;
        // The first dependency may have internal control flow, not another
        // external call, RFI, SC or MSR transition.
        if((op==16u||op==18u)&&(w&1u))return fail(4);
        if(op==17u||(op==31u&&xo==146u)||(op==19u&&(xo==50u||xo==528u||
           (xo==16u&&w!=0x4e800020u))))return fail(4);
        if(op==16u||op==18u){
            const uint32_t bits=op==16u?0x0000fffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
            const uint32_t disp=((w&bits)^sign)-sign;
            const uint32_t dst=(w&2u)?disp:pc+disp;
            if(dst<e_.root||dst>=e_.end)return fail(4);
        }
        if(w==0x4e800020u){
            if(c.lr!=e_.site+4u)return fail(5);
            stage_=3;
        }
        return true;
    }
    template<class C>bool returned(C& c,uint32_t pc){
        if(!same(c)||stage_!=3||pc!=e_.site+4u||c.pc!=pc||c.lr!=pc||
           c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.gpr[13]!=gp_[13])return fail(5);
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return fail(5);
        stage_=4;return true;
    }
private:
    SiHelperExpectation e_;unsigned stage_=0,error_=0;const void* ctx_=nullptr;
    std::array<uint32_t,32> gp_{};uint32_t msr_=0;
    bool fail(unsigned r){if(!error_)error_=r;return false;}
    template<class C>bool same(C& c)const{return !error_&&ctx_==&c&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==msr_&&!(c.msr&0x8000u);}
};
}
