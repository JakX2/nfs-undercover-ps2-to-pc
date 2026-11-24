#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include <iostream>
#include <memory>
#include <sstream>
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
#ifdef V443_SPLIT
#include "functions.h"
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2,"baseline or fixed");
    const std::string_view mode=argv[1];need(mode=="baseline"||mode=="fixed","mode");
    const bool fixed=mode=="fixed";
    constexpr uint32_t low=0x80004000u,high=0x80004100u,back=0x80006000u;
    auto c=std::make_unique<nw::CPUContext>();nw::g_trace_calls=true;
    auto run=[&](void(*func)(nw::CPUContext&),uint32_t pc,uint32_t result,std::string_view marker){
        c->pc=pc;c->lr=back;c->gpr[4]=10;c->inst_count=100;c->is_running=true;
        std::ostringstream capture;auto* old=std::cout.rdbuf(capture.rdbuf());
        try{func(*c);}catch(...){std::cout.rdbuf(old);throw;}
        std::cout.rdbuf(old);
        need(c->pc==back&&c->lr==back&&c->gpr[4]==result,"original branch semantics");
        const auto log=capture.str();
        if(marker.empty())need(log.find("[CALL]")==std::string::npos,"spurious root trace");
        else {const auto at=log.find(marker);need(at!=std::string::npos&&log.find("[CALL]",at+1)==std::string::npos,"root trace");}
    };
    run(func_80004000,low,11,"[CALL] 0x80004000");
    run(func_80004100,high,13,fixed?"[CALL] 0x80004100":"");
    run(func_80004100,low,11,fixed?"":"[CALL] 0x80004000");
    run(func_80004100,high+4,11,"");
    std::cout<<"V443_ROOT_AOT version="<<mode<<" root=1 backwards_tail=1 resume=1 fallback=0\n";
}
