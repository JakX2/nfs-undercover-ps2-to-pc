#include "wii_native_ios_binding.h"
#include <array>
#include <atomic>
#include <iostream>
#include <thread>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
using Bind=NativeIosBinding;
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
template<class F>static void rejects(F f){bool threw=false;try{f();}catch(const std::runtime_error&){threw=true;}need(threw,"unsupported access reached legacy IOS");}
int main(){
    std::array<uint8_t,8192> one{},two{};
    std::atomic<uint32_t> cause{0u},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);
    need(!Bind::active()&&!Bind::read32(B::IPC)&&!Bind::write32(B::IPC,0u)&&!Bind::service_at_guest_boundary(B::MSR_EE),"inactive binding changed legacy behavior");
    {
        Bind scope(host);need(Bind::active(),"binding not installed");
        bool nested=false;try{Bind duplicate(host);}catch(const std::logic_error&){nested=true;}
        need(nested&&Bind::active(),"nested binding clobbered active transport");
        bool foreign=false;std::thread other([&]{foreign=Bind::active()||Bind::read32(B::IPC).has_value();});other.join();
        need(!foreign,"binding escaped CPU thread");
        need(!Bind::read32(B::PI_CAUSE)&&!Bind::write32(B::PI_MASK,0u),"PI ownership transferred from host");
        need(!Bind::read32(0xcc008000u)&&!Bind::write32(0xcc008000u,0u),"GX ownership transferred");
        for(uint32_t a:{B::IPC+M::ARMCTRL,B::IPC+0x10u,B::MIRROR+1u}){
            rejects([&]{(void)Bind::read32(a);});rejects([&]{(void)Bind::write32(a,0u);});rejects([&]{Bind::reject_subword(a);});
        }
        for(uint32_t a:{B::IPC,B::MIRROR,0xcd000000u,0x8d800000u}){
            Bind::check_cpu_access(a,4u,true);
            rejects([&]{Bind::check_cpu_access(a,1u,false);});
            rejects([&]{Bind::check_cpu_access(a,8u,false);});
            rejects([&]{Bind::check_cpu_access(a,4u,false);});
            rejects([&]{Bind::check_cpu_access(a+1u,4u,true);});
            rejects([&]{Bind::check_cpu_access(a-1u,2u,false);});
        }
        rejects([&]{Bind::check_cpu_access(0x4d000000u,4u,true);});
        Bind::check_cpu_access(0x80000700u,8u,false);
        Bind::check_cpu_access(0xcc008000u,1u,false);
        constexpr uint32_t req=0x100u,path=0x400u,en=M::IY1|M::IY2;
        auto& ram=host.physical_ram();const std::string_view dev="/dev/stm/immediate";
        for(std::size_t i=0;i<dev.size();++i)ram.write8(path+uint32_t(i),uint8_t(dev[i]));
        ram.write32(req,S::Open);ram.write32(req+12u,path);
        need(Bind::write32(B::MIRROR+H::PPC_MASK,H::IPC_PPC)&&Bind::write32(B::IPC+M::PPCMSG,req)&&Bind::write32(0xcd800004u,en|M::X1),"register route missing");
        need(host.serviced_steps()==0u&&ram.read32(req)==S::Open,"MMIO pumped IOS");
        auto ack=Bind::service_at_guest_boundary(0u);need(ack&&ack->progress==S::Pump::Ack&&!ack->guest_exception_ready,"explicit ACK failed");
        cause.store(0u);Bind::refresh_pi(0xcc003000u);need(cause.load()==H::PI_HOLLYWOOD,"PI-side clear suppressed source");
        need(Bind::write32(B::IPC+M::PPCCTRL,en|M::Y2)&&Bind::write32(B::MIRROR+H::PPC_FLAG,H::IPC_PPC),"Y2 clear failed");
        auto reply=Bind::service_at_guest_boundary(B::MSR_EE);need(reply&&reply->progress==S::Pump::Replied&&ram.read32(req)==S::Reply,"native reply failed");
        need(Bind::write32(B::IPC+M::PPCCTRL,en|M::Y1)&&Bind::write32(B::MIRROR+H::PPC_FLAG,H::IPC_PPC),"Y1 clear failed");
    }
    need(!Bind::active()&&!Bind::read32(B::IPC)&&!Bind::write32(B::IPC,0u),"scope leaked active native route");
    {Bind another(host);need(Bind::active(),"rebind failed");}
    std::cout<<"PASS: native IOS scoped thread binding and strict MMIO ownership\n";
}
