#include "runtime/cpu_context.h"
#include "functions.h"
#include "v603_private_report_expectations.h"
#include "v650_private_words.h"
#include <iostream>
#include <memory>
#include <source_location>
#include <stdexcept>
namespace nw=nwii::runtime;
using namespace undercover::wii;
using W=BootReportWitness;
static W* witness=nullptr;
static unsigned trial=0,line=0,reason=0,stage=0,reports=0,getters=0,mask=0,computed=0,console=0;
struct Stop{};struct Failure{};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b){line=l.line();throw Failure{};}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(witness);
    if(pc==W::Begin)return;
    if(pc==0x80520410u)console=c.gpr[3]>=0x10000000u&&c.gpr[3]<=0x10000022u?c.gpr[3]-0x10000000u:c.gpr[3]<32?35+c.gpr[3]:67;
    const bool ok=witness->observe(pc,c);
    reason=witness->failure();stage=witness->stage();reports=witness->reports();getters=witness->getters();mask=witness->print_refusal();computed=witness->computed();
    need(ok);
    if(stage==3)throw Stop{};
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
    const auto& exp=v603::expected_report;
    for(trial=0;trial<16;++trial){
        auto c=std::make_unique<nw::CPUContext>();auto& m=c->mmu;
        reason=stage=reports=getters=mask=computed=console=0;
        for(auto w:v650::words)m.write32(w.pc,w.word);
        for(unsigned i=0;i<exp.data.size();++i)m.write8(W::Data+i,exp.data[i]);
        for(unsigned i=0;i<exp.small.size();++i)m.write8(W::Small+i,exp.small[i]);
        // Explicit predecessor state, not a claim of continuous __start.
        constexpr uint32_t sda=0x8070e8e0u,sp=0x80751c60u;
        const unsigned mode=trial%8u;
        m.write32(sda-3400u,1);m.write32(sda-3512u,0x80000000u);
        m.write32(sda-16400u,0x80754000u);m.write32(sda-3472u,0x81700000u);
        m.write32(sda-16396u,0x90000800u);m.write32(sda-3468u,0x93380000u);
        m.write32(0x80000020u,0x10000006u);
        m.write32(0x8000002cu,mode<4?0x10000006u:mode==4?0u:0x10000002u);
        m.write16(0x800030e6u,mode==0||mode==1?0u:mode==2||mode==5?2u:0x8000u);
        m.write32(0x80003118u,mode>=6?0x08000000u:0x04000000u);
        m.write32(0x80003138u,mode==7?17u:mode==5?1u:0u);
        m.write32(0x80003100u,0x01800000u);m.write32(0x80003104u,0x01800000u);m.write32(0x80000028u,0x01800000u);m.write32(0x8000311cu,0x04000000u);
        m.write32(0x80003140u,trial<8?0u:0x00040a21u);m.write32(0x80003144u,trial<8?0u:0x00191226u);
        for(unsigned i=0;i<32;++i)c->gpr[i]=0x12340000u+trial*32+i;
        c->gpr[1]=sp;c->gpr[2]=0x80715ee0u;c->gpr[13]=sda;
        c->pc=c->lr=W::Begin;c->msr=0x32;c->is_running=true;c->inst_count=100;
        W w(exp);witness=&w;need(w.begin(*c));bool stopped=false;
        try{run_game(*c);}catch(const Stop&){stopped=true;}
        need(stopped&&w.stage()==3&&w.reports()==10&&w.getters()==6&&c->pc==W::Return);
        constexpr std::array<unsigned,8> classes{51,51,51,51,2,52,16,33};
        need(console==classes[mode]);
        std::cout<<"V650_REPORT_TRIAL n="<<trial<<" class="<<console<<" calls=10 getters=6 computed="<<computed<<"\n";
        witness=nullptr;
    }
    std::cout<<"V650_REPORT_NATIVE trials=16 returned=16 calls=160 getters=96 output_backend=0 fallback=0 complete_image=0\n";
}catch(const Failure&){
    std::cout<<"V650_REPORT_FAILURE trial="<<trial<<" line="<<line<<" reason="<<reason<<" stage="<<stage<<" reports="<<reports<<" getters="<<getters<<" mask="<<mask<<"\n";return 1;
}catch(const std::exception&){std::cout<<"V650_REPORT_FAILURE trial="<<trial<<" kind=exception\n";return 1;}
