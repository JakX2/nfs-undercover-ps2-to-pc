#pragma once
#include "wii_ioctl_prefix_v1386.h"
#include "open_cache_range_trace_v649.h"
namespace undercover::wii {
struct IoctlAllocationExpectation {
    uint32_t veneer,body,resume,resume_word;
    VectorEdge disable,restore;
    std::span<const ReplyNativeWord> words;
};
// Original third allocation, with EE already masked by STM. A new shadow
// starts only after the authenticated second release and prefix handoff.
class IoctlAllocationWitness {
public:
    explicit IoctlAllocationWitness(IoctlAllocationExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return fence_.stores();}
    unsigned heap_stores()const{return fence_.heap_stores();}
    unsigned metadata_stores()const{return fence_.metadata_stores();}
    unsigned store_failure()const{return fence_.failure();}
    unsigned range_failure()const{return fence_.range_failure();}
    unsigned store_ordinal()const{return ordinal_;}
    unsigned control()const{return control_;}
    uint32_t request()const{return request_;}
    uint32_t allocated_size()const{return size_;}
    template<class C>bool begin(C& c,bool held,AllocatorRange heap,AllocatorRange meta,AllocatorRange guard){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.veneer||c.lr!=e_.resume||
           (c.msr&0x8000u)||c.gpr[4]<64u||c.gpr[4]>4096u||c.gpr[1]<0x80000200u||
           c.gpr[1]>0x817fff70u||(c.gpr[1]&7u)||!known(c,e_.veneer,e_.veneer)||
           !known(c,e_.body,e_.body)||!equal(c,e_.resume,e_.resume_word)||
           !edge(c,e_.disable)||!edge(c,e_.restore)||!meta.size||!guard.size||
           !fence_.begin(c,{c.gpr[1]-512u,520u},heap,meta,guard))return fail(1);
        sp_=c.gpr[1];gp_=c.gpr;msr_=c.msr;cr_=pack(c)&0x00fff000u;size_=c.gpr[4];heap_=heap;meta_=meta;
        if(!mapped(c,sp_+8u,caller_.size()*4u))return fail(1);
        for(unsigned i=0;i<caller_.size();++i)caller_[i]=c.mmu.read32(sp_+8u+4u*i);
        cpu_=&c;active_=next_=c.pc;last_=start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||entry_due_||poll_due_||outer_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,active_,pc,w)||++visits_>1024u)return fail(2);
        if(!fence_.before(c,w)){ordinal_=(pc-active_)/4u+1u;return fail(3);}
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(active_==e_.veneer){
            if(pc!=e_.veneer||op!=18u||(w&3u)||target(pc,w)!=e_.body)return bad(1);
            next_=e_.body;entry_due_=true;return true;
        }
        if(op==18u&&(w&1u)){
            const bool d=!disabled_&&pc+4u==e_.disable.lr&&w==e_.disable.branch_word;
            const bool r=disable_returned_&&!restored_&&pc+4u==e_.restore.lr&&w==e_.restore.branch_word&&c.gpr[3]==0u;
            if(active_!=e_.body||(!d&&!r))return bad(2);
            next_=d?e_.disable.pc:e_.restore.pc;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u)return bad(3);
            if(!taken(c,w))return true;
            if(active_==e_.disable.pc){
                if(!disabled_||c.lr!=e_.disable.lr||c.gpr[3]!=0u)return bad(4);
                disable_returned_=true;active_=e_.body;next_=e_.disable.lr;return true;
            }
            if(active_==e_.restore.pc){
                if(!restored_||c.lr!=e_.restore.lr||c.gpr[3]!=0u)return bad(5);
                restore_returned_=true;active_=e_.body;next_=e_.restore.lr;return true;
            }
            if(active_!=e_.body||!restore_returned_||c.lr!=e_.resume||!abi(c)||!allocation(c))return fail(5);
            outer_=true;next_=e_.resume;return true;
        }
        if(op==31u&&xo==146u){
            if(c.gpr[(w>>21)&31u]!=msr_)return bad(6);
            if(active_==e_.disable.pc&&!disabled_){disabled_=true;return true;}
            if(active_==e_.restore.pc&&disable_returned_&&!restored_){
                restored_=true;return true;
            }
            return bad(6);
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||(op==16u&&(w&1u)))return bad(7);
        if(op==16u||op==18u){
            const auto dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return bad(8);
            if(dst<=pc){poll_due_=true;poll_pc_=pc;}
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        // A non-linking external B returns to the outer native dispatcher.
        // Its poll occurs before the dispatcher's one extra host tick.
        // Direct BL helper entries still require zero additional ticks.
        const bool tail=active_==e_.veneer&&pc==e_.body;
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||
           c.inst_count-last_!=(tail?1u:0u)||(tail&&!tail_poll_)||!fence_.settled(c))return fail(6);
        const bool a=tail&&c.lr==e_.resume&&c.gpr[3]==gp_[3]&&c.gpr[4]==size_;
        const bool d=active_==e_.body&&!disabled_&&pc==e_.disable.pc&&c.lr==e_.disable.lr&&edge(c,e_.disable);
        const bool r=active_==e_.body&&disable_returned_&&!restored_&&pc==e_.restore.pc&&c.lr==e_.restore.lr&&edge(c,e_.restore)&&!c.gpr[3];
        if(!a&&!d&&!r)return fail(6);
        active_=pc;entry_due_=false;last_=c.inst_count;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_||!fence_.settled(c)||++polls_>1024u)return fail(7);
        if(outer_&&c.pc==e_.resume&&c.lr==c.pc&&abi(c)&&allocation(c)){
            stage_=2;outer_=false;return true;
        }
        if(poll_due_&&c.pc==poll_pc_){poll_due_=false;return true;}
        if(entry_due_&&active_==e_.veneer&&c.pc==e_.body&&!tail_poll_){tail_poll_=true;return true;}
        // The native emitter can poll after a masked mtmsr; it cannot deliver
        // an interrupt here, and a duplicate poll is rejected.
        if(active_==e_.restore.pc&&restored_&&c.pc==last_pc_+4u&&!restore_poll_){restore_poll_=true;return true;}
        if(active_==e_.disable.pc&&disabled_&&c.pc==last_pc_+4u&&!disable_poll_){disable_poll_=true;return true;}
        return fail(7);
    }
    template<class C>bool inline_return(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||!outer_||entry_due_||poll_due_||pc!=e_.resume||c.pc!=pc||c.lr!=pc||
           w!=e_.resume_word||!equal(c,pc,w)||c.inst_count-last_!=1u||!abi(c)||!allocation(c))return fail(8);
        last_=c.inst_count;stage_=2;outer_=false;return true;
    }
    template<class C>bool returned(C& c,bool held){
        return stage_==2u&&base(c,held)&&c.pc==e_.resume&&c.lr==c.pc&&c.inst_count==last_&&
               abi(c)&&restore_returned_&&allocation(c);
    }
private:
    IoctlAllocationExpectation e_;AllocatorStoreFence fence_;AllocatorRange heap_{},meta_{};
    const void* cpu_=nullptr;std::array<uint32_t,32> gp_{},caller_{};
    uint32_t sp_=0,msr_=0,cr_=0,size_=0,active_=0,next_=0,last_pc_=0,poll_pc_=0,request_=0;
    uint64_t last_=0,start_=0;unsigned stage_=0,error_=0,visits_=0,polls_=0,ordinal_=0,control_=0;
    bool entry_due_=false,poll_due_=false,outer_=false,disabled_=false,disable_returned_=false,
         restored_=false,restore_returned_=false,tail_poll_=false,restore_poll_=false,disable_poll_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool bad(unsigned n){control_=n;return fail(4);}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{
        return !error_&&cpu_==&c&&held&&safe(c)&&c.msr==msr_&&c.inst_count>=start_&&c.inst_count-start_<=2048u;
    }
    template<class C>bool live(C& c,bool held)const{return stage_==1u&&base(c,held);}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=sp_||c.gpr[2]!=gp_[2]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        for(unsigned i=0;i<caller_.size();++i)if(c.mmu.read32(sp_+8u+4u*i)!=caller_[i])return false;
        return true;
    }
    template<class C>bool allocation(C& c){
        const uint32_t a=OpenCacheRangeTrace::canonical(c.gpr[3]);
        if(!a||(a&31u)||!heap_.contains(a,size_)||!mapped(c,a,size_)||
           !fence_.finished(c)||!fence_.metadata_stores()||(request_&&request_!=a))return false;
        const auto head=c.mmu.read32(meta_.base);
        if(head&&(!heap_.contains(head,16u)||!equal(c,head,0xbabe0000u)||
           (uint64_t(head)<uint64_t(a)+size_&&uint64_t(a)<uint64_t(head)+16u)))return false;
        request_=a;return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||!((a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull)||(a>=0x90000000u&&uint64_t(a)+n<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool equal(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&equal(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&equal(c,pc,w);}
    template<class C>bool edge(C& c,VectorEdge e)const{return e.lr>=4u&&target(e.lr-4u,e.branch_word)==e.pc&&
        e.branch_word>>26==18u&&(e.branch_word&3u)==1u&&equal(c,e.lr-4u,e.branch_word)&&equal(c,e.pc,e.entry_word)&&known(c,e.pc,e.pc);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
