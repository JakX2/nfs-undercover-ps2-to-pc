// Synthetic PowerPC loop emitted by the actual pinned NWiiRecomp, not a
// manual invocation of the instruction boundary helper.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_exi_tick_binding_v497.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI AOT boundary");}
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
int main(){
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);
    constexpr uint32_t csr=0xcd006800u,cr=csr+12,data=csr+16,back=0x80006000u;
    constexpr uint32_t command=0x80001000u,buffer=0x80001100u,readback=0x80001200u;
    unsigned valid=0,refused=0;
    for(unsigned trial=0;trial<6;++trial){
        WiiIrqBanks banks(nw::hw::pi_intsr);ExiController exi(banks,&ios.physical_ram());
        IrqBankBinding mmio(banks,&exi);ExiMxDevice::Sram seed{};
        for(unsigned i=0;i<64;++i)seed[i]=uint8_t(i*13u+trial);
        ExiMxDevice mx(seed,[]{return 0x87654321u;});ExiIdEndpoint id(0xffffffffu);
        ExiEndpointScheduler sched(exi,mx,id,trial==5?1000u:8u);
        auto send=[&](uint32_t addr,uint32_t ctrl,unsigned budget){
            const auto before=c.inst_count;c.pc=0x80004000u;c.lr=back;
            c.gpr[3]=csr;c.gpr[5]=ctrl;c.gpr[6]=budget;c.gpr[8]=addr;
            func_80004000(c);
            need(c.pc==back&&c.inst_count>before&&c.inst_count-before<=8u+5u*budget);
            return c.gpr[3];
        };
        auto select=[&]{c.mmu.write32(csr,0x134u);};
        auto deselect=[&]{c.mmu.write32(csr,8u);};
        auto issue_command=[&](uint32_t cmd,unsigned budget=64u){c.mmu.write32(command,cmd);return send(command,0x35u,budget);};
        auto expected=seed;
        if(trial<4){
            expected[48u+trial*2u]^=0x5au;
            expected[49u+trial*2u]^=0xa5u;
        }
        for(unsigned i=0;i<64;++i){c.mmu.write8(buffer+i,expected[i]);c.mmu.write8(readback+i,0xa7);}
        c.mmu.write8(buffer-1,0x5a);c.mmu.write8(buffer+64,0x5a);
        c.mmu.write8(readback-1,0x5a);c.mmu.write8(readback+64,0x5a);
        select();
        if(trial==4){
            need(!ExiTickBinding::active()&&issue_command(0xa0000600u,3)==1u);
            need(exi.pending(0)&&sched.completed()==0&&mx.sram()==seed&&!mx.dirty());
            ++refused;continue;
        }
        ExiTickBinding tick(sched);
        if(trial==5){
            need(issue_command(0xa0000600u,3)==1u&&exi.pending(0));
            need(sched.completed()==0&&mx.sram()==seed&&!mx.dirty());++refused;continue;
        }
        need(issue_command(0xa0000100u+20u*64u)==0u);
        need(sched.completed()==1&&!mx.dirty()&&mx.sram()==seed);
        for(unsigned i=20;i<64;i+=4){
            need(send(buffer+i,0x35u,64)==0u&&sched.completed()==2u+(i-20u)/4u);
            for(unsigned j=0;j<64;++j)need(mx.sram()[j]==(j>=20&&j<i+4?expected[j]:seed[j]));
        }
        need(mx.dirty()&&mx.sram()==expected&&sched.completed()==12);
        deselect();select();
        need(issue_command(0x20000100u)==0u);
        for(unsigned i=0;i<64;i+=4){
            need(send(command,0x31u,64)==0u);
            c.mmu.write32(readback+i,c.gpr[4]);
        }
        need(sched.completed()==29&&mx.sram()==expected&&!exi.pending(0));
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(readback+i)==expected[i]);
        need(c.mmu.read8(buffer-1)==0x5a&&c.mmu.read8(buffer+64)==0x5a&&
             c.mmu.read8(readback-1)==0x5a&&c.mmu.read8(readback+64)==0x5a);
        need(c.mmu.read32(cr)==0x30u&&c.mmu.read32(data)==c.gpr[4]);
        deselect();need(!(c.mmu.read32(0xcc003000u)&WiiIrqBanks::PI_EXI));++valid;
    }
    need(valid==4&&refused==2&&!ExiTickBinding::active()&&ios.serviced_steps()==0);
    std::cout<<"V817_NATIVE_SRAM_WRITE valid=4 refused=2 guest_mmio=1 offset=20 bytes=44 readback=1 fallback=0 original_execution=0\n";
}
