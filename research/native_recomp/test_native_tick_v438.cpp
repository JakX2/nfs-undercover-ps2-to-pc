#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string_view>
namespace nw=nwii::runtime;
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
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
#ifdef V438_SPLIT
#include "functions.h" // authoritative C linkage from the split emitter
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2,"expected baseline or fixed");
    const std::string_view mode=argv[1];need(mode=="baseline"||mode=="fixed","mode");
    const bool fixed=mode=="fixed";
    constexpr uint32_t back=0x80006000u;
    auto c=std::make_unique<nw::CPUContext>();
    auto reset=[&](uint32_t pc){c->pc=pc;c->lr=back;c->gpr[0]=back;c->gpr[4]=0;c->ctr=0;c->inst_count=100;};
    auto expect=[&](uint64_t ticks,uint32_t result){
        need(c->pc==back&&c->gpr[4]==result,"guest semantics changed");
        need(c->inst_count==100+ticks&&c->read_timebase()==c->inst_count,"native tick mismatch");
    };
    reset(0x80004000u);func_80004000(*c);expect(fixed?10:8,3);
    reset(0x8000400cu);c->ctr=2;c->gpr[4]=8;func_80004000(*c);expect(fixed?5:3,10);
    reset(0x80004100u);func_80004100(*c);expect(6,2);
    reset(0x80004108u);c->gpr[4]=9;func_80004100(*c);expect(fixed?2:1,9);
    std::cout<<"V438_AOT_TICKS mode="<<mode<<" loop=1 resume=1 call=1 call_resume=1 fallback=0\n";
}
