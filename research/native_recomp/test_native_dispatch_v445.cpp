#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>
namespace nw=nwii::runtime;
namespace { struct Stop{};struct Fallback{};constexpr uint32_t Back=0x80006000u; }
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
bool process_pending_callbacks(CPUContext& c){if(c.pc==Back)throw Stop{};return false;}
bool handle_syscall(CPUContext&){throw std::runtime_error("unexpected syscall");}
void interpret_step(CPUContext&){throw Fallback{};}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw Fallback{};}
}
extern "C" void run_game(nw::CPUContext&);
int main(int argc,char** argv){
    need(argc==2,"baseline or fixed");
    const std::string_view version=argv[1];need(version=="baseline"||version=="fixed","version");
    const bool fixed=version=="fixed";
    auto c=std::make_unique<nw::CPUContext>();nw::g_trace_calls=true;
    auto run=[&](uint32_t pc,uint32_t result,std::string_view marker,bool want_fallback){
        c->pc=pc;c->lr=Back;c->gpr[4]=10;c->inst_count=100;c->is_running=true;
        std::ostringstream capture;auto* old=std::cout.rdbuf(capture.rdbuf());
        bool stopped=false,fallback=false;
        try{run_game(*c);}catch(const Stop&){stopped=true;}catch(const Fallback&){fallback=true;}catch(...){std::cout.rdbuf(old);throw;}
        std::cout.rdbuf(old);
        need(fallback==want_fallback&&stopped!=fallback,"dispatch route");
        if(!fallback)need(c->pc==Back&&c->lr==Back&&c->gpr[4]==result,"guest result");
        const auto log=capture.str();
        if(marker.empty())need(log.find("[CALL]")==std::string::npos,"unexpected root trace");
        else need(log.find(marker)!=std::string::npos,"missing root trace");
    };
    run(0x80004000u,11,"[CALL] 0x80004000",false);
    run(0x80004080u,16,"[CALL] 0x80004080",false);
    run(0x80004084u,14,"",!fixed);
    run(0x80004100u,11,fixed?"[CALL] 0x80004100":"",false);
    std::cout<<"V445_DISPATCH version="<<version<<" sparse_resume=1 root_priority=1 expected_fallback="<<unsigned(!fixed)<<'\n';
}
