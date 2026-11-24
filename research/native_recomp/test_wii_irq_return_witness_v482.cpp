#include "wii_irq_return_witness_v482.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("IRQ return witness");}
constexpr std::array<uint32_t,7> addrs{0x0c00401c,0x0c00500a,0x0d006c00,0x0d006800,0x0d006814,0x0d006828,0x0c003004};
constexpr std::array<uint32_t,7> masks{0u,0xfffffe07u,0xffffffd3u,0xffffd3f0u,0xfffff3f0u,0xfffffff0u,0u};
constexpr std::array<uint32_t,7> selected_masks{0xfffffff0u,0x07fffff0u,0x00fffff0u,0x007ffff0u,0x000ffff0u,0x0001fff0u,0x00007ff0u};
void transaction(IrqMaskIo& io,unsigned bank,unsigned fault=0){
    const unsigned width=bank<2?16:32;const bool native=bank!=1&&bank!=6;
    const uint32_t in=width==16?0xf7f7u:0xdeadbeefu;
    if(bank!=0&&bank!=6)io.record(false,addrs[bank],width,in,native);
    const uint32_t out=bank==0?0u:bank==6?0xf0u:in&masks[bank];
    if(fault!=1)io.record(true,addrs[bank]+(fault==2?4u:0u),width+(fault==3?16u:0u),out^(fault==4?1u:0u),native^(fault==5));
    if(fault==6)io.record(true,addrs[bank],width,out,native);
}
struct Mmu{
    std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){if(a==0xcc003004u)return 0xf0u;if(a==0xcd000034u)return 0x40000000u;
        if(auto v=IrqBankBinding::read32(a))return *v;
        auto i=mem.find(a);return i==mem.end()?0:i->second;}
    uint16_t read16(uint32_t a){if(auto v=IrqBankBinding::read16(a))return *v;return 0x800u;}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    for(unsigned bank=0;bank<7;++bank)for(unsigned fault=0;fault<=6;++fault){
        IrqMaskIo io;
        for(unsigned n=0;n<=bank;++n){need(io.begin(n));transaction(io,n,n==bank?fault:0);
            need(io.finish()==(n!=bank||fault==0));}
    }
    for(unsigned fault=0;fault<=8;++fault){
        irq_mask_io={};
        std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);IrqBankBinding binding(banks);
        constexpr IrqReturnExpectations e{{VectorEdge{0x805265ac,0x80526678,1,2},
            VectorEdge{0x805266e0,0x805266a4,3,4},VectorEdge{0x805265d4,0x805266b4,5,6},
            VectorEdge{0x80520e9c,0x805266c4,7,8},VectorEdge{0x80522eb8,0x805208c0,9,10}}};
        Cpu c;auto& m=c.mmu.mem;c.gpr[1]=0x80751000;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        m[c.gpr[13]-3408]=0x80003040;
        for(unsigned i=0;i<15;++i)m[0x80003000+4*i]=0x80520f5c;
        m[0x80003020]=0x805217bc;
        for(auto edge:e.edges){m[edge.pc]=edge.entry_word;m[edge.lr-4]=edge.branch_word;}
        auto enter=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        enter(0);IrqReturnWitness w(e);need(w.begin(c));m[0x800000c4]=0xfffffff0;
        for(unsigned i=0;i<7;++i){enter(1);c.gpr[3]=selected_masks[i];c.gpr[4]=0xfffffff0;
            if(fault==1&&i==4){c.gpr[3]^=1;need(!w.observe(c.pc,c));break;}
            need(w.observe(c.pc,c));transaction(irq_mask_io,i);
        }
        if(fault==1)continue;
        enter(2);c.gpr[3]=0;
        if(fault==2)c.gpr[3]=1;
        if(fault==3)banks.set_mi_mask(1);
        if(fault==4)m[0x80003044]=1;
        if(fault>=2&&fault<=4){need(!w.observe(c.pc,c));continue;}
        need(w.observe(c.pc,c));enter(3);c.gpr[3]=4;c.gpr[4]=0x80526ce0;
        if(fault==5)c.gpr[4]^=4;
        if(fault==5){need(!w.observe(c.pc,c));continue;}
        need(w.observe(c.pc,c));enter(4);c.gpr[1]+=32;c.gpr[3]=0x80520f5c;
        m[0x80003010]=0x80526ce0;
        if(fault==6)m[0x80003010]=0;
        if(fault==7)c.gpr[1]-=4;
        if(fault==8)m[0x80003020]=0;
        const auto before=m;need(w.observe(c.pc,c)==(fault==0));need(before==m);
        if(!fault)need(w.stage()==11&&irq_mask_io.done()==7);else need(w.failure()!=0);
    }
    std::cout<<"PASS: seven-bank transaction sequence and IRQ return witness, 50 negative controls\n";
}
