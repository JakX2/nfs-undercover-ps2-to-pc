#include "runtime/cpu_context.h"
#include "undercover/wii_postack_os_leaf_v703.h"
#include "leaf_test.h"
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,D=0x80005000u,T=0x80006000u,R=0x80007000u;
static uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
static void need(bool ok){if(!ok)throw std::runtime_error("V705 native leaf assertion");}
static PostAckOsLeaf leaves[]={PostAckOsLeaf({H,D,D+16,bl(H,D),1}),
    PostAckOsLeaf({H+4,T,T+12,bl(H+4,T),2}),
    PostAckOsLeaf({H+12,R,R+12,bl(H+12,R),3})};
static unsigned index=0;static bool started=false;static unsigned outer_polls=0;
static std::string mode;
namespace leaf_test{
void before(nwii::runtime::CPUContext& c,uint32_t pc,uint32_t word){
    if(pc>=H&&pc<H+24){
        if(started){
            if(mode=="corrupt"&&index==0)c.gpr[14]^=1u;
            const bool ok=leaves[index].returned(c,pc);
            if(mode=="corrupt"&&index==0){need(!ok&&leaves[index].failure()==4);std::cout<<"V705_REFUSAL reason=4\n";std::_Exit(126);}
            need(ok);++index;started=false;
        }
        if(pc==H+8){need(index==2);return;}
        if(pc==H+16){
            need(index==3&&outer_polls==1&&c.msr==0x32u&&c.gpr[3]==0&&c.srr0==0x80009000u&&c.srr1==0x8032u);
            need(leaves[0].msr_writes()==1&&leaves[1].msr_writes()==0&&leaves[2].msr_writes()==1);
            std::cout<<"V705_LEAF_AOT roots=3 mtmsr=2 inner_callbacks=0 native_return=3 fallback=0\n";std::_Exit(0);
        }
        need(index<3&&leaves[index].start(c,pc,word));started=true;return;
    }
    need(started&&index<3);
    need(leaves[index].before(c,pc,word));
}}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==H)return;
    need(started&&index<3&&leaves[index].entry(pc,c));
}
bool process_pending_callbacks(CPUContext& c){
    if(started){need(!leaves[index].poll(c));throw std::runtime_error("unexpected inner callback");}
    ++outer_polls;return false;
}
bool handle_syscall(CPUContext&){throw std::runtime_error("unexpected syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null call");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected MMIO");}
uint32_t HW_Reg_Read32(uint32_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write32(uint32_t,uint32_t){throw std::runtime_error("unexpected MMIO");}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char**argv){
    need(argc==2);mode=argv[1];auto cpu=std::make_unique<nwii::runtime::CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,std::initializer_list<uint32_t> w){for(auto x:w){c.mmu.write32(a,x);a+=4;}};
    put(H,{bl(H,D),bl(H+4,T),0x38600000u,bl(H+12,R),0x60000000u,0x4e800020u});
    put(D,{0x7c0000a6u,0x7c000124u,0x38600000u,0x4e800020u});
    put(T,{0x7c8c42e6u,0x7c6d42e6u,0x4e800020u});
    put(R,{0x7c0000a6u,0x7c000124u,0x4e800020u});
    for(unsigned r=0;r<32;++r)c.gpr[r]=0x12340000u+r;
    c.gpr[1]=0x80011000u;c.pc=H;c.lr=0x80008000u;c.msr=0x32u;c.srr0=0x80009000u;c.srr1=0x8032u;
    c.is_running=true;c.dispatch_saved_ctx=0;run_game(c);throw std::runtime_error("leaf fixture escaped");
}
