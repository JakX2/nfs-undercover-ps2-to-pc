#pragma once
#include "wii_submit_resume_v1342.h"
#include "wii_allocator_store_fence_v1346.h"
namespace undercover::wii {
struct AllocatorReleaseExpectation {
    uint32_t root,resume,resume_word;
    VectorEdge disable,restore;
    std::span<const ReplyNativeWord> words;
};
// Actual free body and its two interrupt leaves. The observer owns no
// allocation, never changes RAM and only accepts a return after a witnessed
// native heap store and restored nonvolatile ABI.
class AllocatorReleaseWitness {
public:
    explicit AllocatorReleaseWitness(AllocatorReleaseExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned store_failure()const{return fence_.failure();}
    unsigned stores()const{return fence_.stores();}
    unsigned heap_stores()const{return fence_.heap_stores();}
    uint32_t expected_msr()const{return disabled_&&!enabled_?msr_&~0x8000u:msr_;}
    template<class C,class Prior>bool begin(C& c,const Prior& prior,bool held,AllocatorRange heap,uint32_t request){
        if(stage_||error_||!safe(c,held)||!prior.release_at(c,held)||c.pc!=e_.root||c.lr!=e_.resume||
           !(c.msr&0x8000u)||(c.gpr[4]&0x3fffffffu)!=(request&0x3fffffffu)||
           (c.gpr[4]&0xc0000000u)==0x40000000u||!heap.contains(request,32u)||
           !word(c,request,StmIos::Reply)||!word(c,request+4u,0u)||!word(c,request+8u,StmIos::Open)||
           c.gpr[1]<512u||(c.gpr[1]&7u)||!known(c,e_.root,e_.root)||
           !word(c,e_.resume,e_.resume_word)||!direct(c,e_.disable)||!direct(c,e_.restore)||
           !fence_.begin(c,{c.gpr[1]-512u,520u},heap))return fail(1);
        cpu_=&c;gp_=c.gpr;cr_=pack(c)&0x00fff000u;msr_=c.msr;active_=e_.root;
        next_=c.pc;last_=start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||entry_due_||poll_due_||outer_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,active_,pc,w)||++visits_>512u)return fail(2);
        if(!fence_.before(c,w))return fail(3);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const bool d=!disabled_&&pc+4u==e_.disable.lr&&w==e_.disable.branch_word;
            const bool r=disabled_&&!enabled_&&disable_returned_&&pc+4u==e_.restore.lr&&
                w==e_.restore.branch_word&&c.gpr[3]==1u;
            if(active_!=e_.root||(!d&&!r))return fail(4);
            next_=d?e_.disable.pc:e_.restore.pc;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u)return fail(4);
            if(!taken(c,w))return true;
            if(active_==e_.disable.pc){
                if(!disabled_||enabled_||c.lr!=e_.disable.lr||c.gpr[3]!=1u)return fail(4);
                disable_returned_=true;active_=e_.root;next_=e_.disable.lr;return true;
            }
            if(active_==e_.restore.pc){
                if(!enabled_||!restore_polled_||c.lr!=e_.restore.lr||c.gpr[3]!=1u)return fail(4);
                restore_returned_=true;active_=e_.root;next_=e_.restore.lr;return true;
            }
            if(active_!=e_.root||!restore_returned_||c.lr!=e_.resume||!abi(c)||
               !fence_.finished(c))return fail(5);
            outer_=true;next_=e_.resume;return true;
        }
        if(op==31u&&xo==146u){
            const uint32_t v=c.gpr[(w>>21)&31u];
            if(active_==e_.disable.pc&&!disabled_&&v==(msr_&~0x8000u)){disabled_=true;return true;}
            if(active_==e_.restore.pc&&disabled_&&!enabled_&&v==msr_){
                enabled_=true;poll_due_=true;poll_pc_=next_;return true;
            }
            return fail(4);
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||(op==16u&&(w&1u)))return fail(4);
        if(op==16u||op==18u){
            const uint32_t dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return fail(4);
            if(dst<=pc){poll_due_=true;poll_pc_=pc;}
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||c.inst_count!=last_||!fence_.settled(c))return fail(6);
        const bool d=!disabled_&&pc==e_.disable.pc&&c.lr==e_.disable.lr&&direct(c,e_.disable);
        const bool r=disabled_&&!enabled_&&pc==e_.restore.pc&&c.lr==e_.restore.lr&&direct(c,e_.restore)&&c.gpr[3]==1u;
        if(!d&&!r)return fail(6);
        active_=pc;entry_due_=false;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_||!fence_.settled(c))return fail(7);
        if(outer_&&c.pc==e_.resume&&abi(c)&&word(c,c.pc,e_.resume_word)&&fence_.finished(c)){
            stage_=2;outer_=false;return true;
        }
        if(poll_due_&&c.pc==poll_pc_){
            if(active_==e_.restore.pc&&enabled_)restore_polled_=true;
            poll_due_=false;return true;
        }
        return fail(7);
    }
    template<class C>bool returned(C& c,bool held){
        return stage_==2u&&base(c,held)&&c.pc==e_.resume&&c.lr==e_.resume&&c.inst_count==last_&&
            c.msr==msr_&&abi(c)&&restore_returned_&&word(c,c.pc,e_.resume_word)&&fence_.finished(c);
    }
private:
    AllocatorReleaseExpectation e_;AllocatorStoreFence fence_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};uint32_t cr_=0,msr_=0,active_=0,next_=0,poll_pc_=0;
    uint64_t last_=0,start_=0;unsigned stage_=0,error_=0,visits_=0;
    bool disabled_=false,enabled_=false,disable_returned_=false,restore_polled_=false,restore_returned_=false;
    bool entry_due_=false,poll_due_=false,outer_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c,bool held){return held&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{return !error_&&cpu_==&c&&safe(c,held)&&c.inst_count>=start_&&c.inst_count-start_<=2048u;}
    template<class C>bool live(C& c,bool held)const{return stage_==1u&&base(c,held)&&c.msr==expected_msr();}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        const uint64_t end=uint64_t(a)+4u;
        if((a&3u)||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    template<class C>bool direct(C& c,VectorEdge e)const{return e.lr>=4u&&e.branch_word==branch(e.lr-4u,e.pc)&&word(c,e.lr-4u,e.branch_word)&&word(c,e.pc,e.entry_word)&&known(c,e.pc,e.pc);}
    static uint32_t branch(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
