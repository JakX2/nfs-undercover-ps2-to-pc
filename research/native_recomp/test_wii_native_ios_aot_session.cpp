#include "wii_native_ios_aot_session.h"
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Mmu {
    std::span<uint8_t> ram;
    uint8_t* get_ptr(uint32_t a){a&=0x3fffffffu;return a<ram.size()?ram.data()+a:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);return p?*p:0u;}
};
struct Cpu {
    Mmu mmu;uint32_t pc=0x80001000u,msr=0x8000u,srr0=0u,srr1=0u,dispatch_saved_ctx=0u;
    bool is_running=true,in_callback=false,ext_resched_pending=false,vblank_pending=false,expired=false;
    std::atomic<int> pending_cb_count{0};
    bool dec_expired() const{return expired;}
};
static void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
template<class F>static void reject(F f){bool threw=false;try{f();}catch(const std::logic_error&){threw=true;}catch(const std::runtime_error&){threw=true;}need(threw,"unsafe session accepted");}
int main(){
    std::array<uint8_t,8192> one{},two{};constexpr uint32_t req=0x100u,path=0x400u,en=M::IY1|M::IY2,other=1u<<8;
    std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};NativeIosTransport host(one,two,cause,mask);Cpu cpu{{one}},wrong{{one}};
    constexpr std::array<uint8_t,8> vector{0x60,0,0,0,0x4c,0,0,0x64};
    for(std::size_t i=0;i<vector.size();++i)one[0x500+i]=vector[i];
    auto& ram=host.physical_ram();const std::string_view name="/dev/stm/immediate";
    for(std::size_t i=0;i<name.size();++i)ram.write8(path+uint32_t(i),uint8_t(name[i]));
    ram.write32(req,S::Open);ram.write32(req+12u,path);
    {
        NativeIosAotSession<Cpu,8> session(cpu,host,vector);
        const auto put=[&](uint32_t a,uint32_t v){need(NativeIosBinding::write32(a,v),"native MMIO route missing");};
        put(B::MIRROR+H::PPC_MASK,H::IPC_PPC);put(B::IPC+M::PPCMSG,req);put(B::IPC+M::PPCCTRL,en|M::X1);
        reject([&]{session.poll(wrong,true);});
        cpu.pending_cb_count=1;reject([&]{session.poll(cpu,true);});cpu.pending_cb_count=0;
        cpu.vblank_pending=true;reject([&]{session.poll(cpu,true);});cpu.vblank_pending=false;
        cpu.expired=true;reject([&]{session.poll(cpu,true);});cpu.expired=false;
        mask.store(other|H::PI_HOLLYWOOD);reject([&]{session.poll(cpu,true);});mask.store(H::PI_HOLLYWOOD);
        need(!session.poll(cpu,false)&&host.serviced_steps()==0,"uncertified PC serviced IOS");
        const auto resume=cpu.pc;
        need(session.poll(cpu,true)&&session.in_flight()&&session.entries()==1&&cpu.pc==ExternalVector&&ram.read32(req)==S::Open,"ACK exception not entered");
        need(!session.poll(cpu,false)&&host.serviced_steps()==1,"handler reentered");
        cpu.msr=0x8000u;reject([&]{session.poll(cpu,false);});cpu.msr=0;
        put(B::IPC+M::PPCCTRL,en|M::Y2);put(B::MIRROR+H::PPC_FLAG,H::IPC_PPC);
        cpu.pc=cpu.srr0;cpu.msr=cpu.srr1; // synthetic return only in this unit test
        need(cpu.pc==resume&&session.poll(cpu,true)&&session.entries()==2&&session.returns()==1&&ram.read32(req)==S::Reply,"reply exception not entered after resume");
        put(B::IPC+M::PPCCTRL,en|M::Y1);put(B::MIRROR+H::PPC_FLAG,H::IPC_PPC);
        cpu.pc=cpu.srr0;cpu.msr=cpu.srr1;
        need(!session.poll(cpu,true)&&session.returns()==2&&!session.in_flight()&&host.serviced_steps()==2&&cause.load()==other,"final resume incorrect");
    }
    need(!NativeIosBinding::active(),"MMIO binding leaked");
    std::cout<<"PASS: exclusive AOT IOS session ownership, two interrupts and certified resumes\n";
}
