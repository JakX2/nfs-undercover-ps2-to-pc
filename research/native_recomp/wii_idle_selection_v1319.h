#pragma once
#include "wii_ready_idle_return_v1304.h"
namespace undercover::wii {
// Read-only state/ABI join for the original idle scheduler selection.
// The caller must separately authenticate the intervening native labels
// and the earlier cooperative save provenance.
struct IdleSelectionExpectation {
    uint32_t thread,idle,counter,callback_ptr,callback;
    VectorEdge disable,clear,set,load;
    std::span<const VectorEdge> indirect;
};
class IdleSelectionWitness {
public:
    explicit IdleSelectionWitness(IdleSelectionExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool begin(C& c,const ReadyIdleReturnJoin& prior,bool held){
        const auto* ready=prior.ready();
        if(stage_||error_||!ready||!prior.resumed_idle(c,held)||ready->thread()!=e_.thread||
           ready->idle_context()!=e_.idle||e_.thread==e_.idle||!e_.counter||
           !word(c,e_.counter,0u)||!word(c,e_.callback_ptr,e_.callback)||
           e_.indirect.empty()||e_.indirect.size()>4u||
           !direct(c,e_.disable)||!direct(c,e_.clear)||!direct(c,e_.set)||!direct(c,e_.load))return fail(1);
        for(auto edge:e_.indirect)if(edge.pc!=e_.callback||edge.branch_word!=0x4e800421u||
           !word(c,edge.pc,edge.entry_word)||!word(c,edge.lr-4u,edge.branch_word))return fail(1);
        prior_=&prior;cpu_=&c;wait_=ready->waiting_queue();ready_=ready->ready_queue();
        if(!wait_||!ready_||wait_==ready_||!mapped(c,e_.thread+720u,4u))return fail(1);
        priority_=c.mmu.read32(e_.thread+720u);
        if(priority_>31u||!idle_active(c)||!ready_state(c))return fail(1);
        for(unsigned i=0;i<image_.size();++i){
            const uint32_t a=e_.thread+4u*i;
            if(!mapped(c,a,4u))return fail(1);
            image_[i]=c.mmu.read32(a);
        }
        tick_=last_=c.inst_count;stage_=1;return true;
    }
    // Call at each native instruction or callback during selection, before
    // OSLoadContext starts changing CPU registers. Intermediate scheduler
    // list/pointer stores need not be atomic.
    template<class C>bool boundary(C& c,bool held)const{
        if(stage_<1u||stage_>6u||error_||!prior_||cpu_!=&c||!prior_->selection_transport_held(c,held)||
           !word(c,e_.counter,0u)||!word(c,e_.callback_ptr,e_.callback)||
           !word(c,wait_,0u)||!word(c,wait_+4u,0u)||!word(c,e_.thread+720u,priority_)||
           c.inst_count<tick_||c.inst_count-tick_>4096u)return false;
        if(stage_<=2u&&!ready_state(c))return false;
        if(stage_<=4u&&!idle_active(c))return false;
        if(stage_>=4u&&!selected_queue(c))return false;
        if(stage_>=2u&&stage_<=6u&&(c.msr&0x8000u)&&stage_!=2u)return false;
        for(unsigned i=0;i<image_.size();++i)if(!word(c,e_.thread+4u*i,image_[i]))return false;
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!boundary(c,held)||c.pc!=pc||c.inst_count<=last_)return fail(2);
        if(stage_==1u&&matches(c,e_.disable)&&pc==e_.disable.pc&&(c.msr&0x8000u)){
            stage_=2;
        }else if(stage_==2u&&matches(c,e_.clear)&&pc==e_.clear.pc&&!(c.msr&0x8000u)&&c.gpr[3]==e_.idle){
            stage_=3;
        }else if(stage_==3u&&pc==e_.callback&&c.ctr==pc&&c.gpr[4]==e_.thread&&
                 !(c.msr&0x8000u)&&selected_queue(c)&&
                 std::count_if(e_.indirect.begin(),e_.indirect.end(),[&](auto edge){
                     return matches(c,edge);
                 })==1){
            stage_=4;
        }else if(stage_==4u&&matches(c,e_.set)&&pc==e_.set.pc&&c.gpr[3]==e_.thread&&
                 word(c,0x800000e4u,e_.thread)){
            stage_=5;
        }else if(stage_==5u&&matches(c,e_.load)&&pc==e_.load.pc&&c.gpr[3]==e_.thread&&
                 word(c,0x800000e4u,e_.thread)&&active(c,e_.thread)){
            stage_=6;
        }else return fail(3);
        last_=c.inst_count;return true;
    }
    template<class C>bool loader_ready(C& c,bool held)const{
        return stage_==6u&&boundary(c,held)&&c.inst_count==last_&&c.pc==e_.load.pc&&
            c.lr==e_.load.lr&&c.gpr[3]==e_.thread&&word(c,0x800000e4u,e_.thread)&&active(c,e_.thread);
    }
private:
    IdleSelectionExpectation e_;const ReadyIdleReturnJoin* prior_=nullptr;const void* cpu_=nullptr;
    std::array<uint32_t,0x2c8u/4u> image_{};
    uint32_t wait_=0,ready_=0,priority_=0;uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        return n&&a>=0x80000000u&&end<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t v){
        return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==v;
    }
    template<class C>static bool direct(C& c,VectorEdge e){
        return e.lr>=4u&&word(c,e.pc,e.entry_word)&&word(c,e.lr-4u,e.branch_word)&&
            e.branch_word== (0x48000001u|((e.pc-(e.lr-4u))&0x03fffffcu));
    }
    template<class C>static bool matches(C& c,VectorEdge e){
        return c.pc==e.pc&&c.lr==e.lr&&word(c,e.pc,e.entry_word)&&word(c,e.lr-4u,e.branch_word);
    }
    template<class C>bool active(C& c,uint32_t a)const{
        return word(c,0x800000d4u,a)&&word(c,0x800000c0u,a&0x3fffffffu);
    }
    template<class C>bool idle_active(C& c)const{return active(c,e_.idle);}
    template<class C>bool ready_state(C& c)const{
        return mapped(c,e_.thread+712u,2u)&&c.mmu.read16(e_.thread+712u)==1u&&
            word(c,e_.thread+732u,ready_)&&word(c,ready_,e_.thread)&&word(c,ready_+4u,e_.thread)&&
            word(c,e_.thread+736u,0u)&&word(c,e_.thread+740u,0u);
    }
    template<class C>bool selected_queue(C& c)const{
        return mapped(c,e_.thread+712u,2u)&&c.mmu.read16(e_.thread+712u)==2u&&
            word(c,ready_,0u)&&word(c,ready_+4u,0u)&&word(c,e_.thread+736u,0u)&&word(c,e_.thread+740u,0u);
    }
};
}
