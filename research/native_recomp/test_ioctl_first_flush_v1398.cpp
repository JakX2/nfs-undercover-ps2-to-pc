#include "wii_ioctl_first_flush_v1398.h"
#include <array>
#include <atomic>
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
using R=OpenScRoute;using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Mem{
    std::map<uint32_t,uint8_t> bytes;
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=0x81000000u&&a<0x81001000u?ram.data()+a-0x81000000u:nullptr;}
    uint8_t read8(uint32_t a){return bytes[a];}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(24-8*i));}
};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=R::Call,lr=0,msr=0x32,ctr=7,hid0=0x100,srr0=0,srr1=0;
    uint32_t dispatch_saved_ctx=0,guest_sync_count=0,guest_isync_count=0;
    uint64_t inst_count=12;bool is_running=true,in_callback=false;
    uint32_t guest_flush_count=100,guest_last_flush=0;
    OpenCacheRangeTrace open_cache_range;
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
static void trial(unsigned first,unsigned kind,bool empty,unsigned fault){
    std::array<uint8_t,8192> one{},two{};
    std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);NativeIosBinding bind(host);
    wr(H::PPC_MASK,H::IPC_PPC);wr(M::PPCCTRL,M::IY1|M::IY2);
    open(host,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    open(host,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    Cpu c;constexpr uint32_t F=0x805222c0u,P=0x805222e4u,N=0x60000000u,A=0x81000000u;
    c.pc=F;c.lr=kind==1?R::EventInputCaller:kind==2?R::EventOutputCaller:R::SubmitCaller;
    c.gpr[1]=0x81000800u;c.gpr[3]=empty?0u:kind==3?A:A+16u;c.gpr[4]=empty?0u:kind==3?64u:48u;
    c.mmu.write32(F,N);c.mmu.write32(c.lr,N);c.mmu.write32(R::Call,0x44000002u);c.mmu.write32(R::Resume,0x4e800020u);
    assert(c.open_cache_range.begin(c,A,1));
    c.open_cache_range.on_flush(A);++c.guest_flush_count;c.guest_last_flush=A;
    assert(c.open_cache_range.ready_sc(c)&&c.open_cache_range.finish(c));
    std::array<uint32_t,1> polls{P};std::array<uint8_t,28> bytes{};
    IoctlFirstFlushWitness w({N,N,N,polls,fault==9?0u:N},bytes,first,fault==11?4u:kind);
    if(fault==1)c.msr|=0x8000u;
    if(fault==2)c.lr=R::Caller;
    if(fault==3)c.gpr[4]=4097;
    if(fault==10)c.gpr[4]=16;
    if(fault==12)c.gpr[3]+=16;
    bool ok=w.begin(c,true);
    if((fault>=1&&fault<=3)||(kind==3&&empty)||fault>=9){assert(!ok);return;}assert(ok);
    if(!empty||fault==4){
        c.open_cache_range.on_flush(A);++c.guest_flush_count;c.guest_last_flush=A;
        if(!empty&&fault!=4){c.open_cache_range.on_flush(A+32);++c.guest_flush_count;c.guest_last_flush=A+32;}
    }
    c.pc=P;++c.inst_count;
    if(fault==5){++c.pc;assert(!w.poll(c,true));return;}
    assert(w.poll(c,true));
    c.pc=R::Call;++c.inst_count;ok=w.trace(c,c.pc,true);
    if(fault==4){assert(!ok);return;}assert(ok);
    ++c.inst_count;
    auto verify=[](const Cpu& cpu,const auto& gp,uint32_t hid){
        for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
        return true;
    };
    ok=w.dispatch(c,true,[&](Cpu& cpu){
        assert(w.trace(cpu,R::Vector,true));cpu.gpr[9]=cpu.hid0;cpu.gpr[10]=cpu.hid0|8u;
        cpu.inst_count+=7;cpu.pc=cpu.srr0;cpu.msr=cpu.srr1;
        if(fault==6)cpu.msr^=0x8000u;
    },verify);
    if(fault==6){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));
    if(fault==7){assert(!w.poll(c,true));return;}
    c.pc=c.lr;++c.inst_count;
    if(fault==8)c.mmu.write32(c.pc,0);
    ok=w.trace(c,c.pc,true);
    if(fault==8){assert(!ok);return;}assert(ok);
    assert(w.returned(c,true)&&w.lines()==(empty?0u:2u)&&host.serviced_steps()==4u);
}
int main(){
    for(unsigned first:{1u,2u}){
        for(unsigned kind:{1u,2u,3u})for(bool empty:{false,true}){
            for(unsigned fault=0;fault<=8;++fault)trial(first,kind,empty,fault);
        }
        for(unsigned fault=9;fault<=12;++fault)trial(first,3,false,fault);
    }
    std::cout<<"V1398_FLUSH_TEST cases=116 original_execution=0\n";
}
