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
#ifdef V456_SPLIT
#include "functions.h" // authoritative C linkage from the split emitter
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
#endif
int main(){
    auto c=std::make_unique<nw::CPUContext>();
    constexpr uint32_t back=0x80006000u;
    auto reset=[&](uint32_t pc){
        c->pc=pc;c->lr=back;c->is_running=true;c->inst_count=100;
        c->gpr[0]=0xccccccccu;c->gpr[3]=0x80010013u;
        c->gpr[4]=0x90020000u;c->gpr[5]=0x37u;
        c->guest_dcbz_trace.clear();
        c->guest_flush_count=c->guest_invalidate_count=c->guest_sync_count=c->guest_isync_count=0;
        c->guest_store_count=c->guest_eieio_count=0;
    };
    auto fill=[&](uint32_t line){
        for(int i=-1;i<=32;++i){auto* p=c->mmu.get_ptr(line+uint32_t(i));need(p!=nullptr,"mapped");*p=0xa7;}
    };
    auto bytes=[&](uint32_t line,bool zero){
        for(int i=-1;i<=32;++i){auto* p=c->mmu.get_ptr(line+uint32_t(i));need(p&&*p==(zero&&i>=0&&i<32?0:0xa7),"line or guard");}
    };
    for(uint32_t alias:{0x80000000u,0xc0000000u,0x00000000u}){
        reset(0x80004000u);c->gpr[3]=alias+0x10013u;
        fill(0x80010000u);fill(0x90020020u);const auto regs=c->gpr;
        func_80004000(*c);
        need(c->pc==back&&c->lr==back&&c->gpr==regs&&c->inst_count==108,"ABI/ticks");
        bytes(0x80010000u,true);bytes(0x90020020u,false);
        need(c->guest_dcbz_trace.count==1&&c->guest_dcbz_trace.last==alias+0x10000u,"dcbz address");
        need(c->guest_store_count==1&&c->guest_last_store==0x90020020u&&c->guest_eieio_count==1,"dcbst/eieio");
        need(c->guest_flush_count==1&&c->guest_flush_lines[0]==alias+0x10000u&&
             c->guest_invalidate_count==1&&c->guest_invalidate_lines[0]==0x90020020u&&
             c->guest_sync_count==1&&c->guest_isync_count==1,"cache order");
    }
    for(uint32_t alias:{0x90000000u,0xd0000000u}){
        reset(0x80004100u);c->gpr[4]=alias+0x20000u;
        fill(0x90020020u);func_80004100(*c);
        bytes(0x90020020u,true);
        need(c->pc==back&&c->inst_count==102&&c->guest_dcbz_trace.last==alias+0x20020u,"indexed MEM2");
    }
    for(uint32_t addr:{0xcc008000u,0x81800000u,0x94000000u}){
        reset(0x80004100u);c->gpr[4]=addr;c->gpr[5]=0;
        fill(0x80010000u);fill(0x90020020u);
        bool rejected=false;try{func_80004100(*c);}catch(const std::runtime_error& e){rejected=std::string_view(e.what())=="dcbz requires complete contiguous guest RAM cache line";}
        need(rejected&&c->guest_dcbz_trace.count==0,"invalid block rejected");
        bytes(0x80010000u,false);bytes(0x90020020u,false);
    }
    std::cout<<"V456_CACHE_AOT valid=5 invalid=3 ticks=1 guards=1 ordering=1 fallback=0\n";
}
