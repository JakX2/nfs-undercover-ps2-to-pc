#pragma once
#include "wii_wake_ready_v1288.h"
namespace undercover::wii {
struct NestedWakeExpectation {
    uint32_t wake,select,getter,restore,context,counter;
    VectorEdge getter_edge,restore_edge;
    std::span<const ReplyNativeWord> words;
};
// Original nested SelectThread must not switch away while the outer IRQ
// still holds the scheduler disabled. Observe its actual return, the wake
// routine's interrupt restore, and its original return to the reply body.
// The subsequent handler and scheduler re-enable belong to the next seam.
class NestedWakeReturnWitness {
public:
    explicit NestedWakeReturnWitness(NestedWakeExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool begin(C& c,const WakeReadyWitness& prior,ExternalReturnWitness& frame,
                                uint32_t queue,bool held){
        if(stage_||error_||!prior.select_ready(c,frame,queue,e_.select,held)||
           !mapped(c,e_.counter)||!c.mmu.read32(e_.counter)||c.mmu.read32(e_.counter)>1024u||
           e_.words.empty()||e_.words.size()>512u||e_.getter_edge.pc!=e_.getter||
           e_.restore_edge.pc!=e_.restore||!edge(c,e_.getter_edge)||!edge(c,e_.restore_edge)||
           !known(c,e_.select,e_.select)||!known(c,e_.getter,e_.getter)||
           !known(c,e_.restore,e_.restore)||!known(c,e_.wake,c.lr))return fail(1);
        for(auto x:e_.words)if(std::count_if(e_.words.begin(),e_.words.end(),[&](auto y){return y.pc==x.pc;})!=1)
            return fail(1);
        prior_=&prior;cpu_=&c;counter_=c.mmu.read32(e_.counter);tick_=last_=c.inst_count;
        gp_=c.gpr;cr_=pack(c)&0x00fff000u;msr_=c.msr;select_return_=c.lr;
        active_=next_=e_.select;stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!common(c,held)||c.pc!=pc)return fail(2);
        if(!entered_){
            if(pc!=e_.select||c.lr!=select_return_||c.gpr[3]||c.gpr[1]!=gp_[1]||
               c.inst_count-tick_>1u)return fail(2);
            entered_=true;last_=c.inst_count;return true;
        }
        if(!entry_due_||pc!=next_||c.inst_count!=last_||c.lr!=ret_||!known(c,pc,pc))return fail(2);
        entry_due_=false;active_=pc;
        if(pc==e_.getter){if(getter_seen_||select_returned_)return fail(3);getter_seen_=true;return true;}
        if(pc!=e_.restore||!select_returned_||restore_seen_||c.gpr[3]!=0u)return fail(3);
        restore_seen_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!common(c,held)||!entered_||entry_due_||poll_due_||outer_due_||
           pc!=next_||c.inst_count-last_!=(outer_resume_?2u:1u)||
           !known(c,active_,pc,w)||++visits_>2048u)return fail(4);
        if(outer_resume_){
            if(pc!=select_return_||c.pc!=pc||!select_abi(c))return fail(5);
            outer_resume_=false;select_returned_=true;
        }
        if(getter_due_){if(c.gpr[3]!=e_.context||c.lr!=pc)return fail(3);getter_due_=false;}
        if(restore_due_){if(c.msr!=msr_||c.lr!=pc)return fail(3);restore_due_=false;restore_returned_=true;}
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const uint32_t dst=target(pc,w);
            const auto& e=active_==e_.select?e_.getter_edge:e_.restore_edge;
            if(w&2u||ret_||(active_!=e_.select&&active_!=e_.wake)||dst!=e.pc||
               pc+4u!=e.lr||w!=e.branch_word||!edge(c,e)||
               (active_==e_.select?getter_seen_:(!select_returned_||restore_seen_)))return fail(6);
            ret_=pc+4u;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u)return fail(6);
            if(!taken(c,w))return true;
            if(active_==e_.getter||active_==e_.restore){
                if(!ret_||c.lr!=ret_)return fail(6);
                getter_due_=active_==e_.getter;restore_due_=active_==e_.restore;
                active_=getter_due_?e_.select:e_.wake;next_=ret_;ret_=0;return true;
            }
            if(active_==e_.select){
                if(ret_||c.lr!=select_return_||!select_abi(c))return fail(5);
                active_=e_.wake;next_=select_return_;outer_due_=1u;return true;
            }
            if(active_!=e_.wake||ret_||!restore_returned_||!prior_->wake_return_abi(c,held))return fail(5);
            next_=prior_->wake_return();outer_due_=2u;return true;
        }
        if(op==31u&&xo==146u){
            if(active_!=e_.restore||c.gpr[(w>>21)&31u]!=msr_)return fail(6);
            return true;
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||(op==16u&&(w&1u)))return fail(6);
        if(op==16u||op==18u){
            const auto dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return fail(6);
            if(dst<=pc)poll_due_=true;
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!common(c,held))return fail(7);
        if(!entered_&&c.pc==e_.select&&c.inst_count==tick_)return true;
        if(poll_due_&&c.pc==last_pc_&&c.inst_count==last_){poll_due_=false;return true;}
        if(outer_due_&&c.pc==next_&&c.inst_count==last_&&c.lr==next_){
            if(outer_due_==1u){outer_due_=0;outer_resume_=true;return true;}
            if(!prior_->wake_return_abi(c,held))return fail(5);
            outer_due_=0;stage_=2;return true;
        }
        return fail(7);
    }
    bool refuse_mmio(){return fail(8);}
    template<class C>bool returned_at(C& c,const WakeReadyWitness& prior,bool held)const{
        return stage_==2u&&!error_&&cpu_==&c&&prior_==&prior&&restore_returned_&&
            c.pc==prior.wake_return()&&c.lr==c.pc&&c.inst_count==last_&&
            prior.wake_return_abi(c,held)&&mapped(c,e_.counter)&&c.mmu.read32(e_.counter)==counter_;
    }
private:
    NestedWakeExpectation e_;const WakeReadyWitness* prior_=nullptr;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};uint32_t cr_=0,msr_=0,counter_=0,select_return_=0,active_=0,next_=0,ret_=0,last_pc_=0;
    uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0,visits_=0,outer_due_=0;
    bool entered_=false,entry_due_=false,poll_due_=false,outer_resume_=false,select_returned_=false,
         getter_seen_=false,getter_due_=false,restore_seen_=false,restore_due_=false,restore_returned_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>bool common(C& c,bool held)const{
        return stage_==1u&&!error_&&cpu_==&c&&prior_&&prior_->ready_held(c,held)&&
            c.msr==msr_&&mapped(c,e_.counter)&&c.mmu.read32(e_.counter)==counter_&&
            c.inst_count>=tick_&&c.inst_count-tick_<=4096u;
    }
    template<class C>static bool mapped(C& c,uint32_t a){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return mapped(c,a)&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        for(auto x:e_.words)if(x.owner==owner&&x.pc==pc)return word(c,pc,x.word);
        return false;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){
            return x.owner==owner&&x.pc==pc&&x.word==w;})==1&&word(c,pc,w);
    }
    template<class C>bool edge(C& c,const VectorEdge& e)const{
        return e.lr>=4u&&word(c,e.lr-4u,e.branch_word)&&word(c,e.pc,e.entry_word)&&
            e.branch_word>>26==18u&&(e.branch_word&3u)==1u&&target(e.lr-4u,e.branch_word)==e.pc;
    }
    template<class C>bool select_abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.gpr[13]!=gp_[13]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
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
