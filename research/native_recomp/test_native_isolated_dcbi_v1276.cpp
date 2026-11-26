#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
namespace nw=nwii::runtime;
static void need(bool b){if(!b)throw std::runtime_error("V1276 native cache invariant");}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;
MMU* g_mmu=nullptr;
int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
namespace hw {
void vi_trigger_interrupt(){}
extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){throw std::runtime_error("unexpected IOS");}
}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext&){throw std::runtime_error("unexpected syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
}
#ifdef V1276_SPLIT
#include "functions.h"
#else
void func_80004000(nw::CPUContext&);
#endif
int main(){
    auto c=std::make_unique<nw::CPUContext>();
    unsigned cases=0;
    for(uint32_t alias:{0x80000000u,0xc0000000u,0u})
        for(uint32_t base:{0x90000000u,0xd0000000u,0x10000000u})
            for(uint32_t prior:{0u,300u}){
                c->pc=0x80004000u;c->lr=0x80006000u;c->inst_count=100u;c->is_running=true;
                c->gpr[0]=0xccccccccu;c->gpr[3]=alias+0x10013u;
                c->gpr[4]=base+0x20000u;c->gpr[5]=0x37u;
                c->guest_data_invalidate_count=prior;c->guest_data_invalidate_lines.fill(0);
                c->guest_last_data_invalidate=0;
                c->guest_flush_count=c->guest_sync_count=0;
                const auto regs=c->gpr;
                for(uint32_t p:{0x80010000u,0x90020020u})
                    for(int i=-1;i<=32;++i){auto* b=c->mmu.get_ptr(p+uint32_t(i));need(b);*b=0xa7;}
                func_80004000(*c);
                need(c->pc==0x80006000u&&c->lr==c->pc&&c->gpr==regs&&c->inst_count==105u);
                need(c->guest_data_invalidate_count==prior+2u&&c->guest_last_data_invalidate==base+0x20020u);
                if(!prior)need(c->guest_data_invalidate_lines[0]==alias+0x10000u&&
                               c->guest_data_invalidate_lines[1]==base+0x20020u);
                else need(c->guest_data_invalidate_lines[0]==0u);
                need(c->guest_flush_count==1u&&c->guest_last_flush==alias+0x10000u&&c->guest_sync_count==1u);
                for(uint32_t p:{0x80010000u,0x90020020u})
                    for(int i=-1;i<=32;++i)need(*c->mmu.get_ptr(p+uint32_t(i))==0xa7);
                ++cases;
            }
    need(cases==18u);
    std::cout<<"V1276_DCBI_NATIVE cases=18 flat_ram=1 trace_saturation=1 native_ticks=1 fallback=0 original_execution=0\n";
}
