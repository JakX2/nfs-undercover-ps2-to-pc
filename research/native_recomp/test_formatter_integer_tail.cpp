// Synthetic checks only: manually applied CPU effects are never native proof.
#include "wii_formatter_integer_tail.h"
#include <array>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <iostream>

using namespace undercover::wii;
namespace {
constexpr uint32_t Root=0x80010000u,Start=Root+40u,Ret=Root+0x100u;
constexpr uint32_t Next=0x60000000u,Guard=FormatterIntegerTailWitness::guard;
constexpr uint32_t addi(unsigned dst,unsigned src,uint16_t imm){
    return (14u<<26u)|(dst<<21u)|(src<<16u)|uint32_t(imm);
}
constexpr uint32_t cmpwi(unsigned field,unsigned src,uint16_t imm){
    return (11u<<26u)|(field<<23u)|(src<<16u)|uint32_t(imm);
}
constexpr uint32_t extsb(unsigned dst,unsigned src){
    return (31u<<26u)|(src<<21u)|(dst<<16u)|(954u<<1u);
}
struct Memory{
    std::array<uint8_t,512> bytes{};
    uint8_t* get_ptr(uint32_t a){
        return a>=Root&&a-Root<bytes.size()?bytes.data()+(a-Root):nullptr;
    }
    void write32(uint32_t a,uint32_t w){
        for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(w>>(24u-i*8u));
    }
    uint32_t read32(uint32_t a){
        uint32_t w=0;
        for(unsigned i=0;i<4;++i)w=(w<<8u)|*get_ptr(a+i);
        return w;
    }
};
struct Cpu{
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
using Step=FormatterIntegerTailStep;
std::array<Step,4> contract(){
    return {{{addi(5,0,0xff80),{},0,5u,0xffffff80u},
             {addi(6,5,0x81),{{{5,0xffffff80u}}},1,6u,1u},
             {cmpwi(1,6,2),{{{6,1u}}},1,{},0u},
             {extsb(7,5),{{{5,0xffffff80u}}},1,7u,0xffffff80u}}};
}
Cpu seed(std::span<const Step> steps){
    Cpu c;
    for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+i;
    c.gqr[4]=0x3f800000u;c.cr[2].eq=true;
    for(unsigned i=0;i<steps.size();++i)c.mmu.write32(Start+4u*i,steps[i].word);
    c.mmu.write32(Start+4u*unsigned(steps.size()),Next);
    c.mmu.write32(Start+4u*unsigned(steps.size())+4u,Guard);
    c.mmu.write32(Ret,Guard);
    return c;
}
void apply(Cpu& c,unsigned i){
    switch(i){
    case 0:c.gpr[5]=0xffffff80u;break;
    case 1:c.gpr[6]=1u;break;
    case 2:c.cr[1]={true,false,false,true};break;
    case 3:c.gpr[7]=0xffffff80u;break;
    default:assert(false);
    }
    ++c.inst_count;
}
unsigned run(unsigned n,int fault_step=-1,int fault=0){
    auto steps=contract();
    auto seq=std::span<const Step>(steps.data(),n);
    Cpu c=seed(seq);FormatterIntegerTailWitness witness;
    const auto initial=c.gpr;const auto initial_count=c.inst_count;
    assert(witness.arm(c,Root,Start,seq,Next,Ret));
    assert(c.gpr==initial&&c.inst_count==initial_count&&!witness.finished());
    for(unsigned i=0;i<n;++i){
        apply(c,i);
        uint32_t pc=Start+4u*(i+1u);
        uint32_t w=i+1u==n?Next:steps[i+1u].word;
        if(int(i)==fault_step){
            if(fault>=0&&fault<int(n+2u)){
                const auto at=Start+4u*unsigned(fault);
                c.mmu.write32(at,c.mmu.read32(at)^1u);
            }else switch(fault-int(n+2u)){
                case 0:c.mmu.write32(Ret,Next);break;
                case 1:c.gpr[9]^=1u;break;
                case 2:c.gpr[5]^=1u;break;
                case 3:c.cr[2].eq=false;break;
                case 4:c.xer^=1u;break;
                case 5:c.lr^=4u;break;
                case 6:c.ctr^=4u;break;
                case 7:c.msr^=1u;break;
                case 8:c.srr0^=4u;break;
                case 9:c.srr1^=1u;break;
                case 10:c.gqr[4]^=1u;break;
                case 11:++c.inst_count;break;
                case 12:pc+=4u;break;
                case 13:w^=1u;break;
                case 14:c.in_callback=true;break;
                case 15:c.dispatch_saved_ctx=1u;break;
                case 16:c.is_running=false;break;
                case 17:c.pc+=4u;break;
                default:assert(false);
            }
        }
        if(!witness.observe(c,pc,w)){
            assert(witness.failed()&&!witness.finished()&&witness.completed()==i);
            return i;
        }
    }
    assert(witness.finished()&&witness.completed()==n);
    assert(!witness.observe(c,Start+4u*n,Next)&&witness.failed());
    return n;
}
void reject_contracts(){
    auto original=contract();
    auto attempt=[&](auto steps,unsigned fault){
        Cpu c=seed(steps);
        FormatterIntegerTailWitness witness;
        uint32_t start=Start,root=Root,next=Next,ret=Ret;
        switch(fault){
        case 1:c.gpr[5]^=1u;break; // overwritten by first li, allowed
        case 2:c.inst_count=UINT64_MAX;break;
        case 3:c.lr=ret=Start;break;
        case 4:c.mmu.write32(Start+4u*unsigned(steps.size())+4u,Next);break;
        case 5:c.mmu.write32(Start+4u,0u);break;
        case 6:c.in_callback=true;break;
        case 7:start+=2u;break;
        case 8:root+=4u;break;
        case 9:next=Guard;break;
        default:break;
        }
        return witness.arm(c,root,start,steps,next,ret);
    };
    assert(attempt(original,0)&&attempt(original,1));
    for(unsigned i=2;i<=9;++i)assert(!attempt(original,i));
    auto bad=original;bad[1].inputs[0].value=0;
    assert(!attempt(bad,0));
    bad=original;bad[1].input_count=0;assert(!attempt(bad,0));
    bad=original;bad[1].input_count=4;assert(!attempt(bad,0));
    bad=original;bad[1].value=2;assert(!attempt(bad,0));
    bad=original;bad[1].destination=7;assert(!attempt(bad,0));
    bad=original;bad[2].value=1;assert(!attempt(bad,0));
    bad=original;bad[0].word=addi(1,0,1);bad[0].destination=1;
    bad[0].value=1;assert(!attempt(bad,0));
    bad=original;bad[0].word=0x48000004u;assert(!attempt(bad,0));
    assert(!attempt(std::span<const Step>{},0));
    std::array<Step,17> long_tail{};
    assert(!attempt(long_tail,0));
    Cpu c=seed(original),other=c;FormatterIntegerTailWitness w;
    assert(w.arm(c,Root,Start,original,Next,Ret));
    apply(other,0);
    assert(!w.observe(other,Start+4u,original[1].word)&&w.failed());
}
// The advertised 16-step bound must succeed at its actual limit, not
// merely refuse 17 instructions. Use an aliasing arithmetic chain whose
// numeric operands originate from earlier synthetic writes.
void maximum_tail(){
    std::array<Step,FormatterIntegerTailWitness::max_steps> steps{};
    uint32_t value=0xfffffff8u;
    steps[0]={addi(0,0,0xfff8),{},0,0u,value};
    // RA=0 is literal zero in addi, so use r3 for a genuinely dependent
    // wraparound chain after independently initializing it.
    steps[1]={addi(3,0,0xfff8),{},0,3u,value};
    for(unsigned i=2;i<steps.size();++i){
        steps[i]={addi(3,3,1),{{{3u,value}}},1,3u,value+1u};
        ++value;
    }
    Cpu c=seed(steps);
    c.inst_count=UINT64_MAX-steps.size();
    FormatterIntegerTailWitness witness;
    assert(witness.arm(c,Root,Start,steps,Next,Ret));
    value=0xfffffff8u;
    for(unsigned i=0;i<steps.size();++i){
        if(i==0)c.gpr[0]=value;
        else if(i==1)c.gpr[3]=value;
        else c.gpr[3]=++value;
        ++c.inst_count;
        assert(witness.observe(c,Start+4u*(i+1u),
            i+1u==steps.size()?Next:steps[i+1u].word));
        assert(witness.completed()==i+1u);
    }
    assert(witness.finished()&&c.inst_count==UINT64_MAX);
    c=seed(steps);c.inst_count=UINT64_MAX-steps.size()+1u;
    FormatterIntegerTailWitness overflow;
    assert(!overflow.arm(c,Root,Start,steps,Next,Ret));
    c=seed(steps);c.lr=Start+4u*unsigned(steps.size())+4u;
    FormatterIntegerTailWitness alias;
    assert(!alias.arm(c,Root,Start,steps,Next,c.lr));
}
}
int main(){
    reject_contracts();
    maximum_tail();
    unsigned failures=0;
    for(unsigned n=1;n<=4;++n){
        assert(run(n)==n);
        for(unsigned i=0;i<n;++i)
            for(unsigned f=0;f<n+20u;++f){
                assert(run(n,int(i),int(f))==i);++failures;
            }
    }
    assert(failures==230u);
    std::cout<<"FORMATTER_INTEGER_TAIL_SOURCE_ONLY lanes=4 mutation_refusals="
             <<failures<<" original_execution=0\n";
}
