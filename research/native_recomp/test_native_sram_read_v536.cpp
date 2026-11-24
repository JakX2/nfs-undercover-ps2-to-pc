// Synthetic PowerPC loop emitted by the actual pinned NWiiRecomp, not a
// manual invocation of the instruction boundary helper.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_exi_profile_v501.h"
#include "undercover/wii_sram_read_witness_v534.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SRAM owner-profile AOT boundary");}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){throw std::runtime_error("legacy IOS");}}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext&){throw std::runtime_error("syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter");}
}
#ifdef V438_SPLIT
#include "functions.h"
#else
void func_80004000(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2);const auto p=ExiHostProfile::load(argv[1]);
    need(p.sram==sram_read_fixture()&&p.id==0xbeef0010u&&p.di_config==1u&&p.latency==8u);
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);
    constexpr uint32_t csr=0xcd006800u,mar=csr+4,len=csr+8,cr=csr+12,data=csr+16,back=0x80006000;
    auto loop=[&]{
        const auto old=c.inst_count;c.pc=0x80004000;c.lr=back;c.gpr[4]=0;c.ctr=0;
        func_80004000(c);need(c.pc==back&&c.gpr[4]==3&&c.inst_count==old+10);
    };
    for(unsigned fault=0;fault<=5;++fault){
        sram_completion={};exi_id_completion={};
        ExiController exi(banks,&ios.physical_ram());IrqBankBinding mmio(banks,&exi);
        auto profile=p;if(fault==1)profile.sram[0]^=1;if(fault==5)profile.latency=100;
        ExiProfileSession session(exi,profile);
        for(int i=-1;i<=96;++i)c.mmu.write8(SramGuest+uint32_t(i),0xa7);
        need(sram_completion.begin(true));
        c.mmu.write32(csr,0x130u);c.mmu.write32(data,0x20000100u);c.mmu.write32(cr,0x35u);
        for(unsigned i=0;i<32;++i)need(c.mmu.read32(cr)==0x35u);
        loop();
        if(fault==5){
            need(sram_completion.count()==0&&exi.pending(0).has_value()&&session.completed()==0);
            need(!sram_completion.finish());continue;
        }
        need(session.completed()==1&&c.mmu.read32(cr)==0x34u);
        if(fault==2){c.mmu.write32(csr,8);c.mmu.write32(csr,0x130u);
            c.mmu.write32(data,0x20000100u);c.mmu.write32(cr,0x35u);loop();}
        c.mmu.write32(mar,SramGuest+(fault==3?32u:0u));
        c.mmu.write32(len,fault==4?32u:64u);c.mmu.write32(cr,3);
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(SramGuest+i)==0xa7);
        loop();
        need(sram_completion.finish()==(fault==0));
        if(!fault){
            need(session.completed()==2&&!session.sram_dirty()&&!exi.pending(0));
            for(unsigned i=0;i<64;++i)need(c.mmu.read8(SramGuest+i)==p.sram[i]);
            need(c.mmu.read8(SramGuest-1)==0xa7&&c.mmu.read8(SramGuest+64)==0xa7);
        }
        c.mmu.write32(csr,8);
        need(!(c.mmu.read32(0xcc003000)&WiiIrqBanks::PI_EXI));
    }
    need(ios.serviced_steps()==0);
    std::cout<<"PASS: generated PPC drives actual profile-backed SRAM DMA and completion witness; five negative controls\n";
}
