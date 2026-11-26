#pragma once
#include "wii_cooperative_load_lane_v1317.h"
#include "wii_reply_return_v1298.h"
namespace undercover::wii {
// Capture the original sleeping caller before SelectThread changes its
// stack, then observe the cooperative RFI continuation. No guest writes.
struct SleepResumeExpectation{
    uint32_t select,sleep,save_return,sleep_return;
    VectorEdge restore;
    std::span<const ReplyNativeWord> words;
};
class SleepResumeWitness{
public:
    explicit SleepResumeWitness(SleepResumeExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool capture(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.select||c.lr!=e_.sleep_return||
           c.gpr[3]!=0u||(c.msr&0x8000u)||!known(c,e_.select,e_.save_return)||
           !known(c,e_.sleep,e_.sleep_return)||!known(c,e_.sleep,e_.restore.lr-4u)||
           e_.words.empty()||e_.words.size()>512u||!word(c,e_.restore.pc,e_.restore.entry_word)||
           e_.restore.branch_word!=branch(e_.restore.lr-4u,e_.restore.pc)||
           !word(c,e_.restore.lr-4u,e_.restore.branch_word))return fail(1);
        cpu_=&c;gp_=c.gpr;cr_=pack(c)&0x00fff000u;msr_=c.msr;stage_=1;return true;
    }
    template<class C,class Load>bool begin(C& c,const Load& load,bool held){
        if(stage_!=1u||!live(c,held)||!load.restored(c,held)||c.pc!=e_.save_return||
           c.gpr[3]!=1u||c.gpr[1]>=gp_[1]||gp_[1]-c.gpr[1]>256u)return fail(2);
        active_=e_.select;next_=c.pc;last_=c.inst_count;stage_=2;outer_=true;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=2u||!live(c,held)||outer_||poll_due_||entry_due_||pc!=next_||
           c.inst_count-last_!=(resume_?2u:1u)||!known(c,active_,pc,w)||++visits_>512u)return fail(3);
        if(resume_&&c.pc!=pc)return fail(3);
        if(active_==e_.sleep&&!abi(c))return fail(4);
        resume_=false;last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==19u&&xo==16u){
            if(w&1u||active_!=e_.select)return fail(5);
            if(!taken(c,w))return true;
            if(c.lr!=e_.sleep_return||!abi(c))return fail(4);
            active_=e_.sleep;next_=e_.sleep_return;outer_=true;return true;
        }
        if(op==18u&&(w&1u)){
            if(active_!=e_.sleep||pc+4u!=e_.restore.lr||w!=e_.restore.branch_word||
               c.gpr[3]!=0u||!abi(c))return fail(5);
            next_=e_.restore.pc;entry_due_=true;return true;
        }
        if(op==17u||(op==19u&&(xo==528u||xo==50u))||(op==31u&&xo==146u)||
           (op==16u&&(w&1u)))return fail(5);
        if(op==16u||op==18u){
            const uint32_t dst=target(pc,w);
            if((w&3u)||!known(c,active_,dst))return fail(5);
            if(dst<=pc)poll_due_=true;
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=2u||!live(c,held)||c.inst_count!=last_)return fail(6);
        if(outer_&&c.pc==next_){
            if(active_==e_.sleep&&!abi(c))return fail(4);
            outer_=false;resume_=true;return true;
        }
        if(poll_due_&&c.pc==last_pc_){poll_due_=false;return true;}
        return fail(6);
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=2u||!live(c,held)||!entry_due_||pc!=e_.restore.pc||c.pc!=pc||
           c.lr!=e_.restore.lr||c.inst_count!=last_||c.gpr[3]||!abi(c)||
           !word(c,pc,e_.restore.entry_word))return fail(7);
        stage_=3;return true;
    }
    template<class C>bool restored_sleep_at(C& c,bool held)const{
        return stage_==3u&&live(c,held)&&c.inst_count==last_&&c.pc==e_.restore.pc&&
           c.lr==e_.restore.lr&&c.gpr[3]==0u&&abi(c);
    }
private:
    SleepResumeExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};uint32_t cr_=0,msr_=0,active_=0,next_=0,last_pc_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0;
    bool outer_=false,resume_=false,poll_due_=false,entry_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool live(C& c,bool held)const{return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_;}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    static uint32_t branch(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
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
