#pragma once
#include "wii_si_completion_ack_v668.h"
#include <array>
#include <cstdint>
namespace undercover::wii {
struct SiHelperExpectation {uint32_t site,root,end,branch;unsigned save_first=0,save_base=0;int32_t save_disp=0;};
class SiFirstHelper {
public:
    explicit SiFirstHelper(SiHelperExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w){
        if(stage_||error_||pc!=e_.site||w!=e_.branch||e_.root>=e_.end||
           e_.end-e_.root>4096u||((e_.root|e_.end|e_.site)&3u))return fail(1);
        ctx_=&c;gp_=c.gpr;msr_=c.msr;
        if(e_.save_first){
            if(e_.save_first<14||e_.save_first>31||(e_.save_base!=1&&e_.save_base!=11)||
               e_.save_disp>=0||e_.save_disp<-512||(e_.save_disp&3)||
               e_.save_disp+int32_t(31-e_.save_first)*4>=0)return fail(1);
            const auto base=uint64_t(gp_[e_.save_base]);
            if(base<0x80000200ull||base>0x81800000ull)return fail(1);
            save_address_=uint32_t(base+e_.save_disp);
            for(unsigned i=e_.save_first;i<32;++i){
                const auto a=save_address_+4u*(i-e_.save_first);
                if((a&3u)||a<0x80000000u||a>0x817ffffcu||
                   !c.mmu.get_ptr(a)||!c.mmu.get_ptr(a+3u))return fail(1);
            }
        }
        stage_=1;return true;
    }
    template<class C>bool entry(uint32_t a,C& c){
        if(!same(c)||stage_!=1||a!=e_.root||c.pc!=a||c.lr!=e_.site+4u)return fail(2);
        stage_=2;return true;
    }
    template<class C>bool instruction(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,bool native_mmio=false){
        if(!same(c)||stage_!=2||pc<e_.root||pc>=e_.end||(pc&3u)||
           !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w||
           !(native_mmio?ack.before(pc,w):ack.auxiliary_before()))return fail(3);
        if(native_mmio&&ack.phase()==SiCompletionAckTrace::Phase::Complete)return true;
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
        if(e_.save_first)for(unsigned i=e_.save_first;i<32;++i){
            const auto a=save_address_+4u*(i-e_.save_first);
            if(!c.mmu.get_ptr(a)||!c.mmu.get_ptr(a+3u)||c.mmu.read32(a)!=gp_[i])return fail(5);
        }
        stage_=4;return true;
    }
private:
    SiHelperExpectation e_;unsigned stage_=0,error_=0;const void* ctx_=nullptr;
    std::array<uint32_t,32> gp_{};uint32_t msr_=0,save_address_=0;
    bool fail(unsigned r){if(!error_)error_=r;return false;}
    template<class C>bool same(C& c)const{return !error_&&ctx_==&c&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==msr_&&!(c.msr&0x8000u);}
};
}
