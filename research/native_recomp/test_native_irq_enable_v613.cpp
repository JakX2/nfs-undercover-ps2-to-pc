#include "runtime/cpu_context.h"
#include "functions.h"
#include "v613_expected.h"
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
constexpr uint32_t Entry=0x805265c0,Back=0x80520948;
static unsigned entries=0,callbacks=0,yields=0;
static bool suspend=false;
static uint32_t before=0;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V613 line "+std::to_string(l.line()));
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){need(pc==Entry&&c.pc==Entry&&c.lr==Back);++entries;}
bool process_pending_callbacks(CPUContext& c){
    need(c.pc==Resume&&c.msr==(before|0x8000u)&&!(before&0x8000u)&&c.lr==Back);
    ++callbacks;
    if(suspend){++yields;return true;}return false;
}
bool handle_syscall(CPUContext&){throw std::runtime_error("unexpected syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected MMIO");}
uint32_t HW_Reg_Read32(uint32_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write32(uint32_t,uint32_t){throw std::runtime_error("unexpected MMIO");}
}
int main(int argc,char** argv){
    need(argc==2);const std::string_view mode=argv[1];need(mode=="owner"||mode=="synthetic");
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
    for(unsigned trial=0;trial<32;++trial){
        for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+trial*257+i;
        c.gpr[1]=0x80751c60;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        before=0x32u|((trial&2u)?0x2000u:0u)|((trial&1u)?0x8000u:0u)|((trial&4u)?0x1000u:0u);
        suspend=!(trial&1u)&&bool(trial&8u);
        c.pc=Entry;c.lr=Back;c.ctr=0x12345678+trial;c.msr=before;c.inst_count=0;c.is_running=true;
        c.dispatch_saved_ctx=0;c.srr0=0x12345678;c.srr1=0x76543210;
        auto gp=c.gpr;const unsigned cb=callbacks,oldentries=entries;
        func_805265C0(c);
        if(suspend){
            need(c.pc==Resume&&c.inst_count==(Resume-Entry)/4&&callbacks==cb+1);
            const auto tick=c.inst_count;
            suspend=false;func_805265C0(c);
            need(c.inst_count==tick+(Entry+20-Resume)/4&&callbacks==cb+1);
        }
        need(c.pc==Back&&c.lr==Back&&c.is_running&&c.msr==(before|0x8000u)&&
             c.gpr[3]==unsigned(bool(before&0x8000u))&&c.inst_count==5&&entries==oldentries+1);
        need(callbacks==cb+unsigned(!(before&0x8000u))&&c.ctr==0x12345678+trial&&
             c.srr0==0x12345678&&c.srr1==0x76543210&&c.gpr[1]==gp[1]&&c.gpr[2]==gp[2]&&c.gpr[13]==gp[13]);
        for(unsigned i=14;i<32;++i)need(c.gpr[i]==gp[i]);
    }
    need(entries==32&&callbacks==16&&yields==8);
    std::cout<<"V613_IRQ_NATIVE owner="<<unsigned(mode=="owner")<<" trials=32 returned=32 callbacks=16 yields=8 native_resume=8 fallback=0 actual_irq=0 boot_verified=0\n";
}
