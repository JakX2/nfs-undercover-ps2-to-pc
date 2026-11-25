#pragma once
#include "wii_alarm_cancel_queue_v780.h"
#include "wii_postack_os_leaf_v703.h"
#include <array>
#include <cstdint>
namespace undercover::wii {
struct AlarmCallEdge{uint32_t site,target,end,word;};
struct AlarmCancelExpectation{
    uint32_t site,branch,root,end,time,timer,head,tail;
    std::array<AlarmCallEdge,7> root_calls;
    std::array<PostAckLeafExpectation,3> time_calls;
};
// The installer authenticates original words and native direct edges.
// This observer only accepts one cancellation, with bounded native visits.
class AlarmCancelReturnWitness{
public:
    explicit AlarmCancelReturnWitness(AlarmCancelExpectation e):e_(e),
        leaves_{PostAckOsLeaf(leaf(e.root_calls[0],1)),PostAckOsLeaf(leaf(e.root_calls[1],3)),
            PostAckOsLeaf(leaf(e.root_calls[6],3)),PostAckOsLeaf(e.time_calls[0]),
            PostAckOsLeaf(e.time_calls[1]),PostAckOsLeaf(e.time_calls[2])}{}
    unsigned stage()const{return stage_;}unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}unsigned total()const{return total_;}
    unsigned polls()const{return polls_;}unsigned calls()const{return calls_;}
    unsigned queue_failure()const{return queue_.failure();}
    unsigned lane()const{return unsigned(queue_.lane());}
    bool timer_required()const{return queue_.timer_required();}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,bool device){
        if(stage_||error_||!device||!safe(c)||pc!=e_.site||w!=e_.branch||
           !word(c,pc,w)||!direct(pc,w,e_.root)||e_.end<=e_.root||e_.end-e_.root>512u||
           c.inst_count>UINT64_MAX-512u||!queue_.capture(c,e_.head,e_.tail,c.gpr[3]))return fail(1);
        cpu_=&c;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;last_=start_=c.inst_count;
        next_=e_.root;entry_due_=true;stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool device){
        if(!common(c,device)||!entry_due_||pc!=next_||c.pc!=pc||c.inst_count!=last_)return fail(2);
        if(stage_==1){
            if(c.lr!=e_.site+4u)return fail(2);
            stage_=2;
        }else if(stage_!=2)return fail(2);
        else if(active_leaf_<6){
            if(!leaves_[active_leaf_].entry(pc,c))return fail(2);
        }else if(region_==1){
            if(c.lr!=time_return_)return fail(2);
        }else if(region_==2){
            if(c.lr!=timer_return_)return fail(2);
        }else return fail(2);
        entry_due_=false;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool device){
        if(stage_!=2||!common(c,device)||entry_due_||pc!=next_||!word(c,pc,w)||
           c.inst_count-last_!=1u||++visits_>256u)return fail(3);
        last_=c.inst_count;
        if(active_leaf_<6){
            auto& l=leaves_[active_leaf_];
            if(l.stage()==3){
                if(!l.returned(c,pc))return fail(4);
                active_leaf_=6;
            }else{
                if(!l.before(c,pc,w))return fail(4);
                next_=w==BLR?leaf_return_:pc+4u;
                // Leaf witness owns its conditional branches and retry poll.
                // At the next label its own exact control-flow check applies.
                leaf_next_flexible_=w>>26==16u;
                if(leaf_next_flexible_)alternate_=target(pc,w);
                return true;
            }
        }
        if(region_==1&&time_done_){
            if(pc!=time_return_||c.pc!=pc||c.lr!=pc||
               !queue_.time_returned(c,(uint64_t(c.gpr[3])<<32)|c.gpr[4]))return fail(5);
            region_=0;
        }
        if(region_==2&&timer_done_){
            if(pc!=timer_return_||c.pc!=pc||c.lr!=pc)return fail(5);
            region_=0;
        }
        next_=pc+4u;
        if(region_==2){
            if(pc==e_.timer){if(!queue_.timer_before(c,w))return fail(5);}
            else if(pc==e_.timer+4u&&w==BLR&&c.lr==timer_return_){
                if(!queue_.timer_after(c))return fail(5);
                timer_done_=true;next_=timer_return_;
            }else return fail(5);
            return true;
        }
        if(region_==1){
            if(pc<e_.time||pc>=e_.time+100u||++time_visits_>25u)return fail(5);
            for(unsigned i=0;i<3;++i)if(pc==e_.time_calls[i].site){
                if(i!=time_cursor_||w!=e_.time_calls[i].branch||!leaves_[3+i].start(c,pc,w))return fail(4);
                ++time_cursor_;active_leaf_=3+i;leaf_return_=pc+4u;next_=e_.time_calls[i].root;entry_due_=true;return true;
            }
            if(w==BLR){
                if(time_cursor_!=3||time_visits_!=25||c.lr!=time_return_)return fail(5);
                time_done_=true;next_=time_return_;return true;
            }
            if(w>>26==16u||w>>26==18u||forbidden(w))return fail(6);
            return next_<e_.time+100u?true:fail(6);
        }
        if(pc<e_.root||pc>=e_.end)return fail(6);
        for(unsigned i=0;i<7;++i){
            const auto& edge=e_.root_calls[i];if(pc!=edge.site)continue;
            if(w!=edge.word||!direct(pc,w,edge.target)||(calls_&(1u<<i)))return fail(6);
            if(i==0){if(calls_)return fail(6);}
            else if(!(calls_&1u))return fail(6);
            if(i==1||i==6){
                if(calls_&66u||(queue_.timer_required()&&!timer_done_))return fail(6);
            }
            if(i==2){
                if(!queue_.timer_required()||calls_!=1u||edge.target!=e_.time)return fail(6);
                region_=1;time_return_=pc+4u;
            }else if(i>=3&&i<=5){
                if(!queue_.timer_required()||!time_done_||(calls_&56u)||edge.target!=e_.timer)return fail(6);
                region_=2;timer_return_=pc+4u;
            }else{
                active_leaf_=i==0?0u:i==1?1u:2u;leaf_return_=pc+4u;
                if(!leaves_[active_leaf_].start(c,pc,w))return fail(4);
            }
            calls_|=1u<<i;next_=edge.target;entry_due_=true;return true;
        }
        if(w==BLR){
            if(!(calls_&1u)||!(calls_&66u)||(queue_.timer_required()?(!time_done_||!timer_done_):(calls_&60u)!=0)||
               c.lr!=e_.site+4u)return fail(6);
            stage_=3;next_=e_.site+4u;return true;
        }
        if(forbidden(w))return fail(6);
        const unsigned op=w>>26;
        if(op==16u||op==18u){
            if(w&3u)return fail(6);
            const uint32_t dst=target(pc,w);
            if(dst<=pc||dst>=e_.end)return fail(6);
            if(op==18u||taken(c,w))next_=dst;
        }
        return next_>=e_.root&&next_<e_.end?true:fail(6);
    }
    // For original leaf conditional branches, the existing leaf witness
    // checks the exact allowed successor and the emitted retry callback.
    template<class C>bool native_before(C& c,uint32_t pc,uint32_t w,bool device){
        if(leaf_next_flexible_){
            if(pc!=next_&&pc!=alternate_)return fail(4);
            next_=pc;leaf_next_flexible_=false;
        }
        return before(c,pc,w,device);
    }
    template<class C>bool poll(C& c,bool device){
        if(stage_!=2||!common(c,device)||active_leaf_!=4||c.inst_count!=last_||
           !leaves_[active_leaf_].poll(c))return fail(7);
        ++polls_;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,uint32_t w,bool device){
        if(stage_!=3||!common(c,device)||pc!=next_||pc!=e_.site+4u||c.pc!=pc||c.lr!=pc||
           c.inst_count-last_!=1u||!word(c,pc,w)||c.inst_count-start_!=visits_+1u||
           !queue_.finish(c))return fail(8);
        total_=visits_;stage_=4;return true;
    }
private:
    static constexpr uint32_t BLR=0x4e800020u;
    AlarmCancelExpectation e_;AlarmCancelQueueWitness queue_;
    std::array<PostAckOsLeaf,6> leaves_;
    const void* cpu_=nullptr;unsigned stage_=0,error_=0,visits_=0,total_=0,polls_=0,calls_=0,region_=0,
        active_leaf_=6,time_cursor_=0,time_visits_=0;
    uint32_t msr_=0,srr0_=0,srr1_=0,next_=0,alternate_=0,leaf_return_=0,time_return_=0,timer_return_=0;
    uint64_t start_=0,last_=0;bool entry_due_=false,time_done_=false,timer_done_=false,leaf_next_flexible_=false;
    static PostAckLeafExpectation leaf(AlarmCallEdge e,unsigned kind){return {e.site,e.target,e.end,e.word,kind};}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,bool device)const{return device&&!error_&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&c.inst_count>=start_&&c.inst_count-start_<=512u;}
    template<class C>static bool word(C& c,uint32_t pc,uint32_t w){return !(pc&3u)&&pc>=0x80000000u&&pc<=0x817ffffcu&&c.mmu.get_ptr(pc)&&c.mmu.get_ptr(pc+3u)&&c.mmu.read32(pc)==w;}
    static uint32_t target(uint32_t pc,uint32_t w){const bool s=w>>26==16u;const uint32_t b=s?0xfffcu:0x03fffffcu,v=s?0x8000u:0x02000000u;return pc+(((w&b)^v)-v);}
    static bool direct(uint32_t pc,uint32_t w,uint32_t dst){return w>>26==18u&&(w&3u)==1u&&target(pc,w)==dst;}
    static bool forbidden(uint32_t w){const auto op=w>>26,xo=(w>>1)&1023u;return op==17u||(op==31u&&xo==146u)||(op==19u&&(xo==16u||xo==50u||xo==528u));}
    template<class C>static bool taken(C& c,uint32_t w){
        uint32_t cr=0;for(const auto& f:c.cr)cr=(cr<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((cr>>(31u-bi))&1u)==bool(bo&8u));
    }
};
}
