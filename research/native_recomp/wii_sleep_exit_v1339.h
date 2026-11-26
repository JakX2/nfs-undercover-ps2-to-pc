#pragma once
#include "wii_sleep_resume_v1335.h"
namespace undercover::wii {
// Verify the original nested interrupt restore and return to the actual
// synchronous submit caller. The nested restore must not raise EE.
struct SleepExitExpectation{
    uint32_t sleep,submit_return,submit_return_word;
    VectorEdge restore;
    std::span<const ReplyNativeWord> words;
};
class SleepExitWitness{
public:
    explicit SleepExitWitness(SleepExitExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool capture(C& c,bool held){
        if(stage_||error_||!safe(c,held)||c.pc!=e_.sleep||c.lr!=e_.submit_return||
           (c.msr&0x8000u)||!c.gpr[1]||(c.gpr[1]&7u)||!c.gpr[3]||
           !known(c,e_.sleep,e_.sleep)||!known(c,e_.sleep,e_.restore.lr)||
           !known(c,e_.restore.pc,e_.restore.pc)||!word(c,e_.submit_return,e_.submit_return_word)||
           !word(c,e_.restore.lr-4u,e_.restore.branch_word)||!word(c,e_.restore.pc,e_.restore.entry_word)||
           e_.restore.branch_word!=branch(e_.restore.lr-4u,e_.restore.pc))return fail(1);
        cpu_=&c;gp_=c.gpr;cr_=pack(c)&0x00fff000u;msr_=c.msr;tick_=c.inst_count;stage_=1;return true;
    }
    template<class C,class Prior>bool begin(C& c,const Prior& prior,bool held){
        if(stage_!=1u||!live(c,held)||!prior.restored_sleep_at(c,held)||c.pc!=e_.restore.pc||
           c.lr!=e_.restore.lr||c.gpr[3]||c.gpr[1]>=gp_[1]||gp_[1]-c.gpr[1]>256u)return fail(2);
        nested_sp_=c.gpr[1];active_=e_.restore.pc;next_=c.pc;last_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=2u||!live(c,held)||outer_||poll_due_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,active_,pc,w)||++visits_>128u)return fail(3);
        if(active_==e_.restore.pc&&c.gpr[1]!=nested_sp_)return fail(3);
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==19u&&xo==16u){
            if(w&1u)return fail(4);
            if(!taken(c,w))return true;
            if(active_==e_.restore.pc){
                if(c.lr!=e_.restore.lr||c.gpr[3]||msr_writes_!=1u)return fail(4);
                active_=e_.sleep;next_=e_.restore.lr;return true;
            }
            if(active_!=e_.sleep||c.lr!=e_.submit_return||!abi(c)||msr_writes_!=1u)return fail(5);
            next_=e_.submit_return;outer_=true;return true;
        }
        if(op==31u&&xo==146u){
            if(active_!=e_.restore.pc||msr_writes_||c.gpr[(w>>21)&31u]!=msr_)return fail(4);
            ++msr_writes_;
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||(op==18u&&(w&1u))||(op==16u&&(w&1u)))return fail(4);
        if(op==16u||op==18u){
            const uint32_t dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return fail(4);
            if(dst<=pc)poll_due_=true;
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=2u||!live(c,held)||c.inst_count!=last_)return fail(6);
        if(outer_&&c.pc==e_.submit_return&&abi(c)&&word(c,c.pc,e_.submit_return_word)){
            stage_=3;outer_=false;return true;
        }
        if(poll_due_&&c.pc==last_pc_){poll_due_=false;return true;}
        return fail(6);
    }
    template<class C>bool returned(C& c,bool held)const{
        return stage_==3u&&live(c,held)&&c.pc==e_.submit_return&&c.lr==e_.submit_return&&
            c.inst_count==last_&&abi(c)&&msr_writes_==1u&&word(c,c.pc,e_.submit_return_word);
    }
private:
    SleepExitExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};uint32_t cr_=0,msr_=0,nested_sp_=0,active_=0,next_=0,last_pc_=0;
    uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0,visits_=0,msr_writes_=0;
    bool outer_=false,poll_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c,bool held){return held&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool live(C& c,bool held)const{return !error_&&cpu_==&c&&safe(c,held)&&c.msr==msr_&&c.inst_count>=tick_&&c.inst_count-tick_<=32768u;}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
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
