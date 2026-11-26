#pragma once
#include "wii_joined_ipc_reply_entry_v1273.h"
#include "wii_cold_reply_consume_v1278.h"
#include <algorithm>
#include <span>

namespace undercover::wii {
struct ReplyNativeWord{uint32_t owner,pc,word;};
struct ReplyProcessorExpectation{
    uint32_t processor,read_leaf,write_leaf,cache,wake,wake_lr,context,thread;
    std::span<const ReplyNativeWord> words;
    std::span<const VectorEdge> edges;
};
// Synchronous reply lane only. Authenticated native instructions must
// select the response, acknowledge Y1, invalidate its data, and call the
// waiting queue. This witness does not execute instructions or wake it.
class ReplyProcessorWitness{
public:
    explicit ReplyProcessorWitness(ReplyProcessorExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned gate_failure()const{return gate_.failure();}
    unsigned arm_reads()const{return gate_.arm_reads();}
    unsigned invalidations()const{return gate_.invalidations();}
    template<class C>bool begin(C& c,const JoinedIpcReplyEntry& entry,ExternalReturnWitness& frame,
                                uint32_t queue,uint32_t request,bool held){
        if(stage_||error_||!entry.processor_ready(c,frame,queue,request,e_.processor,held)||
           e_.words.empty()||e_.words.size()>1024u||e_.edges.empty()||e_.edges.size()>64u||
           !known(c,e_.processor,e_.processor)||!known(c,e_.wake,e_.wake)||
           !known(c,e_.read_leaf,e_.read_leaf)||!known(c,e_.write_leaf,e_.write_leaf)||
           !known(c,e_.cache,e_.cache)||!gate_.begin(request,true))return fail(1);
        for(size_t i=0;i<e_.words.size();++i){
            auto x=e_.words[i];
            if((x.pc&3u)||(x.owner&3u)||std::count_if(e_.words.begin(),e_.words.end(),
                [&](auto y){return x.pc==y.pc;})!=1)return fail(1);
        }
        cpu_=&c;frame_=&frame;queue_=queue;msr_=c.msr;tick_=last_=c.inst_count;
        active_=next_=e_.processor;stage_=1;
        return common(c,held)||fail(1);
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!common(c,held)||c.pc!=pc)return fail(2);
        if(!entered_){
            if(pc!=e_.processor||c.inst_count-tick_>1u)return fail(2);
            entered_=true;last_=c.inst_count;return true;
        }
        if(!entry_due_||pc!=next_||c.inst_count!=last_||c.lr!=ret_||
           !known(c,pc,pc)||!edge(c,pc,ret_,last_word_))return fail(2);
        entry_due_=false;active_=pc;
        if(pc==e_.wake){
            if(ret_!=e_.wake_lr||c.gpr[3]!=queue_||!gate_.ready_for_wakeup(c,true))
                return fail(3);
            stage_=2;return true;
        }
        if(pc==e_.cache&&!gate_.begin_invalidation(c,c.gpr[3],c.gpr[4],true))return fail(4);
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!common(c,held)||!entered_||entry_due_||poll_due_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,active_,pc,w)||++visits_>4096u)return fail(5);
        // The previous instruction really executed: the native emitter
        // incremented its cache counter and recorded the effective address.
        if(dcbi_due_){
            if(!gate_.invalidated(c,dcbi_ea_,true))return fail(4);
            dcbi_due_=false;
        }
        if(cache_return_){
            if(active_!=e_.processor||!gate_.finish_invalidation(c,true))return fail(4);
            cache_return_=false;
        }
        last_=c.inst_count;last_pc_=pc;last_word_=w;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==31u&&xo==470u){
            if(active_!=e_.cache)return fail(4);
            unsigned ra=(w>>16)&31u,rb=(w>>11)&31u;
            dcbi_ea_=(ra?c.gpr[ra]:0u)+c.gpr[rb];dcbi_due_=true;return true;
        }
        if(op==18u&&(w&1u)){
            const auto dst=target(pc,w);
            if((w&2u)||active_!=e_.processor||ret_||
               (dst!=e_.read_leaf&&dst!=e_.write_leaf&&dst!=e_.cache&&dst!=e_.wake)||
               !edge(c,dst,pc+4u,w))return fail(6);
            ret_=pc+4u;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if((w&1u)||active_==e_.processor||!ret_)return fail(6);
            if(!taken(c,w))return true;
            if(c.lr!=ret_)return fail(6);
            cache_return_=active_==e_.cache;active_=e_.processor;next_=ret_;ret_=0;return true;
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||
           (op==31u&&xo==146u)||(op==16u&&(w&1u)))return fail(6);
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
        if(!entered_&&c.pc==e_.processor&&c.inst_count==tick_)return true;
        if(poll_due_&&c.pc==last_pc_&&c.inst_count==last_){poll_due_=false;return true;}
        return fail(7);
    }
    template<class C>std::optional<uint32_t> read(C& c,uint32_t a,bool held){
        const unsigned op=last_word_>>26,xo=(last_word_>>1)&1023u;
        if(!common(c,held)||active_!=e_.read_leaf||c.inst_count!=last_||
           !(op==32u||(op==31u&&xo==23u))){fail(8);return {};}
        auto v=gate_.read(a,c.msr,true);if(!v)fail(8);return v;
    }
    template<class C>bool write(C& c,uint32_t a,uint32_t v,bool held){
        const unsigned op=last_word_>>26,xo=(last_word_>>1)&1023u;
        return (common(c,held)&&active_==e_.write_leaf&&c.inst_count==last_&&
                (op==36u||(op==31u&&xo==151u))&&gate_.write(a,v,c.msr,true))||fail(8);
    }
private:
    ReplyProcessorExpectation e_;ColdReplyConsumeGate gate_;
    ExternalReturnWitness* frame_=nullptr;const void* cpu_=nullptr;
    uint32_t queue_=0,msr_=0,active_=0,next_=0,ret_=0,last_pc_=0,last_word_=0,dcbi_ea_=0;
    uint64_t tick_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0;
    bool entered_=false,entry_due_=false,poll_due_=false,dcbi_due_=false,cache_return_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        auto x=std::find_if(e_.words.begin(),e_.words.end(),[&](auto w){return w.owner==owner&&w.pc==pc;});
        return x!=e_.words.end()&&word(c,pc,x->word);
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){
            return x.owner==owner&&x.pc==pc&&x.word==w;})==1&&word(c,pc,w);
    }
    template<class C>bool edge(C& c,uint32_t dst,uint32_t lr,uint32_t w)const{
        return std::count_if(e_.edges.begin(),e_.edges.end(),[&](auto e){
            return e.pc==dst&&e.lr==lr&&e.branch_word==w&&word(c,dst,e.entry_word)&&word(c,lr-4u,w);
        })==1;
    }
    template<class C>bool common(C& c,bool held)const{
        return stage_==1u&&!error_&&held&&cpu_==&c&&frame_&&c.is_running&&!c.in_callback&&
            !c.dispatch_saved_ctx&&c.msr==msr_&&!(c.msr&0x8000u)&&
            c.inst_count>=tick_&&c.inst_count-tick_<=8192u&&gate_.boundary(true)&&
            frame_->saved_integer(c,e_.context).ok()&&word(c,0x800000d4u,e_.context)&&
            word(c,0x800000c0u,e_.context&0x3fffffffu)&&c.mmu.read16(e_.thread+712u)==4u&&
            word(c,e_.thread+732u,queue_)&&word(c,queue_,e_.thread)&&word(c,queue_+4u,e_.thread)&&
            word(c,e_.thread+736u,0u)&&word(c,e_.thread+740u,0u);
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
