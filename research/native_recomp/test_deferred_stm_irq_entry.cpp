#include "wii_deferred_stm_irq_entry.h"
#include <cassert>
#include <atomic>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=NativeIosBinding;using I=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
constexpr uint32_t Base=0x80000000u,Req=0x100u,Path=0x400u,Out=0x800u,Resume=Base+0x900u,
    Context=Base+0x1000u,en=M::IY1|M::IY2;
struct Mem{
    std::array<uint8_t,8192> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=Base&&a-Base<ram.size()?ram.data()+a-Base:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint16_t read16(uint32_t a){return uint16_t((read8(a)<<8)|read8(a+1));}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=Resume+4,ctr=1,xer=2,msr=0x8032,srr0=3,srr1=4,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void wr(uint32_t off,uint32_t v){assert(B::write32(I::IPC+off,v));}
static void open(Cpu& c,std::string_view path,unsigned fd){
    for(unsigned i=0;i<path.size();++i)*c.mmu.get_ptr(Base+Path+i)=uint8_t(path[i]);
    *c.mmu.get_ptr(Base+Path+uint32_t(path.size()))=0;
    c.mmu.write32(Base+Req,S::Open);c.mmu.write32(Base+Req+12,Path);c.mmu.write32(Base+Req+16,0);
    wr(M::PPCMSG,Req);wr(M::PPCCTRL,en|M::X1);
    auto a=B::service_at_guest_boundary(0);assert(a&&a->progress==S::Pump::Ack);
    wr(M::PPCCTRL,en|M::Y2);wr(H::PPC_FLAG,H::IPC_PPC);
    auto b=B::service_at_guest_boundary(0);assert(b&&b->progress==S::Pump::Replied&&c.mmu.read32(Base+Req+4)==fd);
    wr(M::PPCCTRL,en|M::Y1);wr(H::PPC_FLAG,H::IPC_PPC);
}
static void trial(unsigned first,unsigned fault){
    Cpu c;std::array<uint8_t,8192> two{};std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(c.mmu.ram,two,cause,mask);B bind(host);
    wr(H::PPC_MASK,H::IPC_PPC);wr(M::PPCCTRL,en);
    open(c,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    open(c,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    uint32_t fd=first==2?0u:1u;
    c.mmu.write32(Base+Req,S::Ioctl);c.mmu.write32(Base+Req+8,fd);c.mmu.write32(Base+Req+12,S::EventHook);
    c.mmu.write32(Base+Req+16,0);c.mmu.write32(Base+Req+20,0);c.mmu.write32(Base+Req+24,Out);c.mmu.write32(Base+Req+28,32);
    StmDeferredEventGate gate;
    assert(gate.begin({Req,fd,0,0,Out,32},first,true)&&gate.submit_write(I::IPC+M::PPCMSG,Req,0,true)&&
           gate.submit_write(I::IPC+M::PPCCTRL,en|M::X1,0,true));
    if(fault!=1)assert(gate.accept(0,true));
    c.mmu.write32(Base+0xc0,Context&0x3fffffffu);c.mmu.write32(Base+0xd4,Context);c.mmu.write32(Base+0xe4,Context);
    c.mmu.write32(Context+712,2u<<16);c.mmu.write32(Resume,0x60000000u);
    std::array<uint8_t,4> vector{0x60,0,0,0};
    for(unsigned i=0;i<vector.size();++i)*c.mmu.get_ptr(ExternalVector+i)=vector[i];
    if(fault==2)c.msr&=~0x8000u;
    if(fault==3)c.pc+=4;
    if(fault==4)c.mmu.write32(Context+712,4u<<16);
    if(fault==5)c.mmu.write32(Base+0xe4,Context+8u);
    if(fault==6)c.mmu.write32(ExternalVector,0);
    if(fault==7)c.dispatch_saved_ctx=1;
    if(fault==8)c.mmu.write32(Base+Req+60,1);
    if(fault==9)c.in_callback=true;
    if(fault==10)c.msr|=0x40u;
    if(fault==11)cause.fetch_or(0x100u),mask.fetch_or(0x100u);
    if(fault==12)c.mmu.write32(Resume,0);
    ExternalReturnWitness frame;
    const auto pc=c.pc,msr=c.msr,srr0=c.srr0,srr1=c.srr1;
    const auto tick=c.inst_count;const auto prior=host.cold_ipc_snapshot();
    bool ok=enter_deferred_stm_irq(c,host,gate,frame,vector,fault==13?Req+32:Req,Context,Resume,0x60000000u,fault!=14);
    if(fault){assert(!ok&&frame.stage()==0u&&c.pc==pc&&c.msr==msr&&c.srr0==srr0&&c.srr1==srr1&&c.inst_count==tick&&
                   same_scheduler_ipc_snapshot(prior,host.cold_ipc_snapshot()));return;}
    assert(ok&&frame.stage()==1u&&c.pc==ExternalVector&&c.srr0==Resume&&!(c.msr&0x8000u)&&
           gate.deferred_held(true)&&host.serviced_steps()==5u&&host.services().event_pending());
}
int main(){for(unsigned first:{1u,2u})for(unsigned f=0;f<=14;++f)trial(first,f);
    std::cout<<"DEFERRED_STM_IRQ_ENTRY_TEST cases=30 original_execution=0\n";}
