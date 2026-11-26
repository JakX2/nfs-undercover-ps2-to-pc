#pragma once
#include "wii_ioctl_first_flush_v1398.h"
#include "wii_ioctl_construction_v1392.h"
namespace undercover::wii {
struct IoctlFlushTailExpectation{
    VectorEdge output,submit;
    std::span<const ReplyNativeWord> words;
};
// Same CPU, immutable constructed request. Admit only the original
// read-only wrapper corridors between the cache helpers and submit.
class IoctlFlushTailWitness{
public:
    explicit IoctlFlushTailWitness(IoctlFlushTailExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;} unsigned visits()const{return visits_;}
    template<class C>bool begin(C& c,bool held,uint32_t request,uint32_t output,uint32_t size){
        if(stage_||!held||!safe(c)||c.pc!=OpenScRoute::EventInputCaller||c.lr!=c.pc||
           !request||(request&31u)||!output||size<4u||size>4096u||!known(c,c.pc)||
           !edge(c,e_.output)||!edge(c,e_.submit)||e_.output.lr!=OpenScRoute::EventOutputCaller)return fail(1);
        cpu_=&c;sp_=c.gpr[1];msr_=c.msr;request_=request;output_=output;size_=size;
        next_=c.pc;tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if((stage_!=1u&&stage_!=3u)||!live(c,held)||due_||pc!=next_||c.inst_count-tick_!=1u||
           !known(c,pc)||c.mmu.read32(pc)!=w||++visits_>32u)return fail(2);
        tick_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            auto e=stage_==1u?e_.output:e_.submit;
            if(pc+4u!=e.lr||w!=e.branch_word||!edge(c,e))return fail(3);
            if(stage_==1u?(canonical(c.gpr[3])!=output_||c.gpr[4]!=size_):canonical(c.gpr[3])!=request_)return fail(4);
            next_=e.pc;due_=true;return true;
        }
        // No writes, system state changes, or arbitrary transfers in
        // this corridor. An unexpected opcode fails closed.
        if(op==16u||op==18u){
            if(w&3u)return fail(5);
            auto dst=target(pc,w);
            if(dst<=pc)return fail(5);
            if(op==18u||taken(c,w))next_=dst;
            if(!known(c,next_))return fail(5);
        }else if(!(op==10u||op==11u||op==14u||op==15u||op==20u||op==21u||op==23u||
            (op>=24u&&op<=29u)||op==32u||op==34u||op==40u||op==42u||
            (op==31u&&(xo==0u||xo==32u||xo==28u||xo==444u||xo==266u||xo==316u))))return fail(5);
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if((stage_!=1u&&stage_!=3u)||!live(c,held)||!due_||c.pc!=pc||pc!=next_||c.inst_count!=tick_)return fail(6);
        const auto e=stage_==1u?e_.output:e_.submit;
        if(pc!=e.pc||c.lr!=e.lr||!edge(c,e))return fail(6);
        due_=false;++stage_;return true;
    }
    template<class C>bool output_return(C& c,bool held){
        if(stage_!=2u||!live(c,held)||c.pc!=e_.output.lr||c.lr!=c.pc||
           c.inst_count<=tick_||!known(c,c.pc))return fail(7);
        next_=c.pc;tick_=c.inst_count;stage_=3;return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==4u&&live(c,held)&&c.pc==e_.submit.pc&&c.lr==e_.submit.lr&&
            c.inst_count==tick_&&canonical(c.gpr[3])==request_&&edge(c,e_.submit);
    }
private:
    IoctlFlushTailExpectation e_;const void* cpu_=nullptr;uint32_t sp_=0,msr_=0,request_=0,output_=0,size_=0,next_=0;
    uint64_t tick_=0;unsigned stage_=0,error_=0,visits_=0;bool due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static uint32_t canonical(uint32_t a){return OpenCacheRangeTrace::canonical(a);}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr[1]==sp_&&c.msr==msr_&&c.inst_count>=tick_;}
    template<class C>bool known(C& c,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.pc==pc&&c.mmu.read32(pc)==x.word;})==1;
    }
    template<class C>bool edge(C& c,VectorEdge e)const{
        return e.lr>=4u&&e.branch_word>>26==18u&&(e.branch_word&3u)==1u&&target(e.lr-4u,e.branch_word)==e.pc&&
            known(c,e.lr-4u)&&c.mmu.read32(e.lr-4u)==e.branch_word&&c.mmu.read32(e.pc)==e.entry_word;
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
