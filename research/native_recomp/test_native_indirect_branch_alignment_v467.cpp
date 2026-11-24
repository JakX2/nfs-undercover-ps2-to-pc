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
bool interpret_one(CPUContext&);

}
#ifdef V467_SPLIT
#include "functions.h" // authoritative C linkage from the split emitter
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
void func_80004200(nw::CPUContext&);
void func_80004300(nw::CPUContext&);
void func_80004400(nw::CPUContext&);
void func_80004500(nw::CPUContext&);
void func_80004600(nw::CPUContext&);
#endif
int main(int argc,char** argv){
    need(argc==2,"baseline or fixed");
    const std::string_view mode=argv[1];need(mode=="baseline"||mode=="fixed","mode");
    const bool fixed=mode=="fixed";
    using Fn=void(*)(nw::CPUContext&);
    struct Test{Fn f;uint32_t root;unsigned xo,bo,bi,lk;};
    const Test tests[]={
        {func_80004000,0x80004000u,16,20,0,0},{func_80004100,0x80004100u,16,20,0,1},
        {func_80004200,0x80004200u,528,20,0,0},{func_80004300,0x80004300u,528,20,0,1},
        {func_80004400,0x80004400u,16,12,2,0},{func_80004500,0x80004500u,528,12,2,1},
        {func_80004600,0x80004600u,16,16,0,1}};
    auto native=std::make_unique<nw::CPUContext>(),reference=std::make_unique<nw::CPUContext>();
    unsigned taken_count=0,not_taken_count=0,mismatches=0;
    for(const auto& x:tests)for(unsigned low=0;low<4;++low)for(unsigned pred=0;pred<2;++pred){
        const uint32_t raw=0x80006000u|low;
        auto setup=[&](nw::CPUContext& c){
            c.pc=x.root;c.lr=raw;c.ctr=x.xo==528?raw:pred+1u;c.cr[0].eq=pred!=0;
            c.is_running=true;c.inst_count=100;
        };
        setup(*native);setup(*reference);
        const uint32_t opcode=(19u<<26)|(x.bo<<21)|(x.bi<<16)|(x.xo<<1)|x.lk;
        reference->mmu.write32(x.root,opcode);
        reference->mmu.write32(x.root+4,0x48000000u|((0x80100000u-x.root-4)&0x03fffffcu));
        need(nw::interpret_one(*reference),"reference branch");
        const bool taken=reference->pc!=x.root+4;
        if(!taken){++not_taken_count;need(nw::interpret_one(*reference),"reference tail");}
        else ++taken_count;
        x.f(*native);
        need(native->lr==reference->lr&&native->ctr==reference->ctr&&native->is_running,"branch register semantics");
        if(native->inst_count!=(taken?101u:102u)){
            std::cerr<<"V467_SYNTHETIC_MISMATCH xo="<<x.xo<<" bo="<<x.bo<<" lk="<<x.lk<<" low="<<low<<" predicate="<<pred<<" taken="<<taken<<" ticks="<<native->inst_count-100<<"\n";
            throw std::runtime_error("dynamic instruction count");
        }
        const bool mismatch=native->pc!=reference->pc;
        need(mismatch==(!fixed&&taken&&low!=0),"native aligned target comparison");
        if(mismatch)++mismatches;
        need(native->pc==(taken?(fixed?raw&~3u:raw):0x80100000u),"exact target");
    }
    need(taken_count==44&&not_taken_count==12&&mismatches==(fixed?0u:33u),"coverage");
    std::cout<<"V467_BRANCH_AOT mode="<<mode<<" taken=44 not_taken=12 mismatches="<<mismatches<<" lr_ctr=1 ticks=1\n";
}
