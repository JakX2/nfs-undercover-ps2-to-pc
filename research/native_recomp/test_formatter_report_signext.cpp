#include "wii_formatter_report_signext.h"

#include <array>
// This verification executable must not become vacuous when compiled with
// release flags. All positive and negative checks use assert().
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstdint>
#include <iostream>

using namespace undercover::wii;

namespace {
constexpr uint32_t Root=0x80010000u,PC=Root+16u;
constexpr uint32_t Next=0x60000000u,Guard=0x44000002u;
constexpr uint32_t Return=Root+0x100u;
constexpr uint32_t instruction(unsigned r,unsigned a,unsigned rc=0u,
                               unsigned rb=0u,unsigned xo=954u) {
    return (31u<<26u)|(r<<21u)|(a<<16u)|(rb<<11u)|(xo<<1u)|rc;
}
constexpr uint32_t reference(uint32_t value) {
    return (value&0x80u)?(value&0xffu)|0xffffff00u:value&0xffu;
}

struct Memory {
    std::array<uint8_t,512> bytes{};
    uint8_t* get_ptr(uint32_t address) {
        return address>=Root&&address-Root<bytes.size()
            ?bytes.data()+(address-Root):nullptr;
    }
    void write32(uint32_t address,uint32_t value) {
        for(unsigned i=0;i<4u;++i)*get_ptr(address+i)=
            uint8_t(value>>(24u-i*8u));
    }
    uint32_t read32(uint32_t address) {
        uint32_t out=0;
        for(unsigned i=0;i<4u;++i)out=(out<<8u)|*get_ptr(address+i);
        return out;
    }
};
struct Cpu {
    struct Field {bool lt=false,gt=false,eq=false,so=false;};
    Memory mmu;
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Field,8> cr{};
    uint32_t pc=Root,lr=Return,ctr=0x81123456u,xer=0x80000000u;
    uint32_t msr=0x8032u,srr0=Root,srr1=0x8032u,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
Cpu seed(unsigned reg,uint32_t value) {
    Cpu c;
    for(unsigned i=0;i<32u;++i)c.gpr[i]=0x10000000u+i*0x01010101u;
    for(unsigned i=0;i<8u;++i) {
        c.cr[i]={bool(i&1u),bool(i&2u),bool(i&4u),bool(i&1u)};
        c.gqr[i]=i*23u;
    }
    c.gpr[reg]=value;
    c.mmu.write32(PC,instruction(reg,reg));
    c.mmu.write32(PC+4u,Next);
    c.mmu.write32(PC+8u,Guard);
    c.mmu.write32(Return,Guard);
    return c;
}
bool arm(FormatterSignextWitness& w,Cpu& c,unsigned reg,uint32_t before,
         uint32_t after) {
    return w.arm(c,Root,PC,instruction(reg,reg),Next,Return,reg,before,after);
}

unsigned positive_cases(){
    unsigned count=0;
    for(unsigned reg:{0u,3u,7u,9u,12u})
    for(unsigned low=0;low<256u;++low) {
        const uint32_t before=0x12345600u|low;
        Cpu c=seed(reg,before);
        const auto old=c.gpr;
        FormatterSignextWitness w;
        const uint32_t expected=reference(before);
        assert(arm(w,c,reg,before,expected));
        assert(w.stage()==1u&&!w.failed());
        c.gpr[reg]=expected;
        ++c.inst_count; // actual translated extsb would increment this
        assert(w.observe(c,PC+4u,Next));
        assert(w.stage()==2u&&!w.failed());
        for(unsigned r=0;r<32u;++r)
            assert(c.gpr[r]==(r==reg?expected:old[r]));
        ++count;
    }
    return count;
}
unsigned arm_refusals() {
    unsigned count=0;
    constexpr unsigned R=9u;
    for(unsigned fault=0;fault<26u;++fault) {
        Cpu c=seed(R,0x12340080u);
        uint32_t before=0x12340080u,after=0xffffff80u;
        uint32_t root=Root,pc=PC,word=instruction(R,R);
        uint32_t next=Next,ret=Return,reg=R;
        switch(fault) {
        case 0:word=instruction(R,3u);break;
        case 1:word=instruction(R,R,1u);break;
        case 2:word=instruction(R,R,0u,1u);break;
        case 3:word=instruction(R,R,0u,0u,922u);break;
        case 4:before^=1u;break;
        case 5:after^=1u;break;
        case 6:reg=3u;break;
        case 7:pc+=4u;break;
        case 8:root+=4u;break;
        case 9:ret=Root+0x200u;break;
        case 10:next=Guard;break;
        case 11:c.mmu.write32(PC,0u);break;
        case 12:c.mmu.write32(PC+4u,0u);break;
        case 13:c.mmu.write32(PC+8u,0u);break;
        case 14:c.mmu.write32(Return,0u);break;
        case 15:c.inst_count=UINT64_MAX;break;
        case 16:c.in_callback=true;break;
        case 17:c.is_running=false;break;
        case 18:c.dispatch_saved_ctx=1;break;
        case 19:c.pc+=4u;break;
        case 20:c.lr=PC+4u;ret=c.lr;break;
        case 21:root=0x81800000u;break;
        case 22:pc=Root+20u;break;
        // Earlier original words are not valid synthetic return sites,
        // even if a corrupted fixture replaces one with a syscall guard.
        case 23:ret=Root+4u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 24:ret=Root+8u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 25:ret=Root+12u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        default:assert(false);
        }
        FormatterSignextWitness w;
        assert(!w.arm(c,root,pc,word,next,ret,reg,before,after));
        assert(w.failed()&&w.stage()==0u);
        ++count;
    }
    return count;
}
unsigned observe_refusals(){
    unsigned count=0;
    constexpr unsigned R=9u;
    for(unsigned fault=0;fault<24u;++fault) {
        Cpu c=seed(R,0x81234580u);
        FormatterSignextWitness w;
        assert(arm(w,c,R,0x81234580u,0xffffff80u));
        c.gpr[R]=0xffffff80u;
        ++c.inst_count;
        uint32_t next_pc=PC+4u,next_word=Next;
        switch(fault) {
        case 0:c.gpr[R]^=1u;break;
        case 1:c.gpr[3u]^=1u;break;
        case 2:c.gpr[0u]^=1u;break;
        case 3:c.gqr[4u]^=1u;break;
        case 4:c.cr[0].lt=!c.cr[0].lt;break;
        case 5:c.cr[7].so=!c.cr[7].so;break;
        case 6:c.xer^=1u;break;
        case 7:c.lr^=4u;break;
        case 8:c.ctr^=4u;break;
        case 9:c.msr^=1u;break;
        case 10:c.srr0^=4u;break;
        case 11:c.srr1^=1u;break;
        case 12:++c.inst_count;break;
        case 13:--c.inst_count;break;
        case 14:c.pc+=4u;break;
        case 15:c.mmu.write32(PC,0u);break;
        case 16:c.mmu.write32(PC+4u,0u);break;
        case 17:c.mmu.write32(PC+8u,0u);break;
        case 18:c.mmu.write32(Return,0u);break;
        case 19:next_pc=PC;break;
        case 20:next_word=0u;break;
        case 21:c.in_callback=true;break;
        case 22:c.dispatch_saved_ctx=1;break;
        case 23:c.is_running=false;break;
        default:assert(false);
        }
        assert(!w.observe(c,next_pc,next_word));
        assert(w.failed()&&w.stage()==1u);
        ++count;
    }
    return count;
}
void duplicate_and_cross_cpu_refused(){
    Cpu c=seed(9u,0x80u),other=seed(9u,0x80u);
    FormatterSignextWitness w;
    assert(arm(w,c,9u,0x80u,0xffffff80u));
    assert(!arm(w,c,9u,0x80u,0xffffff80u)&&w.failed());
    FormatterSignextWitness x;
    assert(arm(x,c,9u,0x80u,0xffffff80u));
    other.gpr[9]=0xffffff80u;++other.inst_count;
    assert(!x.observe(other,PC+4u,Next)&&x.failed());
    FormatterSignextWitness y;
    assert(arm(y,c,9u,0x80u,0xffffff80u));
    c.gpr[9]=0xffffff80u;++c.inst_count;
    assert(y.observe(c,PC+4u,Next));
    assert(!y.observe(c,PC+4u,Next)&&y.failed());
}
}

int main() {
    const auto positives=positive_cases();
    const auto wrong_arm=arm_refusals();
    const auto wrong_observation=observe_refusals();
    duplicate_and_cross_cpu_refused();
    assert(positives==1280u&&wrong_arm==26u&&wrong_observation==24u);
    std::cout<<"FORMATTER_SIGNEXT_WITNESS_SOURCE_ONLY cases="<<positives
             <<" arm_refusals="<<wrong_arm
             <<" observation_refusals="<<wrong_observation
             <<" original_execution=0\n";
}
