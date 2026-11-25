#include "runtime/cpu_context.h"
#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
constexpr uint32_t Entry=0x80004000u,Dispatcher=0x80004200u,Trampoline=0x80004300u,Data=0x80010000u;
static void need(bool ok){if(!ok)throw std::runtime_error("V679 register-save assertion");}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static unsigned stage=0,stops=0;
static uint64_t before=0;
static std::array<uint32_t,32> saved{};
static uint32_t lr=0,ctr=0,xer=0,msr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc);
    if(stage==0){need(pc==Entry);++stage;return;}
    if(stage==1){need(pc==Trampoline);before=c.inst_count;++stage;return;}
    need(stage==2&&pc==Dispatcher&&c.inst_count>=before+5&&c.inst_count<=before+6);
    need(c.gpr==saved&&c.lr==lr&&c.ctr==ctr&&c.xer==xer&&c.msr==msr);
    for(unsigned i=0;i<32;++i){
        if(i==3||i==4||i==5)need(c.mmu.read32(Data+4*i)==0xdeadbeefu);
        else need(c.mmu.read32(Data+4*i)==saved[i]);
    }
    need(c.mmu.read32(Data-4)==0x12345678u&&c.mmu.read32(Data+128)==0x87654321u);
    ++stage;
}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext& c){need(stage==3&&c.pc==Dispatcher);++stops;c.is_running=false;return true;}
void interpret_step(CPUContext&){throw std::runtime_error("V679 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V679 micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V679 null call");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V679 unexpected MMIO");}
uint32_t HW_Reg_Read32(uint32_t){throw std::runtime_error("V679 unexpected MMIO");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V679 unexpected MMIO");}
void HW_Reg_Write32(uint32_t,uint32_t){throw std::runtime_error("V679 unexpected MMIO");}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(){
    using namespace nwii::runtime;
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    for(unsigned trial=0;trial<32;++trial){
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[4]=Data;c.pc=Entry;c.lr=0x80006000u;c.ctr=0x01020304u;c.xer=0x40000000u;c.msr=0x32u;
        c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;
        saved=c.gpr;lr=c.lr;ctr=c.ctr;xer=c.xer;msr=c.msr;stage=0;
        for(unsigned i=0;i<32;++i)c.mmu.write32(Data+4*i,0xdeadbeefu);
        c.mmu.write32(Data-4,0x12345678u);c.mmu.write32(Data+128,0x87654321u);
        run_game(c);
        need(stage==3&&stops==trial+1&&!c.is_running);
    }
    std::cout<<"V679_SYNTHETIC_TRAMPOLINE cases=32 gpr_save=29 backward_tail=1 fallback=0 original_execution=0\n";
}
