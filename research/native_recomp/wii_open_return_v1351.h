#pragma once
#include "wii_allocator_release_v1347.h"
namespace undercover::wii {
struct OpenReturnExpectation{
    uint32_t open,submit,free_resume,submit_resume,stm_resume;
    uint32_t open_call_word,submit_call_word,stm_resume_word;
    std::span<const ReplyNativeWord> words;
};
// Observe the actual native submit and IOS_Open returns after free.
// Capture each caller ABI at its own original entry, not after sleep.
class OpenReturnWitness{
public:
    explicit OpenReturnWitness(OpenReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    uint32_t expected_msr()const{return msr_;}
    template<class C>bool capture_open(C& c,bool held){
        if(stage_||error_||!safe(c,held)||c.pc!=e_.open||c.lr!=e_.stm_resume||
           !(c.msr&0x8000u)||!c.gpr[1]||(c.gpr[1]&7u)||c.gpr[4]||
           !known(c,e_.open,e_.open)||!known(c,e_.open,e_.submit_resume)||
           !word(c,e_.stm_resume,e_.stm_resume_word)||e_.open_call_word!=branch(e_.stm_resume-4u,e_.open)||
           !word(c,e_.stm_resume-4u,e_.open_call_word))return fail(1);
        cpu_=&c;msr_=c.msr;open_=capture(c);start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool capture_submit(C& c,bool held){
        if(stage_!=1u||!base(c,held)||c.pc!=e_.submit||c.lr!=e_.submit_resume||
           c.gpr[1]>=open_.gp[1]||open_.gp[1]-c.gpr[1]>1024u||
           !known(c,e_.submit,e_.submit)||!known(c,e_.submit,e_.free_resume)||
           e_.submit_call_word!=branch(e_.submit_resume-4u,e_.submit)||
           !word(c,e_.submit_resume-4u,e_.submit_call_word))return fail(2);
        submit_=capture(c);stage_=2;return true;
    }
    template<class C,class Prior>bool begin(C& c,Prior& prior,bool held,bool descriptor,uint32_t fd){
        if(stage_!=2u||!base(c,held)||!descriptor||!prior.returned(c,held)||
           c.pc!=e_.free_resume||c.gpr[1]>=submit_.gp[1]||submit_.gp[1]-c.gpr[1]>1024u)
            return fail(3);
        fd_=fd;active_=e_.submit;next_=c.pc;last_=c.inst_count;stage_=3;resume_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held,bool descriptor){
        if(!live(c,held,descriptor)||outer_||poll_due_||pc!=next_||
           c.inst_count-last_!=(resume_?2u:1u)||!known(c,active_,pc,w)||++visits_>256u)
            return fail(4);
        if(resume_&&c.pc!=pc)return fail(4);
        resume_=false;last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==19u&&xo==16u){
            if(w&1u)return fail(5);
            if(!taken(c,w))return true;
            const auto expected=stage_==3u?e_.submit_resume:e_.stm_resume;
            const auto& a=stage_==3u?submit_:open_;
            if(c.lr!=expected||c.gpr[3]!=fd_||!abi(c,a))return fail(5);
            next_=expected;outer_=true;return true;
        }
        if(op==17u||(op==19u&&(xo==50u||xo==528u))||(op==31u&&xo==146u)||
           (op==18u&&(w&1u))||(op==16u&&(w&1u)))return fail(5);
        if(op==16u||op==18u){
            const uint32_t dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return fail(5);
            if(dst<=pc)poll_due_=true;
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held,bool descriptor){
        if(!live(c,held,descriptor)||c.inst_count!=last_)return fail(6);
        if(outer_&&c.pc==next_&&c.gpr[3]==fd_){
            if(stage_==3u&&abi(c,submit_)&&known(c,e_.open,e_.submit_resume)){
                stage_=4;active_=e_.open;resume_=true;outer_=false;return true;
            }
            if(stage_==4u&&abi(c,open_)&&word(c,e_.stm_resume,e_.stm_resume_word)){
                stage_=5;outer_=false;return true;
            }
            return fail(6);
        }
        if(poll_due_&&c.pc==last_pc_){poll_due_=false;return true;}
        return fail(6);
    }
    template<class C>bool returned(C& c,bool held,bool descriptor)const{
        return stage_==5u&&base(c,held)&&descriptor&&c.inst_count==last_&&c.pc==e_.stm_resume&&
            c.lr==e_.stm_resume&&c.gpr[3]==fd_&&abi(c,open_)&&word(c,c.pc,e_.stm_resume_word);
    }
private:
    struct Abi{std::array<uint32_t,32> gp{};uint32_t cr=0;};
    OpenReturnExpectation e_;const void* cpu_=nullptr;Abi open_{},submit_{};
    uint32_t msr_=0,fd_=0,active_=0,next_=0,last_pc_=0;uint64_t last_=0,start_=0;
    unsigned stage_=0,error_=0,visits_=0;bool resume_=false,outer_=false,poll_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c,bool held){return held&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{return !error_&&cpu_==&c&&safe(c,held)&&c.msr==msr_&&c.inst_count>=start_&&c.inst_count-start_<=65536u;}
    template<class C>bool live(C& c,bool held,bool descriptor)const{return (stage_==3u||stage_==4u)&&base(c,held)&&descriptor;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static Abi capture(C& c){return {c.gpr,pack(c)&0x00fff000u};}
    template<class C>static bool abi(C& c,const Abi& a){
        if(c.gpr[1]!=a.gp[1]||c.gpr[2]!=a.gp[2]||(pack(c)&0x00fff000u)!=a.cr)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=a.gp[i])return false;
        return true;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    static uint32_t branch(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
