#pragma once
#include "wii_idle_selection_v1319.h"

namespace undercover::wii {
// Native control-flow observer from the second idle RFI to OSLoadContext.
// State transitions remain the responsibility of IdleSelectionWitness.
struct IdleRouteExpectation {
    uint32_t enable,enable_resume,select,enable_return,loader;
    std::span<const ReplyNativeWord> words;
    std::span<const VectorEdge> direct,indirect;
};
class IdleRouteWitness {
public:
    explicit IdleRouteWitness(IdleRouteExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!c.is_running||c.in_callback||c.dispatch_saved_ctx||
           c.pc!=e_.enable_resume||c.lr!=e_.enable_return||!(c.msr&0x8000u)||
           e_.words.empty()||e_.words.size()>512u||e_.direct.size()!=4u||e_.indirect.empty()||
           !known(c,e_.enable,e_.enable_resume)||!known(c,e_.select,e_.enable_return))return fail(1);
        cpu_=&c;last_=c.inst_count;active_=e_.enable;next_=c.pc;
        stage_=1;outer_=true;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||outer_||pc!=next_||c.pc!=pc||c.lr!=ret_||
           c.inst_count-last_!=(resume_?1u:0u)||!known(c,pc,pc))return fail(2);
        active_=pc;entry_due_=false;
        if(pc==e_.loader){
            if(resume_||!ret_)return fail(2);
            stage_=2;
        }
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||entry_due_||outer_||poll_due_||pc!=next_||
           c.inst_count-last_!=(resume_?2u:1u)||!known(c,active_,pc,w)||++visits_>2048u)return fail(3);
        if(resume_&&c.pc!=pc)return fail(3);
        resume_=false;last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const uint32_t dst=target(pc,w);
            if(active_!=e_.select||ret_||(w&2u)||!edge(c,e_.direct,pc,w,dst))return fail(4);
            ret_=next_;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==528u){
            if(active_!=e_.select||ret_||w!=0x4e800421u||!edge(c,e_.indirect,pc,w,c.ctr))return fail(4);
            ret_=next_;next_=c.ctr;entry_due_=outer_=indirect_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u)return fail(4);
            if(!taken(c,w))return true;
            if(active_==e_.enable){
                if(ret_||c.lr!=e_.enable_return)return fail(4);
                active_=e_.select;next_=e_.enable_return;outer_=true;return true;
            }
            if(!ret_||active_==e_.select||c.lr!=ret_)return fail(4);
            active_=e_.select;next_=ret_;ret_=0;
            if(indirect_){outer_=true;indirect_=false;}
            return true;
        }
        if(op==31u&&xo==146u){
            if(c.gpr[(w>>21)&31u]!=(c.msr&~0x8000u))return fail(4);
        }
        if(op==17u||(op==19u&&xo==50u)||(op==16u&&(w&1u)))return fail(4);
        if(op==16u||op==18u){
            const auto dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return fail(4);
            if(dst<=pc)poll_due_=true;
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_)return fail(5);
        if(outer_&&c.pc==next_){
            if(entry_due_&&c.lr!=ret_)return fail(5);
            outer_=false;resume_=true;return true;
        }
        if(poll_due_&&c.pc==last_pc_){poll_due_=false;return true;}
        return fail(5);
    }
    template<class C>bool loader_at(C& c,bool held)const{
        return stage_==2u&&!error_&&held&&cpu_==&c&&c.pc==e_.loader&&c.lr==ret_&&
            c.inst_count==last_&&!(c.msr&0x8000u)&&!entry_due_&&!outer_&&!poll_due_;
    }
private:
    IdleRouteExpectation e_;const void* cpu_=nullptr;
    uint32_t active_=0,next_=0,ret_=0,last_pc_=0;uint64_t last_=0;
    unsigned stage_=0,error_=0,visits_=0;
    bool entry_due_=false,outer_=false,resume_=false,poll_due_=false,indirect_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>bool live(C& c,bool held)const{
        return stage_==1u&&!error_&&held&&cpu_==&c&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{
        return known(c,owner,pc)&&word(c,pc,w);
    }
    template<class C>bool edge(C& c,std::span<const VectorEdge> edges,uint32_t pc,uint32_t w,uint32_t dst)const{
        return std::count_if(edges.begin(),edges.end(),[&](auto x){
            return x.pc==dst&&x.lr==pc+4u&&x.branch_word==w&&word(c,dst,x.entry_word)&&known(c,dst,dst);
        })==1;
    }
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
