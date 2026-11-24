#include "runtime/cpu_context.h"
#include "wii_arena_sc_pair_v598.h"
#include "v574_private_sc_expectations.h"
#include "functions.h"
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
using Pair=undercover::wii::ArenaScPair;
using Route=undercover::wii::BootScRoute;
using Trace=undercover::wii::ArenaCacheRangeTrace;
constexpr uint32_t Entry=0x805222c0;
static std::unique_ptr<Pair> pair;
static bool suppress_arm=false;static unsigned vectors=0,delegated=0;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V598 line "+std::to_string(loc.line()));
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==Route::Call){if(!suppress_arm)pair->arm(pc,c,c.arena_cache_range);return;}
    if(pc==Route::Vector){need(pair->vector_trace(pc,c));++vectors;return;}
    need(pc==Entry);
}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext& c){
    if(!pair->dispatch(c,[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        }))++delegated;
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
    need(argc==2);const std::string_view mode=argv[1];need(mode=="owner"||mode=="synthetic");
    const auto& installed=undercover::wii::v574::expected_vector;
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
    for(unsigned fault=0;fault<=8;++fault){
        pair=std::make_unique<Pair>(installed);c.arena_cache_range={};
        suppress_arm=false;vectors=delegated=0;
        c.guest_dcbz_trace.clear();c.guest_flush_count=87;c.guest_flush_lines.fill(0);
        c.guest_sync_count=c.guest_isync_count=0;c.inst_count=0;
        for(unsigned i=0;i<installed.size();++i){c.mmu.write8(Route::Vector+i,installed[i]);c.mmu.write8(Route::Source+i,installed[i]);}
        c.mmu.write32(Route::Call,0x44000002);c.mmu.write32(Route::Resume,0x4e800020);
        for(unsigned i=0;i<32;++i)c.gpr[i]=i+0x100;
        c.gpr[1]=0x81701000;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        c.is_running=true;c.msr=0x2002;c.hid0=0x110100;c.dispatch_saved_ctx=0;c.srr0=c.srr1=0;
        c.pc=0x80004000;c.lr=0x80004004;need(!nw::handle_syscall(c)&&delegated==1);
        bool rejected=false;
        try{
            for(unsigned lane=1;lane<=2;++lane){
                const uint32_t lo=lane==1?0x81000000u:0x90010000u,hi=lo+0x80000u;
                auto* p=c.mmu.get_ptr(lo);need(p&&c.mmu.get_ptr(hi)==p+(hi-lo));
                std::fill(p,p+hi-lo,0x81);c.mmu.write8(lo-1,0xa5);c.mmu.write8(hi,0x5a);
                c.pc=Entry;c.lr=Pair::Callers[lane-1];
                need(c.arena_cache_range.begin(c,lane,lo,hi));
                for(uint32_t a=lo;a<hi;a+=32)c.guest_dcbz(a);
                need(c.arena_cache_range.begin_flush(c,hi-Trace::Tail,Trace::Tail));
                c.gpr[3]=hi-Trace::Tail;c.gpr[4]=Trace::Tail;
                if(lane==1&&fault==1)c.lr=Pair::Callers[1];
                if(lane==1&&fault==2)suppress_arm=true;
                if(lane==1&&fault==3)c.mmu.write8(Route::Vector,installed[0]^1u);
                if(lane==1&&fault==4)c.mmu.write8(Route::Source,installed[0]^1u);
                if(lane==1&&fault==5)c.msr|=0x8000;
                if(lane==1&&fault==6)c.gpr[4]-=32;
                func_805222C0(c);
                if(lane==1&&fault==7)c.pc+=4;
                need(pair->finish(c));
                if(lane==1&&fault==8){c.pc=Route::Call;c.lr=Pair::Callers[0];nw::handle_syscall(c);}
                need(c.pc==Pair::Callers[lane-1]&&c.msr==0x2002&&c.hid0==0x110100&&vectors==lane&&delegated==1);
                need(c.mmu.read8(lo-1)==0xa5&&c.mmu.read8(hi)==0x5a);
            }
        }catch(const std::exception&){rejected=true;}
        need(rejected==(fault!=0));
        if(!fault)need(pair->completed()==2&&vectors==2&&c.arena_cache_range.zeros()==32768&&
            c.arena_cache_range.flushes()==16384&&c.guest_flush_count==87+16384);
        else need(pair->failed());
    }
    std::cout<<"V598_ARENA_SC owner="<<unsigned(mode=="owner")<<" lanes=2 flush_lines=16384 vectors=2 refusal=8 fallback=0 boot_verified=0\n";
}
