#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only witness for the authenticated indexed channel lookup and its
// original conditional. All code/data locations are owner-local metadata.
struct HandlerIndexBranchExpectation{
    uint32_t resume,load,compare,branch,destination;
    std::array<uint32_t,4> table;
    unsigned selector;
};
class HandlerIndexBranchWitness{
public:
    explicit HandlerIndexBranchWitness(HandlerIndexBranchExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    bool taken()const{return taken_;}
    template<class C>bool start(C& c,uint32_t pc){
        const auto bo=(e_.branch>>21)&31u,bi=(e_.branch>>16)&31u;
        if(stage_||error_||pc!=e_.resume||c.pc!=pc||e_.resume<0x80000000u||e_.resume>0x817fff80u||
           e_.selector>=32u||e_.selector<14u||c.gpr[e_.selector]>3u||
           e_.load>>26!=31u||((e_.load>>1)&1023u)!=23u||e_.compare>>26!=10u||(e_.compare&(1u<<21))||
           ((e_.compare>>16)&31u)!=((e_.load>>21)&31u)||e_.branch>>26!=16u||(e_.branch&3u)||
           !(bo&4u)||(bo&16u)||bi/4u!=((e_.compare>>23)&7u)||bi%4u==3u||
           e_.destination!=e_.resume+52u+(((e_.branch&0xfffcu)^0x8000u)-0x8000u)||
           e_.destination<=e_.resume+56u||!mapped(c,e_.destination)||
           !word(c,e_.resume+44u,e_.load)||!word(c,e_.resume+48u,e_.compare)||!word(c,e_.resume+52u,e_.branch))return fail(1);
        for(unsigned i=0;i<4;++i)
            if(!mapped(c,e_.table[i])||e_.table[i]!=e_.table[0]+4u*i)return fail(1);
        cpu_=&c;channel_=c.gpr[e_.selector];next_=pc;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w){
        if(error_||!stage_||cpu_!=&c)return fail(2);
        if(stage_==5u)return true;
        if(pc!=next_||c.inst_count-last_!=unsigned(visits_!=0)||!word(c,pc,w)||++visits_>15u)return fail(2);
        last_=c.inst_count;next_=pc+4u;
        if(stage_==1u){
            if(pc<e_.resume+44u)return true;
            if(w!=e_.load||pc!=e_.resume+44u)return fail(3);
            const unsigned ra=(w>>16)&31u,rb=(w>>11)&31u;
            const uint32_t a=(ra?c.gpr[ra]:0u)+c.gpr[rb];
            if(a!=e_.table[channel_]||!mapped(c,a))return fail(3);
            loaded_=c.mmu.read32(a);stage_=2u;return true;
        }
        if(stage_==2u){
            if(w!=e_.compare||pc!=e_.resume+48u||c.gpr[(w>>16)&31u]!=loaded_)return fail(4);
            stage_=3u;return true;
        }
        if(stage_==3u){
            if(w!=e_.branch||pc!=e_.resume+52u)return fail(4);
            const unsigned bi=(w>>16)&31u,bo=(w>>21)&31u;
            const uint32_t imm=e_.compare&0xffffu;
            const auto f=c.cr[bi/4u];
            const std::array<bool,3> flags{loaded_<imm,loaded_>imm,loaded_==imm};
            if(f.lt!=flags[0]||f.gt!=flags[1]||f.eq!=flags[2])return fail(4);
            taken_=flags[bi%4u]==bool(bo&8u);next_=taken_?e_.destination:pc+4u;
            ctr_=c.ctr;stage_=4u;return true;
        }
        if(stage_!=4u||c.ctr!=ctr_||visits_!=15u)return fail(5);
        stage_=5u;return true;
    }
private:
    HandlerIndexBranchExpectation e_;const void* cpu_=nullptr;
    unsigned stage_=0,error_=0,visits_=0,channel_=0;
    uint32_t next_=0,loaded_=0,ctr_=0;uint64_t last_=0;bool taken_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool mapped(C& c,uint32_t a){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        for(unsigned i=0;i<4;++i)if(!c.mmu.get_ptr(a+i))return false;
        return true;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return mapped(c,a)&&c.mmu.read32(a)==w;}
};
}
