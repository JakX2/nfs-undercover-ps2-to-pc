#pragma once
#include "wii_external_return_v706.h"
#include <array>
#include <cstdint>
namespace undercover::wii {
// The installer must authenticate all native labels and direct edges.
// This observer never performs a context switch or writes guest state.
struct LiveEpilogueExpectation{
    uint32_t dispatcher,enable,reschedule,disable,restore,loader,switch_target,context;
    int32_t counter_disp,hint_disp;
    unsigned context_reg,gqr_mask;
    uint32_t switch_getter=0,switch_getter_return=0,switch_tail=0;
};
class LiveEpilogueWitness{
public:
    explicit LiveEpilogueWitness(LiveEpilogueExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned entry_refusal()const{return refusal_;}
    unsigned select_state()const{return select_state_;}
    template<class C>bool begin(C& c,ExternalReturnWitness& captured,uint32_t cause,uint32_t mask){
        return begin_impl(c,captured,cause,mask,false);
    }
    template<class C>bool begin_pending(C& c,ExternalReturnWitness& captured,uint32_t cause,uint32_t mask){
        return begin_impl(c,captured,cause,mask,true);
    }
    template<class C>bool pending_rfi_return(C& c,uint32_t cause,uint32_t mask){
        if(stage_!=2u||!pending_return_||!captured_||c.gqr!=gqr_||!captured_->pending_rfi_return(c,cause,mask))return fail(8);
        stage_=3;return true;
    }
private:
    template<class C>bool begin_impl(C& c,ExternalReturnWitness& captured,uint32_t cause,uint32_t mask,bool pending){
        refusal_=0;
        if(stage_||error_||captured.stage()!=1)refusal_|=1u;
        if(!safe(c)||!c.inst_count||c.pc!=e_.dispatcher)refusal_|=2u;
        if(e_.context_reg<14||e_.context_reg>31||c.gpr[e_.context_reg]!=e_.context)refusal_|=4u;
        if(!captured.saved_integer(c,e_.context).ok())refusal_|=8u;
        const uint32_t source=pending?captured.source():0u;
        if((cause&mask)!=source||(pending&&(!source||!captured.pending_source(c,cause,mask))))refusal_|=16u;
        if(!e_.gqr_mask||e_.gqr_mask>255u)refusal_|=32u;
        if((e_.switch_getter||e_.switch_getter_return||e_.switch_tail)&&
           (!e_.switch_getter||!e_.switch_getter_return||!e_.switch_tail||!e_.switch_target||!pending))refusal_|=32u;
        if(refusal_)return fail(1);
        const int64_t counter=int64_t(c.gpr[13])+e_.counter_disp,hint=int64_t(c.gpr[13])+e_.hint_disp;
        if(counter<0x80000000ll||counter>0x817ffffcll||hint<0x80000000ll||hint>0x817ffffcll||
           (counter&3)||(hint&3)||counter==hint){refusal_|=64u;return fail(1);}
        counter_=uint32_t(counter);hint_=uint32_t(hint);
        if(!mapped(c,counter_)||!mapped(c,hint_)){refusal_|=128u;return fail(1);}
        initial_=c.mmu.read32(counter_);if(!initial_||initial_>1024u){refusal_|=256u;return fail(1);}
        pending_return_=pending;pending_source_=source;cpu_=&c;captured_=&captured;cause_=cause;mask_=mask;msr_=c.msr;
        gp_=c.gpr;cr_=pack(c)&0x00fff000u;next_=e_.dispatcher;last_=c.inst_count-1u;stage_=1;return true;
    }
public:
    template<class C>bool entry(C& c,uint32_t pc,uint32_t cause,uint32_t mask){
        if(select_state_==2u){
            if(stage_!=1u||!common(c,cause,mask)||pc!=e_.switch_target||c.pc!=pc||next_!=pc||
               c.inst_count-last_!=1u||depth_!=1u||c.lr!=stack_[0]||c.gpr[3]!=0u||
               !captured_->saved_integer(c,e_.context).ok())return fail(2);
            last_=c.inst_count;select_state_=3u;return true;
        }
        if(stage_!=1||!common(c,cause,mask)||pending_||pc!=next_||c.pc!=pc||
           c.inst_count!=last_||!entry_due_||!depth_||c.lr!=stack_[depth_-1])return fail(2);
        entry_due_=false;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,uint32_t cause,uint32_t mask){
        const bool outer_resume=select_state_==5u;
        if(stage_!=1||!common(c,cause,mask)||entry_due_||pending_||pc!=next_||
           (select_state_==1u||select_state_==2u||select_state_==4u)||
           c.inst_count-last_!=(outer_resume?2u:1u)||!mapped(c,pc)||c.mmu.read32(pc)!=w||++visits_>512u)return fail(3);
        if(outer_resume){
            if(pc!=e_.dispatcher+8u||c.pc!=pc||depth_||!getter_returned_||c.lr!=pc)return fail(7);
            select_state_=6u;
        }
        if(getter_pending_&&depth_==1u){
            if(select_state_!=3u||pc!=e_.switch_getter_return||c.gpr[3]!=e_.context||c.lr!=pc)return fail(7);
            getter_pending_=false;getter_returned_=true;
        }
        last_=c.inst_count;
        if(pc==e_.dispatcher+4u){
            if(depth_||!abi(c)||c.gpr[3]!=initial_||c.mmu.read32(counter_)!=initial_-1u||c.lr!=pc||calls_!=7u)return fail(4);
        }
        if(pc==e_.dispatcher+8u){
            const auto hint=c.mmu.read32(hint_);
            if(depth_||!abi(c)||c.lr!=pc||calls_!=15u||
               (select_state_==6u?(!getter_returned_||(hint&&hint!=switch_hint_)):hint!=0u))return fail(4);
        }
        if(pc==e_.dispatcher+12u){
            if(depth_||!abi(c)||c.gpr[3]!=e_.context||!captured_->saved_integer(c,e_.context).ok()||calls_!=15u)return fail(4);
            for(unsigned i=0;i<8;++i){
                const uint32_t a=e_.context+0x1a4u+4*i;if(!mapped(c,a))return fail(4);
                gqr_[i]=(e_.gqr_mask&(1u<<i))?c.mmu.read32(a):c.gqr[i];
            }
        }
        if(w==0x4c000064u){
            if(depth_!=1||calls_!=31u||c.mmu.read16(e_.context+0x1a2u)!=0||c.gqr!=gqr_||
               !(pending_return_?captured_->before_pending_rfi(c,pc,w,cause,mask):captured_->before_rfi(c,pc,w,cause,mask)))return fail(5);
            stage_=2;return true;
        }
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        next_=pc+4u;
        if(op==18u&&(w&1u)){
            if(w&2u||depth_>=2u)return fail(6);
            const uint32_t dst=target(pc,w);
            if(select_state_==3u){
                if(depth_!=1u||getter_pending_||getter_returned_||dst!=e_.switch_getter||
                   pc+4u!=e_.switch_getter_return)return fail(7);
                getter_pending_=true;stack_[depth_++]=next_;next_=dst;entry_due_=true;return true;
            }
            const unsigned bit=dst==e_.enable?1u:dst==e_.disable?2u:dst==e_.restore?4u:dst==e_.reschedule?8u:dst==e_.loader?16u:0u;
            if(!bit||(calls_&bit)||(bit==1u&&(pc!=e_.dispatcher||depth_))||
               ((bit==2u||bit==4u)&&(depth_!=1||stack_[0]!=e_.dispatcher+4u))||
               (bit==8u&&(pc!=e_.dispatcher+4u||depth_))||(bit==16u&&(pc!=e_.dispatcher+12u||depth_)))return fail(6);
            calls_|=bit;stack_[depth_++]=next_;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u||!depth_)return fail(6);
            if(!taken(c,w))return true;
            if(c.lr!=stack_[depth_-1])return fail(6);
            if(select_state_==3u&&depth_==1u){
                if(!getter_returned_||getter_pending_||!abi(c)||!captured_->saved_integer(c,e_.context).ok())return fail(7);
                select_state_=4u;
            }
            next_=stack_[--depth_];return true;
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||(op==16u&&(w&1u)))return fail(6);
        if(op==31u&&xo==146u){
            if(c.gpr[(w>>21)&31u]&0x8000u)return fail(6);
            return true;
        }
        if(op==16u||op==18u){
            if(w&3u)return fail(6);
            const uint32_t dst=target(pc,w);
            if(op==18u||taken(c,w)){
                if(dst==e_.switch_target){
                    if(!e_.switch_getter||select_state_||pc!=e_.switch_tail||op!=18u||
                       depth_!=1u||stack_[0]!=e_.dispatcher+8u||c.lr!=stack_[0]||calls_!=15u||
                       c.gpr[3]!=0u||!(switch_hint_=c.mmu.read32(hint_))||
                       c.mmu.read32(counter_)!=initial_-1u||!captured_->saved_integer(c,e_.context).ok())return fail(7);
                    select_state_=1u;next_=dst;return true;
                }
                next_=dst;
            }
            if(dst<=pc){
                pending_=true;poll_pc_=pc;poll_gp_=c.gpr;poll_cr_=pack(c);
                poll_lr_=c.lr;poll_ctr_=c.ctr;poll_xer_=c.xer;poll_msr_=c.msr;
                poll_srr0_=c.srr0;poll_srr1_=c.srr1;
            }
        }
        return true;
    }
    template<class C>bool poll(C& c,uint32_t cause,uint32_t mask){
        if(stage_==2||stage_==3){
            // GQR state must already be correct at the first RFI poll;
            // a later resume check cannot excuse an earlier bad restore.
            if(pending_return_||c.gqr!=gqr_||!captured_->poll(c,cause,mask))return fail(8);
            ++stage_;return true;
        }
        if(select_state_==1u||select_state_==4u){
            if(stage_!=1u||!common(c,cause,mask)||c.pc!=next_||c.inst_count!=last_||
               c.lr!=e_.dispatcher+8u||!captured_->saved_integer(c,e_.context).ok())return fail(8);
            select_state_=select_state_==1u?2u:5u;return true;
        }
        if(stage_!=1||!common(c,cause,mask)||!pending_||c.pc!=poll_pc_||c.inst_count!=last_||
           c.gpr!=poll_gp_||pack(c)!=poll_cr_||c.lr!=poll_lr_||c.ctr!=poll_ctr_||c.xer!=poll_xer_||
           c.msr!=poll_msr_||c.srr0!=poll_srr0_||c.srr1!=poll_srr1_)return fail(8);
        pending_=false;return true;
    }
    template<class C>bool resume(C& c,uint32_t pc,uint32_t w,uint32_t cause,uint32_t mask){
        if(stage_!=4||c.gqr!=gqr_||!captured_->resume(c,pc,w,cause,mask))return fail(9);
        stage_=5;return true;
    }
private:
    LiveEpilogueExpectation e_;ExternalReturnWitness* captured_=nullptr;const void* cpu_=nullptr;
    unsigned stage_=0,error_=0,visits_=0,depth_=0,calls_=0,refusal_=0;
    bool pending_return_=false;
    unsigned select_state_=0;uint32_t switch_hint_=0;
    bool getter_pending_=false,getter_returned_=false;
    uint32_t pending_source_=0;
    uint32_t cause_=0,mask_=0,msr_=0,cr_=0,counter_=0,hint_=0,initial_=0,next_=0,poll_pc_=0,poll_cr_=0,poll_lr_=0,poll_ctr_=0,poll_xer_=0,poll_msr_=0,poll_srr0_=0,poll_srr1_=0;
    uint64_t last_=0;bool entry_due_=false,pending_=false;
    std::array<uint32_t,2> stack_{};
    std::array<uint32_t,32> gp_{},poll_gp_{};
    std::array<uint32_t,8> gqr_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,uint32_t cause,uint32_t mask)const{
        return !error_&&cpu_==&c&&safe(c)&&cause==cause_&&mask==mask_&&(cause&mask)==pending_source_;
    }
    template<class C>static bool mapped(C& c,uint32_t pc){return !(pc&3u)&&pc>=0x80000000u&&pc<=0x817ffffcu&&c.mmu.get_ptr(pc)&&c.mmu.get_ptr(pc+3u);}
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return v;
    }
    template<class C>bool abi(C& c)const{
        if(c.msr!=msr_||c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.gpr[13]!=gp_[13]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool short_=w>>26==16u;const uint32_t mask=short_?0xfffcu:0x03fffffcu,sign=short_?0x8000u:0x02000000u;
        return pc+(((w&mask)^sign)-sign);
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));
    }
};
}
