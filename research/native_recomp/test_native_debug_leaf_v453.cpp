#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
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
#ifdef V453_SPLIT
#include "functions.h"
#else
void func_804E50B8(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2,"word count");
    const unsigned words=std::stoul(argv[1]);need(words>=1&&words<=32,"word bound");
    auto c=std::make_unique<nw::CPUContext>();
    for(unsigned run=0;run<4;++run){
        c->pc=0x804e50b8u;c->lr=0x80006000u+4*run;c->is_running=true;c->inst_count=100;
        for(unsigned i=0;i<32;++i){c->gpr[i]=0x12345678u+100*run+i;c->fpr[i]=double(i+run)*0.5;c->ps1[i]=double(i+run)*0.25;}
        c->gpr[1]=0x80751cb8u;c->gpr[3]=run?0x80010000u:0u;
        for(unsigned i=0;i<c->cr.size();++i){
            auto& f=c->cr[i];f.lt=(i+run)&1u;f.gt=(i+run)&2u;f.eq=(i+run)&4u;f.so=(i+run)&8u;
        }
        c->xer=run<<29;c->ctr=7+run;c->msr=0x2000u;c->fpscr=run;
        const auto gpr=c->gpr;const auto fpr=c->fpr;const auto ps1=c->ps1;
        const auto cr=c->cr;
        const auto lr=c->lr,xer=c->xer,ctr=c->ctr,msr=c->msr,fpscr=c->fpscr;
        func_804E50B8(*c);
        need(c->pc==lr&&c->lr==lr&&c->is_running&&c->inst_count==100+words,"return or exact ticks");
        need(c->gpr==gpr&&c->fpr==fpr&&c->ps1==ps1&&c->xer==xer&&c->ctr==ctr&&c->msr==msr&&c->fpscr==fpscr,"leaf ABI");
        for(unsigned i=0;i<cr.size();++i){
            const auto& a=cr[i];const auto& b=c->cr[i];
            need(a.lt==b.lt&&a.gt==b.gt&&a.eq==b.eq&&a.so==b.so,"condition field preservation");
        }
    }
    std::cout<<"V453_DEBUG_NATIVE runs=4 words="<<std::dec<<words<<" return=1 abi=1 fallback=0 boot_verified=0\n";
}
