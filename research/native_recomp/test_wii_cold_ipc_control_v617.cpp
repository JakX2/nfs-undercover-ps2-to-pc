#include "wii_native_ios_binding.h"
#include <array>
#include <iostream>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using B=NativeIosBinding;using I=IosBus;using M=IpcMailbox;using H=HollywoodIrq;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V617 line "+std::to_string(l.line()));
}
template<class F>static void refuse(F f){bool bad=false;try{f();}catch(const std::runtime_error&){bad=true;}need(bad);}
int main(){
    std::array<uint8_t,4096> ram{},mem2{};
    std::atomic<uint32_t> cause{0x100},mask{H::PI_HOLLYWOOD};
    need(!B::begin_cold_control(0x30)&&!B::finish_cold_control());
    for(uint32_t base:{I::IPC,I::MIRROR})for(uint32_t alias:{0u,0x80000000u,0xc0000000u}){
        NativeIosTransport host(ram,mem2,cause,mask);B bind(host);
        need(B::write32(base+H::PPC_MASK,H::IPC_PPC));
        need(B::begin_cold_control(0x36));
        need(B::write32(alias+base+M::PPCCTRL,0x36));
        need(B::finish_cold_control());
        auto s=host.cold_ipc_snapshot();
        need(s.control==0x30&&!s.queued&&!s.replies&&!s.event&&!s.steps&&s.pi_cause==0x100);
        // Normal request submission remains enabled after successful proof.
        need(B::write32(base+M::PPCMSG,0x100));
        need(B::write32(base+M::PPCCTRL,0x31)&&host.cold_ipc_snapshot().queued);
    }
    for(unsigned fault=0;fault<12;++fault){
        cause=0x100;mask=H::PI_HOLLYWOOD;
        NativeIosTransport host(ram,mem2,cause,mask);B bind(host);
        if(fault==0){need(!B::begin_cold_control(0));continue;}
        if(fault==1){need(!B::begin_cold_control(0x31));continue;}
        if(fault==2){need(!B::begin_cold_control(0x70));continue;}
        if(fault==3){B::write32(I::IPC+M::PPCCTRL,0x31);need(!B::begin_cold_control(0x30));continue;}
        if(fault==4){mask=0x100;need(!B::begin_cold_control(0x30));continue;}
        need(B::begin_cold_control(0x30));
        if(fault==5){need(!B::finish_cold_control());continue;}
        if(fault==6){need(!B::begin_cold_control(0x30));continue;}
        if(fault==7){refuse([&]{B::write32(I::IPC+M::PPCCTRL,0x20);});need(host.cold_ipc_snapshot().control==0);continue;}
        if(fault==8){refuse([&]{B::write32(I::IPC+M::PPCMSG,0x100);});need(host.cold_ipc_snapshot().ppc==0);continue;}
        need(B::write32(I::IPC+M::PPCCTRL,0x30));
        if(fault==9){refuse([&]{B::write32(I::IPC+M::PPCCTRL,0x30);});need(!B::finish_cold_control());continue;}
        if(fault==10){cause=0x200;need(!B::finish_cold_control());continue;}
        if(fault==11){host.write32(I::IPC+M::PPCMSG,0x100);need(!B::finish_cold_control());continue;}
    }
    std::cout<<"V617_IPC_CONTROL aliases=6 writes=6 refusal=12 native_transport=1 queued=0 serviced=0 actual_ios=0\n";
}
