// Original-free V376: real native ACK/Y1 and PowerPC external exception.
#include "wii_nand_y1_exception.h"
#include "wii_nand_ios_reply_yield.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
static void need(bool b,const char* msg){if(!b)throw std::runtime_error(msg);}
struct Ram final:IosMemory{
    std::array<uint8_t,8192> bytes{};
    bool valid(uint32_t a,uint32_t n)const override{
        return uint64_t(a)+n<=bytes.size();
    }
    uint8_t read8(uint32_t a)const override{return bytes.at(a);}
    void write8(uint32_t a,uint8_t value)override{bytes.at(a)=value;}
    void put_path(uint32_t a,std::string_view s){
        need(valid(a,uint32_t(s.size()+1u)),"bad pathname fixture");
        for(char c:s)write8(a++,uint8_t(c));
        write8(a,0);
    }
};
struct Alias{
    Ram& ram;
    uint8_t read8(uint32_t guest_addr)const{
        return ram.read8(guest_addr&0x3fffffffu);
    }
};
struct Cpu{
    Alias mmu;
    uint32_t pc=0x805265d4u,msr=0x0000b032u;
    uint32_t srr0=0xaabbccddu,srr1=0x11223344u;
    uint32_t dispatch_saved_ctx=0u;
    uint32_t lr=0x80519bbcu,ctr=0u,xer=0x5a5a5a5au;
    std::array<uint32_t,32> gpr{};
};
int main(){
    Ram ram;B bus(ram);Cpu c{{ram}};
    constexpr std::array<uint8_t,8> vector{0x60,0,0,0,0x4c,0,0,0x64};
    for(unsigned i=0;i<vector.size();++i)ram.write8(0x500u+i,vector[i]);
    for(unsigned i=0;i<c.gpr.size();++i)c.gpr[i]=0x90000000u+i;
    const auto regs=c.gpr;
    const uint32_t pc=c.pc,msr=c.msr,lr=c.lr,ctr=c.ctr,xer=c.xer;
    auto entry=[&](bool safe=true){return enter_queued_nand_y1(c,bus,vector,safe);};
    auto unchanged=[&]{
        return c.pc==pc&&c.msr==msr&&c.srr0==0xaabbccddu&&
               c.srr1==0x11223344u&&c.gpr==regs&&
               c.lr==lr&&c.ctr==ctr&&c.xer==xer;
    };
    need(entry()==ExternalEntry::NotPending&&unchanged(),"no-reply interrupt fabricated");
    auto write=[&](uint32_t a,uint32_t v){need(bus.write32(a,v),"MMIO write failed");};
    constexpr uint32_t request=0x100u,path=0x800u;
    constexpr uint32_t ien=M::IY1|M::IY2;
    ram.put_path(path,"/dev/stm/immediate");
    ram.write32(request,S::Open);ram.write32(request+12u,path);
    write(B::IPC+H::PPC_MASK,H::IPC_PPC);
    write(B::PI_MASK,H::PI_HOLLYWOOD);
    write(B::IPC+M::PPCMSG,request);write(B::IPC+M::PPCCTRL,ien|M::X1);
    IosYieldScheduler scheduler(bus);
    need(scheduler.service_one(c.msr).progress==S::Pump::Ack,
         "original X1 did not produce native Starlet ACK");
    need(bus.services().queued_replies()==1u&&ram.read32(request)==S::Open,
         "ACK changed request into reply");
    need(entry()==ExternalEntry::NotPending&&unchanged(),"Y2 mistaken for Y1");
    write(B::IPC+M::PPCCTRL,ien|M::Y2);
    write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    need(!bus.external_irq_level(),"Y2 acknowledgment not respected");
    need(entry()==ExternalEntry::NotPending&&unchanged(),
         "unpublished queued reply mistaken for IRQ");
    const auto published=service_deferred_reply_at_guest_boundary(bus,c.msr);
    need(published&&published->progress==S::Pump::Replied&&
         published->guest_exception_ready,"genuine native Y1 not published");
    need(ram.read32(request)==S::Reply&&ram.read32(request+8u)==S::Open&&
         bus.services().queued_replies()==0u,"native Y1 mutated original reply");
    c.msr&=~B::MSR_EE;
    need(entry()==ExternalEntry::NotPending,"disabled guest EE admitted IRQ");
    c.msr=msr;
    need(entry(false)==ExternalEntry::Deferred&&unchanged(),
         "unsafe host dispatch context entered IRQ");
    c.dispatch_saved_ctx=0x80001234u;
    need(entry()==ExternalEntry::Deferred&&unchanged(),
         "in-flight guest context overwritten");
    c.dispatch_saved_ctx=0u;
    bool mismatch=false;
    ram.write8(0x500u,0);
    try{(void)entry();}catch(const std::runtime_error&){mismatch=true;}
    need(mismatch&&unchanged(),"guest exception vector mismatch accepted");
    ram.write8(0x500u,vector[0]);
    need(entry()==ExternalEntry::Entered,"real native Y1 exception not admitted");
    need(c.pc==ExternalVector&&c.srr0==pc&&
         c.srr1==(msr&ExternalSrr1Mask)&&
         c.msr==(msr&~ExternalMsrClear)&&
         c.gpr==regs&&c.lr==lr&&c.ctr==ctr&&c.xer==xer,
         "PowerPC SRRs, exception PC or preserved registers differ");
    need(bus.external_irq_level()&&
         (bus.read32(B::IPC+M::PPCCTRL).value()&M::Y1)!=0u&&
         ram.read32(request)==S::Reply,
         "IRQ helper improperly ACKed hardware or invented guest handler");
    need(entry()==ExternalEntry::NotPending,
         "guest EE disabled after exception entry should mask re-entry");
    // Original PowerPC handler semantics: acknowledging Y1 alone cannot
    // clear the separate Hollywood flag or PI-level interrupt. Verify
    // the same bus transitions that the V387 original guest path expects.
    write(B::IPC+M::PPCCTRL,ien|M::Y1);
    need((bus.read32(B::IPC+M::PPCCTRL).value()&(M::Y1|M::Y2))==0u &&
         (bus.read32(B::IPC+H::PPC_FLAG).value()&H::IPC_PPC)!=0u &&
         bus.external_irq_level(),
         "original Broadway Y1 acknowledgement prematurely retired IRQ");
    write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    need((bus.read32(B::IPC+H::PPC_FLAG).value()&H::IPC_PPC)==0u &&
         !bus.external_irq_level(),
         "Hollywood W1C did not release native IRQ after Broadway Y1 ACK");
    // A delivered Broadway Y1 remains genuine while another native IOS
    // completion awaits scheduling. Queue occupancy must not mask a
    // hardware IRQ that is already latched and eligible in guest MSR.
    {
        Ram multi_ram;B multi_bus(multi_ram);Cpu multi{{multi_ram}};
        for(unsigned i=0;i<vector.size();++i)
            multi_ram.write8(0x500u+i,vector[i]);
        constexpr uint32_t first=0x200u,second=0x280u;
        constexpr uint32_t firstpath=0xa00u,secondpath=0xb00u;
        multi_ram.put_path(firstpath,"/dev/stm/immediate");
        multi_ram.put_path(secondpath,"/dev/stm/eventhook");
        multi_ram.write32(first,S::Open);multi_ram.write32(first+12u,firstpath);
        multi_ram.write32(second,S::Open);multi_ram.write32(second+12u,secondpath);
        const auto multi_write=[&](uint32_t a,uint32_t v){
            need(multi_bus.write32(a,v),"multiple-request MMIO write failed");
        };
        multi_write(B::IPC+H::PPC_MASK,H::IPC_PPC);
        multi_write(B::PI_MASK,H::PI_HOLLYWOOD);
        IosYieldScheduler multi_scheduler(multi_bus);
        const auto ack=[&](uint32_t req){
            multi_write(B::IPC+M::PPCMSG,req);
            multi_write(B::IPC+M::PPCCTRL,ien|M::X1);
            need(multi_scheduler.service_one(multi.msr).progress==S::Pump::Ack,
                 "multiple-request native ACK missing");
            multi_write(B::IPC+M::PPCCTRL,ien|M::Y2);
            multi_write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        };
        ack(first);ack(second);
        need(multi_bus.services().queued_replies()==2u,
             "multiple-request pre-publication queue count differs");
        const auto first_reply=service_deferred_reply_at_guest_boundary(
            multi_bus,multi.msr);
        need(first_reply&&first_reply->progress==S::Pump::Replied&&
             multi_bus.services().queued_replies()==1u&&
             multi_ram.read32(first)==S::Reply&&
             multi_ram.read32(second)==S::Open,
             "first real Y1 did not leave second completion queued");
        const auto multi_result=enter_queued_nand_y1(multi,multi_bus,vector,true);
        need(multi_result==ExternalEntry::Entered&&
             multi.pc==ExternalVector&&multi.srr0==0x805265d4u&&
             multi_bus.services().queued_replies()==1u&&
             (multi_bus.read32(B::IPC+M::PPCCTRL).value()&M::Y1)!=0u&&
             multi_ram.read32(second)==S::Open,
             "real Y1 was masked or pending IOS queue was mutated");
    }
    std::cout<<"PASS: V376 authentic IOS Y1 exception entry saves guest SRRs and keeps reply latched\n";
}
