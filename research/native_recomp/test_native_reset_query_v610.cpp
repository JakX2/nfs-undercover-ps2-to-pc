#include "runtime/cpu_context.h"
#include "wii_arena_reset_v606.h"
#include "functions.h"
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
using P=undercover::wii::ArenaResetProfile;
using B=undercover::wii::ArenaResetBinding;
static constexpr uint32_t Entry=0x805285d0,Flag=0x806f4f0c;
static constexpr std::array<uint32_t,2> Callers{0x8051ffe0,0x805201bc};
static unsigned entries=0,reads=0;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V610 line "+std::to_string(l.line()));
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){need(pc==Entry&&(c.lr==Callers[0]||c.lr==Callers[1]));++entries;}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext&){throw std::runtime_error("unexpected syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected MMIO");}
uint32_t HW_Reg_Read32(uint32_t a){
    auto v=B::read32(a);need(v.has_value());++reads;return *v;
}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write32(uint32_t,uint32_t){throw std::runtime_error("unexpected MMIO");}
}
int main(int argc,char** argv){
    need(argc==2);const std::string_view mode=argv[1];need(mode=="owner"||mode=="synthetic");
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
    auto init=[&](unsigned trial,unsigned lane){
        for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+trial*257+i;
        c.gpr[1]=0x80751c00u-trial*16;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        c.pc=Entry;c.lr=Callers[lane];c.ctr=0x12345678+trial;c.msr=0x32;
        c.inst_count=0;c.is_running=true;c.dispatch_saved_ctx=0;
        c.mmu.write32(Flag,0);c.mmu.write32(Flag-4,0xaabbccdd);c.mmu.write32(Flag+4,0x11223344);
    };
    for(unsigned trial=0;trial<16;++trial){
        P p;B bind(p);
        for(unsigned lane=0;lane<2;++lane){
            init(trial,lane);auto gp=c.gpr;auto before=reads;
            need(p.arm(lane+1));func_805285D0(c);
            need(c.pc==Callers[lane]&&c.lr==Callers[lane]&&c.is_running&&c.gpr[3]==P::ColdValue/8u&&
                 c.msr==0x32&&c.ctr==0x12345678+trial&&c.inst_count>0&&c.inst_count<=12);
            need(c.gpr[1]==gp[1]&&c.gpr[2]==gp[2]&&c.gpr[13]==gp[13]&&reads==before+1&&p.reads()==lane+1);
            for(unsigned i=14;i<32;++i)need(c.gpr[i]==gp[i]);
            need(c.mmu.read32(Flag)==0&&c.mmu.read32(Flag-4)==0xaabbccdd&&c.mmu.read32(Flag+4)==0x11223344);
        }
        need(p.complete());
    }
    need(entries==32&&reads==32);
    for(unsigned fault=0;fault<2;++fault){
        P p;B bind(p);init(0,0);if(fault){need(p.arm(1));func_805285D0(c);init(0,0);}
        bool rejected=false;try{func_805285D0(c);}catch(const std::exception&){rejected=true;}
        need(rejected&&p.failed());
    }
    std::cout<<"V610_RESET_NATIVE owner="<<unsigned(mode=="owner")<<" trials=16 reads=32 returned=32 refusal=2 fallback=0 boot_verified=0\n";
}
