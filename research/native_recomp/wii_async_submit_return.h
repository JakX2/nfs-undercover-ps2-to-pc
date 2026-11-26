#pragma once
#include "wii_ipc_dispatch_execution.h"
namespace undercover::wii {
struct AsyncSubmitReturnExpectation {
    uint32_t submit,start,caller,caller_word;
    IpcDispatchEdge restore;
    std::span<const IpcDispatchWord> words;
};
// Original async submit's successful return, with the nested interrupt
// restore required to keep EE masked. No sleep, free, service or MMIO.
class AsyncSubmitReturnWitness {
public:
    explicit AsyncSubmitReturnWitness(AsyncSubmitReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned polls()const{return polls_;}
    unsigned ordinal()const{return ordinal_;}
    template<class C>bool begin(C& c,bool held,uint32_t caller_sp){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.start||
           !known(c,e_.submit,e_.start)||!word(c,e_.caller,e_.caller_word)||
           !known(c,e_.submit,e_.restore.call,e_.restore.word)||
           !known(c,e_.restore.target,e_.restore.target)||
           e_.restore.word>>26!=18u||(e_.restore.word&3u)!=1u||
           target(e_.restore.call,e_.restore.word)!=e_.restore.target||
           caller_sp<=c.gpr[1]||caller_sp-c.gpr[1]>512u||(caller_sp&7u))return fail(1);
        cpu_=&c;sp_=c.gpr[1];caller_sp_=caller_sp;msr_=c.msr;r2_=c.gpr[2];r13_=c.gpr[13];
        owner_=e_.submit;next_=e_.start;tick_=last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||entry_due_||return_due_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,owner_,pc,w)||++visits_>256u)return fail(2);
        ordinal_=(pc-owner_)/4u+1u;
        if(ctr_due_&&c.ctr!=ctr_expected_)return fail(3);
        ctr_due_=false;last_=c.inst_count;next_=pc+4u;poll_pc_=0;polled_=false;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u||
           op==52u||op==53u||op==54u||op==55u||op==60u||op==61u||
           (op==31u&&(xo==150u||xo==151u||xo==183u||xo==215u||xo==247u||xo==407u||
             xo==439u||xo==661u||xo==662u||xo==725u||xo==918u||xo==663u||xo==695u||
             xo==727u||xo==759u||xo==983u||xo==1014u)))return fail(4);
        if(op==18u&&(w&1u)){
            if(owner_!=e_.submit||restored_||pc!=e_.restore.call||w!=e_.restore.word||c.gpr[3]!=0u)
                return fail(5);
            entry_due_=true;next_=e_.restore.target;return true;
        }
        if(op==31u&&xo==146u){
            if(owner_!=e_.restore.target||msr_written_||c.gpr[(w>>21)&31u]!=msr_)return fail(5);
            msr_written_=true;poll_pc_=next_;return true;
        }
        if(op==31u&&xo==467u){
            const unsigned spr=((w>>16)&31u)|(((w>>11)&31u)<<5);
            if(owner_!=e_.submit||spr!=8u||c.gpr[(w>>21)&31u]!=e_.caller)return fail(5);
        }
        if(op==17u||(op==19u&&(xo==50u||xo==528u)))return fail(5);
        if(op==19u&&xo==16u){
            if(w&1u)return fail(5);
            const bool transfer=taken(c,w);
            predict_ctr(c,w);
            if(transfer){
                if(owner_==e_.restore.target){
                    if(!msr_written_||c.lr!=e_.restore.call+4u||!helper_abi(c))return fail(5);
                    owner_=e_.submit;restored_=true;next_=c.lr;return true;
                }
                if(owner_!=e_.submit||!restored_||c.lr!=e_.caller||c.gpr[1]!=caller_sp_||c.gpr[3]!=0u)
                    return fail(5);
                return_due_=true;next_=e_.caller;return true;
            }
        }
        if(op==16u||op==18u){
            if(w&3u)return fail(5);
            const auto dst=target(pc,w);
            if(dst<=pc)poll_pc_=pc;
            if(op==18u||taken(c,w))next_=dst;
            if(op==16u)predict_ctr(c,w);
        }
        if(!known(c,owner_,next_))return fail(5);
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||pc!=e_.restore.target||
           c.lr!=e_.restore.call+4u||c.inst_count!=last_||c.gpr[1]!=sp_)return fail(6);
        owner_=pc;entry_due_=false;helper_=c.gpr;helper_cr_=pack(c)&0x00fff000u;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||!poll_pc_||polled_||c.pc!=poll_pc_||c.inst_count!=last_||++polls_>32u)return fail(7);
        polled_=true;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,bool held,bool caller_abi){
        if(stage_!=1u||!live(c,held)||!return_due_||!caller_abi||pc!=e_.caller||c.pc!=pc||c.lr!=pc||
           c.inst_count!=last_||c.gpr[1]!=caller_sp_||c.gpr[3]!=0u||!word(c,pc,e_.caller_word)||
           (ctr_due_&&c.ctr!=ctr_expected_))return fail(8);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held,bool caller_abi)const{
        return stage_==2u&&live(c,held)&&caller_abi&&c.pc==e_.caller&&c.lr==e_.caller&&
            c.inst_count==last_&&c.gpr[1]==caller_sp_&&c.gpr[3]==0u&&word(c,c.pc,e_.caller_word);
    }
private:
    AsyncSubmitReturnExpectation e_;
    const void* cpu_=nullptr;
    std::array<uint32_t,32> helper_{};
    uint32_t sp_=0,caller_sp_=0,msr_=0,r2_=0,r13_=0,owner_=0,next_=0,poll_pc_=0,helper_cr_=0,ctr_expected_=0;
    uint64_t tick_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0,polls_=0,ordinal_=0;
    bool entry_due_=false,return_due_=false,restored_=false,msr_written_=false,polled_=false,ctr_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.gpr[2]==r2_&&c.gpr[13]==r13_&&
            (c.gpr[1]==sp_||c.gpr[1]==caller_sp_)&&c.inst_count>=tick_&&c.inst_count-tick_<=256u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool helper_abi(C& c)const{
        if(c.gpr[1]!=helper_[1]||c.gpr[2]!=helper_[2]||(pack(c)&0x00fff000u)!=helper_cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=helper_[i])return false;
        return true;
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));}
    template<class C>void predict_ctr(C& c,uint32_t w){if(!((w>>21)&4u)){ctr_due_=true;ctr_expected_=c.ctr-1u;}}
};
}
