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
static unsigned scenario=0,syscalls=0,callbacks=0;
bool process_pending_callbacks(CPUContext& c){
    ++callbacks;
    if(scenario==3){c.is_running=false;return true;}
    return false;
}
bool handle_syscall(CPUContext& c){
    need(c.pc==0x80004200u,"syscall PC");++syscalls;
    if(scenario==1){c.pc=c.lr;c.is_running=false;return true;}
    if(scenario==2){c.pc=0x80004008u;c.is_running=false;return true;}
    // In dispatcher test the callback stopped before entry. Legacy
    // dispatch still reaches the sc, whose stop prevents an infinite loop.
    if(scenario==3){c.pc=c.lr;c.is_running=false;return true;}
    return false;
}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
}
#ifdef V463_SPLIT
#include "functions.h" // authoritative C linkage from the split emitter
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
#endif
extern "C" void run_game(nw::CPUContext&);
int main(int argc,char** argv){
    need(argc==2,"baseline or fixed");
    const std::string_view mode=argv[1];need(mode=="baseline"||mode=="fixed","mode");
    const bool fixed=mode=="fixed";
    auto c=std::make_unique<nw::CPUContext>();
    auto reset=[&](unsigned scenario){
        nw::scenario=scenario;nw::syscalls=nw::callbacks=0;
        c->pc=0x80004000u;c->lr=0x80006000u;c->is_running=true;
        c->gpr[4]=10;c->gpr[5]=20;c->gpr[6]=30;c->inst_count=100;
    };
    reset(0);func_80004000(*c);
    need(c->pc==0x80006000u&&c->is_running&&nw::syscalls==1&&c->gpr[4]==11&&c->gpr[5]==22&&c->gpr[6]==34&&c->inst_count==113,"normal nested return");
    reset(1);func_80004000(*c);
    need(!c->is_running&&nw::syscalls==1&&c->gpr[6]==30,"leaf stop");
    need(c->pc==(fixed?0x80004108u:0x80006000u)&&c->gpr[4]==(fixed?10u:11u)&&c->gpr[5]==(fixed?20u:22u)&&c->inst_count==(fixed?105u:111u),"stop propagates through child");
    reset(2);func_80004000(*c);
    need(!c->is_running&&nw::syscalls==1&&c->gpr[5]==20&&c->gpr[6]==30,"nonmatching child PC");
    need(c->pc==(fixed?0x80004008u:0x80006000u)&&c->gpr[4]==(fixed?10u:11u)&&c->inst_count==(fixed?105u:108u),"stop propagates through parent");
    reset(3);run_game(*c);
    need(!c->is_running&&nw::callbacks==1&&nw::syscalls==(fixed?0u:1u)&&c->gpr[4]==(fixed?10u:11u)&&c->gpr[5]==(fixed?20u:22u)&&c->gpr[6]==30,"dispatcher stop");
    std::cout<<"V463_NATIVE_STOP_AOT mode="<<mode<<" normal=1 nested=1 parent=1 dispatch=1 fallback=0\n";
}
