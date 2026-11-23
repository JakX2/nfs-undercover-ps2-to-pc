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
    std::cout<<"PASS: V376 authentic IOS Y1 exception entry saves guest SRRs and keeps reply latched\n";
}
