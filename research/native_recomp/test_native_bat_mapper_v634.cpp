#include "runtime/cpu_context.h"
#include "functions.h"
#include "v634_private_bat.h"
#include <algorithm>
#include <iostream>
#include <memory>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=BatMappingWitness;
namespace nw=nwii::runtime;
static W* witness=nullptr;
static unsigned trial=0,stage=0,reason=0,line=0,dispatches=0,returns=0;
static constexpr uint32_t root=0x80527568,outer_return=0x80527770,helper=0x80527550;
struct Stop {};
struct Failure {};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b){line=l.line();throw Failure{};}
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(witness);
    const bool ok=pc==root?witness->begin(c,true):witness->observe(pc,c);
    stage=witness->stage();reason=witness->failure();need(ok);
}
bool process_pending_callbacks(CPUContext& c){
    need(witness&&c.is_running&&!c.dispatch_saved_ctx&&++dispatches<=128);
    if(c.pc==outer_return){
        need(stage==7&&c.lr==outer_return&&witness->final_state(c));++returns;throw Stop{};
    }
    if(c.pc==root||c.pc==W::Resume[0]||c.pc==W::Resume[1]||
       c.pc==(W::Entry[0]&0x3fffffffu)||c.pc==(W::Entry[1]&0x3fffffffu))return false;
    need(std::find(v634::polls.begin(),v634::polls.end(),c.pc)!=v634::polls.end());return false;
}
bool handle_syscall(CPUContext&){need(false);return false;}
void interpret_step(CPUContext&){need(false);}
void micro_interpret(CPUContext&,uint32_t,uint32_t){need(false);}
void note_null_call(uint32_t,uint32_t){need(false);}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){need(false);}void GX_WGPIPE_Write16(uint16_t){need(false);}void GX_WGPIPE_Write32(uint32_t){need(false);}
void GX_WGPIPE_WriteF32(float){need(false);}void GX_WGPIPE_WriteF64(double){need(false);}
uint16_t HW_Reg_Read16(uint32_t){need(false);return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){need(false);}
uint32_t HW_Reg_Read32(uint32_t){need(false);return 0;}
void HW_Reg_Write32(uint32_t,uint32_t){need(false);}
}
extern "C" void run_game(nw::CPUContext&);
int main()try{
    for(trial=0;trial<16;++trial){
        auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
        W w(v634::expected);witness=&w;stage=reason=dispatches=0;
        for(auto x:v634::words)c.mmu.write32(x.pc,x.word);
        c.mmu.write32(0x80003100,0x01800000);c.mmu.write32(0x80003104,0x01800000);
        c.mmu.write32(0x8000311c,0x04000000);c.mmu.write32(0x80003120,0x93400000);
        for(unsigned i=0;i<32;++i){c.gpr[i]=0x12340000u+trial*32+i;c.bat_registers[i]=0xaaaa0000u+trial*32+i;}
        const uint32_t prior=(trial/4)*8;
        for(unsigned i=0;i<prior;++i)c.write_bat(528+i%16,0xbbbb0000u+i);
        c.gpr[1]=0x80751c20;c.gpr[2]=0x80715ee0;c.gpr[3]=0x000ba2cf;c.gpr[13]=0x8070e8e0;
        const uint32_t initial_msr=2u|((trial&3u)<<4)|((trial&4u)?0x1000u:0u);
        c.msr=initial_msr;c.pc=root;c.lr=outer_return;c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;
        const auto stack=c.gpr[1];const auto before=c.gpr;
        bool stopped=false;
        try{run_game(c);}catch(const Stop&){stopped=true;}
        need(stopped&&returns==trial+1&&stage==7&&c.pc==outer_return&&c.gpr[1]==stack&&c.msr==(initial_msr|0x30u));
        need(c.bat_write_count==prior+32&&c.srr0==W::Resume[1]&&c.srr1==(initial_msr|0x30u));
        for(unsigned i=14;i<32;++i)need(c.gpr[i]==before[i]);
        witness=nullptr;
    }
    std::cout<<"V634_BAT_NATIVE owner=1 trials=16 returned=16 physical=32 rfi_returns=32 writes=512 modes=4 fallback=0 permissions=0 complete_image=0 boot_verified=0\n";
}catch(const Failure&){
    std::cout<<"V634_BAT_FAILURE trial="<<trial<<" stage="<<stage<<" reason="<<reason<<" line="<<line<<"\n";return 1;
}catch(const std::exception&){std::cout<<"V634_BAT_FAILURE kind=exception trial="<<trial<<" stage="<<stage<<"\n";return 1;}
