#include "wii_open_sc_route_v637.h"
#include <array>
#include <atomic>
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
using R=OpenScRoute;using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Mem{
    std::map<uint32_t,uint8_t> bytes;
    uint8_t read8(uint32_t a){return bytes[a];}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(24-8*i));}
};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=R::Call,lr=0,msr=0x32,ctr=7,hid0=0x100,srr0=0,srr1=0;
    uint32_t dispatch_saved_ctx=0,guest_sync_count=0,guest_isync_count=0;
    uint64_t inst_count=12;bool is_running=true;
};
static void wr(uint32_t a,uint32_t v){assert(NativeIosBinding::write32(B::IPC+a,v));}
static void open(NativeIosTransport& host,std::string_view name,unsigned fd){
    constexpr uint32_t req=0x100,path=0x400,en=M::IY1|M::IY2;
    auto& ram=host.physical_ram();
    for(unsigned i=0;i<name.size();++i)ram.write8(path+i,uint8_t(name[i]));
    ram.write8(path+uint32_t(name.size()),0);
    ram.write32(req,S::Open);ram.write32(req+12,path);ram.write32(req+16,0);
    wr(M::PPCMSG,req);wr(M::PPCCTRL,en|M::X1);
    auto a=NativeIosBinding::service_at_guest_boundary(0);assert(a&&a->progress==S::Pump::Ack);
    wr(M::PPCCTRL,en|M::Y2);wr(H::PPC_FLAG,H::IPC_PPC);
    auto b=NativeIosBinding::service_at_guest_boundary(0);assert(b&&b->progress==S::Pump::Replied&&ram.read32(req+4)==fd);
    wr(M::PPCCTRL,en|M::Y1);wr(H::PPC_FLAG,H::IPC_PPC);
}
static void trial(unsigned first,uint32_t caller,unsigned fault){
    std::array<uint8_t,8192> one{},two{};
    std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);NativeIosBinding bind(host);
    wr(H::PPC_MASK,H::IPC_PPC);wr(M::PPCCTRL,M::IY1|M::IY2);
    open(host,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    if(fault!=1)open(host,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    Cpu c;c.lr=caller;
    for(unsigned i=0;i<32;++i)c.gpr[i]=i+100;
    c.mmu.write32(R::Call,0x44000002);c.mmu.write32(R::Resume,0x4e800020);
    std::array<uint8_t,28> bytes{};unsigned called=0;bool rejected=false;
    try{
        R route(bytes,fault==2?R::Caller:caller,fault==3?3u-first:first,R::Mode::DeferredStm);
        if(fault==4)c.msr|=0x8000u;
        if(fault==5)cause.store(H::PI_HOLLYWOOD);
        if(fault==6)wr(M::PPCCTRL,M::IY2);
        if(fault==7)c.dispatch_saved_ctx=1;
        route.arm(R::Call,c);++c.inst_count;
        if(fault==8)wr(M::PPCMSG,0x800);
        if(fault==9)c.mmu.bytes[R::Vector]=1;
        if(fault==10)++c.inst_count;
        assert(route.dispatch(c,[&](Cpu& cpu){
            ++called;assert(route.vector_trace(R::Vector,cpu));cpu.gpr[9]=cpu.hid0;cpu.gpr[10]=cpu.hid0|8u;
            cpu.inst_count+=7;cpu.pc=cpu.srr0;cpu.msr=cpu.srr1;
            if(fault==11)cpu.msr^=0x8000u;
        },[](const Cpu& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        }));
        c.pc=caller;assert(route.returned(c)&&c.msr==0x32u&&host.serviced_steps()==4u);
        if(fault==12){c.lr+=4;assert(!route.returned(c));return;}
    }catch(const std::runtime_error& e){
        if(std::string_view(e.what())!="V637 open SC route rejected")throw;
        rejected=true;
    }
    assert(rejected==(fault!=0u));
    assert(called==(fault==0u||fault==11u?1u:0u));
    assert(host.serviced_steps()==(fault==1u?2u:4u));
}
int main(){
    for(unsigned first:{1u,2u})for(uint32_t caller:{R::EventInputCaller,R::EventOutputCaller,R::SubmitCaller})
        for(unsigned fault=0;fault<=12;++fault)trial(first,caller,fault);
    std::cout<<"V1384_DEFERRED_SC synthetic=1 cases=78 both_orders=1 callers=3 masked_rfi=1 original_execution=0\n";
}
