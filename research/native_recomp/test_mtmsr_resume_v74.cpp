#include "runtime/cpu_context.h"
#include <cassert>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
constexpr uint32_t ENTRY=0x80004000u,RESUME=ENTRY+12u,IRQ=0x80005000u,STOP=0x80006000u;
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static unsigned entry_count=0,irq_count=0,deliveries=0,stops=0;
static bool pending=false;
void trace_call(uint32_t pc,CPUContext&){
    if(pc==ENTRY)++entry_count;
    else if(pc==IRQ)++irq_count;
    else if(pc!=STOP)throw std::runtime_error("unexpected function entry");
}
bool process_pending_callbacks(CPUContext& c){
    if(!pending||!(c.msr&0x8000u))return false;
    assert(c.pc==RESUME&&c.gpr[5]==0u&&c.gpr[6]==0u);
    pending=false;++deliveries;
    c.srr0=c.pc;c.srr1=c.msr;c.msr&=~0x8000u;c.pc=IRQ;
    return true;
}
bool handle_syscall(CPUContext& c){
    assert(c.pc==STOP);++stops;c.is_running=false;return true;
}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){}
void HW_Reg_Write32(uint32_t,uint32_t){}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    using namespace nwii::runtime;
    std::ostringstream output,errors;
    auto* old=std::cout.rdbuf(output.rdbuf());auto* err=std::cerr.rdbuf(errors.rdbuf());
    for(unsigned trial=0;trial<64;++trial){
        auto& c=*ctx;c.pc=ENTRY;c.lr=STOP;c.msr=0;c.is_running=true;
        c.gpr[5]=c.gpr[6]=0;pending=(trial%2==0);
        run_game(c);
        assert(!c.is_running&&c.gpr[5]==1u&&c.gpr[6]==uint32_t(trial%2==0)&&c.msr==0x8000u);
    }
    std::cout.rdbuf(old);std::cerr.rdbuf(err);
    assert(entry_count==64u&&irq_count==32u&&deliveries==32u&&stops==64u);
    assert(errors.str().find("Fallback dispatch")==std::string::npos&&errors.str().find("UNKNOWN DISPATCH")==std::string::npos);
    std::cout<<"PASS: 64 native mtmsr/rfi dispatch trials, 32 actual generated IRQ returns, no fallback\n";
}
