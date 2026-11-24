#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include "wii_debug_stack_oracle_v458.h"
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
#ifdef V458_SPLIT
#include "functions.h"
#else
void func_804E50B8(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2,"private DOL");
    nwii::loader::Executable exe;
    need(exe.load_dol(argv[1])&&exe.entry_point==0x804e50b8u&&exe.sections.size()==1,"image");
    const auto& data=exe.sections[0].data;
    need(!data.empty()&&data.size()%4==0&&data.size()<=256,"extent");
    std::vector<uint32_t> words;
    for(size_t i=0;i<data.size();i+=4){uint32_t w=0;for(unsigned n=0;n<4;++n)w=(w<<8)|data[i+n];words.push_back(w);}
    auto c=std::make_unique<nw::CPUContext>();unsigned conditional=0;
    uint64_t min_ticks=65,max_ticks=0;
    for(unsigned run=0;run<8;++run){
        c->pc=0x804e50b8u;c->lr=0x80006000u+4u*run;c->is_running=true;c->inst_count=100;
        for(unsigned i=0;i<32;++i){c->gpr[i]=0x12345678u+100u*run+i;c->fpr[i]=double(i+run)*0.5;c->ps1[i]=double(i+run)*0.25;}
        c->gpr[1]=0x80751c00u+run*0x400u;c->gpr[3]=0x80010000u+run*4u;
        for(unsigned i=0;i<c->cr.size();++i){auto& f=c->cr[i];f.lt=(i+run)&1u;f.gt=(i+run)&2u;f.eq=(i+run)&4u;f.so=(i+run)&8u;}
        c->cr[1].eq=(run&1u)!=0;
        c->xer=run<<29;c->ctr=7+run;c->msr=0x2000u;c->fpscr=run;
        undercover::wii::DebugStackState oracle{};
        oracle.gpr=c->gpr;oracle.fpr=c->fpr;oracle.base=c->gpr[1]-256u;
        for(unsigned i=0;i<c->cr.size();++i){
            const auto& f=c->cr[i];oracle.cr[i*4]=f.lt;oracle.cr[i*4+1]=f.gt;oracle.cr[i*4+2]=f.eq;oracle.cr[i*4+3]=f.so;
        }
        for(unsigned i=0;i<oracle.stack.size();++i){
            oracle.stack[i]=uint8_t(0xa7u^i^run);
            c->mmu.write8(oracle.base+i,oracle.stack[i]);
        }
        c->mmu.write8(oracle.base-1,0x6bu);c->mmu.write8(oracle.base+512,0x9du);
        const auto expected=undercover::wii::reference_debug_stack(words,oracle);
        const auto fpr=c->fpr;const auto ps1=c->ps1;const auto cr=c->cr;
        const auto lr=c->lr,xer=c->xer,ctr=c->ctr,msr=c->msr,fpscr=c->fpscr;
        func_804E50B8(*c);
        need(c->pc==lr&&c->lr==lr&&c->is_running&&c->inst_count==100+expected.ticks,"return/ticks");
        need(c->gpr==expected.gpr&&c->fpr==fpr&&c->ps1==ps1&&c->xer==xer&&c->ctr==ctr&&c->msr==msr&&c->fpscr==fpscr,"register ABI");
        for(unsigned i=0;i<cr.size();++i){
            const auto& a=cr[i];const auto& b=c->cr[i];
            need(a.lt==b.lt&&a.gt==b.gt&&a.eq==b.eq&&a.so==b.so,"condition bits");
        }
        for(unsigned i=0;i<expected.stack.size();++i)need(c->mmu.read8(expected.base+i)==expected.stack[i],"stack byte");
        need(c->mmu.read8(expected.base-1)==0x6bu&&c->mmu.read8(expected.base+512)==0x9du,"stack guards");
        if(expected.stack!=oracle.stack)++conditional;
        if(expected.ticks<min_ticks)min_ticks=expected.ticks;if(expected.ticks>max_ticks)max_ticks=expected.ticks;
    }
    need(conditional==8&&min_ticks<max_ticks,"both conditional stack paths");
    std::cout<<"V458_DEBUG_NATIVE runs=8 stack=1 conditional=2 return=1 abi=1 fallback=0 boot_verified=0\n";
}
