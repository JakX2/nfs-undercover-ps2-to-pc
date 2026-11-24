#include "wii_stm_prefix_witness_v629.h"
#include <iostream>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=IpcClientWitness;using S=StmPrefixWitness;using B=NativeIosBinding;using H=HollywoodIrq;using M=IpcMailbox;
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)throw std::runtime_error("V629 line "+std::to_string(l.line()));}
struct Mmu{
    std::vector<uint8_t> mem1=std::vector<uint8_t>(24u*1024u*1024u),mem2=std::vector<uint8_t>(32);
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?mem1.data()+(a-0x80000000u):nullptr;}
    uint8_t read8(uint32_t a){auto* p=get_ptr(a);need(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write8(uint32_t a,uint8_t v){auto* p=get_ptr(a);need(p);*p=v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)write8(a+i,uint8_t(v>>(24-8*i)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=S::Begin,lr=S::Begin,msr=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true;
};
int main(){
    StmPrefixExpectations e{};
    e.bridge={1,2,3,4,5,6,7};
    e.stm={S::Stm,0x80520968u,7,0x100};e.open={S::Open,0x8052b090u,8,0x200};
    e.paths[0]={0x80601000,1};e.paths[1]={0x80602000,2};e.path_count=2;e.irq_handler=0x80519318;
    for(unsigned fault=0;fault<=16;++fault){
        Cpu c;auto& m=c.mmu;
        std::atomic<uint32_t> cause{0},mask{0xf0|H::PI_HOLLYWOOD};
        NativeIosTransport host(m.mem1,m.mem2,cause,mask);B binding(host);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        need(B::write32(IosBus::IPC+M::PPCCTRL,0x30));
        c.gpr[1]=W::Stack;c.gpr[2]=0x80715ee0;c.gpr[13]=W::Sda;
        m.write32(W::IrqGlobal,W::Table);m.write32(W::Table+108,e.irq_handler);
        m.write32(W::MaskA,0xf7fff7e0);
        for(unsigned i=0;i<e.bridge.size();++i)m.write32(S::Begin+4*i,e.bridge[i]);
        for(auto edge:{e.stm,e.open}){m.write32(edge.pc,edge.entry_word);m.write32(edge.lr-4,edge.branch_word);}
        for(auto p:e.paths){if(!p.addr)continue;std::string_view path=p.kind==1?"/dev/stm/immediate":"/dev/stm/eventhook";
            for(unsigned i=0;i<path.size();++i)m.write8(p.addr+i,uint8_t(path[i]));}
        if(fault==2)m.write32(S::Begin,0);
        if(fault==3)m.write32(W::IrqGlobal,0);
        if(fault==4)need(B::write32(IosBus::IPC+M::PPCCTRL,0x31));
        if(fault==5)c.msr&=~0x8000u;
        S w(e);const bool bad_begin=fault>=1&&fault<=5;
        need(w.begin(c,fault!=1)==!bad_begin);if(bad_begin)continue;
        c.pc=S::Stm;c.lr=e.stm.lr;c.inst_count+=7;
        if(fault==6)c.lr+=4;
        if(fault==7)c.gpr[1]-=8;
        if(fault==8)m.write32(W::Table+4,1);
        if(fault==9)c.inst_count=100;
        const bool bad_root=fault>=6&&fault<=9;need(w.observe(c.pc,c)==!bad_root);if(bad_root)continue;
        c.pc=S::Open;c.lr=e.open.lr;c.gpr[1]-=32;c.gpr[3]=e.paths[fault==16?1:0].addr;c.gpr[4]=0;c.inst_count+=22;
        if(fault==10)c.gpr[4]=1;
        if(fault==11)c.gpr[3]+=1;
        if(fault==12)m.write8(c.gpr[3]+18,1);
        if(fault==13)need(B::write32(IosBus::IPC+M::PPCMSG,0x100));
        if(fault==14)c.gpr[1]=W::Stack;
        if(fault==15)c.msr^=0x8000;
        const bool good=fault==0||fault==16;
        need(w.observe(c.pc,c)==good);
        if(good){need(w.stage()==3&&w.path_kind()==(fault==16?2:1)&&host.serviced_steps()==0);need(!w.observe(c.pc,c));}
    }
    std::cout<<"V629_STM_WITNESS positive=2 refusal=15 stages=3 pathname=1 transport_unchanged=1 actual_ios=0 boot_verified=0\n";
}
