#include "wii_ios_yield_scheduler.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>

using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;

static void require(bool ok,const char* what){if(!ok)throw std::runtime_error(what);}
struct Ram final:IosMemory{
    std::array<uint8_t,0x2000> bytes{};
    bool valid(uint32_t a,uint32_t n)const override{return uint64_t(a)+n<=bytes.size();}
    uint8_t read8(uint32_t a)const override{return bytes.at(a);}
    void write8(uint32_t a,uint8_t x)override{bytes.at(a)=x;}
    void path(uint32_t p,std::string_view s){
        require(valid(p,uint32_t(s.size()+1)),"path not mapped");
        for(char ch:s)write8(p++,uint8_t(ch));
        write8(p,0);
    }
};
int main(){
    Ram ram;B bus(ram);IosYieldScheduler scheduler(bus);
    constexpr uint32_t request=0x100,event=0x180,name=0x300,event_output=0x500;
    constexpr uint32_t en=M::IY1|M::IY2;
    auto write=[&](uint32_t reg,uint32_t value){
        require(bus.write32(reg,value),"native hardware write refused");
    };
    auto read=[&](uint32_t reg)->uint32_t{
        auto result=bus.read32(reg);
        require(result.has_value(),"native hardware read refused");
        return *result;
    };
    auto request_submit=[&](uint32_t p,uint32_t cmd,uint32_t fd,uint32_t a=0,
                            uint32_t b=0,uint32_t c=0,uint32_t d=0,uint32_t e=0){
        const std::array<uint32_t,8> words{cmd,0u,fd,a,b,c,d,e};
        for(unsigned i=0;i<words.size();++i)ram.write32(p+i*4u,words[i]);
        write(B::IPC+M::PPCMSG,p);
        write(B::IPC+M::PPCCTRL,en|M::X1);
        require((read(B::IPC+M::PPCCTRL)&M::X1)!=0u,"X1 request missing");
    };
    auto clear=[&](uint32_t bit){
        write(B::IPC+M::PPCCTRL,en|bit);
        // Hardware latch requires explicit W1C after the guest clears IPC.
        require(scheduler.service_one(B::MSR_EE).progress==S::Pump::Busy,
                "latched IRQ was serviced before original guest acknowledged");
        write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        require(!bus.external_irq_level(),"IRQ not released by guest clear");
    };
    auto run_reply=[&](uint32_t p,uint32_t cmd,int32_t expected){
        const auto step=scheduler.service_one(B::MSR_EE);
        require(step.progress==S::Pump::Replied&&step.guest_exception_ready,
                "IOS completion was not published with external guest IRQ");
        require(read(B::IPC+M::ARMMSG)==p,"IOS reply slot changed");
        require(ram.read32(p)==S::Reply&&ram.read32(p+4u)==uint32_t(expected)&&
                ram.read32(p+8u)==cmd,"IOS reply bytes differ");
        clear(M::Y1);
    };
    write(B::IPC+H::PPC_MASK,H::IPC_PPC);
    write(B::PI_MASK,H::PI_HOLLYWOOD);
    auto idle=scheduler.service_one(B::MSR_EE);
    require(idle.progress==S::Pump::Idle&&!idle.guest_exception_ready&&
            idle.serviced_steps==1u,"idle host IOS scheduler emitted unsolicited interrupt");

    ram.path(name,"/dev/stm/immediate");
    request_submit(request,S::Open,0,name);
    require(bus.services().queued_replies()==0u&&!bus.external_irq_level(),
            "original pending request completed without host yield");
    const auto accepted=scheduler.service_one(0u);
    require(accepted.progress==S::Pump::Ack&&accepted.broadway_irq_level&&
            !accepted.guest_exception_ready,"IOS ACK or MSR.EE masking differs");
    require(bus.external_exception_pending(B::MSR_EE),"guest external IRQ unavailable when EE enabled");
    require((read(B::IPC+M::PPCCTRL)&M::X1)==0u&&
            (read(B::IPC+M::PPCCTRL)&M::Y2)!=0u&&
            bus.services().queued_replies()==1u,"Starlet did not acknowledge X1 correctly");
    const auto blocked=scheduler.service_one(B::MSR_EE);
    require(blocked.progress==S::Pump::Busy&&
            blocked.serviced_steps==accepted.serviced_steps&&
            ram.read32(request)==S::Open,"latched IRQ allowed premature duplicate IOS work");
    clear(M::Y2);
    run_reply(request,S::Open,0);
    require(bus.services().is_open(0u,S::Device::Immediate),"original STM immediate device not opened");

    ram.path(name,"/dev/stm/eventhook");
    request_submit(request,S::Open,0,name);
    require(scheduler.service_one(B::MSR_EE).progress==S::Pump::Ack,
            "event device was not accepted");
    clear(M::Y2);
    run_reply(request,S::Open,1);
    require(bus.services().is_open(1u,S::Device::Event),"STM event device missing");

    ram.write32(event_output,0xbadc0ffeu);
    request_submit(event,S::Ioctl,1,S::EventHook,0,0,event_output,4);
    const auto deferred=scheduler.service_one(B::MSR_EE);
    require(deferred.progress==S::Pump::Deferred&&deferred.guest_exception_ready,
            "event registration did not defer and raise normal ACK");
    clear(M::Y2);
    require(bus.services().event_pending()&&bus.services().queued_replies()==0u,
            "untriggered deferred event synthesized a completion");
    for(unsigned n=0;n<3;++n){
        const auto wait=scheduler.service_one(B::MSR_EE);
        require(wait.progress==S::Pump::Idle&&!wait.guest_exception_ready&&
                ram.read32(event)==S::Ioctl&&ram.read32(event_output)==0xbadc0ffeu,
                "idle host scheduler invented a deferred STM event response");
    }
    require(bus.services().signal_event(0x20000u),"host external event was not explicitly accepted");
    require(!bus.external_irq_level(),"event notified Broadway before host scheduler step");
    run_reply(event,S::Ioctl,0);
    require(ram.read32(event_output)==0x20000u&&!bus.services().event_pending(),
            "explicit event did not complete on guest service boundary");

    // Invalid physical request may not publish success or raise an IRQ.
    request_submit(0x1fe0u,S::Open,0,name);
    const auto invalid=scheduler.service_one(B::MSR_EE);
    require(invalid.progress==S::Pump::InvalidAddress&&!invalid.broadway_irq_level&&
            !invalid.guest_exception_ready&&bus.services().queued_replies()==0u,
            "invalid guest request was serviced without a valid 64-byte span");
    require(read(B::IPC+M::PPCCTRL)&M::X1,"invalid request silently cleared X1");
    require(scheduler.serviced_steps()>=9u,"scheduler did not record individual service steps");
    // Separate second-open guest-yield scenario: Broadway can clear live
    // X1 after submitting the actual request. The native IOS event is still
    // serviced only on the explicit guest scheduler boundary, not on MMIO.
    {
        Ram lateram;
        B latebus(lateram);
        IosYieldScheduler late(latebus);
        require(latebus.write32(B::IPC+H::PPC_MASK,H::IPC_PPC),
                "late IPC interrupt mask rejected");
        require(latebus.write32(B::PI_MASK,H::PI_HOLLYWOOD),
                "late processor interrupt mask rejected");
        lateram.path(name,"/dev/stm/immediate");
        lateram.write32(request,S::Open);
        lateram.write32(request+12u,name);
        require(latebus.write32(B::IPC+M::PPCMSG,request),"late PPCMSG rejected");
        require(latebus.write32(B::IPC+M::PPCCTRL,en|M::X1),"late X1 rejected");
        require(latebus.write32(B::IPC+M::PPCCTRL,en),"late X1 clear rejected");
        require(latebus.pending_native_ios_request(),"native IOS event lost before yield");
        require((latebus.read32(B::IPC+M::PPCCTRL).value()&M::X1)==0u,
                "live X1 bit was not guest-clearable");
        require(lateram.read32(request)==S::Open&&
                latebus.services().queued_replies()==0u,
                "guest request was serviced before a yield");
        const auto lateack=late.service_one(0u);
        require(lateack.progress==S::Pump::Ack&&lateack.serviced_steps==1u&&
                !latebus.pending_native_ios_request()&&
                latebus.services().queued_replies()==1u,
                "native IOS guest-yield failed to acknowledge latched request");
        require(lateram.read32(request)==S::Open,
                "native IOS ACK incorrectly wrote an early reply");
        const auto duplicate=late.service_one(B::MSR_EE);
        require(duplicate.progress==S::Pump::Busy&&
                duplicate.serviced_steps==lateack.serviced_steps,
                "native IOS accepted a duplicate while old IRQ was pending");
        // Match the original V192-V193 interrupt-enable/disable transition:
        // MSR.EE controls exception eligibility, not the Hollywood IRQ
        // latch or the Starlet's deferred second IOS_Open completion.
        require(latebus.external_irq_level()&&
                !latebus.external_exception_pending(0u)&&
                latebus.external_exception_pending(B::MSR_EE)&&
                (latebus.read32(B::IPC+M::PPCCTRL).value()&M::Y2)!=0u&&
                latebus.services().queued_replies()==1u,
                "pending second Open Y2/IRQ did not survive MSR.EE toggle");
        const auto masked_recheck=late.service_one(0u);
        const auto enabled_recheck=late.service_one(B::MSR_EE);
        require(masked_recheck.progress==S::Pump::Busy&&
                !masked_recheck.guest_exception_ready&&
                enabled_recheck.progress==S::Pump::Busy&&
                enabled_recheck.guest_exception_ready&&
                masked_recheck.serviced_steps==lateack.serviced_steps&&
                enabled_recheck.serviced_steps==lateack.serviced_steps&&
                lateram.read32(request)==S::Open&&
                latebus.services().queued_replies()==1u,
                "MSR.EE toggling incorrectly serviced or lost pending second IOS Open");
        // Complete the *same* deferred second Open. The guest must ACK Y2,
        // clear the Hollywood W1C cause, then explicitly yield again.
        // No reply is published by writing PPCCTRL or by consuming X1.
        require(latebus.write32(B::IPC+M::PPCCTRL,en|M::Y2),
                "late Broadway Y2 W1C rejected");
        require(lateram.read32(request)==S::Open&&
                latebus.services().queued_replies()==1u&&
                latebus.external_irq_level(),
                "late Y2 W1C published an early reply or skipped Hollywood cause");
        const auto blocked_w1c=late.service_one(B::MSR_EE);
        require(blocked_w1c.progress==S::Pump::Busy&&
                blocked_w1c.serviced_steps==lateack.serviced_steps,
                "unacknowledged Hollywood cause permitted second IOS service");
        require(latebus.write32(B::IPC+H::PPC_FLAG,H::IPC_PPC),
                "late Hollywood IPC W1C rejected");
        require(!latebus.external_irq_level(),
                "late Hollywood IPC W1C failed to clear asserted IRQ");
        const auto published=late.service_one(B::MSR_EE);
        require(published.progress==S::Pump::Replied&&
                published.serviced_steps==lateack.serviced_steps+1u&&
                published.guest_exception_ready&&
                lateram.read32(request)==S::Reply&&
                lateram.read32(request+4u)==0u&&
                lateram.read32(request+8u)==S::Open&&
                latebus.read32(B::IPC+M::ARMMSG).value()==request&&
                latebus.services().queued_replies()==0u,
                "deferred native IOS Open did not publish exactly one authentic reply");
        require(latebus.write32(B::IPC+M::PPCCTRL,en|M::Y1),
                "late Broadway Y1 W1C rejected");
        require(latebus.write32(B::IPC+H::PPC_FLAG,H::IPC_PPC),
                "late second Hollywood IPC W1C rejected");
        require(!latebus.external_irq_level()&&
                late.service_one(B::MSR_EE).progress==S::Pump::Idle&&
                lateram.read32(request)==S::Reply&&
                !latebus.pending_native_ios_request(),
                "second native IOS Open republished a reply after guest ACK");
    }
    std::cout<<"PASS: native IOS guest-yield service, X1 ACK, deferred event, W1C IRQ, MSR.EE and request bounds\n";
}
