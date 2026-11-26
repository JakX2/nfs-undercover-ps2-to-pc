#include "wii_cold_open_reply_gate_v1253.h"
#include <iostream>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V1253 line "+std::to_string(l.line()));
}
int main(){
    constexpr uint32_t req=0x10000100u,path=0x400u,en=M::IY1|M::IY2,other=1u<<8;
    unsigned positive=0,refused=0;
    for(unsigned lane=0;lane<=19;++lane){
        std::array<uint8_t,4096> mem1{},mem2{};
        std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};
        NativeIosTransport host(mem1,mem2,cause,mask);B binding(host);
        auto& ram=host.physical_ram();
        const unsigned kind=lane==19?2u:1u;
        const std::string_view name=kind==1u?"/dev/stm/immediate":"/dev/stm/eventhook";
        for(unsigned i=0;i<name.size();++i)ram.write8(path+i,uint8_t(name[i]));
        ram.write32(req,S::Open);ram.write32(req+12u,path);ram.write32(req+16u,0u);
        ram.write32(req+20u,0x12345678u);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        need(B::write32(IosBus::IPC+M::PPCMSG,req));
        need(B::write32(IosBus::MIRROR+M::PPCCTRL,en|M::X1));
        const auto ack=B::service_at_guest_boundary(0);
        need(ack&&ack->progress==S::Pump::Ack&&host.serviced_steps()==1u);
        ColdOpenReplyGate gate;
        if(lane==1)ram.write32(req+16u,1u);
        if(lane==2)ram.write8(path,0);
        if(lane==3)mask.fetch_or(other);
        if(lane==4)need(B::write32(IosBus::IPC+M::PPCCTRL,en|M::Y2));
        const bool begin_ok=lane<1||lane>=7;
        need(gate.begin(lane==5?req+32u:req,lane==6?2u:kind,true)==begin_ok);
        if(!begin_ok){need(gate.failure()==1&&host.serviced_steps()==1);++refused;continue;}
        need(gate.stage()==1&&gate.boundary(true));
        if(lane==7){need(!gate.publish(0,true)&&host.serviced_steps()==1);++refused;continue;}
        if(lane==8)ram.write32(req+20u,0);
        if(lane==9){need(!gate.write(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC,0,true));++refused;continue;}
        bool ok=gate.write(IosBus::MIRROR+M::PPCCTRL,en|M::Y2|(lane==10?M::X1:0u),lane==11?0x8000u:0u,lane!=12);
        need(ok==!(lane==8||(lane>=10&&lane<=12)));
        if(!ok){need(gate.failure()==2&&host.serviced_steps()==1);++refused;continue;}
        need(gate.stage()==2&&(cause.load()&H::PI_HOLLYWOOD));
        if(lane==13){need(!gate.publish(0,true));++refused;continue;}
        if(lane==14)need(B::write32(IosBus::IPC+M::PPCMSG,req+32u));
        ok=gate.write(IosBus::IPC+H::PPC_FLAG,lane==15?0u:H::IPC_PPC,0,true);
        need(ok==!(lane==14||lane==15));
        if(!ok){need(gate.failure()==2&&host.serviced_steps()==1);++refused;continue;}
        need(gate.stage()==3&&cause.load()==other);
        if(lane==16)ram.write32(req+4u,77);
        ok=gate.publish(lane==17?0x8000u:0u,lane!=18);
        const bool good=lane==0||lane==19;
        need(ok==good);
        if(!good){need(gate.failure()==3&&host.serviced_steps()==1);++refused;continue;}
        need(gate.stage()==4&&gate.reply_pending(true)&&host.serviced_steps()==2u);
        need(ram.read32(req)==S::Reply&&ram.read32(req+4u)==0&&ram.read32(req+8u)==S::Open&&
             ram.read32(req+20u)==0x12345678u&&cause.load()==(other|H::PI_HOLLYWOOD));
        ram.write32(req+20u,0);need(!gate.reply_pending(true));ram.write32(req+20u,0x12345678u);
        need(gate.reply_pending(true)&&!gate.publish(0,true)&&host.serviced_steps()==2u);++positive;
    }
    need(positive==2&&refused==18);
    std::cout<<"V1253_REPLY_GATE positive=2 refused=18 ack_w1c=1 latch_w1c=1 native_reply=1 other_pi=1 wakeup=0 original_execution=0 boot_verified=0\n";
}
