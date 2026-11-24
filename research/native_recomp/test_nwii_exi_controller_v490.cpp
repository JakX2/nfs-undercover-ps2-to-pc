#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_irq_bank_binding_v481.h"
#include <iostream>
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){return -4;}}
}
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("pinned EXI controller");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    nw::CPUContext c;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    constexpr uint32_t base=0xcd006800u,pi=0xcc003000u;
    nw::hw::pi_intsr=0x300u;
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);
    {IrqBankBinding old(banks);reject([&]{c.mmu.read32(base+12);});}
    ExiController exi(banks);
    std::atomic<uint32_t> unrelated{0};WiiIrqBanks wrong(unrelated);
    reject([&]{IrqBankBinding invalid(wrong,&exi);});
    {
        IrqBankBinding bound(banks,&exi);
        for(unsigned ch=0;ch<3;++ch){
            const uint32_t a=base+20*ch;
            need(c.mmu.read32(a+12)==0);
            c.mmu.write32(a+4,0x12345);need(c.mmu.read32(a+0x800004)==0x12340);
            c.mmu.write32(a+8,0x7f);need(c.mmu.read32(a+8)==0x60);
            c.mmu.write32(a,0x84);c.mmu.write32(a+16,0xaabbccdd);
            reject([&]{c.mmu.write32(a+12,0x31);});
            need(!exi.pending(ch)&&c.mmu.read32(a+12)==0);
            exi.attach(ch,0,true);
            c.mmu.write32(a+0x80000c,0x31);
            auto p=exi.pending(ch);need(p&&p->length==4&&p->direction==0&&p->tx==0xaabbccdd);
            need(c.mmu.read32(a+12)==0x31&&c.mmu.read32(pi)==0x300);
            exi.complete_immediate(ch,p->token,0x12345678);
            need(c.mmu.read32(a+16)==0x12345678&&c.mmu.read32(a+12)==0x30);
            need(c.mmu.read32(pi)==(0x300|WiiIrqBanks::PI_EXI));
            c.mmu.write32(a,0x8c);need(c.mmu.read32(pi)==0x300);
            reject([&]{c.mmu.read16(a+12);});reject([&]{c.mmu.write64(a+8,0);});
            reject([&]{c.mmu.write_f32(a+12,0.0f);});reject([&]{c.mmu.write32(a+1,0);});
            reject([&]{c.mmu.read32((a&0x3fffffffu)|0x40000000u);});
        }
        c.mmu.write32(base,0x2000);need(c.mmu.read32(base)==0x2000);
        c.mmu.write32(base,0);need(c.mmu.read32(base)==0);
        c.mmu.write32(0xcd000034u,0x40000000u);
        need(c.mmu.read32(0xcd800034u)==0x40000000u&&ios.serviced_steps()==0);
        c.mmu.write32(0x80001000u,0x12345678u);need(c.mmu.read32(0x80001000u)==0x12345678u);
    }
    need(!IrqBankBinding::active());nw::g_ctx_ptr=nullptr;nw::g_mmu=nullptr;
    std::cout<<"PASS: pinned EXI controller aliases, idle polling, explicit transfer completion and PI interrupt\n";
}
