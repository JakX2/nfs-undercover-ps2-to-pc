#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only integer ABI and control-flow witness for the SI handler suffix.
// The surrounding authenticated ACK route must separately check device state.
struct SiHandlerReturnExpectation{uint32_t root,end,second_return,resume,resume_word;};
class SiHandlerReturnWitness{
public:
    explicit SiHandlerReturnWitness(SiHandlerReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned polls()const{return polls_;}
    bool pending()const{return pending_;}
    const std::array<uint32_t,32>& entry_gprs()const{return gpr_;}
    uint32_t entry_cr()const{return cr_nonvolatile_;}
    template<class C>bool capture(C& c){
        if(stage_||error_||!safe(c)||c.pc!=e_.root||c.lr!=e_.resume||
           !span(e_.root)||e_.end<=e_.root||e_.end-e_.root>4096u||
           !span(e_.second_return)||!word(c,e_.resume,e_.resume_word)||
           (e_.resume>=e_.root&&e_.resume<e_.end)||c.inst_count>UINT64_MAX-32768u)
            return fail(1);
        cpu_=&c;gpr_=c.gpr;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;
        cr_nonvolatile_=pack_cr(c)&0x00fff000u;start_tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool start(C& c,uint32_t pc,bool device){
        if(stage_!=1||!common(c)||!device||pc!=e_.second_return||c.pc!=pc||c.lr!=pc||
           c.inst_count<=start_tick_||c.inst_count-start_tick_>32768u)return fail(2);
        next_=pc;last_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool device,bool authenticated_restore=false){
        // Compatibility lane for older single-call scopes.
        return before_slot(c,pc,w,device,authenticated_restore?1u:0u);
    }
    template<class C>bool before_authenticated(C& c,uint32_t pc,uint32_t w,bool device,unsigned slot){
        if(!slot||slot>12u)return fail(8);
        return before_slot(c,pc,w,device,slot);
    }
    // Admission is separate from direct-call slots. The installer must
    // authenticate the precise original bctrl and full target identity.
    template<class C>bool before_authenticated_indirect(C& c,uint32_t pc,uint32_t w,bool device,unsigned slot){
        if((slot!=6u&&slot!=11u)||!(completed_calls_&16u)||w!=0x4e800421u)return fail(8);
        return before_slot(c,pc,w,device,slot,true);
    }
    // Authenticate a new linked boundary without executing or admitting it.
    // Repeated indirect sites are classified rather than called.
    template<class C>bool stop_before_call(C& c,uint32_t pc,uint32_t w,bool device,unsigned slot,unsigned kind){
        if(stage_!=2||!common(c)||!device||pending_||active_call_||pc!=next_||
           !span(pc)||!word(c,pc,w)||c.inst_count-last_!=(visits_?1u:0u)||
           visits_>=1024u||!slot||slot>12u||
           !((kind==1u&&w>>26==18u&&(w&3u)==1u)||(kind==2u&&w==0x4e800421u)))return fail(8);
        last_=c.inst_count;++visits_;stage_=6;return true;
    }
    unsigned completed_calls()const{return completed_calls_;}
    unsigned active_call()const{return active_call_;}
    bool callback_pending()const{return active_indirect_;}
private:
    template<class C>bool before_slot(C& c,uint32_t pc,uint32_t w,bool device,unsigned slot,bool indirect=false){
        if(stage_!=2||!common(c)||!device||pending_||active_call_||pc!=next_||!span(pc)||!word(c,pc,w)||
           c.inst_count-last_!=(visits_?1u:0u)||++visits_>1024u)return fail(3);
        last_=c.inst_count;
        const auto op=w>>26,xo=(w>>1)&1023u;
        if(slot){
            if((completed_calls_&(1u<<(slot-1u)))||(!indirect&&(op!=18u||(w&3u)!=1u))||(indirect&&w!=0x4e800421u)||!span(pc+4u))return fail(8);
            active_call_=slot;active_indirect_=indirect;next_=pc+4u;return true;
        }
        if(w==0x4e800020u){
            if(!abi(c)||c.lr!=e_.resume)return fail(5);
            stage_=3;return true;
        }
        // No newly encountered calls, external branches, exception returns,
        // system calls, interrupt enable changes or indirect transfers.
        if(op==17u||(op==31u&&xo==146u)||(op==19u&&(xo==16u||xo==50u||xo==528u)))return fail(4);
        next_=pc+4u;
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            const uint32_t mask=op==16u?0xfffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
            const uint32_t dst=pc+(((w&mask)^sign)-sign);
            if(!span(dst))return fail(4);
            if(op==18u||taken(c,w))next_=dst;
            if(dst<=pc){
                pending_=true;poll_pc_=pc;poll_gpr_=c.gpr;poll_cr_=pack_cr(c);
                poll_lr_=c.lr;poll_ctr_=c.ctr;poll_xer_=c.xer;
            }
        }
        if(!span(next_))return fail(4);
        return true;
    }
public:
    template<class C>bool restore_returned(C& c,uint32_t pc,unsigned visits,bool device,unsigned slot=1){
        if(visits>19u)return fail(8);
        return helper_returned(c,pc,visits,device,slot);
    }
    template<class C>bool helper_returned(C& c,uint32_t pc,unsigned visits,bool device,unsigned slot=1){
        return complete_call(c,pc,visits,device,slot,128u);
    }
    // Only the independently authenticated fourth SI transfer call can
    // use the larger 256-visit limit (108 original words plus four leaves).
    template<class C>bool transfer_returned(C& c,uint32_t pc,unsigned visits,bool device){
        return complete_call(c,pc,visits,device,4u,256u);
    }
    template<class C>bool alarm_returned(C& c,uint32_t pc,unsigned visits,bool device){
        return complete_call(c,pc,visits,device,5u,256u);
    }
    // The full callback witness must prove its original BLR, outer
    // dispatch poll/tick and matching caller label before this handoff.
    // Count the real elapsed ticks, including both dispatcher ticks, not
    // just the last epilogue's instruction visits.
    template<class C>bool callback_returned(C& c,uint32_t pc,uint64_t call_tick,bool verified,bool device,unsigned slot){
        if(!verified||(slot!=6u&&slot!=11u)||!active_indirect_||call_tick!=last_||
           c.inst_count<=call_tick||c.inst_count-call_tick<14u||
           c.inst_count-call_tick>16385u)return fail(8);
        return complete_call(c,pc,unsigned(c.inst_count-call_tick-1u),device,slot,16384u,true);
    }
private:
    template<class C>bool complete_call(C& c,uint32_t pc,unsigned visits,bool device,unsigned slot,unsigned limit,bool indirect=false){
        if(stage_!=2||!common(c)||!device||!active_call_||active_call_!=slot||active_indirect_!=indirect||pending_||
           pc!=next_||c.pc!=pc||c.lr!=pc||visits<2u||visits>limit||c.inst_count-last_!=visits+1u)return fail(8);
        completed_calls_|=1u<<(active_call_-1u);active_call_=0;active_indirect_=false;last_=c.inst_count-1u;return true;
    }
public:
    template<class C>bool poll(C& c,bool device){
        if(!common(c)||!device||active_call_||c.inst_count!=last_)return fail(6);
        if(stage_==2){
            if(!pending_||c.pc!=poll_pc_||c.gpr!=poll_gpr_||pack_cr(c)!=poll_cr_||
               c.lr!=poll_lr_||c.ctr!=poll_ctr_||c.xer!=poll_xer_||++polls_>1024u)return fail(6);
            pending_=false;return true;
        }
        if(stage_!=3||pending_||c.pc!=e_.resume||c.lr!=e_.resume||!abi(c))return fail(6);
        stage_=4;return true;
    }
    template<class C>bool resumed(C& c,uint32_t pc,uint32_t w,bool device){
        if(stage_!=4||!common(c)||!device||pending_||pc!=e_.resume||c.pc!=pc||
           w!=e_.resume_word||!word(c,pc,w)||c.inst_count-last_!=2u||!abi(c)||c.lr!=pc)
            return fail(7);
        stage_=5;return true;
    }
private:
    SiHandlerReturnExpectation e_;
    const void* cpu_=nullptr;unsigned stage_=0,error_=0,visits_=0,polls_=0;
    bool pending_=false,active_indirect_=false;
    unsigned active_call_=0,completed_calls_=0;
    std::array<uint32_t,32> gpr_{},poll_gpr_{};
    uint32_t msr_=0,srr0_=0,srr1_=0,cr_nonvolatile_=0,next_=0,poll_pc_=0,
             poll_cr_=0,poll_lr_=0,poll_ctr_=0,poll_xer_=0;
    uint64_t start_tick_=0,last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool span(uint32_t pc)const{return !(pc&3u)&&pc>=0x80000000u&&pc<0x81800000u&&pc>=e_.root&&pc<e_.end;}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c)const{
        return !error_&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&
            c.inst_count>=start_tick_&&c.inst_count-start_tick_<=32768u;
    }
    template<class C>static uint32_t pack_cr(C& c){
        uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return v;
    }
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gpr_[1]||c.gpr[2]!=gpr_[2]||c.gpr[13]!=gpr_[13]||
           (pack_cr(c)&0x00fff000u)!=cr_nonvolatile_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gpr_[i])return false;
        return true;
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        const bool ctr_ok=(bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u));
        const bool cr_ok=(bo&16u)||((bool((pack_cr(c)>>(31u-bi))&1u))==bool(bo&8u));
        return ctr_ok&&cr_ok;
    }
};
}
