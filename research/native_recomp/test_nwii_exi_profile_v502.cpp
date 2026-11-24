#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_exi_profile_v501.h"
#include <iostream>
#include <memory>
#include <source_location>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)throw std::runtime_error("pinned EXI profile line "+std::to_string(loc.line()));}
template<class F>void reject(F f,const std::source_location loc=std::source_location::current()){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught,loc);}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){throw std::runtime_error("legacy IOS");}}
}
int main(){
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);
    unsigned legacy=0;
    d.register_region(0x0d006024u,0x0d006027u,[&](uint32_t){++legacy;return 0xffu;},[&](uint32_t,uint32_t){++legacy;});
    // Dispatcher uses first-match ordering; its broad IPC region otherwise shadows the test fixture.
    nw::hw::register_ipc(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);ExiController exi(banks,&ios.physical_ram());
    IrqBankBinding mmio(banks,&exi);
    constexpr uint32_t cfg=0xcd006024u,csr=0xcd006800u,mar=csr+4,len=csr+8,cr=csr+12,data=csr+16;
    need(!ExiDiConfigBinding::active()&&c.mmu.read32(cfg)==0xff&&legacy==1);
    c.mmu.write32(csr,0x200);reject([&]{c.mmu.write32(cr,0x15);});
    c.mmu.write32(csr,0);
    ExiHostProfile p{};p.id=0xfeedcafe;p.di_config=1;p.rtc_seconds=0x12345678;p.latency=8;
    for(unsigned i=0;i<64;++i)p.sram[i]=uint8_t(i*5+1);
    {
        ExiProfileSession session(exi,p);
        need(c.mmu.read32(cfg)==1&&c.mmu.read32(0xcd806024u)==1&&legacy==1);
        reject([&]{c.mmu.write32(cfg,1);});reject([&]{c.mmu.read16(cfg);});reject([&]{c.mmu.read8(cfg);});
        reject([&]{c.mmu.write_f32(cfg,1.0f);});reject([&]{c.mmu.read64(cfg);});
        reject([&]{c.mmu.read32(0x4d006024u);});reject([&]{c.mmu.read32(cfg+1);});
        need(legacy==1);
        auto run=[&](uint32_t ctl){
            c.mmu.write32(cr,ctl);const auto done=session.completed();
            ++c.inst_count;c.exi_instruction_boundary();
            for(unsigned i=0;i<7;++i){++c.inst_count;c.exi_instruction_boundary();need(c.mmu.read32(cr)&1u);}
            ++c.inst_count;c.exi_instruction_boundary();
            need(!(c.mmu.read32(cr)&1u)&&session.completed()==done+1);
        };
        c.mmu.write32(csr,0x200);c.mmu.write32(data,0);run(0x15);run(0x31);need(c.mmu.read32(data)==p.id);
        c.mmu.write32(csr,8);c.mmu.write32(csr,0x130);
        c.mmu.write32(data,0x20000100);run(0x35);
        c.mmu.write32(mar,0x80001000);c.mmu.write32(len,64);run(3);
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(0x80001000+i)==p.sram[i]);
        c.mmu.write32(csr,8);need(session.completed()==4&&!session.sram_dirty());
    }
    need(!ExiDiConfigBinding::active()&&!ExiTickBinding::active()&&c.mmu.read32(cfg)==0xff&&legacy==2);
    need(ios.serviced_steps()==0);
    std::cout<<"PASS: pinned native host profile session, actual DI configuration MMIO aliases and scheduled ID/SRAM transfers\n";
}
