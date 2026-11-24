#include "runtime/cpu_context.h"
#include "native_sc_vector_v63.h"
#include "functions.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
constexpr uint32_t Entry=0x805222c0,Sc=Entry+40,Resume=Sc+4,Back=0x80006000,Vector=0x80000c00;
static uint32_t staging=0x81000000;
static std::array<uint8_t,28> installed{};
static unsigned scs=0,vectors=0;
static bool owner=false, stop_after_sc=false;
static unsigned expected_syncs=0,expected_isyncs=0;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("SC overlay line "+std::to_string(loc.line()));
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext&){if(pc==Vector)++vectors;else need(pc==Entry);}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext& c){
    need(c.pc==Sc&&c.guest_flush_count==4);
    for(unsigned i=0;i<4;++i)need(c.guest_flush_lines[i]==staging+32*i);
    const auto prior_sync=c.guest_sync_count,prior_isync=c.guest_isync_count;
    const auto gp=c.gpr;const uint32_t hid=c.hid0,msr=c.msr,lr=c.lr,ctr=c.ctr;
    boot_native_sc(c,Vector,installed,[](auto& cpu){func_80000C00(cpu);});
    need(c.pc==Resume&&c.hid0==hid&&c.msr==msr&&c.lr==lr&&c.ctr==ctr);
    for(unsigned i=0;i<32;++i){
        const uint32_t wanted=owner?(i==9?hid:i==10?(hid|8u):gp[i]):(i==11?gp[i]+1u:gp[i]);
        need(c.gpr[i]==wanted);
    }
    need(c.guest_sync_count-prior_sync==expected_syncs&&c.guest_isync_count-prior_isync==expected_isyncs);
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
    unsigned syncs=0,isyncs=0;
    for(unsigned i=0;i<installed.size();i+=4){
        const uint32_t word=(uint32_t(installed[i])<<24)|(uint32_t(installed[i+1])<<16)|(uint32_t(installed[i+2])<<8)|installed[i+3];
        if(word==0x4c00012cu)++isyncs;
        if(word>>26==31&&((word>>1)&1023u)==598u)++syncs;
    }
    expected_syncs=syncs;expected_isyncs=isyncs;
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
    auto reset=[&](unsigned trial){
        for(unsigned i=0;i<32;++i)c.gpr[i]=trial*257+i;
        for(unsigned i=0;i<installed.size();++i)c.mmu.write8(Vector+i,installed[i]);
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
        need(c.pc==Back&&c.hid0==hid&&c.msr==msr&&c.srr0==Resume);
        need(scs==i+1&&vectors==i+1&&c.inst_count>7&&c.inst_count<256&&c.guest_flush_count==4);
        need(c.mmu.read8(staging-1)==0xA5&&c.mmu.read8(staging+128)==0x5A);
        for(unsigned j=0;j<128;++j)need(c.mmu.read8(staging+j)==uint8_t(j^i));
    }
    for(unsigned fault=0;fault<3;++fault){
        reset(fault);if(fault==0)c.mmu.write8(Vector,installed[0]^1u);
        if(fault==1)c.msr|=0x8000u;
        if(fault==2)c.dispatch_saved_ctx=0x80001234u;
        bool rejected=false;try{func_805222C0(c);}catch(const std::exception&){rejected=true;}
        need(rejected&&scs==32&&vectors==32&&c.pc==Sc&&c.srr0==0&&c.srr1==0);
    }
    reset(33);stop_after_sc=true;func_805222C0(c);
    need(!c.is_running&&c.pc==Resume&&scs==33&&vectors==33);
    std::cout<<"V568_SC_FLUSH owner="<<unsigned(owner)<<" trials=32 lines=128 vectors=32 refusal=3 stop=1 fallback=0 boot_verified=0\n";
}
