#include "wii_open_request_witness_v639.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
using W=OpenRequestWitness;using I=IpcClientWitness;using R=OpenScRoute;using B=NativeIosBinding;using H=HollywoodIrq;using M=IpcMailbox;
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)throw std::runtime_error("V639 line "+std::to_string(l.line()));}
struct Mmu{
    std::vector<uint8_t> mem1=std::vector<uint8_t>(24u*1024u*1024u),mem2=std::vector<uint8_t>(0x20000);
    uint8_t* get_ptr(uint32_t a){
        if(a>=0x80000000u&&a<0x81800000u)return mem1.data()+(a-0x80000000u);
        if(a>=0x90000000u&&a<0x90020000u)return mem2.data()+(a-0x90000000u);
        return nullptr;
    }
    uint8_t read8(uint32_t a){auto* p=get_ptr(a);need(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write8(uint32_t a,uint8_t v){auto* p=get_ptr(a);need(p);*p=v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)write8(a+i,uint8_t(v>>(24-8*i)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=W::Open,lr=0x8052b090,msr=0x8032,dispatch_saved_ctx=0,srr0=0,srr1=0,ctr=0,hid0=0x100;
    OpenCacheRangeTrace open_cache_range;
    uint32_t guest_flush_count=18000,guest_last_flush=0,guest_sync_count=0,guest_isync_count=0;
    uint64_t inst_count=100;bool is_running=true;
};
int main(){
    OpenRequestExpectations e{{W::Open,0x8052b0b8,1,2},{W::Profile,0x8051998c,3,4},
        {W::Disable,0x8051ab64,5,6},{W::Restore,0x8051ad14,7,8},
        {W::Flush,R::Caller,9,10},{W::Submit,0x80519a3c,11,12},13,0x44000002,14};
    const std::array<uint8_t,28> bytes{};constexpr uint32_t path=0x8060100c,lo=0x90000020,size=0x4000,req=lo+0x80;
    Cpu c;
    unsigned good=0,bad=0;
    for(unsigned fault=0;fault<22;++fault){
        auto& m=c.mmu;std::fill(m.mem1.begin(),m.mem1.end(),0);std::fill(m.mem2.begin(),m.mem2.end(),0);
        c.pc=W::Open;c.lr=e.entry.lr;c.msr=0x8032;c.dispatch_saved_ctx=0;c.srr0=c.srr1=0;c.inst_count=100;
        c.gpr.fill(0);c.gpr[1]=I::Stack-32;c.gpr[2]=0x80715ee0;c.gpr[13]=I::Sda;c.gpr[3]=path;
        c.open_cache_range=OpenCacheRangeTrace{};c.guest_flush_count=18000;c.guest_sync_count=c.guest_isync_count=0;
        std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD|0x40u};
        NativeIosTransport host(m.mem1,m.mem2,cause,mask);B binding(host);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC)&&B::write32(IosBus::IPC+M::PPCCTRL,0x30));
        const unsigned kind=fault==21?2:1,first=3u-kind;
        // Real source-only IOS service completes the first transaction;
        // the second guest construction is still synthetic.
        constexpr uint32_t first_req=0x100u,first_path=0x400u;
        auto& ram=host.physical_ram();
        const std::string_view old=first==1?"/dev/stm/immediate":"/dev/stm/eventhook";
        for(unsigned i=0;i<old.size();++i)ram.write8(first_path+i,uint8_t(old[i]));
        ram.write8(first_path+uint32_t(old.size()),0);
        ram.write32(first_req,StmIos::Open);ram.write32(first_req+12u,first_path);
        need(host.write32(IosBus::IPC+M::PPCMSG,first_req)&&host.write32(IosBus::IPC+M::PPCCTRL,0x31));
        auto ack=host.service_at_guest_boundary(0x8032u);
        need(ack&&ack->progress==StmIos::Pump::Ack);
        need(host.write32(IosBus::IPC+M::PPCCTRL,0x30u|M::Y2)&&host.write32(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC));
        auto reply=host.service_at_guest_boundary(0x8032u);
        need(reply&&reply->progress==StmIos::Pump::Replied&&ram.read32(first_req+4u)==0);
        need(host.write32(IosBus::IPC+M::PPCCTRL,0x30u|M::Y1)&&host.write32(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC));
        need(host.serviced_steps()==2u&&B::is_open(0u,first==1?StmIos::Device::Immediate:StmIos::Device::Event));
        OpenTransactionEpoch epoch(first),cold,wrong(kind);
        auto snap=B::cold_snapshot();need(snap&&epoch.quiet(*snap)&&!cold.quiet(*snap)&&!wrong.quiet(*snap));
        need(c.open_cache_range.begin(c,path,19));
        c.open_cache_range.on_flush(path&~31u);++c.guest_flush_count;c.guest_last_flush=path&~31u;
        need(c.open_cache_range.ready_sc(c)&&c.open_cache_range.finish(c));
        const std::string_view str=kind==1?"/dev/stm/immediate":"/dev/stm/eventhook";
        for(unsigned i=0;i<str.size();++i)m.write8(path+i,uint8_t(str[i]));
        m.write32(I::Lo,lo);m.write32(I::Hi,0x90010000);m.write32(I::IrqGlobal,I::Table);m.write32(I::MaskA,0xf7fff7e0);
        m.write8(lo-1,0xaa);m.write8(lo+size,0xbb);
        for(auto x:{e.entry,e.profile,e.disable,e.restore,e.flush,e.submit}){m.write32(x.pc,x.entry_word);m.write32(x.lr-4,x.branch_word);}
        m.write32(W::Alloc,e.alloc_word);m.write32(R::Call,e.sc_word);m.write32(R::Resume,0x4e800020);m.write32(R::Caller,e.flush_return_word);
        W w(e,first);R route(bytes,R::Caller,first);
        if(fault==1)c.gpr[4]=1;
        if(fault==2)m.write8(path,0);
        if(fault==3)cause.store(0x40);
        const bool b0=fault>=1&&fault<=3;
        need(w.begin_second(c,kind,fault==4?32u:size)==!(b0||fault==4));if(b0||fault==4){++bad;continue;}
        c.gpr[1]-=32;
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;c.inst_count+=10;};
        enter(e.profile);if(fault==5)c.lr+=4;
        need(w.observe(c.pc,c,route)==(fault!=5));if(fault==5){++bad;continue;}
        c.pc=W::Alloc;c.inst_count+=1;c.gpr[4]=fault==6?32u:64u;
        need(w.observe(c.pc,c,route)==(fault!=6));if(fault==6){++bad;continue;}
        enter(e.disable);if(fault==7)c.msr&=~0x8000u;
        need(w.observe(c.pc,c,route)==(fault!=7));if(fault==7){++bad;continue;}
        enter(e.restore);c.msr&=~0x8000u;c.gpr[3]=fault==8?0u:1u;
        need(w.observe(c.pc,c,route)==(fault!=8));if(fault==8){++bad;continue;}
        enter(e.flush);c.msr|=0x8000u;c.gpr[3]=path;c.gpr[4]=fault==9?1u:uint32_t(str.size()+1);
        if(fault==10)m.write32(I::Table+4,1);
        need(w.observe(c.pc,c,route)==(fault!=9&&fault!=10));if(fault==9||fault==10){++bad;continue;}
        c.open_cache_range.on_flush((path&~31u)+(fault==12?32u:0u));
        c.pc=R::Call;c.inst_count+=10;c.guest_flush_count+=fault==11?2u:1u;c.guest_last_flush=(path&~31u)+(fault==12?32u:0u);
        need(w.observe(c.pc,c,route)==(fault!=11&&fault!=12));if(fault==11||fault==12){++bad;continue;}
        ++c.inst_count;
        need(route.dispatch(c,[&](Cpu& cpu){
            need(route.vector_trace(R::Vector,cpu));cpu.gpr[9]=cpu.hid0;cpu.gpr[10]=cpu.hid0|8;
            cpu.inst_count+=7;cpu.pc=cpu.srr0;cpu.msr=cpu.srr1;
        },[](const Cpu&,const auto&,uint32_t){return true;}));
        c.pc=R::Caller;c.inst_count+=1;if(fault==13)c.lr+=4;
        need(w.observe(c.pc,c,route)==(fault!=13));if(fault==13){++bad;continue;}
        enter(e.submit);c.gpr[3]=fault==14?lo+size-4u:fault==15?0x500000a0u:req;
        m.write32(req,fault==16?2u:1u);m.write32(req+12,fault==17?path+4:path&0x3fffffffu);m.write32(req+16,fault==18?1u:0u);
        if(fault==19)m.write8(lo+size,0);
        if(fault==20)need(B::write32(IosBus::IPC+M::PPCMSG,0x100));
        const bool ok=fault==0||fault==21;
        need(w.observe(c.pc,c,route)==ok);
        if(ok){need(w.stage()==9&&w.request()==req&&host.serviced_steps()==2);++good;}else ++bad;
    }
    std::cout<<"V1361_SECOND_REQUEST synthetic=1 stages=9 positive="<<good<<" refusal="<<bad<<" request=1 first_fd_held=1 prior_steps=2 new_steps=0 boot_verified=0\n";
}
