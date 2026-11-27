#include "wii_formatter_report_sixth_immediate.h"
#include "wii_formatter_report_fifth_immediate.h"

#include <array>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <cstdint>
#include <iostream>

using namespace undercover::wii;

namespace {
constexpr uint32_t Root=0x80010000u,PC=Root+36u;
constexpr uint32_t Next=0x60000000u,Guard=0x44000002u;
constexpr uint32_t Return=Root+0x100u;
constexpr uint32_t addi(unsigned dst,unsigned base,uint16_t imm,unsigned op=14u) {
    return (op<<26u)|(dst<<21u)|(base<<16u)|uint32_t(imm);
}
constexpr uint32_t signextend(uint16_t imm) {
    return (imm&0x8000u)?(uint32_t(imm)|0xffff0000u):uint32_t(imm);
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
        for(unsigned i=0;i<4u;++i)
            out=(out<<8u)|*get_ptr(address+i);
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
Cpu seed(unsigned dst,uint16_t imm,uint32_t initial=0xdeadbeefu) {
    Cpu c;
    for(unsigned i=0;i<32u;++i)c.gpr[i]=0x10000000u+i*0x01010101u;
    for(unsigned i=0;i<8u;++i) {
        c.cr[i]={bool(i&1u),bool(i&2u),bool(i&4u),bool(i&1u)};
        c.gqr[i]=i*23u;
    }
    c.gpr[dst]=initial;
    c.mmu.write32(PC,addi(dst,0u,imm));
    c.mmu.write32(PC+4u,Next);
    c.mmu.write32(PC+8u,Guard);
    c.mmu.write32(Return,Guard);
    return c;
}
bool arm(FormatterSixthImmediateWitness& w,Cpu& c,unsigned dst,
         uint16_t imm) {
    return w.arm(c,Root,PC,addi(dst,0u,imm),Next,Return,
                 dst,signextend(imm));
}
unsigned positives() {
    unsigned cases=0;
    for(unsigned dst:{0u,3u,7u,9u,12u})
    for(unsigned imm=0;imm<65536u;++imm) {
        Cpu c=seed(dst,uint16_t(imm));
        const auto old=c.gpr;
        FormatterSixthImmediateWitness w;
        assert(arm(w,c,dst,uint16_t(imm)));
        assert(w.stage()==1u&&!w.failed());
        c.gpr[dst]=signextend(uint16_t(imm));
        ++c.inst_count;  // original translated addi would increment this
        assert(w.observe(c,PC+4u,Next));
        assert(w.stage()==2u&&!w.failed());
        for(unsigned r=0;r<32u;++r)
            assert(c.gpr[r]==(r==dst?signextend(uint16_t(imm)):old[r]));
        ++cases;
    }
    return cases;
}
unsigned arm_refusals() {
    unsigned count=0;
    constexpr unsigned D=9u;
    constexpr uint16_t IMM=0xff80u;
    for(unsigned fault=0;fault<29u;++fault) {
        Cpu c=seed(D,IMM);
        uint32_t root=Root,pc=PC,word=addi(D,0u,IMM);
        uint32_t next=Next,ret=Return,value=signextend(IMM);
        unsigned dst=D;
        switch(fault) {
        case 0:word=addi(D,1u,IMM);break;
        case 1:word=addi(D,0u,IMM,15u);break;
        case 2:word=addi(13u,0u,IMM);dst=13u;c.mmu.write32(PC,word);break;
        case 3:word=addi(D,0u,IMM^1u);break;
        case 4:dst=3u;break;
        case 5:value^=1u;break;
        case 6:pc+=4u;break;
        case 7:root+=4u;break;
        case 8:ret=Root+0x200u;break;
        case 9:next=Guard;break;
        case 10:c.mmu.write32(PC,0u);break;
        case 11:c.mmu.write32(PC+4u,0u);break;
        case 12:c.mmu.write32(PC+8u,0u);break;
        case 13:c.mmu.write32(Return,0u);break;
        case 14:c.inst_count=UINT64_MAX;break;
        case 15:c.in_callback=true;break;
        case 16:c.is_running=false;break;
        case 17:c.dispatch_saved_ctx=1;break;
        case 18:c.pc+=4u;break;
        case 19:c.lr=PC+4u;ret=c.lr;break;
        case 20:root=0x81800000u;break;
        case 21:ret=Root;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 22:ret=Root+4u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 23:ret=Root+8u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 24:ret=Root+12u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 25:ret=Root+16u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 26:ret=PC;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 27:ret=PC+8u;c.lr=ret;c.mmu.write32(ret,Guard);break;
        case 28:word=addi(D,0u,IMM);c.gpr[3u]^=1u;value^=1u;break;
        default:assert(false);
        }
        FormatterSixthImmediateWitness w;
        assert(!w.arm(c,root,pc,word,next,ret,dst,value));
        assert(w.failed()&&w.stage()==0u);
        ++count;
    }
    return count;
}
unsigned observation_refusals() {
    unsigned count=0;
    constexpr unsigned D=9u;
    constexpr uint16_t IMM=0xff80u;
    for(unsigned fault=0;fault<24u;++fault) {
        Cpu c=seed(D,IMM);
        FormatterSixthImmediateWitness w;
        assert(arm(w,c,D,IMM));
        c.gpr[D]=signextend(IMM);
        ++c.inst_count;
        uint32_t next_pc=PC+4u,next_word=Next;
        switch(fault) {
        case 0:c.gpr[D]^=1u;break;
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
void duplicate_and_cross_cpu_refused() {
    Cpu c=seed(9u,0xff80u),other=seed(9u,0xff80u);
    FormatterSixthImmediateWitness w;
    assert(arm(w,c,9u,0xff80u));
    assert(!arm(w,c,9u,0xff80u)&&w.failed());
    FormatterSixthImmediateWitness x;
    assert(arm(x,c,9u,0xff80u));
    other.gpr[9]=signextend(0xff80u);++other.inst_count;
    assert(!x.observe(other,PC+4u,Next)&&x.failed());
    FormatterSixthImmediateWitness y;
    assert(arm(y,c,9u,0xff80u));
    c.gpr[9]=signextend(0xff80u);++c.inst_count;
    assert(y.observe(c,PC+4u,Next));
    assert(!y.observe(c,PC+4u,Next)&&y.failed());
}
}


void paired_126_127_regression() {
    // All words and register changes here are synthetic. Only original
    // NWiiRecomp-generated execution can satisfy the private native gate.
    constexpr unsigned previous_dst=5u,current_dst=9u;
    constexpr uint16_t previous_imm=0x8001u,current_imm=0xff80u;
    constexpr uint32_t previous_pc=PC-4u;
    constexpr uint32_t previous_word=addi(previous_dst,0u,previous_imm);
    constexpr uint32_t current_word=addi(current_dst,0u,current_imm);
    const auto run=[](int phase,uint32_t fault_address)->unsigned {
        Cpu c=seed(current_dst,current_imm);
        c.mmu.write32(previous_pc,previous_word);
        const auto mutate=[&](int at) {
            if(phase==at)
                c.mmu.write32(fault_address,c.mmu.read32(fault_address)^1u);
        };
        FormatterFifthImmediateWitness previous;
        mutate(0);
        if(!previous.arm(c,Root,previous_pc,previous_word,current_word,
                         Return,previous_dst,signextend(previous_imm),Next))
            return 0u;
        c.gpr[previous_dst]=signextend(previous_imm);
        ++c.inst_count;
        mutate(1);
        if(!previous.observe(c,PC,current_word))return 1u;
        FormatterSixthImmediateWitness current;
        mutate(2);
        if(!arm(current,c,current_dst,current_imm))return 2u;
        c.gpr[current_dst]=signextend(current_imm);
        ++c.inst_count;
        mutate(3);
        if(!current.observe(c,PC+4u,Next))return 3u;
        assert(previous.stage()==2u&&!previous.failed());
        assert(current.stage()==2u&&!current.failed());
        assert(c.inst_count==102u);
        return 4u;
    };
    assert(run(-1,0u)==4u);
    for(int phase=0;phase<=3;++phase) {
        const std::array<uint32_t,5> targets{
            previous_pc,PC,PC+4u,PC+8u,Return
        };
        for(unsigned i=(phase>=2?1u:0u);i<targets.size();++i)
            assert(run(phase,targets[i])==unsigned(phase));
    }
}

int main() {
    const unsigned good=positives();
    const unsigned reject_arm=arm_refusals();
    const unsigned reject_observe=observation_refusals();
    duplicate_and_cross_cpu_refused();
    paired_126_127_regression();
    assert(good==5u*65536u&&reject_arm==29u&&reject_observe==24u);
    std::cout<<"FORMATTER_SIXTH_IMMEDIATE_SOURCE_ONLY cases="<<good
             <<" arm_refusals="<<reject_arm
             <<" observation_refusals="<<reject_observe
             <<" original_execution=0\n";
}
