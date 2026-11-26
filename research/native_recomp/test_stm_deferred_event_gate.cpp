#include "wii_stm_deferred_event_gate.h"
#include <array>
#include <atomic>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=NativeIosBinding;using I=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
constexpr uint32_t req=0x100u,path=0x400u,out=0x800u,en=M::IY1|M::IY2,other=0x100u;
static void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
static void wr(uint32_t a,uint32_t v){need(B::write32(I::IPC+a,v),"MMIO");}
static void open(NativeIosTransport& host,std::string_view name,unsigned fd){
    auto& ram=host.physical_ram();
    for(unsigned i=0;i<name.size();++i)ram.write8(path+i,uint8_t(name[i]));
    ram.write8(path+uint32_t(name.size()),0);
    ram.write32(req,S::Open);ram.write32(req+12,path);ram.write32(req+16,0);
    wr(M::PPCMSG,req);wr(M::PPCCTRL,en|M::X1);
    auto a=B::service_at_guest_boundary(0);need(a&&a->progress==S::Pump::Ack,"open ACK");
    wr(M::PPCCTRL,en|M::Y2);wr(H::PPC_FLAG,H::IPC_PPC);
    auto b=B::service_at_guest_boundary(0);need(b&&b->progress==S::Pump::Replied&&ram.read32(req+4)==fd,"open reply");
    wr(M::PPCCTRL,en|M::Y1);wr(H::PPC_FLAG,H::IPC_PPC);
}
static void trial(unsigned first,unsigned fault){
    std::array<uint8_t,8192> one{},two{};
    std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);B bind(host);auto& ram=host.physical_ram();
    wr(H::PPC_MASK,H::IPC_PPC);wr(M::PPCCTRL,en);
    open(host,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    open(host,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    need(host.serviced_steps()==4,"two opens");
    uint32_t fd=first==2?0u:1u;
    for(unsigned i=0;i<16;++i)ram.write32(req+4*i,0xdead0000u+i);
    ram.write32(req,S::Ioctl);ram.write32(req+8,fd);ram.write32(req+12,S::EventHook);
    ram.write32(req+16,0);ram.write32(req+20,0);ram.write32(req+24,out);ram.write32(req+28,32);
    for(unsigned i=0;i<32;++i)ram.write8(out+i,0xa5);
    StmDeferredEventGate gate;
    auto args=StmDeferredEventGate::Arguments{req,fd,0,0,out,32};
    if(fault==2)args.fd^=1u;
    if(fault==3)ram.write32(req,S::Open);
    if(fault==4){args.output=req;ram.write32(req+24,req);}
    bool begun=gate.begin(args,fault==1?3u-first:first,fault!=5);
    if(fault>=1&&fault<=5){need(!begun&&gate.failure()==1&&host.serviced_steps()==4,"begin refusal");return;}
    need(begun,"begin");
    if(fault==6){need(!gate.accept(0,true)&&host.serviced_steps()==4,"early service");return;}
    bool msg=gate.submit_write(I::IPC+M::PPCMSG,fault==7?req+32:req,0,true);
    if(fault==7){need(!msg&&host.serviced_steps()==4,"wrong msg");return;}need(msg,"msg");
    bool ctl=gate.submit_write(I::MIRROR+M::PPCCTRL,fault==8?M::X1:en|M::X1,0,true);
    if(fault==8){need(!ctl&&host.serviced_steps()==4,"wrong control");return;}need(ctl,"control");
    if(fault==9)ram.write32(req+60,0);
    if(fault==10)ram.write8(out+7,0);
    bool accepted=gate.accept(fault==11?I::MSR_EE:0,true);
    if(fault>=9&&fault<=11){need(!accepted&&host.serviced_steps()==4,"pre-service refusal");return;}
    need(accepted&&host.services().event_pending()&&host.serviced_steps()==5,"deferred service");
    need(ram.read32(req)==S::Ioctl,"unsolicited reply");
    if(fault==12){need(!gate.ack_write(I::IPC+H::PPC_FLAG,H::IPC_PPC,0,true),"ACK order");return;}
    if(fault==13){need(!gate.ack_write(I::IPC+M::PPCCTRL,en|M::Y2,I::MSR_EE,true),"unmasked ACK");return;}
    if(fault==14){need(!gate.ack_write(I::IPC+M::PPCCTRL,en|M::Y2,0,false),"unauthenticated ACK");return;}
    need(gate.ack_write(I::IPC+M::PPCCTRL,en|M::Y2,0,true),"Y2 clear");
    if(fault==15){need(!gate.ack_write(I::IPC+H::PPC_FLAG,0,0,true),"bad flag");return;}
    need(gate.ack_write(I::MIRROR+H::PPC_FLAG,H::IPC_PPC,0,true)&&gate.completed(true),"ACK finish");
    need(!B::service_at_guest_boundary(I::MSR_EE)&&gate.completed(true)&&host.serviced_steps()==5,"idle service published reply");
    need(cause.load()==other&&host.services().event_pending()&&ram.read32(req)==S::Ioctl,"pending event state");
    if(fault==16){ram.write8(out,0);need(!gate.completed(true),"output mutation accepted");}
}
int main(){for(unsigned first:{1u,2u})for(unsigned f=0;f<=16;++f)trial(first,f);
    std::cout<<"PASS: STM deferred event contract 34/34 (both descriptor orders, native broker, no unsolicited reply)\n";}
