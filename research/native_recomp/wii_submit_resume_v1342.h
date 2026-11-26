#pragma once
#include "wii_sleep_exit_v1339.h"
namespace undercover::wii {
// Original synchronous submit after the sleeping caller has returned.
// Hold the completed response, then observe the outer interrupt restore
// and original allocator-free entry. No host writes or IOS service.
struct SubmitResumeExpectation{
    uint32_t submit,submit_resume,open_return,open_call_word;
    VectorEdge restore,release;
    std::span<const ReplyNativeWord> words;
};
class SubmitResumeWitness{
public:
    explicit SubmitResumeWitness(SubmitResumeExpectation e,uint32_t fd=0):e_(e),fd_(fd){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    uint32_t expected_msr()const{return enabled_?msr_:(msr_&~0x8000u);}
    template<class C>bool capture(C& c,bool held){
        if(stage_||error_||fd_>1u||!safe(c,held)||c.pc!=e_.submit||c.lr!=e_.open_return||
           !(c.msr&0x8000u)||!c.gpr[1]||(c.gpr[1]&7u)||!mapped(c,c.gpr[3],32u)||
           (c.gpr[3]&31u)||!word(c,c.gpr[3],StmIos::Open)||
           !known(c,e_.submit,e_.submit)||!known(c,e_.submit,e_.submit_resume)||
           !direct(c,e_.restore)||!direct(c,e_.release)||
           e_.open_call_word!=branch(e_.open_return-4u,e_.submit)||
           !word(c,e_.open_return-4u,e_.open_call_word))return fail(1);
        cpu_=&c;req_=c.gpr[3];sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;
        tick_=c.inst_count;stage_=1;return true;
    }
    template<class C,class Prior>bool begin(C& c,const Prior& prior,bool held){
        if(stage_!=1u||!base(c,held)||!prior.returned(c,held)||c.pc!=e_.submit_resume||
           c.msr!=(msr_&~0x8000u)||c.gpr[1]>=sp_||sp_-c.gpr[1]>1024u||
           !word(c,req_,StmIos::Reply)||!word(c,req_+4u,fd_)||!word(c,req_+8u,StmIos::Open))return fail(2);
        for(unsigned i=0;i<reply_.size();++i)reply_[i]=c.mmu.read32(req_+4u*i);
        active_=e_.submit;next_=c.pc;last_=c.inst_count;stage_=2;resume_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||entry_due_||poll_due_||pc!=next_||
           c.inst_count-last_!=(resume_?2u:1u)||!known(c,active_,pc,w)||++visits_>512u)return fail(3);
        if(resume_&&c.pc!=pc)return fail(3);
        resume_=false;last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const bool restoring=!restored_&&pc+4u==e_.restore.lr&&w==e_.restore.branch_word&&c.gpr[3]&&!(c.msr&0x8000u);
            const bool releasing=restored_&&pc+4u==e_.release.lr&&w==e_.release.branch_word&&
                c.msr==msr_&&(c.gpr[4]&0x3fffffffu)==(req_&0x3fffffffu)&&
                (c.gpr[4]&0xc0000000u)!=0x40000000u;
            if(active_!=e_.submit||(!restoring&&!releasing))return fail(4);
            next_=restoring?e_.restore.pc:e_.release.pc;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u||active_!=e_.restore.pc)return fail(4);
            if(!taken(c,w))return true;
            if(c.lr!=e_.restore.lr||c.msr!=msr_||!enabled_||!polled_)return fail(4);
            restored_=true;active_=e_.submit;next_=e_.restore.lr;return true;
        }
        if(op==31u&&xo==146u){
            if(active_!=e_.restore.pc||enabled_||c.msr!=(msr_&~0x8000u)||
               c.gpr[(w>>21)&31u]!=msr_)return fail(4);
            enabled_=true;poll_due_=true;poll_pc_=next_;return true;
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
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||c.inst_count!=last_)return fail(5);
        if(!restored_&&pc==e_.restore.pc&&c.lr==e_.restore.lr&&direct(c,e_.restore)){
            active_=pc;entry_due_=false;return true;
        }
        if(restored_&&pc==e_.release.pc&&c.lr==e_.release.lr&&direct(c,e_.release)&&
           (c.gpr[4]&0x3fffffffu)==(req_&0x3fffffffu)&&c.msr==msr_){
            stage_=3;entry_due_=false;return true;
        }
        return fail(5);
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||!poll_due_||c.inst_count!=last_||c.pc!=poll_pc_)return fail(6);
        if(enabled_&&!polled_){
            if(c.msr!=msr_||active_!=e_.restore.pc)return fail(6);
            polled_=true;
        }
        poll_due_=false;return true;
    }
    template<class C>bool release_at(C& c,bool held)const{
        return stage_==3u&&base(c,held)&&wire(c)&&c.pc==e_.release.pc&&c.lr==e_.release.lr&&
            c.inst_count==last_&&c.msr==msr_&&restored_&&enabled_&&polled_&&
            (c.gpr[4]&0x3fffffffu)==(req_&0x3fffffffu)&&
            (c.gpr[4]&0xc0000000u)!=0x40000000u&&direct(c,e_.release);
    }
private:
    SubmitResumeExpectation e_;uint32_t fd_;const void* cpu_=nullptr;
    std::array<uint32_t,8> reply_{};
    uint32_t req_=0,sp_=0,r2_=0,r13_=0,msr_=0,active_=0,next_=0,last_pc_=0,poll_pc_=0;
    uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0,visits_=0;
    bool resume_=false,entry_due_=false,poll_due_=false,enabled_=false,polled_=false,restored_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c,bool held){return held&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{
        return !error_&&cpu_==&c&&safe(c,held)&&c.gpr[2]==r2_&&c.gpr[13]==r13_&&
            c.inst_count>=tick_&&c.inst_count-tick_<=32768u;
    }
    template<class C>bool live(C& c,bool held)const{
        return stage_==2u&&base(c,held)&&wire(c)&&
            c.msr==(enabled_?msr_:(msr_&~0x8000u));
    }
    template<class C>bool wire(C& c)const{
        for(unsigned i=0;i<reply_.size();++i)if(!word(c,req_+4u*i,reply_[i]))return false;
        return true;
    }
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
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
