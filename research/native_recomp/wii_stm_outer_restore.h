#pragma once
#include "wii_ipc_dispatch_execution.h"
namespace undercover::wii {
struct StmOuterRestoreExpectation {
    uint32_t root,caller,caller_word,enable_site,resume,resume_word;
    std::span<const IpcDispatchWord> words;
};
// Stop at the actual rising-EE poll emitted for the original mtmsr.
// No interrupt entry until the independent native IRQ adapter validates
// the active thread, vector, device and resume PC.
class StmOuterRestoreWitness {
public:
    explicit StmOuterRestoreWitness(StmOuterRestoreExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    uint32_t expected_msr()const{return masked_|0x8000u;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.root||c.lr!=e_.caller||c.gpr[3]!=1u||
           c.msr&0x8000u||!known(c,e_.root)||!word(c,e_.caller,e_.caller_word)||
           !known(c,e_.enable_site)||e_.resume!=e_.enable_site+4u||!known(c,e_.resume)||
           !word(c,e_.resume,e_.resume_word))return fail(1);
        auto w=c.mmu.read32(e_.enable_site);
        if(w>>26!=31u||((w>>1)&1023u)!=146u)return fail(1);
        cpu_=&c;gp_=c.gpr;cr_=pack(c)&0x00fff000u;masked_=c.msr;
        next_=e_.root;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||due_||c.msr!=masked_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,pc)||!word(c,pc,w)||++visits_>32u)return fail(2);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u;
        if(op==31u&&xo==146u){
            if(pc!=e_.enable_site||c.gpr[rs]!=(masked_|0x8000u)||next_!=e_.resume)return fail(3);
            // Capture the exact architectural state before the only
            // admitted MSR write. The emitter must change just MSR/PC.
            enable_gp_=c.gpr;enable_cr_=pack(c);enable_lr_=c.lr;enable_ctr_=c.ctr;
            due_=true;return true;
        }
        if(op==16u||op==18u){
            if(w&3u||target(pc,w)<=pc||(op==16u&&!((w>>21)&4u)))return fail(3);
            if(op==18u||taken(c,w))next_=target(pc,w);
        }else if(op==31u&&xo==83u){} // mfmsr
        else if(!(op==10u||op==11u||op==14u||op==15u||op==20u||op==21u||op==23u||
                   (op>=24u&&op<=29u)||(op==31u&&(xo==0u||xo==32u||xo==28u||xo==444u||
                      xo==266u||xo==316u))))return fail(3);
        if(!known(c,next_))return fail(3);
        return true;
    }
    template<class C>bool poll(C& c,bool held,bool pending){
        if(stage_!=1u||!live(c,held)||!due_||!pending||c.pc!=e_.resume||c.msr!=expected_msr()||
           c.inst_count!=last_||!word(c,e_.resume,e_.resume_word)||c.gpr!=enable_gp_||
           pack(c)!=enable_cr_||c.lr!=enable_lr_||c.ctr!=enable_ctr_)return fail(4);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held,bool pending)const{
        return stage_==2u&&live(c,held)&&pending&&c.pc==e_.resume&&c.msr==expected_msr()&&
               c.inst_count==last_&&word(c,e_.resume,e_.resume_word)&&c.gpr==enable_gp_&&
               pack(c)==enable_cr_&&c.lr==enable_lr_&&c.ctr==enable_ctr_;
    }
private:
    StmOuterRestoreExpectation e_;
    const void* cpu_=nullptr;std::array<uint32_t,32> gp_{},enable_gp_{};
    uint32_t masked_=0,next_=0,cr_=0,enable_cr_=0,enable_lr_=0,enable_ctr_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0;bool due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool live(C& c,bool held)const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||
           c.lr!=e_.caller||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==e_.root&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;return (bo&16u)||bit==bool(bo&8u);}
};
}
