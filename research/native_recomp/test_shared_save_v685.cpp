#include "runtime/cpu_context.h"
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
constexpr uint32_t Entry=0x80004000u,Parent=0x80004100u,Alias=Parent+12u,Frame=0x80010000u;
constexpr uint32_t Canary=0xdeadbeefu;
static void need(bool ok){if(!ok)throw std::runtime_error("V685 shared alias assertion");}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static unsigned stage=0,stops=0;static std::array<uint32_t,32> saved{};
static void check_frame(CPUContext& c,uint32_t frame,unsigned first){
    for(unsigned r=14;r<32;++r)need(c.mmu.read32(frame-4*(32-r))==(r>=first?saved[r]:Canary));
    need(c.mmu.read32(frame-76)==Canary&&c.mmu.read32(frame)==Canary);
}
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc);
    if(stage==0){need(pc==Entry);++stage;return;}
    if(stage==1){need(pc==Parent&&c.lr==Entry+4&&c.gpr[11]==Frame);++stage;return;}
    need(stage==2&&pc==Alias&&c.lr==Entry+12&&c.gpr[11]==Frame+256);
    check_frame(c,Frame,14);check_frame(c,Frame+256,32);++stage;
}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext& c){
    need(stage==3&&c.pc==Entry+12);check_frame(c,Frame,14);check_frame(c,Frame+256,17);
    for(unsigned r=0;r<32;++r)need(c.gpr[r]==(r==11?Frame+256:saved[r]));
    need(c.lr==Entry+12);++stops;c.is_running=false;return true;
}
void interpret_step(CPUContext&){throw std::runtime_error("V685 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V685 micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V685 null call");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V685 unexpected MMIO");}
uint32_t HW_Reg_Read32(uint32_t){throw std::runtime_error("V685 unexpected MMIO");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V685 unexpected MMIO");}
void HW_Reg_Write32(uint32_t,uint32_t){throw std::runtime_error("V685 unexpected MMIO");}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(){
    using namespace nwii::runtime;
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    for(unsigned trial=0;trial<32;++trial){
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[11]=Frame;c.pc=Entry;c.lr=0x80006000u;c.msr=0x32u;
        c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;
        saved=c.gpr;stage=0;
        for(auto frame:{Frame,Frame+256})for(unsigned i=0;i<=19;++i)c.mmu.write32(frame-4*i,Canary);
        run_game(c);need(stage==3&&stops==trial+1&&!c.is_running);
    }
    std::cout<<"V685_SHARED_ALIAS synthetic=1 cases=32 parent_registers=18 alias_registers=15 fallback=0 original_execution=0\n";
}
