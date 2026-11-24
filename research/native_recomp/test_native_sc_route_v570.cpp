#include "runtime/cpu_context.h"
#include "wii_boot_sc_route_v570.h"
#include "functions.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
constexpr uint32_t Entry=0x805222c0,Sc=Entry+40,Resume=Sc+4,Back=0x80522044,Vector=0x80000c00;
static uint32_t staging=0x81000000;
static std::array<uint8_t,28> installed{};
static unsigned scs=0,vectors=0;
static bool owner=false, stop_after_sc=false;
using Route=undercover::wii::BootScRoute;
static std::unique_ptr<Route> route;
static bool suppress_arm=false;
static unsigned delegated=0;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("SC overlay line "+std::to_string(loc.line()));
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==Sc){if(!suppress_arm)route->arm(pc,c);return;}
    if(pc==Vector){need(route->vector_trace(pc,c));++vectors;return;}
    need(pc==Entry);
}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext& c){
    if(c.pc!=Sc){need(!route->dispatch(c,[](auto&){need(false);},[](auto&,const auto&,uint32_t){return false;}));++delegated;return false;}
    need(c.guest_flush_count==4);
    for(unsigned i=0;i<4;++i)need(c.guest_flush_lines[i]==staging+32*i);
    if(!route->dispatch(c,[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i){
                const uint32_t wanted=owner?(i==9?hid:i==10?(hid|8u):gp[i]):(i==11?gp[i]+1u:gp[i]);
                if(cpu.gpr[i]!=wanted)return false;
            }
            return true;
        })){++delegated;return false;}
    ++scs;
    // V461 honours explicit transfer or a stopped CPU; normal RFI resumes
    // the generated original caller at its following BLR.
    if(stop_after_sc)c.is_running=false;
    return false;
}
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
    need(argc==3);const std::string_view mode=argv[2];need(mode=="owner"||mode=="synthetic");owner=mode=="owner";
    std::ifstream raw(argv[1],std::ios::binary);raw.read(reinterpret_cast<char*>(installed.data()),installed.size());
    need(raw.gcount()==std::streamsize(installed.size())&&raw.peek()==std::char_traits<char>::eof());
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
    auto reset=[&](unsigned trial){
        for(unsigned i=0;i<32;++i)c.gpr[i]=trial*257+i;
        route=std::make_unique<Route>(installed);suppress_arm=false;
        for(unsigned i=0;i<installed.size();++i){c.mmu.write8(Vector+i,installed[i]);c.mmu.write8(Route::Source+i,installed[i]);}
        c.mmu.write32(Sc,0x44000002u);c.mmu.write32(Resume,0x4e800020u);
        staging=0x81000000u+trial*0x100u;
        c.gpr[3]=staging;c.gpr[4]=128;
        c.mmu.write8(staging-1,0xA5);c.mmu.write8(staging+128,0x5A);
        for(unsigned i=0;i<128;++i)c.mmu.write8(staging+i,uint8_t(i^trial));
        c.pc=Entry;c.lr=Back;c.ctr=0x1234+trial;c.msr=trial&1?2u:0x2002u;c.hid0=trial*0x10101u;
        c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;c.srr0=0;c.srr1=0;c.guest_sync_count=0;c.guest_isync_count=0;c.guest_flush_count=0;c.guest_flush_lines.fill(0);
    };
    for(unsigned i=0;i<32;++i){
        reset(i);const auto hid=c.hid0,msr=c.msr;
        func_805222C0(c);
        need(c.pc==Back&&c.hid0==hid&&c.msr==msr&&c.srr0==Resume&&route->returned(c));
        need(scs==i+1&&vectors==i+1&&c.inst_count>7&&c.inst_count<256&&c.guest_flush_count==4);
        need(c.mmu.read8(staging-1)==0xA5&&c.mmu.read8(staging+128)==0x5A);
        for(unsigned j=0;j<128;++j)need(c.mmu.read8(staging+j)==uint8_t(j^i));
    }
    for(unsigned fault=0;fault<6;++fault){
        reset(fault);if(fault==0)c.mmu.write8(Vector,installed[0]^1u);
        if(fault==1)c.msr|=0x8000u;
        if(fault==2)c.dispatch_saved_ctx=0x80001234u;
        if(fault==3)c.mmu.write8(Route::Source,installed[0]^1u);
        if(fault==4)c.mmu.write32(Resume,0x60000000u);
        if(fault==5)suppress_arm=true;
        bool rejected=false;try{func_805222C0(c);}catch(const std::exception&){rejected=true;}
        need(rejected&&scs==32&&vectors==32&&c.pc==Sc&&c.srr0==0&&c.srr1==0&&route->phase()==Route::Phase::Failed);
    }
    reset(34);c.pc=0x80004000;need(!nw::handle_syscall(c)&&delegated==1&&route->phase()==Route::Phase::Idle);
    reset(33);stop_after_sc=true;func_805222C0(c);
    need(!c.is_running&&c.pc==Resume&&scs==33&&vectors==33);
    std::cout<<"V570_SC_ROUTE owner="<<unsigned(owner)<<" trials=32 lines=128 vectors=32 refusal=6 delegated=1 stop=1 fallback=0 boot_verified=0\n";
}
