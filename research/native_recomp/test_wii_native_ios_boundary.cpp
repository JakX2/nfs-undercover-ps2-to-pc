#include "wii_native_ios_boundary.h"
#include <array>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using R=NativeBoundaryRoute;using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
static void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
struct Mmu {
    std::span<uint8_t> ram;
    uint8_t* get_ptr(uint32_t a){a&=0x3fffffffu;return a<ram.size()?ram.data()+a:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);return p?*p:0u;}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0x80001000u,msr=0x0000b032u,lr=0x80001004u,ctr=2u,xer=3u,srr0=4u,srr1=5u;
    uint32_t dispatch_saved_ctx=0u;bool is_running=true,in_callback=false,ext_resched_pending=false;
};
int main(){
    std::array<uint8_t,8192> one{},two{};constexpr uint32_t other=1u<<8,req=0x100u,path=0x400u,en=M::IY1|M::IY2;
    std::atomic<uint32_t> cause{other},mask{other|H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);Cpu c{{one}};
    constexpr std::array<uint8_t,8> vector{0x60,0,0,0,0x4c,0,0,0x64};
    for(std::size_t i=0;i<vector.size();++i)one[0x500+i]=vector[i];
    for(std::size_t i=0;i<c.gpr.size();++i)c.gpr[i]=uint32_t(i+10);
    const auto regs=c.gpr;const auto pc=c.pc,msr=c.msr,lr=c.lr,ctr=c.ctr,xer=c.xer;
    const auto put=[&](uint32_t a,uint32_t v){need(host.write32(a,v),"native write failed");};
    const auto step=[&](bool safe=true){return service_native_ios_boundary(host,c,vector,safe);};
    const auto unchanged=[&]{return c.pc==pc&&c.lr==lr&&c.ctr==ctr&&c.xer==xer&&c.gpr==regs&&c.srr0==4u&&c.srr1==5u;};
    auto& ram=host.physical_ram();const std::string_view dev="/dev/stm/immediate";
    for(std::size_t i=0;i<dev.size();++i)ram.write8(path+uint32_t(i),uint8_t(dev[i]));
    ram.write32(req,S::Open);ram.write32(req+12u,path);
    put(B::MIRROR+H::PPC_MASK,H::IPC_PPC);put(B::IPC+M::PPCMSG,req);put(B::IPC+M::PPCCTRL,en|M::X1);
    need(step(false).route==R::Unsafe&&unchanged()&&host.serviced_steps()==0u,"unsafe boundary serviced IOS");
    c.in_callback=true;need(step().route==R::Unsafe,"host callback admitted");c.in_callback=false;
    c.dispatch_saved_ctx=1;need(step().route==R::Unsafe,"in-flight context admitted");c.dispatch_saved_ctx=0;
    c.ext_resched_pending=true;need(step().route==R::Unsafe,"HLE reschedule admitted");c.ext_resched_pending=false;
    c.is_running=false;need(step().route==R::Unsafe,"stopped CPU admitted");c.is_running=true;
    c.pc=0u;need(step().route==R::Unsafe,"idle CPU admitted");c.pc=pc;
    c.msr|=1u;need(step().route==R::Unsafe,"unsupported CPU mode admitted");c.msr=msr;
    auto pending=step();need(pending.route==R::OtherPending&&!pending.service&&pending.enabled_pi==other&&unchanged()&&host.serviced_steps()==0u,"unrelated PI source consumed");
    mask.store(H::PI_HOLLYWOOD);c.msr&=~B::MSR_EE;
    auto ack=step();need(ack.route==R::NativeMasked&&ack.service&&ack.service->progress==S::Pump::Ack&&unchanged()&&ram.read32(req)==S::Open,"masked native ACK incorrect");
    need(step().route==R::NativeMasked&&host.serviced_steps()==1u,"pending IRQ advanced IOS twice");
    c.msr=msr;one[0x500]^=1u;bool rejected=false;try{(void)step();}catch(const std::runtime_error&){rejected=true;}
    need(rejected&&unchanged()&&cause.load()==(other|H::PI_HOLLYWOOD),"bad vector modified CPU or retired IRQ");one[0x500]=vector[0];
    auto y2=step();need(y2.route==R::NativeEntered&&!y2.service&&c.pc==ExternalVector&&c.srr0==pc&&c.srr1==(msr&ExternalSrr1Mask)&&c.msr==(msr&~ExternalMsrClear)&&c.gpr==regs&&c.lr==lr&&c.ctr==ctr&&c.xer==xer,"native Y2 exception did not preserve guest state");
    need(ram.read32(req)==S::Open&&host.serviced_steps()==1u,"exception entry published reply");
    // Synthetic guest ACK and explicit synthetic return for this isolated test.
    // The bridge itself performs neither operation.
    put(B::IPC+M::PPCCTRL,en|M::Y2);put(B::MIRROR+H::PPC_FLAG,H::IPC_PPC);
    c.pc=c.srr0;c.msr=msr;c.srr0=4u;c.srr1=5u;
    auto y1=step();need(y1.route==R::NativeEntered&&y1.service&&y1.service->progress==S::Pump::Replied&&c.pc==ExternalVector&&c.srr0==pc&&ram.read32(req)==S::Reply&&host.serviced_steps()==2u,"native Y1 publication and entry not coherent");
    put(B::IPC+M::PPCCTRL,en|M::Y1);put(B::MIRROR+H::PPC_FLAG,H::IPC_PPC);
    c.pc=c.srr0;c.msr=msr;c.srr0=4u;c.srr1=5u;
    need(step().route==R::Idle&&unchanged()&&cause.load()==other&&host.serviced_steps()==2u,"idle fabricated IOS work or cleared another PI source");
    std::cout<<"PASS: native IOS boundary deferral, authenticated vector entry, distinct ACK/reply and preserved PI\n";
}
