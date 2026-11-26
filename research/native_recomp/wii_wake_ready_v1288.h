#pragma once
#include "wii_reply_processor_v1280.h"
namespace undercover::wii {
struct WakeReadyExpectation {
    uint32_t wake,disable,select,context,thread;
    VectorEdge disable_edge,select_edge;
    std::span<const ReplyNativeWord> words;
};
// Read-only handoff from the original reply processor. Execute the actual
// wake routine and nested interrupt-disable leaf; stop before SelectThread.
// Do not alter the thread state, ready queue, scheduler hint or CPU context.
class WakeReadyWitness {
public:
    explicit WakeReadyWitness(WakeReadyExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    uint32_t ready_queue()const{return ready_;}
    template<class C>bool begin(C& c,const ReplyProcessorWitness& prior,ExternalReturnWitness& frame,uint32_t queue,bool held){
        const auto s=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!prior.wake_ready(c,frame,queue,e_.wake,held)||!s||
           e_.words.empty()||e_.words.size()>256u||
           e_.disable_edge.pc!=e_.disable||e_.select_edge.pc!=e_.select||
           e_.wake==e_.disable||e_.wake==e_.select||e_.disable==e_.select||
           !known(c,e_.wake,e_.wake)||!known(c,e_.disable,e_.disable)||
           !known(c,e_.select,e_.select)||!edge(c,e_.disable_edge)||!edge(c,e_.select_edge)||
           !mapped(c,e_.thread,744u)||!mapped(c,queue,8u))return fail(1);
        for(auto x:e_.words)if(std::count_if(e_.words.begin(),e_.words.end(),[&](auto y){return x.pc==y.pc;})!=1)
            return fail(1);
        cpu_=&c;frame_=&frame;queue_=queue;mail_=*s;msr_=c.msr;tick_=last_=c.inst_count;
        sp_=c.gpr[1];lr_=c.lr;caller_gp_=c.gpr;caller_cr_=pack(c)&0x00fff000u;
        active_=next_=e_.wake;priority_=c.mmu.read32(e_.thread+720u);
        for(unsigned i=0;i<saved_.size();++i)saved_[i]=c.mmu.read32(e_.thread+4u*i);
        if(priority_>31u||!waiting(c)||!common(c,held))return fail(1);
        stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(2);
        if(!entered_){
            if(pc!=e_.wake||c.lr!=lr_||c.gpr[1]!=sp_||c.gpr[3]!=queue_||
               c.inst_count-tick_>1u||!waiting(c))return fail(2);
            entered_=true;last_=c.inst_count;return true;
        }
        if(!entry_due_||pc!=next_||c.inst_count!=last_||c.lr!=ret_||
           !known(c,pc,pc))return fail(2);
        entry_due_=false;
        if(pc==e_.disable){
            if(disable_seen_||!edge(c,e_.disable_edge)||!waiting(c)||
               c.gpr[1]>=sp_||sp_-c.gpr[1]>256u)return fail(3);
            disable_seen_=true;active_=pc;return true;
        }
        if(pc!=e_.select||!disable_returned_||!edge(c,e_.select_edge)||c.gpr[3]!=0u||
           c.gpr[1]>=sp_||sp_-c.gpr[1]>256u||!ready(c))return fail(4);
        ready_=c.mmu.read32(e_.thread+732u);select_sp_=c.gpr[1];stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||!entered_||entry_due_||poll_due_||
           pc!=next_||c.inst_count-last_!=1u||!known(c,active_,pc,w)||++visits_>1024u)return fail(5);
        if(disable_return_due_){
            if(active_!=e_.wake||pc!=e_.disable_edge.lr||c.gpr[3]!=0u||c.lr!=pc||!waiting(c))return fail(3);
            disable_return_due_=false;disable_returned_=true;
        }
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const uint32_t dst=target(pc,w);
            const auto& e=dst==e_.disable?e_.disable_edge:e_.select_edge;
            if((w&2u)||active_!=e_.wake||ret_||e.pc!=dst||e.lr!=pc+4u||
               e.branch_word!=w||!edge(c,e)||(dst==e_.disable?disable_seen_:!disable_returned_))return fail(6);
            ret_=pc+4u;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u||active_!=e_.disable||!ret_)return fail(6);
            if(!taken(c,w))return true;
            if(c.lr!=ret_)return fail(6);
            active_=e_.wake;next_=ret_;ret_=0;disable_return_due_=true;return true;
        }
        if(op==31u&&xo==146u){
            if(active_!=e_.disable||c.gpr[(w>>21)&31u]!=msr_)return fail(6);
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
        if(stage_!=1u||!common(c,held))return fail(7);
        if(!entered_&&c.pc==e_.wake&&c.inst_count==tick_)return true;
        if(poll_due_&&c.pc==last_pc_&&c.inst_count==last_){poll_due_=false;return true;}
        return fail(7);
    }
    bool refuse_mmio(){return fail(8);}
    uint32_t wake_return()const{return lr_;}
    template<class C>bool ready_held(C& c,bool held)const{
        return stage_==2u&&common(c,held)&&ready(c)&&word(c,e_.thread+732u,ready_);
    }
    template<class C>bool ready_context_held(C& c,bool held)const{
        return stage_==2u&&context_common(c,held)&&ready(c)&&word(c,e_.thread+732u,ready_);
    }
    template<class C>bool select_ready(C& c,ExternalReturnWitness& frame,uint32_t queue,uint32_t select,bool held)const{
        return ready_held(c,held)&&frame_==&frame&&queue==queue_&&select==e_.select&&
            c.pc==select&&c.lr==e_.select_edge.lr&&c.gpr[3]==0u&&c.gpr[1]==select_sp_&&
            c.inst_count==last_&&last_pc_==e_.select_edge.lr-4u&&edge(c,e_.select_edge);
    }
    template<class C>bool wake_return_abi(C& c,bool held)const{
        if(!ready_held(c,held)||c.lr!=lr_||c.gpr[1]!=sp_||c.gpr[2]!=caller_gp_[2]||
           c.gpr[13]!=caller_gp_[13]||(pack(c)&0x00fff000u)!=caller_cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=caller_gp_[i])return false;
        return true;
    }
private:
    WakeReadyExpectation e_;
    ExternalReturnWitness* frame_=nullptr;const void* cpu_=nullptr;
    // OSContext occupies the entire prefix before OSThread.state (0x2c8).
    // Include every GQR and paired-single/FPU save slot, not just the
    // integer frame and the first quantization register.
    static constexpr unsigned ContextBytes=0x2c8u;
    ColdIpcSnapshot mail_{};std::array<uint32_t,ContextBytes/4u> saved_{};
    std::array<uint32_t,32> caller_gp_{};uint32_t caller_cr_=0,select_sp_=0;
    uint32_t queue_=0,ready_=0,priority_=0,msr_=0,sp_=0,lr_=0,active_=0,next_=0,ret_=0,last_pc_=0;
    uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0,visits_=0;
    bool entered_=false,entry_due_=false,poll_due_=false,disable_seen_=false,disable_return_due_=false,disable_returned_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t v){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==v;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        for(auto x:e_.words)if(x.owner==owner&&x.pc==pc)return word(c,pc,x.word);
        return false;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){
            return x.owner==owner&&x.pc==pc&&x.word==w;})==1&&word(c,pc,w);
    }
    template<class C>bool edge(C& c,const VectorEdge& e)const{
        return word(c,e.pc,e.entry_word)&&e.lr>=4u&&word(c,e.lr-4u,e.branch_word)&&
            e.branch_word>>26==18u&&(e.branch_word&3u)==1u&&target(e.lr-4u,e.branch_word)==e.pc;
    }
    template<class C>bool waiting(C& c)const{
        return c.mmu.read16(e_.thread+712u)==4u&&word(c,e_.thread+732u,queue_)&&
            word(c,queue_,e_.thread)&&word(c,queue_+4u,e_.thread)&&
            word(c,e_.thread+736u,0u)&&word(c,e_.thread+740u,0u);
    }
    template<class C>bool ready(C& c)const{
        const uint32_t q=c.mmu.read32(e_.thread+732u);
        return c.mmu.read16(e_.thread+712u)==1u&&q&&q!=queue_&&
            word(c,queue_,0u)&&word(c,queue_+4u,0u)&&
            word(c,q,e_.thread)&&word(c,q+4u,e_.thread)&&
            word(c,e_.thread+736u,0u)&&word(c,e_.thread+740u,0u);
    }
    template<class C>bool common(C& c,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return s&&same_scheduler_ipc_snapshot(mail_,*s)&&context_common(c,held);
    }
    template<class C>bool context_common(C& c,bool held)const{
        if(error_||!held||cpu_!=&c||!frame_||!c.is_running||c.in_callback||c.dispatch_saved_ctx||
           c.msr!=msr_||(c.msr&0x8000u)||c.inst_count<tick_||c.inst_count-tick_>4096u||
           !frame_->saved_integer(c,e_.context).ok()||
           !word(c,0x800000d4u,e_.context)||!word(c,0x800000c0u,e_.context&0x3fffffffu)||
           !word(c,e_.thread+720u,priority_))return false;
        const auto state=c.mmu.read16(e_.thread+712u);
        if(state!=4u&&(!disable_returned_||state!=1u))return false;
        for(unsigned i=0;i<saved_.size();++i)if(!word(c,e_.thread+4u*i,saved_[i]))return false;
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
