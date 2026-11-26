#include "wii_cold_open_reply_gate_v1253.h"
#include <iostream>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V1367 gate line "+std::to_string(l.line()));
}
int main(){
    constexpr uint32_t req=0x10000100u,path=0x400u,en=M::IY1|M::IY2,other=1u<<8;
    unsigned positive=0,refused=0;
    for(unsigned lane=0;lane<=19;++lane){
        std::array<uint8_t,4096> mem1{},mem2{};
        std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};
        NativeIosTransport host(mem1,mem2,cause,mask);B binding(host);
        auto& ram=host.physical_ram();
        const unsigned kind=lane==19?2u:1u,first=3u-kind;
        const std::string_view old=first==1u?"/dev/stm/immediate":"/dev/stm/eventhook";
        for(unsigned i=0;i<old.size();++i)ram.write8(path+i,uint8_t(old[i]));
        ram.write8(path+uint32_t(old.size()),0);
        ram.write32(req,S::Open);ram.write32(req+12u,path);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        need(B::write32(IosBus::IPC+M::PPCMSG,req)&&B::write32(IosBus::IPC+M::PPCCTRL,en|M::X1));
        auto first_ack=B::service_at_guest_boundary(0);need(first_ack&&first_ack->progress==S::Pump::Ack);
        need(B::write32(IosBus::IPC+M::PPCCTRL,en|M::Y2)&&B::write32(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC));
        auto first_reply=B::service_at_guest_boundary(0);need(first_reply&&first_reply->progress==S::Pump::Replied&&ram.read32(req+4u)==0u);
        need(B::write32(IosBus::IPC+M::PPCCTRL,en|M::Y1)&&B::write32(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC));
        need(host.serviced_steps()==2u);
        const std::string_view name=kind==1u?"/dev/stm/immediate":"/dev/stm/eventhook";
        for(unsigned i=0;i<name.size();++i)ram.write8(path+i,uint8_t(name[i]));
        ram.write8(path+uint32_t(name.size()),0);
        ram.write32(req,S::Open);ram.write32(req+12u,path);ram.write32(req+16u,0u);
        ram.write32(req+20u,0x12345678u);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        need(B::write32(IosBus::IPC+M::PPCMSG,req));
        need(B::write32(IosBus::MIRROR+M::PPCCTRL,en|M::X1));
        const auto ack=B::service_at_guest_boundary(0);
        need(ack&&ack->progress==S::Pump::Ack&&host.serviced_steps()==3u);
        ColdOpenReplyGate gate(first);
        ColdOpenReplyGate wrong(3u-first),cold;
        need(!wrong.begin(req,kind,true)&&!cold.begin(req,kind,true));
        if(lane==1)ram.write32(req+16u,1u);
        if(lane==2)ram.write8(path,0);
        if(lane==3)mask.fetch_or(other);
        if(lane==4)need(B::write32(IosBus::IPC+M::PPCCTRL,en|M::Y2));
        const bool begin_ok=lane<1||lane>=7;
        need(gate.begin(lane==5?req+32u:req,lane==6?2u:kind,true)==begin_ok);
        if(!begin_ok){need(gate.failure()==1&&host.serviced_steps()==3);++refused;continue;}
        need(gate.stage()==1&&gate.boundary(true));
        if(lane==7){need(!gate.publish(0,true)&&host.serviced_steps()==3);++refused;continue;}
        if(lane==8)ram.write32(req+20u,0);
        if(lane==9){need(!gate.write(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC,0,true));++refused;continue;}
        bool ok=gate.write(IosBus::MIRROR+M::PPCCTRL,en|M::Y2|(lane==10?M::X1:0u),lane==11?0x8000u:0u,lane!=12);
        need(ok==!(lane==8||(lane>=10&&lane<=12)));
        if(!ok){need(gate.failure()==2&&host.serviced_steps()==3);++refused;continue;}
        need(gate.stage()==2&&(cause.load()&H::PI_HOLLYWOOD));
        if(lane==13){need(!gate.publish(0,true));++refused;continue;}
        if(lane==14)need(B::write32(IosBus::IPC+M::PPCMSG,req+32u));
        ok=gate.write(IosBus::IPC+H::PPC_FLAG,lane==15?0u:H::IPC_PPC,0,true);
        need(ok==!(lane==14||lane==15));
        if(!ok){need(gate.failure()==2&&host.serviced_steps()==3);++refused;continue;}
        need(gate.stage()==3&&cause.load()==other);
        if(lane==16)ram.write32(req+4u,77);
        ok=gate.publish(lane==17?0x8000u:0u,lane!=18);
        const bool good=lane==0||lane==19;
        need(ok==good);
        if(!good){need(gate.failure()==3&&host.serviced_steps()==3);++refused;continue;}
        need(gate.stage()==4&&gate.reply_pending(true)&&host.serviced_steps()==4u);
        need(ram.read32(req)==S::Reply&&ram.read32(req+4u)==1&&ram.read32(req+8u)==S::Open&&
             ram.read32(req+20u)==0x12345678u&&cause.load()==(other|H::PI_HOLLYWOOD));
        ram.write32(req+20u,0);need(!gate.reply_pending(true));ram.write32(req+20u,0x12345678u);
        need(gate.reply_pending(true)&&!gate.publish(0,true)&&host.serviced_steps()==4u);++positive;
    }
    need(positive==2&&refused==18);
    std::cout<<"V1367_SECOND_REPLY_GATE positive=2 refused=18 ack_w1c=1 latch_w1c=1 native_reply=1 second_fd=1 steps=4 other_pi=1 wakeup=0 original_execution=0 boot_verified=0\n";
}
