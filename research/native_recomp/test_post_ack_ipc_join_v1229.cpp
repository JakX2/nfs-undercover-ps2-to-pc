#include "wii_post_ack_ipc_join_v1229.h"
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
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0,lr=0,msr=0x8032,dispatch_saved_ctx=0;
    std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t ctr=0,xer=0,srr0=0,srr1=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
int main(){
    constexpr uint32_t branch=0x48000001u|((W::Root-W::Call)&0x03fffffcu);
    constexpr uint32_t entry=0x60000000u;
    IpcClientExpectations e{};
    e.edges[0]={W::Root,W::Return,branch,entry};
    e.handler=0x80519094u;e.handler_word=0x1234u;
    unsigned valid=0,refused=0;
    for(unsigned fault=0;fault<=17;++fault){
        Cpu c;auto& m=c.mmu;std::atomic<uint32_t> cause{0},mask{0xf0};
        NativeIosTransport host(m.mem1,m.mem2,cause,mask);B binding(host);
        PostAckIpcJoin w(e,{W::Call,W::Root,branch,entry});
        c.pc=c.lr=W::Call;c.gpr[1]=W::Stack;c.gpr[13]=W::Sda;
        m.write32(W::Call,branch);m.write32(W::Root,entry);
        m.write32(e.handler,e.handler_word);
        m.write32(W::Lo,Mmu::heap);m.write32(W::Hi,0x93400000u);
        m.write32(W::Sda-16336u,Mmu::heap);m.write32(W::Sda-3352u,0x93400000u);
        m.write32(W::MaskA,0xf7fff7f0u);m.write32(W::IrqGlobal,W::Table);
        if(fault==3)m.write32(W::MaskA,0);
        if(fault==4)c.inst_count=UINT64_MAX;
        if(fault==5)m.write32(W::Table+108u,1);
        bool ok=w.pre_dispatch(c,W::Call,fault!=1,fault!=2);
        if(fault>=1&&fault<=5){
            need(!ok&&w.failure()==1);
            if(fault==3)need(w.cold_refusal()==128u);
            if(fault==5)need(w.cold_refusal()==16384u);
            ++refused;continue;
        }
        need(ok&&w.stage()==1);
        c.inst_count+=fault==6?0u:fault==7?2u:1u;
        ok=w.before_call(c,W::Call,fault==8?branch^4u:branch,fault!=9,fault!=10);
        if(fault>=6&&fault<=10){need(!ok&&w.failure()==2);++refused;continue;}
        need(ok&&w.stage()==2);
        c.pc=W::Root;c.lr=W::Return;
        if(fault==11)++c.inst_count;
        if(fault==12)c.lr+=4;
        if(fault==13)c.gqr[3]^=1;
        if(fault==14)m.write32(W::Root,entry^1u);
        if(fault==15)m.write32(W::Lo,Mmu::heap+32u);
        if(fault==17)c.gpr[14]^=1;
        ok=w.target_entry(c,W::Root,fault!=16);
        if(fault>=11){need(!ok&&w.failure()==3);++refused;continue;}
        need(ok&&w.stage()==3&&host.serviced_steps()==0);
        need(!w.target_entry(c,W::Root,true));++valid;
    }
    need(valid==1&&refused==17);
    std::cout<<"V1229_POST_ACK_IPC_JOIN valid=1 refused=17 cold_witness=1 same_tick=1 original_execution=0 boot_verified=0\n";
}
