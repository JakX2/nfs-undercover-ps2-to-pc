#pragma once
#include "wii_pending_external_reentry_v932.h"
#include <span>
namespace undercover::wii {
struct SecondVectorExpectation {
    uint32_t trampoline,dispatcher,context,dispatcher_word;
    std::span<const uint32_t> vector,trampoline_words;
};
// Authenticated native labels only. Observe vector execution without
// synthesizing register stores, exception return, or dispatch.
class SecondVectorWitness {
public:
    explicit SecondVectorWitness(SecondVectorExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned vector_visits()const{return vv_;}
    unsigned trampoline_visits()const{return tv_;}
    uint64_t last_tick()const{return last_;}
    uint32_t gpr_mask()const{return gpr_mask_;}
    unsigned special_mask()const{return special_mask_;}
    template<class C>bool begin(C& c,PendingExternalReentry& second,uint32_t cause,uint32_t mask,bool held){
        if(second.stage()!=3u||second.captured().source()!=8u)return fail(1);
        return begin_captured(c,second.captured(),cause,mask,held);
    }
    // The first IPC exception also uses this original vector; the caller
    // captures the interrupted context before hardware entry.
    template<class C>bool begin_captured(C& c,ExternalReturnWitness& captured,uint32_t cause,uint32_t mask,bool held){
        if(stage_||error_||captured.stage()!=1u||!held||!safe(c)||c.pc!=ExternalVector||
           !captured.source()||(cause&mask)!=captured.source()||
           e_.vector.empty()||e_.vector.size()>64u||e_.trampoline_words.empty()||e_.trampoline_words.size()>64u||
           !mapped(c,e_.dispatcher)||c.mmu.read32(e_.dispatcher)!=e_.dispatcher_word)return fail(1);
        for(unsigned i=0;i<e_.vector.size();++i)if(!word(c,ExternalVector+4u*i,e_.vector[i]))return fail(1);
        for(unsigned i=0;i<e_.trampoline_words.size();++i)if(!word(c,e_.trampoline+4u*i,e_.trampoline_words[i]))return fail(1);
        ctx_=&c;captured_=&captured;cause_=cause;mask_=mask;last_=c.inst_count;
        gqr_=c.gqr;next_=ExternalVector;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,uint32_t cause,uint32_t mask,bool held){
        if(!common(c,cause,mask,held)||stage_>2u||edge_||local_poll_||pc!=next_||
           c.inst_count-last_!=1u||!word(c,pc,w)||!in_span(pc,stage_))return fail(2);
        const uint32_t base=stage_==1u?ExternalVector:e_.trampoline;
        const auto ws=stage_==1u?e_.vector:e_.trampoline_words;
        if(ws[(pc-base)/4u]!=w||++(stage_==1u?vv_:tv_)>128u)return fail(2);
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==17u)return fail(3);
        if(op==31u&&xo==146u&&(c.gpr[(w>>21)&31u]&0x8000u))return fail(3);
        if(w==0x4c000064u){
            if(stage_!=1u||(c.srr1&0x8000u)||canon(c.srr0)!=e_.trampoline)return fail(3);
            next_=e_.trampoline;edge_=2;expected_msr_=c.srr1;check_msr_=true;return true;
        }
        if(op==19u&&(xo==16u||xo==528u)){
            if(w&1u)return fail(3);
            if(!taken(c,w))return true;
            next_=canon(xo==16u?c.lr:c.ctr);
            if(next_!=(stage_==1u?e_.trampoline:e_.dispatcher))return fail(3);
            edge_=2;return true;
        }
        if(op==16u||op==18u){
            if(w&3u)return fail(3);
            const uint32_t dst=target(pc,w);
            if(in_span(dst,stage_)&&dst<=pc)local_poll_=true;
            if(op==18u||taken(c,w))next_=dst;
            if(!in_span(next_,stage_)){
                if(next_!=(stage_==1u?e_.trampoline:e_.dispatcher))return fail(3);
                // Pinned emitter returns to the outer dispatcher for a
                // non-link unconditional cross-root branch. A conditional
                // mapped branch can instead call the native root directly.
                edge_=op==18u?2u:1u;
            }
        }
        return true;
    }
    template<class C>bool poll(C& c,uint32_t cause,uint32_t mask,bool held){
        if(!common(c,cause,mask,held)||stage_>2u||c.inst_count!=last_)return fail(4);
        if(local_poll_&&c.pc==last_pc_){local_poll_=false;return true;}
        if(edge_==2u&&canon(c.pc)==next_&&(!check_msr_||c.msr==expected_msr_)){edge_=3;return true;}
        return fail(4);
    }
    template<class C>bool entry(C& c,uint32_t pc,uint32_t cause,uint32_t mask,bool held){
        if(!common(c,cause,mask,held)||stage_>2u||local_poll_||(edge_!=1u&&edge_!=3u)||
           c.pc!=pc||pc!=next_||pc!=(stage_==1u?e_.trampoline:e_.dispatcher)||
           c.inst_count-last_!=unsigned(edge_==3u)||!captured_||
           c.gpr[3]!=4u||c.gpr[4]!=e_.context)return fail(5);
        const auto saved=captured_->saved_integer(c,e_.context);
        gpr_mask_=saved.gpr_mask;special_mask_=saved.special_mask;
        if(!saved.valid||(stage_==1u?((gpr_mask_&0x38u)||(special_mask_&0x3eu)):!saved.ok()))return fail(6);
        if(stage_==2u&&(!word(c,e_.dispatcher,e_.dispatcher_word)||!vv_||!tv_))return fail(6);
        last_=c.inst_count;edge_=0;check_msr_=false;++stage_;return true;
    }
private:
    SecondVectorExpectation e_;ExternalReturnWitness* captured_=nullptr;const void* ctx_=nullptr;
    uint32_t cause_=0,mask_=0,next_=0,last_pc_=0,expected_msr_=0,gpr_mask_=0;
    unsigned stage_=0,error_=0,edge_=0,vv_=0,tv_=0,special_mask_=0;
    uint64_t last_=0;bool local_poll_=false,check_msr_=false;
    std::array<uint32_t,8> gqr_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,uint32_t cause,uint32_t mask,bool held)const{
        return !error_&&ctx_==&c&&held&&safe(c)&&cause==cause_&&mask==mask_&&c.gqr==gqr_;
    }
    template<class C>static bool mapped(C& c,uint32_t a){return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return mapped(c,a)&&c.mmu.read32(a)==w;}
    bool in_span(uint32_t a,unsigned s)const{
        const uint32_t base=s==1u?ExternalVector:e_.trampoline;
        const auto ws=s==1u?e_.vector:e_.trampoline_words;
        return !(a&3u)&&a>=base&&uint64_t(a)<uint64_t(base)+4u*ws.size();
    }
    static uint32_t canon(uint32_t a){return a<0x01800000u?a|0x80000000u:a;}
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool short_=w>>26==16u;const uint32_t m=short_?0xfffcu:0x03fffffcu,s=short_?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
