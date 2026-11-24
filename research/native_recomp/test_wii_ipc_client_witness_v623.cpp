#include "wii_ipc_client_witness_v623.h"
#include <iostream>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=IpcClientWitness;using B=NativeIosBinding;using H=HollywoodIrq;using M=IpcMailbox;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V623 line "+std::to_string(l.line()));
}
struct Mmu {
    static constexpr uint32_t heap=0x93380000u;
    std::vector<uint8_t> mem1=std::vector<uint8_t>(24u*1024u*1024u);
    std::array<uint8_t,W::HeapLimit+2u> mem2{};
    uint8_t* get_ptr(uint32_t a){
        if(a>=0x80000000u&&a<0x81800000u)return mem1.data()+a-0x80000000u;
        if(a>=heap-1u&&a<=heap+W::HeapLimit)return mem2.data()+a-(heap-1u);
        return nullptr;
    }
    uint8_t read8(uint32_t a){auto* p=get_ptr(a);need(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto* p=get_ptr(a+i);need(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0,lr=0,msr=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true;
};
int main(){
    constexpr std::array<uint32_t,17> pc{
        W::Root,0x80518fc8,0x8052ae70,0x8052ae78,0x80519084,0x8051907c,0x8051aa04,
        0x805265ac,0x805265d4,0x8051908c,0x805265f8,0x805269bc,0x805265ac,
        0x805266e0,0x805265d4,0x8051906c,0x8051af28};
    constexpr std::array<uint32_t,17> lr{
        W::Return,0x805194f8,0x80518fe4,0x80518fec,0x805194fc,0x80519508,0x80519524,
        0x8051aa2c,0x8051ab14,0x80519530,0x80519540,0x80519548,0x805269dc,
        0x80526a0c,0x80526a1c,0x80519554,0x80519558};
    IpcClientExpectations e{};
    for(unsigned i=0;i<pc.size();++i)e.edges[i]={pc[i],lr[i],0x100u+i,pc[i]};
    e.handler=0x80519094u;e.handler_word=0x1234u;e.return_word=0x5678u;
    for(unsigned fault=0;fault<=17;++fault){
        Cpu c;auto& m=c.mmu;std::atomic<uint32_t> cause{0},mask{0xf0};
        NativeIosTransport host(m.mem1,m.mem2,cause,mask);B binding(host);W w(e);
        m.mem2.fill(0x6b);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        c.pc=c.lr=W::Call;c.gpr[1]=W::Stack;c.gpr[13]=W::Sda;
        for(auto x:e.edges){m.write32(x.pc,x.entry_word);m.write32(x.lr-4u,x.branch_word);}
        m.write32(e.handler,e.handler_word);m.write32(W::Return,e.return_word);
        m.write32(W::Lo,Mmu::heap);m.write32(W::Hi,0x93400000u);
        m.write32(W::Sda-16336u,Mmu::heap);m.write32(W::Sda-3352u,0x93400000u);
        m.write32(W::MaskA,0xf7fff7f0u);
        if(fault==1)c.msr&=~0x8000u;
        if(fault==2)m.write32(W::Hi,Mmu::heap+16);
        if(fault==3)m.write32(W::Table+108u,1);
        if(fault==4)need(B::write32(IosBus::IPC+M::PPCCTRL,0x31));
        const bool bad_begin=fault>=1&&fault<=4;
        need(w.begin(c)==!bad_begin);if(bad_begin)continue;
        bool stopped=false;
        for(unsigned i=0;i<17;++i){
            c.pc=pc[i];c.lr=lr[i];c.inst_count+=10;
            c.msr=(i==8||i==13||i==14)?0x32u:0x8032u;
            if(i==0)c.gpr[3]=0;
            if(i==5)c.gpr[3]=Mmu::heap;
            if(i==6){c.gpr[3]=Mmu::heap;c.gpr[4]=fault==6?33:64;}
            if(i==8||i==14)c.gpr[3]=1;
            if(i==9){
                c.gpr[3]=Mmu::heap+64;
                if(fault!=7)m.write32(Mmu::heap,0x12345678);
                if(fault==8)*m.get_ptr(Mmu::heap-1u)^=1;
                if(fault==9)*m.get_ptr(Mmu::heap+64u)^=1;
            }
            if(i==10){c.gpr[3]=27;c.gpr[4]=e.handler+(fault==10?4:0);}
            if(i==11){c.gpr[3]=0x10;m.write32(W::Table+108u,e.handler);}
            if(i==13)c.gpr[3]=0x10;
            if(i==15){
                mask.fetch_or(H::PI_HOLLYWOOD);
                m.write32(W::MaskA,0xf7fff7e0u);
                c.gpr[3]=1;c.gpr[4]=fault==11?0x31:0x36;
            }
            if(i==2&&fault==5)c.lr+=4;
            if(i==12&&fault==12)cause=0x10;
            if(i==16&&fault!=13){
                need(B::write32(IosBus::IPC+M::PPCCTRL,0x36));
                if(fault==14){bool refused=false;try{B::write32(IosBus::IPC+M::PPCCTRL,0x36);}catch(const std::runtime_error&){refused=true;}need(refused);}
            }
            const bool bad=(i==2&&fault==5)||(i==6&&fault==6)||(i==9&&fault>=7&&fault<=9)||
                (i==10&&fault==10)||(i==15&&fault==11)||(i==12&&fault==12)||(i==16&&(fault==13||fault==14));
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
        }
        if(stopped)continue;
        c.pc=c.lr=W::Return;c.gpr[3]=0;c.msr=0x8032;c.inst_count+=10;
        if(fault==15)c.gpr[14]=1;
        if(fault==16)m.write32(W::Table+4,1);
        if(fault==17)m.write32(W::MaskA,0xf7fff7f0u);
        need(w.observe(c.pc,c)==(fault==0));
        if(!fault){need(w.stage()==19&&w.heap_size()==64&&host.serviced_steps()==0);need(!w.observe(c.pc,c));}
    }
    std::cout<<"V623_IPC_CLIENT positive=1 stages=19 calls=17 heap=1 mailbox=1 refusal=17 native_transport=1 actual_ios=0 boot_verified=0\n";
}
