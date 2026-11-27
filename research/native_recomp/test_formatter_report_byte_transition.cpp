#include "wii_formatter_report_byte_transition.h"
#include "wii_formatter_caller_integer.h"
#include <array>
#include <cassert>
#include <bit>
#include <cstdint>
#include <iostream>
#include <limits>
#include <optional>
using namespace undercover::wii;

constexpr uint32_t Base = 0x80000000u;
constexpr uint32_t Entry = Base + 0x400u;
constexpr uint32_t Address = Base + 0x20u;
constexpr uint32_t Sp = Base + 0x1f00u;
constexpr uint32_t Link = Base + 0x1000u;
constexpr uint32_t Nop = 0x60000000u;
constexpr uint32_t lbz(unsigned rt) {
    return (34u << 26) | (rt << 21) | (7u << 16) | 0x10u;
}
constexpr uint32_t lbzx(unsigned rt) {
    return (31u << 26) | (rt << 21) | (7u << 16) |
           (8u << 11) | (87u << 1);
}
struct Mem {
    std::array<uint8_t,8192> bytes{};
    uint8_t* get_ptr(uint32_t addr) {
        return addr >= Base && addr-Base < bytes.size()
            ? bytes.data() + (addr-Base) : nullptr;
    }
    uint8_t read8(uint32_t addr) {
        auto* p=get_ptr(addr);
        assert(p);
        return *p;
    }
    uint32_t read32(uint32_t addr) {
        uint32_t result=0;
        for(unsigned i=0;i<4;++i) result=(result<<8)|read8(addr+i);
        return result;
    }
    void write32(uint32_t addr,uint32_t value) {
        for(unsigned i=0;i<4;++i) {
            auto* p=get_ptr(addr+i);
            assert(p);
            *p=uint8_t(value>>(24u-i*8u));
        }
    }
};
struct Cr {bool lt=false,gt=false,eq=false,so=false;};
struct Cpu {
    Mem mmu;
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Cr,8> cr{};
    uint32_t pc=Entry,lr=Link,ctr=5,xer=3,msr=0x8032,
             srr0=Entry,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
struct Report {
    uint8_t byte=0;
    bool allow=true;
    unsigned reads=0;
    template<class C>
    std::optional<uint8_t> observed_child_byte(
        C& c,bool held,uint32_t sp,uint32_t link,uint32_t depth,
        uint32_t address,uint32_t extra) {
        ++reads;
        if(!allow||!held||sp!=Sp||c.gpr[1]!=Sp||
           link!=Link||depth!=736u||extra!=0u||address!=Address)
            return {};
        return byte;
    }
};
struct Harness {
    Cpu cpu;
    Report report;
    FormatterReportByteTransition witness;
    FormatterReportByteStep step{};
    Harness(unsigned rt,unsigned value,bool indexed) {
        cpu.gpr[1]=Sp;
        cpu.gpr[7]=Base+0x10u;
        cpu.gpr[8]=0x10u;
        report.byte=uint8_t(value);
        const uint32_t word=indexed?lbzx(rt):lbz(rt);
        cpu.mmu.write32(Entry,word);
        cpu.mmu.write32(Entry+4u,Nop);
        step={Entry,word,Entry+4u,Nop,Link,Address,Sp,Link,736u,0u,uint8_t(value)};
    }
    bool arm() {return witness.arm(cpu,report,step,true);}
    bool observe(bool held=true) {return witness.observe(cpu,report,held);}
    void execute(unsigned rt,unsigned value) {
        ++cpu.inst_count;
        cpu.pc=Entry+4u;
        cpu.gpr[rt]=value;
    }
};
static unsigned positives() {
    unsigned cases=0;
    constexpr std::array<unsigned,11> targets{0,3,4,5,6,7,8,9,10,11,12};
    for(bool indexed:{false,true})
        for(unsigned rt:targets)
            for(unsigned value=0;value<=255u;++value) {
                Harness h(rt,value,indexed);
                assert(h.arm());
                assert(h.report.reads==1u);
                assert(h.witness.stage()==1u&&!h.witness.failed());
                h.execute(rt,value);
                assert(h.observe());
                assert(h.report.reads==2u);
                assert(h.witness.stage()==2u&&!h.witness.failed());
                assert(!h.observe()&&h.witness.failed());
                ++cases;
            }
    return cases;
}
static void negative(unsigned fault) {
    Harness h(9u,0x5au,false);
    // Faults 0-13 corrupt the post-execution architectural state or code.
    if(fault>=20u) {
        switch(fault) {
        case 20:h.step.word=lbz(13);h.cpu.mmu.write32(Entry,h.step.word);break;
        case 21:h.step.word=lbz(1);h.cpu.mmu.write32(Entry,h.step.word);break;
        case 22:h.step.word=(35u<<26)|(9u<<21)|(7u<<16)|0x10u;h.cpu.mmu.write32(Entry,h.step.word);break;
        case 23:h.step.word=lbzx(9u)|1u;h.cpu.mmu.write32(Entry,h.step.word);break;
        case 24:h.step.next_pc=Entry+8u;break;
        case 25:h.step.expected_byte^=1u;break;
        case 26:h.step.guest_address+=1u;break;
        case 27:h.step.child_depth=735u;break;
        case 28:h.cpu.pc+=4u;break;
        case 29:h.cpu.lr+=4u;break;
        case 30:h.cpu.is_running=false;break;
        case 31:h.cpu.in_callback=true;break;
        case 32:h.cpu.dispatch_saved_ctx=1;break;
        default:assert(false);
        }
        assert(!h.arm()&&h.witness.failed()&&h.witness.stage()==0u);
        return;
    }
    assert(h.arm());
    if(fault==19) {
        h.cpu.inst_count=std::numeric_limits<uint64_t>::max();
        assert(!h.observe()&&h.witness.failed());
        return;
    }
    h.execute(9u,0x5au);
    switch(fault) {
    case 0:h.cpu.gpr[9]^=1u;break;
    case 1:h.cpu.gpr[7]^=1u;break;
    case 2:h.cpu.gpr[1]+=8u;break;
    case 3:h.cpu.pc+=4u;break;
    case 4:h.cpu.lr+=4u;break;
    case 5:h.cpu.ctr+=1u;break;
    case 6:h.cpu.xer+=1u;break;
    case 7:h.cpu.msr^=0x8000u;break;
    case 8:h.cpu.srr0+=4u;break;
    case 9:h.cpu.srr1+=1u;break;
    case 10:h.cpu.gqr[4]^=1u;break;
    case 11:h.cpu.cr[2].eq=true;break;
    case 12:h.cpu.inst_count+=1u;break;
    case 13:h.cpu.mmu.write32(Entry,Nop);break;
    case 14:h.cpu.mmu.write32(Entry+4u,Nop^1u);break;
    case 15:h.report.allow=false;break;
    case 16:h.report.byte^=1u;break;
    case 17:assert(!h.observe(false)&&h.witness.failed());return;
    case 18: {
        Cpu other=h.cpu;
        assert(!h.witness.observe(other,h.report,true)&&h.witness.failed());
        return;
    }
    default:assert(false);
    }
    assert(!h.observe()&&h.witness.failed());
}

static unsigned native_positives() {
    // The translated PPC callee reaches a local native label while the
    // dispatch PC remains at the function root. Both must be checked.
    unsigned cases=0;
    constexpr std::array<unsigned,11> targets{0,3,4,5,6,7,8,9,10,11,12};
    for(bool indexed:{false,true})
        for(unsigned rt:targets)
            for(unsigned value=0;value<=255u;++value) {
                Harness h(rt,value,indexed);
                h.cpu.mmu.write32(Entry+8u,0x44000002u);
                h.cpu.mmu.write32(Link,0x44000002u);
                assert(h.witness.arm_native(h.cpu,h.report,h.step,true));
                assert(h.report.reads==1u);
                ++h.cpu.inst_count;
                h.cpu.gpr[rt]=value;
                assert(h.cpu.pc==Entry);
                assert(h.witness.observe_native_label(h.cpu,h.report,
                    Entry+4u,Nop,true));
                assert(h.report.reads==2u);
                assert(h.witness.stage()==2u&&!h.witness.failed());
                assert(!h.witness.observe_native_label(h.cpu,h.report,
                    Entry+4u,Nop,true));
                ++cases;
            }
    return cases;
}
static void native_negative(unsigned fault) {
    Harness h(9u,0x5au,false);
    h.cpu.mmu.write32(Entry+8u,0x44000002u);
    h.cpu.mmu.write32(Link,0x44000002u);
    if(fault==0)h.cpu.mmu.write32(Entry+8u,Nop);
    if(fault==1)h.cpu.mmu.write32(Link,Nop);
    if(fault==2){h.cpu.lr=Entry;h.step.lr=Entry;}
    if(fault<=2) {
        assert(!h.witness.arm_native(h.cpu,h.report,h.step,true));
        assert(h.witness.failed());
        return;
    }
    assert(h.witness.arm_native(h.cpu,h.report,h.step,true));
    ++h.cpu.inst_count;
    h.cpu.gpr[9]=0x5au;
    if(fault==3)h.cpu.pc=Entry+4u;
    if(fault==6)h.cpu.mmu.write32(Entry+8u,Nop);
    if(fault==7)h.cpu.mmu.write32(Link,Nop);
    if(fault==8)h.report.byte^=1u;
    if(fault==10)h.cpu.cr[1].eq=true;
    if(fault==12) {
        assert(!h.witness.arm_native(h.cpu,h.report,h.step,true));
        assert(h.witness.failed());
        return;
    }
    if(fault==13)++h.cpu.inst_count;
    if(fault==9) {
        assert(!h.observe()&&h.witness.failed());
        return;
    }
    const bool ok=h.witness.observe_native_label(h.cpu,h.report,
        fault==4?Entry:Entry+4u,fault==5?Nop^1u:Nop,true);
    if(fault==11) {
        assert(ok&&!h.witness.failed());
        assert(!h.witness.observe_native_label(h.cpu,h.report,
            Entry+4u,Nop,true)&&h.witness.failed());
    } else assert(!ok&&h.witness.failed());
}

// A synthetic two-instruction callee joins the original 118 byte-load
// witness to the 119 immediate-compare witness. Both observers are read-only;
// neither advances the instruction counter or mutates architectural state.
static unsigned native_compare_chain() {
    unsigned cases=0;
    for(unsigned op:{10u,11u})
        for(unsigned field=0;field<8u;++field)
            for(unsigned value=0;value<=255u;++value)
                for(unsigned so:{0u,1u})
                    for(unsigned source_reg:{9u,8u,7u}) {
                        // Only r9 changes in the original byte load. The
                        // comparison may instead consume a separately proven
                        // constant in r8 or an upper-half address in r7.
                        Harness h(9u,value,false);
                        const unsigned imm=(value&1u)?0x8000u:0x5au;
                        const uint32_t cmp=(op<<26u)|(field<<23u)|
                            (source_reg<<16u)|imm;
                        h.step.next_word=cmp;
                        h.cpu.mmu.write32(Entry+4u,cmp);
                        h.cpu.mmu.write32(Entry+8u,Nop);
                        h.cpu.mmu.write32(Entry+12u,0x44000002u);
                        h.cpu.mmu.write32(Link,0x44000002u);
                        h.cpu.xer=(so<<31u)|0x60000000u;
                        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,Nop));
                        ++h.cpu.inst_count;h.cpu.gpr[9]=value;
                        assert(h.witness.observe_native_label(h.cpu,h.report,
                            Entry+4u,cmp,true));
                        const uint32_t source_value=h.cpu.gpr[source_reg];
                        CallerImmediateCompareWitness next;
                        assert(next.arm(h.cpu,Entry,Entry+4u,cmp,Nop,
                            {source_reg,source_value}));
                        const int64_t operand=op==11u&&imm>=0x8000u?
                            int64_t(imm)-0x10000ll:int64_t(imm);
                        const int64_t lhs=op==11u?
                            int64_t(std::bit_cast<int32_t>(source_value)):
                            int64_t(source_value);
                        h.cpu.cr[field]={lhs<operand,lhs>operand,
                            lhs==operand,bool(so)};
                        ++h.cpu.inst_count;
                        assert(next.observe(h.cpu,Entry+8u,Nop));
                        assert(next.stage()==2u&&!next.failed());
                        ++cases;
                    }
    return cases;
}
static void native_compare_chain_rejections() {
    const uint32_t cmp=(11u<<26u)|(3u<<23u)|(9u<<16u)|0x5au;
    for(unsigned fault=0;fault<9;++fault){
        Harness h(9u,0x5au,false);
        h.step.next_word=cmp;
        h.cpu.mmu.write32(Entry+4u,cmp);
        h.cpu.mmu.write32(Entry+8u,Nop);
        h.cpu.mmu.write32(Entry+12u,0x44000002u);
        h.cpu.mmu.write32(Link,0x44000002u);
        if(fault==0)h.cpu.mmu.write32(Entry+8u,0u);
        if(fault==1)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==2)h.cpu.lr=Entry+12u;
        if(fault<=2){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,Nop));
            continue;
        }
        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,Nop));
        ++h.cpu.inst_count;h.cpu.gpr[9]=0x5au;
        if(fault==3)h.cpu.mmu.write32(Entry+8u,0u);
        if(fault==4)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault<=4){
            assert(!h.witness.observe_native_label(h.cpu,h.report,
                Entry+4u,cmp,true));
            continue;
        }
        assert(h.witness.observe_native_label(h.cpu,h.report,
            Entry+4u,cmp,true));
        CallerImmediateCompareWitness next;
        assert(next.arm(h.cpu,Entry,Entry+4u,cmp,Nop,{9u,0x5au}));
        h.cpu.cr[3]={false,false,true,false};
        ++h.cpu.inst_count;
        if(fault==5)h.cpu.cr[3].eq=false;
        if(fault==6)h.cpu.cr[4].eq=true;
        if(fault==7)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==8)h.cpu.inst_count+=1u;
        assert(!next.observe(h.cpu,Entry+8u,Nop));
    }
}

// The authentic 119 boundary consumes a constant other than the
// preceding load's destination. Refuse incorrect proof, post-arm writes,
// selected-CR corruption, and corruption of an unrelated CR field.
static unsigned native_independent_compare_refusals() {
    constexpr uint32_t guard=0x44000002u;
    const uint32_t cmp=(11u<<26u)|(3u<<23u)|(8u<<16u)|16u;
    for(unsigned fault=0;fault<4u;++fault) {
        Harness h(9u,0x5au,false);
        h.step.next_word=cmp;
        h.cpu.mmu.write32(Entry+4u,cmp);
        h.cpu.mmu.write32(Entry+8u,Nop);
        h.cpu.mmu.write32(Entry+12u,guard);
        h.cpu.mmu.write32(Link,guard);
        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,Nop));
        ++h.cpu.inst_count;h.cpu.gpr[9]=0x5au;
        assert(h.witness.observe_native_label(h.cpu,h.report,
            Entry+4u,cmp,true));
        CallerImmediateCompareWitness compare;
        if(fault==0u) {
            assert(!compare.arm(h.cpu,Entry,Entry+4u,cmp,Nop,{8u,17u}));
            continue;
        }
        assert(compare.arm(h.cpu,Entry,Entry+4u,cmp,Nop,{8u,16u}));
        h.cpu.cr[3]={false,false,true,false};
        if(fault==1u)h.cpu.gpr[8]=17u;
        if(fault==2u)h.cpu.cr[3].eq=false;
        if(fault==3u)h.cpu.cr[0].eq=true;
        ++h.cpu.inst_count;
        assert(!compare.observe(h.cpu,Entry+8u,Nop));
    }
    return 4u;
}

// Exercise the exact three-instruction guarded geometry without original data.
// Both earlier witnesses must accept the extra authenticated word, but neither
// may authorize an altered word, return guard, or an execution past its label.
static unsigned extended_guard_cases() {
    constexpr uint32_t guard=0x44000002u;
    constexpr uint32_t cmp=(11u<<26u)|(3u<<23u)|(8u<<16u)|16u;
    constexpr uint32_t copy=(31u<<26u)|(1u<<21u)|(10u<<16u)|(1u<<11u)|(444u<<1u);
    constexpr uint32_t following=0x38630001u;
    for(unsigned fault=0;fault<15u;++fault){
        Harness h(9u,0x5au,false);
        h.step.next_word=cmp;
        h.cpu.mmu.write32(Entry+4u,cmp);
        h.cpu.mmu.write32(Entry+8u,copy);
        h.cpu.mmu.write32(Entry+12u,following);
        h.cpu.mmu.write32(Entry+16u,guard);
        h.cpu.mmu.write32(Link,guard);
        if(fault==1u)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==2u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault==3u){h.cpu.lr=Entry+12u;h.step.lr=h.cpu.lr;}
        if(fault==4u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,{},following));
            continue;
        }
        if(fault>=1u&&fault<=3u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,copy,following));
            continue;
        }
        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,copy,following));
        ++h.cpu.inst_count;h.cpu.gpr[9]=0x5au;
        if(fault==5u)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==6u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault==7u)h.cpu.mmu.write32(Entry+8u,0u);
        if(fault>=5u&&fault<=7u){
            assert(!h.witness.observe_native_label(h.cpu,h.report,Entry+4u,cmp,true));
            continue;
        }
        assert(h.witness.observe_native_label(h.cpu,h.report,Entry+4u,cmp,true));
        CallerImmediateCompareWitness compare;
        if(fault==8u)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==9u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault==10u){h.cpu.lr=Entry+16u;}
        if(fault>=8u&&fault<=10u){
            assert(!compare.arm(h.cpu,Entry,Entry+4u,cmp,copy,{8u,16u},following));
            continue;
        }
        assert(compare.arm(h.cpu,Entry,Entry+4u,cmp,copy,{8u,16u},following));
        h.cpu.cr[3]={false,false,true,false};
        ++h.cpu.inst_count;
        if(fault==11u)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==12u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault==13u)h.cpu.gpr[10]=Sp;
        if(fault==14u)++h.cpu.inst_count;
        assert(compare.observe(h.cpu,Entry+8u,copy)==(fault==0u));
    }
    return 15u;
}

// An optional fourth native word may move the guard to the fifth slot.
// The original 120 path remains unchanged when that option is omitted.
static unsigned fourth_guard_cases() {
    constexpr uint32_t guard=0x44000002u;
    constexpr uint32_t cmp=(11u<<26u)|(3u<<23u)|(8u<<16u)|16u;
    constexpr uint32_t copy=(31u<<26u)|(1u<<21u)|(10u<<16u)|(1u<<11u)|(444u<<1u);
    constexpr uint32_t immediate=(14u<<26u)|(3u<<21u)|0xfffeu;
    constexpr uint32_t following=0x60000000u;
    for(unsigned fault=0;fault<15u;++fault){
        Harness h(9u,0x5au,false);
        h.step.next_word=cmp;
        h.cpu.mmu.write32(Entry+4u,cmp);
        h.cpu.mmu.write32(Entry+8u,copy);
        h.cpu.mmu.write32(Entry+12u,immediate);
        h.cpu.mmu.write32(Entry+16u,following);
        h.cpu.mmu.write32(Entry+20u,guard);
        h.cpu.mmu.write32(Link,guard);
        if(fault==1u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault==2u)h.cpu.mmu.write32(Entry+20u,0u);
        if(fault==3u){h.cpu.lr=Entry+16u;h.step.lr=h.cpu.lr;}
        if(fault==4u) {
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,copy,immediate,following==guard?following:guard));
            continue;
        }
        if(fault==5u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,copy,{},following));
            continue;
        }
        if(fault>=1u&&fault<=3u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,copy,immediate,following));
            continue;
        }
        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,copy,immediate,following));
        ++h.cpu.inst_count;h.cpu.gpr[9]=0x5au;
        if(fault==6u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault==7u)h.cpu.mmu.write32(Entry+20u,0u);
        if(fault==8u)h.cpu.mmu.write32(Entry+12u,0u);
        if(fault==9u)h.cpu.mmu.write32(Entry+8u,0u);
        if(fault==10u)h.cpu.mmu.write32(Link,0u);
        if(fault==11u)h.cpu.gpr[7]^=1u;
        if(fault==12u)++h.cpu.inst_count;
        if(fault==13u)h.cpu.lr=Entry+16u;
        if(fault==14u)h.cpu.cr[2].eq=!h.cpu.cr[2].eq;
        assert(h.witness.observe_native_label(h.cpu,h.report,
            Entry+4u,cmp,true)==(fault==0u));
    }
    return 15u;
}


/* Authenticate the entire original-free 118..124 six-successor chain.
   Each guard mutation must be rejected at the earliest owning witness.
   This extends old tests without changing their short-chain behavior. */
static unsigned sixth_guard_cases() {
    constexpr uint32_t guard=0x44000002u;
    constexpr uint32_t cmp=(11u<<26u)|(3u<<23u)|(8u<<16u)|16u;
    constexpr uint32_t copy=(31u<<26u)|(1u<<21u)|(10u<<16u)|(1u<<11u)|(444u<<1u);
    constexpr uint32_t immediate=(14u<<26u)|(3u<<21u)|0xfffeu;
    constexpr uint32_t signext=(31u<<26u)|(9u<<21u)|(9u<<16u)|(954u<<1u);
    constexpr uint32_t second=(14u<<26u)|(11u<<21u)|0x8000u;
    constexpr uint32_t following=Nop;
    for(unsigned fault=0;fault<17u;++fault) {
        Harness h(9u,0x5au,false);
        h.step.next_word=cmp;
        h.cpu.mmu.write32(Entry+4u,cmp);
        h.cpu.mmu.write32(Entry+8u,copy);
        h.cpu.mmu.write32(Entry+12u,immediate);
        h.cpu.mmu.write32(Entry+16u,signext);
        h.cpu.mmu.write32(Entry+20u,second);
        h.cpu.mmu.write32(Entry+24u,following);
        h.cpu.mmu.write32(Entry+28u,guard);
        h.cpu.mmu.write32(Link,guard);
        if(fault==1u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault==2u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==3u)h.cpu.mmu.write32(Entry+20u,0u);
        if(fault==4u) {
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,
                   copy,immediate,signext,{},following));
            continue;
        }
        if(fault>=1u&&fault<=3u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,
                   copy,immediate,signext,second,following));
            continue;
        }
        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,
               copy,immediate,signext,second,following));
        ++h.cpu.inst_count;h.cpu.gpr[9u]=0x5au;
        if(fault==5u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault==6u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==7u)h.cpu.mmu.write32(Entry+16u,0u);
        if(fault>=5u&&fault<=7u){
            assert(!h.witness.observe_native_label(
                   h.cpu,h.report,Entry+4u,cmp,true));
            continue;
        }
        assert(h.witness.observe_native_label(
               h.cpu,h.report,Entry+4u,cmp,true));
        CallerImmediateCompareWitness compare;
        if(fault==8u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault==9u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==10u){h.cpu.lr=Entry+24u;}
        if(fault>=8u&&fault<=10u) {
            assert(!compare.arm(h.cpu,Entry,Entry+4u,cmp,copy,
                   {8u,16u},immediate,signext,second,following));
            continue;
        }
        assert(compare.arm(h.cpu,Entry,Entry+4u,cmp,copy,
               {8u,16u},immediate,signext,second,following));
        h.cpu.cr[3u]={false,false,true,false};
        ++h.cpu.inst_count;
        if(fault==11u)h.cpu.mmu.write32(Entry+20u,0u);
        if(fault==12u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault==13u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==14u)h.cpu.cr[3u].eq=false;
        if(fault==15u)h.cpu.gpr[0u]^=1u;
        if(fault==16u)++h.cpu.inst_count;
        assert(compare.observe(h.cpu,Entry+8u,copy)==(fault==0u));
    }
    return 17u;
}


/* The optional seventh successor is a read-only 125 stop, not an
   authorization to execute it. Both independent observers must refuse
   mutations in the owner-original 124 extension, including the guard. */
static unsigned seventh_guard_cases() {
    constexpr uint32_t guard=0x44000002u;
    constexpr uint32_t cmp=(11u<<26u)|(3u<<23u)|(8u<<16u)|16u;
    constexpr uint32_t copy=(31u<<26u)|(1u<<21u)|(10u<<16u)|(1u<<11u)|(444u<<1u);
    constexpr uint32_t immediate=(14u<<26u)|(3u<<21u)|0xfffeu;
    constexpr uint32_t signext=(31u<<26u)|(9u<<21u)|(9u<<16u)|(954u<<1u);
    constexpr uint32_t second=(14u<<26u)|(11u<<21u)|0x8000u;
    constexpr uint32_t third=(14u<<26u)|(6u<<21u)|0xff80u;
    constexpr uint32_t following=Nop;
    for(unsigned fault=0;fault<20u;++fault) {
        Harness h(9u,0x5au,false);
        h.step.next_word=cmp;
        h.cpu.mmu.write32(Entry+4u,cmp);
        h.cpu.mmu.write32(Entry+8u,copy);
        h.cpu.mmu.write32(Entry+12u,immediate);
        h.cpu.mmu.write32(Entry+16u,signext);
        h.cpu.mmu.write32(Entry+20u,second);
        h.cpu.mmu.write32(Entry+24u,third);
        h.cpu.mmu.write32(Entry+28u,following);
        h.cpu.mmu.write32(Entry+32u,guard);
        h.cpu.mmu.write32(Link,guard);
        if(fault==1u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault==2u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==3u)h.cpu.mmu.write32(Entry+32u,0u);
        if(fault==4u)h.cpu.mmu.write32(Entry+20u,0u);
        if(fault==5u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,
                   copy,immediate,signext,second,{},following));
            continue;
        }
        if(fault==6u)h.cpu.lr=Entry+28u;
        if((fault>=1u&&fault<=4u)||fault==6u){
            assert(!h.witness.arm_native(h.cpu,h.report,h.step,true,
                   copy,immediate,signext,second,third,following));
            continue;
        }
        assert(h.witness.arm_native(h.cpu,h.report,h.step,true,
               copy,immediate,signext,second,third,following));
        ++h.cpu.inst_count;h.cpu.gpr[9u]=0x5au;
        if(fault==7u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==8u)h.cpu.mmu.write32(Entry+32u,0u);
        if(fault==9u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault>=7u&&fault<=9u){
            assert(!h.witness.observe_native_label(h.cpu,h.report,Entry+4u,cmp,true));
            continue;
        }
        assert(h.witness.observe_native_label(
               h.cpu,h.report,Entry+4u,cmp,true));
        CallerImmediateCompareWitness compare;
        if(fault==10u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==11u)h.cpu.mmu.write32(Entry+32u,0u);
        if(fault==12u)h.cpu.lr=Entry+28u;
        if(fault>=10u&&fault<=12u){
            assert(!compare.arm(h.cpu,Entry,Entry+4u,cmp,copy,
                   {8u,16u},immediate,signext,second,third,following));
            continue;
        }
        assert(compare.arm(h.cpu,Entry,Entry+4u,cmp,copy,
               {8u,16u},immediate,signext,second,third,following));
        h.cpu.cr[3u]={false,false,true,false};
        ++h.cpu.inst_count;
        if(fault==13u)h.cpu.mmu.write32(Entry+28u,0u);
        if(fault==14u)h.cpu.mmu.write32(Entry+32u,0u);
        if(fault==15u)h.cpu.mmu.write32(Entry+24u,0u);
        if(fault==16u)h.cpu.cr[3u].eq=false;
        if(fault==17u)h.cpu.gpr[0u]^=1u;
        if(fault==18u)++h.cpu.inst_count;
        if(fault==19u)h.cpu.mmu.write32(Entry+20u,0u);
        assert(compare.observe(h.cpu,Entry+8u,copy)==(fault==0u));
    }
    return 20u;
}

int main() {
    const auto successful=positives();
    const auto native_successful=native_positives();
    for(unsigned fault=0;fault<=32u;++fault)negative(fault);
    for(unsigned fault=0;fault<=13u;++fault)native_negative(fault);
    const auto compare_chain=native_compare_chain();
    native_compare_chain_rejections();
    const auto independent_rejected=native_independent_compare_refusals();
    const auto extended=extended_guard_cases();
    const auto fourth=fourth_guard_cases();
    const auto sixth=sixth_guard_cases();
    const auto seventh=seventh_guard_cases();
    assert(fourth==15u&&sixth==17u&&seventh==20u);
    assert(compare_chain==24576u&&independent_rejected==4u);
    std::cout<<"FORMATTER_REPORT_BYTE_TRANSITION_TEST valid="<<successful
             <<" native_valid="<<native_successful
             <<" rejected=47 compare_chain="<<compare_chain
             <<" compare_chain_rejected=9 independent_source_rejected="
             <<independent_rejected<<" extended_guard_cases="<<extended<<" fourth_guard_cases="<<fourth<<" sixth_guard_cases="<<sixth<<" seventh_guard_cases="<<seventh<<" original_execution=0\n";
}
