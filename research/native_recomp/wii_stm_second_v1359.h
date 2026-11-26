#pragma once
#include "wii_open_return_v1351.h"
#include "wii_stm_prefix_witness_v629.h"
namespace undercover::wii {
struct StmSecondExpectation {
    uint32_t resume,call,open,entry_word;
    std::span<const ReplyNativeWord> words;
    std::span<const uint32_t> exits;
    std::span<const StmPath> paths;
};
// Observe original STM after first Open. Do not execute second Open yet.
class StmSecondWitness {
public:
    explicit StmSecondWitness(StmSecondExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return stores_;}
    unsigned path_kind()const{return 3u-first_kind_;}
    template<class C,class Prior>bool begin(C& c,Prior& prior,bool held,bool descriptor,unsigned kind){
        if(stage_||error_||!held||!descriptor||!prior.returned(c,held,descriptor)||
           c.pc!=e_.resume||c.lr!=e_.resume||c.gpr[3]!=0u||!(c.msr&0x8000u)||
           (kind!=1u&&kind!=2u)||!known(c,e_.resume)||!known(c,e_.call)||
           !word(c,e_.open,e_.entry_word)||e_.paths.empty()||e_.paths.size()>8u)return fail(1);
        cpu_=&c;msr_=c.msr;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];first_kind_=kind;
        next_=e_.resume;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held,bool descriptor){
        if(!live(c,held,descriptor)||pending_call_||poll_due_||pc!=next_||
           c.inst_count-last_!=(resume_?2u:1u)||!known(c,pc,w)||++visits_>32u)return fail(2);
        if(resume_&&c.pc!=pc)return fail(2);
        if(!settled(c))return fail(3);
        resume_=false;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rs=(w>>21)&31u;
        if(op==36u){
            const int64_t ea=int64_t(ra==13u?r13_:r2_)+int32_t((w&0xffffu)^0x8000u)-0x8000;
            if((ra!=2u&&ra!=13u)||ea<0x80000000ll||ea>0x817ffffcll||(ea&3)||c.gpr[rs]!=0u||stores_)return fail(3);
            addr_=uint32_t(ea);if(!mapped(c,addr_,4u))return fail(3);
            ++stores_;
        }else if((op>=37u&&op<=39u)||(op>=44u&&op<=45u)||op==47u||
                 (op>=52u&&op<=55u)||op==60u||op==61u||
                 (op==31u&&(xo==150u||xo==151u||xo==183u||xo==215u||xo==247u||xo==407u||xo==439u||
                   xo==661u||xo==725u||xo==662u||xo==918u||xo==663u||xo==695u||xo==727u||xo==759u||xo==983u||xo==1014u)))return fail(3);
        if(pc==e_.call){
            if(w!=branch(pc,e_.open)||!stores_||!path(c)||c.gpr[4]||!settled(c))return fail(4);
            pending_call_=true;next_=e_.open;return true;
        }
        if(op==17u||(op==19u&&(xo==16u||xo==50u||xo==528u))||(op==31u&&xo==146u))return fail(4);
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            const auto dst=target(pc,w);
            const bool take=op==18u||taken(c,w);
            if(!known(c,dst)&&(take||std::count(e_.exits.begin(),e_.exits.end(),dst)!=1))return fail(4);
            if(dst<=pc){poll_due_=true;poll_pc_=pc;}
            if(take)next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held,bool descriptor){
        if(!live(c,held,descriptor)||!poll_due_||c.pc!=poll_pc_||c.inst_count!=last_||!settled(c))return fail(5);
        poll_due_=false;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held,bool descriptor){
        if(!live(c,held,descriptor)||!pending_call_||poll_due_||pc!=e_.open||c.pc!=pc||
           c.lr!=e_.call+4u||c.inst_count!=last_||!word(c,pc,e_.entry_word)||
           !path(c)||c.gpr[4]||!settled(c)||!stores_)return fail(6);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held,bool descriptor)const{
        return stage_==2u&&base(c,held,descriptor)&&c.pc==e_.open&&c.lr==e_.call+4u&&
            c.inst_count==last_&&path(c)&&!c.gpr[4]&&stores_==1u&&word(c,addr_,0u);
    }
private:
    StmSecondExpectation e_;const void* cpu_=nullptr;uint32_t msr_=0,sp_=0,r2_=0,r13_=0,next_=0,poll_pc_=0,addr_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0,first_kind_=0;
    bool resume_=true,pending_call_=false,poll_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>bool base(C& c,bool held,bool descriptor)const{
        return !error_&&cpu_==&c&&held&&descriptor&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            c.msr==msr_&&c.gpr[1]==sp_&&c.gpr[2]==r2_&&c.gpr[13]==r13_;
    }
    template<class C>bool live(C& c,bool held,bool descriptor)const{return stage_==1u&&base(c,held,descriptor);}
    template<class C>bool settled(C& c)const{return !stores_||word(c,addr_,0u);}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||a<0x80000000u||uint64_t(a)+n>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t pc,uint32_t w)const{return known(c,pc)&&word(c,pc,w);}
    template<class C>bool path(C& c)const{
        const std::string_view name=path_kind()==1u?"/dev/stm/immediate":"/dev/stm/eventhook";
        const uint32_t a=c.gpr[3];
        if(std::count_if(e_.paths.begin(),e_.paths.end(),[&](auto p){return p.addr==a&&p.kind==path_kind();})!=1||
           !mapped(c,a,unsigned(name.size()+1)))return false;
        for(unsigned i=0;i<name.size();++i)if(c.mmu.read8(a+i)!=uint8_t(name[i]))return false;
        return c.mmu.read8(a+uint32_t(name.size()))==0;
    }
    static uint32_t branch(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
