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
static unsigned scenario=0,calls=0;
static constexpr uint32_t Sc=0x80004004u,Resume=0x80004008u,Callback=0x80004100u,Back=0x80006000u;
bool handle_syscall(CPUContext& c){
    need(c.pc==Sc,"handler saw stale syscall PC");++calls;
    c.gpr[3]=0x12345678u;
    if(scenario==1){c.pc=Callback;c.lr=Resume;return true;}
    if(scenario==2)c.is_running=false;
    return false;
}
bool interpret_one(CPUContext&);

}
#ifdef V461_SPLIT
#include "functions.h" // authoritative C linkage from the split emitter
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2,"baseline or fixed");
    const std::string_view mode=argv[1];need(mode=="baseline"||mode=="fixed","mode");
    const bool fixed=mode=="fixed";
    auto c=std::make_unique<nw::CPUContext>();
    auto reset=[&](uint32_t pc,unsigned scenario){
        nw::scenario=scenario;nw::calls=0;c->pc=pc;c->lr=nw::Back;c->is_running=true;
        c->gpr[3]=0;c->gpr[4]=10;c->gpr[5]=20;c->inst_count=100;
    };
    reset(0x80004000u,0);func_80004000(*c);
    need(c->pc==nw::Back&&c->gpr[4]==13&&c->gpr[3]==0x12345678u&&nw::calls==1&&c->inst_count==104,"normal native sc");
    reset(0x80004000u,1);func_80004000(*c);
    if(fixed){
        need(c->pc==nw::Callback&&c->gpr[4]==11&&c->inst_count==102,"native transfer");
        func_80004100(*c);
        need(c->pc==nw::Resume&&c->gpr[5]==24&&c->inst_count==104,"callback return");
        c->lr=nw::Back;func_80004000(*c);
        need(c->pc==nw::Back&&c->gpr[4]==13&&nw::calls==1&&c->inst_count==106,"resume exactly once");
    }else{
        need(c->pc==nw::Resume&&c->gpr[4]==13&&c->gpr[5]==20&&c->inst_count==104,"legacy lost callback");
    }
    reset(0x80004000u,2);func_80004000(*c);
    need(!c->is_running&&nw::calls==1&&c->gpr[4]==(fixed?11u:13u)&&c->pc==(fixed?nw::Sc:nw::Back),"stop after sc");
    c->mmu.write32(nw::Sc,0x44000002u);
    for(unsigned scenario=0;scenario<3;++scenario){
        reset(nw::Sc,scenario);
        need(nw::interpret_one(*c)&&nw::calls==1&&c->gpr[3]==0x12345678u,"real interpreter sc");
        uint32_t expected=nw::Resume;
        if(fixed&&scenario==1)expected=nw::Callback;
        if(fixed&&scenario==2)expected=nw::Sc;
        need(c->pc==expected&&c->is_running==(scenario!=2),"interpreter transfer");
    }
    std::cout<<"V461_SYSCALL_AOT mode="<<mode<<" normal=1 transfer=1 stopped=1 resume=1 interpreter=1\n";
}
