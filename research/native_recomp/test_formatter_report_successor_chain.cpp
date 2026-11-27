// Synthetic predecessor-chain integration; no original game code or bytes.
#include "wii_formatter_report_signext.h"
#include "wii_formatter_report_second_immediate.h"
#include "wii_formatter_report_third_immediate.h"
#include "wii_formatter_report_fourth_immediate.h"
#include "wii_formatter_report_fifth_immediate.h"
#include "wii_formatter_report_sixth_immediate.h"
#include <array>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstdint>
#include <iostream>
#include <optional>

using namespace undercover::wii;
namespace {
constexpr uint32_t Root=0x80010000u,Start=Root+16u,Ret=Root+0x100u;
constexpr uint32_t Guard=0x44000002u;
constexpr unsigned R=9u;
constexpr uint32_t Extsb=(31u<<26u)|(R<<21u)|(R<<16u)|(954u<<1u);
constexpr uint32_t Li0=(14u<<26u)|0xfffeu;
constexpr uint32_t Li9=(14u<<26u)|(R<<21u)|0x1234u;
constexpr uint32_t Lookahead=(14u<<26u)|(4u<<21u)|0x4567u;
constexpr uint32_t Next126=(14u<<26u)|(5u<<21u)|0x7fffu;
constexpr uint32_t Next127=(14u<<26u)|(6u<<21u)|0x8000u;
constexpr uint32_t Next128=(14u<<26u)|(7u<<21u)|0x1234u;
constexpr std::array<uint32_t,7> Code{
    Extsb,Li0,Li9,Lookahead,Next126,Next127,Next128};

struct Memory {
    std::array<uint8_t,512> bytes{};
    uint8_t* get_ptr(uint32_t a){
        return a>=Root&&a-Root<bytes.size()?bytes.data()+(a-Root):nullptr;
    }
    void write32(uint32_t a,uint32_t w){
        for(unsigned i=0;i<4u;++i)*get_ptr(a+i)=uint8_t(w>>(24u-i*8u));
    }
    uint32_t read32(uint32_t a){
        uint32_t w=0;
        for(unsigned i=0;i<4u;++i)w=(w<<8u)|*get_ptr(a+i);
        return w;
    }
};
struct Cpu {
    struct Field{bool lt=false,gt=false,eq=false,so=false;};
    Memory mmu;
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Field,8> cr{};
    uint32_t pc=Root,lr=Ret,ctr=0x81123456u,xer=0x80000000u;
    uint32_t msr=0x8032u,srr0=Root,srr1=0x8032u,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};

// steps=1..6 cover original instructions 122..127 in strictly guarded
// synthetic succession. Every witness sees the exact authenticated tail.
// Hand-applied register updates are NOT native/original game execution.
unsigned run(unsigned steps,int fault_phase=-1,uint32_t fault_address=0){
    assert(steps>=1u&&steps<=6u);
    Cpu c;
    for(unsigned i=0;i<32u;++i)c.gpr[i]=0x12345600u+i;
    c.gpr[R]=0x12345680u;
    c.gpr[0]=0xdeadbeefu;
    c.cr[3].eq=true;c.gqr[4]=0x3f800000u;
    for(unsigned i=0;i<=steps;++i)c.mmu.write32(Start+i*4u,Code[i]);
    c.mmu.write32(Start+(steps+1u)*4u,Guard);
    c.mmu.write32(Ret,Guard);
    auto mutate=[&](int phase){
        if(fault_phase==phase)
            c.mmu.write32(fault_address,c.mmu.read32(fault_address)^1u);
    };
    auto expected=c.gpr;
    FormatterSignextWitness sign;
    FormatterSecondImmediateWitness second;
    FormatterThirdImmediateWitness third;
    FormatterFourthImmediateWitness fourth;
    FormatterFifthImmediateWitness fifth;
    FormatterSixthImmediateWitness sixth;
    const auto following=steps>=2u?std::optional<uint32_t>{Li9}:std::nullopt;
    const auto trailing=steps>=3u?std::optional<uint32_t>{Lookahead}:std::nullopt;
    const auto fourth_following=steps>=4u?
        std::optional<uint32_t>{Next126}:std::nullopt;
    const auto fifth_following=steps>=5u?
        std::optional<uint32_t>{Next127}:std::nullopt;
    const auto sixth_following=steps>=6u?
        std::optional<uint32_t>{Next128}:std::nullopt;
    mutate(0);
    if(!sign.arm(c,Root,Start,Extsb,Li0,Ret,R,0x12345680u,0xffffff80u,
                 following,trailing,fourth_following,fifth_following,sixth_following))return 0;
    c.gpr[R]=expected[R]=0xffffff80u;++c.inst_count;
    mutate(1);
    if(!sign.observe(c,Start+4u,Li0))return 0;
    assert(c.gpr==expected&&sign.stage()==2u);
    if(steps==1u)return 1;
    mutate(2);
    if(!second.arm(c,Root,Start+4u,Li0,Li9,Ret,0u,0xfffffffeu,
                   trailing,fourth_following,fifth_following,sixth_following))
        return 1;
    c.gpr[0]=expected[0]=0xfffffffeu;++c.inst_count;
    mutate(3);
    if(!second.observe(c,Start+8u,Li9))return 1;
    assert(c.gpr==expected&&second.stage()==2u);
    if(steps==2u)return 2;
    mutate(4);
    if(!third.arm(c,Root,Start+8u,Li9,Lookahead,Ret,R,0x1234u,
                  fourth_following,fifth_following,sixth_following))return 2;
    c.gpr[R]=expected[R]=0x1234u;++c.inst_count;
    mutate(5);
    if(!third.observe(c,Start+12u,Lookahead))return 2;
    assert(c.gpr==expected&&third.stage()==2u);
    assert(c.inst_count==103u);
    if(steps==3u)return 3;
    mutate(6);
    if(!fourth.arm(c,Root,Start+12u,Lookahead,Next126,Ret,4u,0x4567u,
                   fifth_following,sixth_following))
        return 3;
    c.gpr[4u]=expected[4u]=0x4567u;++c.inst_count;
    mutate(7);
    if(!fourth.observe(c,Start+16u,Next126))return 3;
    assert(c.gpr==expected&&fourth.stage()==2u);
    assert(c.inst_count==104u);
    if(steps==4u)return 4;
    mutate(8);
    if(!fifth.arm(c,Root,Start+16u,Next126,Next127,Ret,5u,0x7fffu,
                  sixth_following))return 4;
    c.gpr[5u]=expected[5u]=0x7fffu;++c.inst_count;
    mutate(9);
    if(!fifth.observe(c,Start+20u,Next127))return 4;
    assert(c.gpr==expected&&fifth.stage()==2u);
    assert(c.inst_count==105u);
    if(steps==5u)return 5;
    mutate(10);
    if(!sixth.arm(c,Root,Start+20u,Next127,Next128,Ret,6u,0xffff8000u))
        return 5;
    c.gpr[6u]=expected[6u]=0xffff8000u;++c.inst_count;
    mutate(11);
    if(!sixth.observe(c,Start+24u,Next128))return 5;
    assert(c.gpr==expected&&sixth.stage()==2u);
    assert(c.inst_count==106u);
    return 6;
}
// Refuse gaps in authenticated successors and reject return aliases to
// either the fourth successor or the relocated synthetic stop guard.
void reject_unproven_fourth_tail(){
    Cpu c;
    c.gpr[R]=0x12345680u;
    c.gpr[0]=0xdeadbeefu;
    c.mmu.write32(Start,Extsb);
    c.mmu.write32(Start+4u,Li0);
    c.mmu.write32(Start+8u,Li9);
    c.mmu.write32(Start+12u,Lookahead);
    c.mmu.write32(Start+16u,Next126);
    c.mmu.write32(Start+20u,Guard);
    c.mmu.write32(Ret,Guard);
    auto attempt=[&](std::optional<uint32_t> f,
                     std::optional<uint32_t> t,
                     std::optional<uint32_t> q,uint32_t ret=Ret){
        Cpu probe=c;
        probe.lr=ret;
        FormatterSignextWitness witness;
        return witness.arm(probe,Root,Start,Extsb,Li0,ret,R,
                           0x12345680u,0xffffff80u,f,t,q);
    };
    assert(attempt(Li9,Lookahead,Next126));
    assert(!attempt({},Lookahead,Next126));
    assert(!attempt(Li9,{},Next126));
    assert(!attempt(Li9,Lookahead,{}));
    assert(!attempt(Li9,Lookahead,Guard));
    assert(!attempt(Li9,Guard,Next126));
    assert(!attempt(Guard,Lookahead,Next126));
    assert(!attempt(Li9,Lookahead,Next126,Start+16u));
    assert(!attempt(Li9,Lookahead,Next126,Start+20u));
}
void reject_unproven_sixth_tail(){
    Cpu c;
    c.gpr[R]=0x12345680u;
    c.gpr[0]=0xdeadbeefu;
    for(unsigned i=0u;i<Code.size();++i)
        c.mmu.write32(Start+i*4u,Code[i]);
    c.mmu.write32(Start+28u,Guard);
    c.mmu.write32(Ret,Guard);
    const auto attempt=[&](std::optional<uint32_t> fifth_word,
                            std::optional<uint32_t> sixth_word,
                            uint32_t ret=Ret){
        Cpu probe=c;
        probe.lr=ret;
        FormatterSignextWitness observer;
        return observer.arm(probe,Root,Start,Extsb,Li0,ret,R,
                            0x12345680u,0xffffff80u,
                            Li9,Lookahead,Next126,fifth_word,sixth_word);
    };
    assert(attempt(Next127,Next128));
    assert(!attempt({},Next128));
    assert(!attempt(Next127,{}));
    assert(!attempt(Guard,Next128));
    assert(!attempt(Next127,Guard));
    assert(!attempt(Next127,Next128,Start+24u));
    assert(!attempt(Next127,Next128,Start+28u));
    Cpu changed=c;
    changed.mmu.write32(Start+24u,Next128^1u);
    FormatterSignextWitness witness;
    assert(!witness.arm(changed,Root,Start,Extsb,Li0,Ret,R,
                        0x12345680u,0xffffff80u,
                        Li9,Lookahead,Next126,Next127,Next128));
}
}
int main(){
    reject_unproven_fourth_tail();
    reject_unproven_sixth_tail();
    unsigned positive=0,negative=0;
    for(unsigned steps=1;steps<=6;++steps){
        assert(run(steps)==steps);++positive;
        for(unsigned step=0;step<steps;++step)
        for(unsigned phase=0;phase<2;++phase){
            // Every current or later word and the terminal guard must
            // remain correct at arm and observation. No original data.
            for(unsigned slot=step;slot<=steps+1u;++slot){
                assert(run(steps,int(step*2u+phase),Start+slot*4u)==step);
                ++negative;
            }
            assert(run(steps,int(step*2u+phase),Ret)==step);
            ++negative;
        }
    }
    // 1..6 lanes produce Σ n(n+7)=238 independent corruption checks.
    assert(positive==6u&&negative==238u);
    std::cout<<"FORMATTER_SUCCESSOR_CHAIN_SOURCE_ONLY lanes="<<positive
             <<" negative_mutations="<<negative<<" original_execution=0\n";
}
