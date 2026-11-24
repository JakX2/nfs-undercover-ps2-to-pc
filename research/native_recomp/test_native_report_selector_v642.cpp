#include "runtime/cpu_context.h"
#include "functions.h"
#include "v642_private_report.h"
#include <algorithm>
#include <iostream>
#include <memory>
#include <source_location>
#include <stdexcept>
namespace nw=nwii::runtime;
constexpr uint32_t Entry=0x80520410,Print=0x80522f00,Data=0x8060b7a8;
static unsigned trial=0,line=0,hits=0,site=0,fmt=0,arg=0,cr=0;
static uint32_t input=0,actual=0;static bool query=false;
struct Stop{};struct Failure{};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b){line=l.line();throw Failure{};}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==Entry){actual=c.gpr[3];return;}
    if(std::find(v642::roots.begin(),v642::roots.end(),pc)!=v642::roots.end()){need(query);return;}
    need(pc==Print&&c.pc==Print&&++hits==1);
    auto it=std::find(v642::sites.begin(),v642::sites.end(),c.lr);
    need(it!=v642::sites.end()&&c.gpr[3]>=Data&&c.gpr[3]<Data+496);
    site=unsigned(it-v642::sites.begin());fmt=c.gpr[3]-Data;arg=unsigned(c.gpr[4]==actual);cr=unsigned(c.cr[1].eq);
    throw Stop{};
}
bool process_pending_callbacks(CPUContext&){return false;}
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
    auto c=std::make_unique<nw::CPUContext>();
    for(trial=0;trial<75;++trial){
        query=trial>=67;
        input=trial<35?0x10000000u+trial:trial<67?trial-35u:0u;
        actual=input;
        for(unsigned i=0;i<32;++i)c->gpr[i]=0x12340000u+i;
        c->gpr[1]=0x80751c50;c->gpr[2]=0x80715ee0;c->gpr[13]=0x8070e8e0;
        // Original report prologue carries the format data in a saved
        // register. The private fixture checks its identity separately.
        c->gpr[31]=Data;c->gpr[3]=input;c->pc=c->lr=Entry;c->msr=0x32;c->is_running=true;c->inst_count=0;
        if(query){
            const unsigned mode=trial-67u;
            c->pc=0x8051fd44u;
            c->mmu.write32(0x8000002cu,mode<4?0x10000006u:mode==4?0u:0x10000002u);
            c->mmu.write16(0x800030e6u,mode==0||mode==1?0u:mode==2||mode==5?2u:0x8000u);
            c->mmu.write32(0x80003118u,mode>=6?0x08000000u:0x04000000u);
            c->mmu.write32(0x8000311cu,0x04000000u);
            c->mmu.write32(0x80003138u,mode==7?17u:mode==5?1u:0u);
        }
        for(unsigned i=0;i<v642::data.size();++i)c->mmu.write8(Data+i,v642::data[i]);
        hits=0;bool stopped=false;
        try{run_game(*c);}catch(const Stop&){stopped=true;}
        need(stopped&&hits==1&&c->gpr[1]==0x80751c50&&c->inst_count<256);
        const unsigned kind=actual>=0x10000000u&&actual<=0x10000022u?actual-0x10000000u:actual<32u?35u+actual:67u;
        std::cout<<"V644_REPORT_CASE trial="<<trial<<" class="<<kind<<" call_offset="<<v642::sites[site]-Entry<<" fmt="<<fmt<<" value_arg="<<arg<<" cr="<<cr<<"\n";
    }
    std::cout<<"V644_REPORT_NATIVE trials=75 returned_to_print=75 query=8 fallback=0 complete_image=0\n";
}catch(const Failure&){std::cout<<"V642_REPORT_FAILURE trial="<<trial<<" line="<<line<<"\n";return 1;}
catch(const std::exception&){std::cout<<"V642_REPORT_FAILURE trial="<<trial<<" kind=exception\n";return 1;}
