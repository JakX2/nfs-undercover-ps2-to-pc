// Synthetic labels and state transitions only; no original game code.
#include "wii_formatter_compare_129.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <limits>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>

using namespace undercover::wii;
namespace {
constexpr uint32_t Root=0x80010000u, Ret=Root+0x100u;
constexpr uint32_t Next=0x60000000u, Guard=FormatterCompare129Witness::guard;
constexpr uint32_t cmpi(unsigned bf,unsigned ra,int imm){
    return (11u<<26u)|(bf<<23u)|(ra<<16u)|(uint32_t(imm)&0xffffu);
}
struct Mem {
    std::array<uint8_t,512> data{};
    uint8_t* get_ptr(uint32_t at){
        return at>=Root&&at-Root<data.size()?data.data()+(at-Root):nullptr;
    }
    void write32(uint32_t at,uint32_t value){
        for(unsigned i=0;i<4u;++i)*get_ptr(at+i)=uint8_t(value>>(24u-i*8u));
    }
    uint32_t read32(uint32_t at){
        uint32_t out=0;
        for(unsigned i=0;i<4u;++i)out=(out<<8u)|*get_ptr(at+i);
        return out;
    }
};
struct Cpu {
    struct Flag{
        bool lt=false,gt=false,eq=false,so=false;
        bool operator==(const Flag&)const=default;
    };
    Mem mmu;
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Flag,8> cr{};
    uint32_t pc=Root,lr=Ret,ctr=0x80010055u,xer=0;
    uint32_t msr=0x8032u,srr0=Root,srr1=0x8032u,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
Cpu seed(unsigned bf=3u,unsigned reg=5u,uint32_t value=7u,int imm=7,
         bool old_so=false,bool so=true){
    Cpu c;
    for(unsigned i=0;i<c.gpr.size();++i)c.gpr[i]=0x12340000u+i;
    c.gpr[reg]=value;c.gqr[4]=0x3f800000u;
    for(auto& f:c.cr)f={true,false,true,old_so};
    c.xer=(so?0x80000000u:0u)|0x20000000u;
    c.mmu.write32(Root,cmpi(bf,reg,imm));
    c.mmu.write32(Root+4u,Next);
    c.mmu.write32(Root+8u,Guard);
    c.mmu.write32(Ret,Guard);
    return c;
}
void apply_reference(Cpu& c,unsigned bf,unsigned reg,int imm){
    const auto value=c.gpr[reg];
    const int64_t v=value<0x80000000u?int64_t(value):
        int64_t(value)-0x100000000ll;
    c.cr[bf]={v<imm,v>imm,v==imm,bool(c.xer&0x80000000u)};
    ++c.inst_count;
}
bool arm(FormatterCompare129Witness& w,Cpu& c){
    return w.arm(c,Root,cmpi(3u,5u,7),Root+4u,Next,Ret,{5u,7u},true);
}
void matrix(){
    constexpr std::array<uint32_t,8> values{
        0u,1u,0x7fffu,0x8000u,0x7fffffffu,0x80000000u,
        0xffff8000u,0xffffffffu};
    constexpr std::array<int,5> immediates{-32768,-1,0,1,32767};
    unsigned cases=0;
    for(unsigned bf=0;bf<8;++bf)
    for(auto value:values)
    for(auto imm:immediates)
    for(bool old_so:{false,true})
    for(bool so:{false,true}){
        // Exercise both architectural GPR0 and a nonvolatile source.
        const unsigned reg=(bf&1u)?0u:31u;
        auto c=seed(bf,reg,value,imm,old_so,so);
        const auto before=c;
        FormatterCompare129Witness w;
        assert(w.arm(c,Root,cmpi(bf,reg,imm),Root+4u,Next,Ret,
                     {reg,value},true));
        assert(w.stage()==1u&&!w.failed());
        assert(c.gpr==before.gpr&&c.cr==before.cr&&
               c.inst_count==before.inst_count&&c.mmu.data==before.mmu.data);
        apply_reference(c,bf,reg,imm);
        assert(w.observe(c,Root+4u,Next)&&w.stage()==2u&&!w.failed());
        assert(!w.observe(c,Root+4u,Next)&&w.failed());
        ++cases;
    }
    assert(cases==1280u);
}
void arm_refusals(){
    for(unsigned fault=0;fault<17u;++fault){
        auto c=seed();
        uint32_t root=Root,w=cmpi(3u,5u,7),next=Root+4u,word=Next,ret=Ret;
        CallerIntegerInput input{5u,7u};bool previous=true;
        switch(fault){
        case 0:previous=false;break;
        case 1:c.pc+=4u;break;
        case 2:w^=1u<<26u;c.mmu.write32(Root,w);break; // unsigned compare
        case 3:w|=0x00200000u;c.mmu.write32(Root,w);break; // L=1
        case 4:w|=0x00400000u;c.mmu.write32(Root,w);break; // reserved bit
        case 5:input.reg=6u;break;
        case 6:input.reg=32u;break;
        case 7:input.value=8u;break;
        case 8:next+=4u;break;
        case 9:word=Guard;c.mmu.write32(next,Guard);break;
        case 10:c.mmu.write32(Root+8u,Next);break;
        case 11:c.mmu.write32(Ret,Next);break;
        case 12:c.lr=ret=Root+8u;break;
        case 13:c.in_callback=true;break;
        case 14:c.is_running=false;break;
        case 15:c.dispatch_saved_ctx=1u;break;
        case 16:c.inst_count=std::numeric_limits<uint64_t>::max();break;
        }
        FormatterCompare129Witness witness;
        assert(!witness.arm(c,root,w,next,word,ret,input,previous));
        assert(witness.failed()&&witness.stage()==0u);
    }
}
void observe_refusals(){
    for(unsigned fault=0;fault<20u;++fault){
        auto c=seed();
        FormatterCompare129Witness w;
        assert(arm(w,c));
        apply_reference(c,3u,5u,7);
        uint32_t label=Root+4u,word=Next;
        switch(fault){
        case 0:label+=4u;break;
        case 1:word^=1u;break;
        case 2:++c.inst_count;break;
        case 3:c.gpr[5]^=1u;break;
        case 4:c.gpr[9]^=1u;break;
        case 5:c.cr[3].eq=false;break;
        case 6:c.cr[3].so=false;break; // stale SO from before compare
        case 7:c.cr[2].lt=false;break; // wrong CR field
        case 8:c.xer^=0x20000000u;break;
        case 9:c.gqr[4]^=1u;break;
        case 10:c.lr+=4u;break;
        case 11:c.ctr^=4u;break;
        case 12:c.msr^=1u;break;
        case 13:c.srr0^=4u;break;
        case 14:c.srr1^=4u;break;
        case 15:c.pc=Root+4u;break; // wrong local-label dispatch PC
        case 16:c.mmu.write32(Root,cmpi(3u,5u,8));break;
        case 17:c.mmu.write32(Root+4u,Next^1u);break;
        case 18:c.mmu.write32(Root+8u,Next);break;
        case 19:c.mmu.write32(Ret,Next);break;
        }
        assert(!w.observe(c,label,word)&&w.failed()&&w.stage()==1u);
    }
    auto c=seed();FormatterCompare129Witness w;
    assert(arm(w,c));
    auto other=c;
    apply_reference(other,3u,5u,7);
    assert(!w.observe(other,Root+4u,Next));
}
}
int main(){
    matrix();arm_refusals();observe_refusals();
    std::cout<<"FORMATTER_COMPARE_129_SOURCE_ONLY cases=1280"
             <<" arm_refusals=17 observe_refusals=21"
             <<" selected_root=1 xer_so=1 original_execution=0\n";
}
