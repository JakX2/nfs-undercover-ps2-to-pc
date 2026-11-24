#include "runtime/cpu_context.h"
#include "wii_open_sc_route_v637.h"
#include "functions.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
extern "C" void run_game(nw::CPUContext&);
constexpr uint32_t Entry=0x805222c0,Sc=Entry+40,Resume=Sc+4,Back=0x80519a1c,Vector=0x80000c00;
static uint32_t staging=0x81000000;
static std::array<uint8_t,28> installed{};
static unsigned scs=0,vectors=0;
static bool owner=false, stop_after_sc=false;
using Route=undercover::wii::OpenScRoute;
static std::unique_ptr<Route> route;
static bool suppress_arm=false;
static unsigned delegated=0;
using namespace undercover::wii;
static std::atomic<uint32_t> cause{0},mask{HollywoodIrq::PI_HOLLYWOOD|0x40u};
static unsigned fault_id=0,expected_lines=4;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V638 line "+std::to_string(loc.line()));
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
    need(c.guest_flush_count==expected_lines);
    for(unsigned i=0;i<expected_lines;++i)need(c.guest_flush_lines[i]==staging+32*i);
    if(fault_id==6)cause.fetch_or(0x40u);
    if(fault_id==7)mask.fetch_or(0x100u);
    if(!route->dispatch(c,[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i){
                const uint32_t wanted=i==9?hid:i==10?(hid|8u):gp[i];
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
        cause=0;mask=HollywoodIrq::PI_HOLLYWOOD|0x40u;
        fault_id=0;
        for(unsigned i=0;i<32;++i)c.gpr[i]=trial*257+i;
        route=std::make_unique<Route>(installed);suppress_arm=false;
        for(unsigned i=0;i<installed.size();++i){c.mmu.write8(Vector+i,installed[i]);c.mmu.write8(Route::Source+i,installed[i]);}
        c.mmu.write32(Sc,0x44000002u);c.mmu.write32(Resume,0x4e800020u);
        staging=0x81000000u+trial*0x100u;
        const unsigned offset=owner?trial%32u:0u,n=owner?19u:128u;
        c.gpr[3]=staging+offset;c.gpr[4]=n;expected_lines=(offset+n+31u)/32u;
        c.mmu.write8(staging-1,0xA5);c.mmu.write8(staging+128,0x5A);
        for(unsigned i=0;i<128;++i)c.mmu.write8(staging+i,uint8_t(i^trial));
        c.pc=Entry;c.lr=Back;c.ctr=0x1234+trial;c.msr=trial&1?0x8032u:0xa032u;c.hid0=trial*0x10101u;
        c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;c.srr0=0;c.srr1=0;c.guest_sync_count=0;c.guest_isync_count=0;c.guest_flush_count=0;c.guest_flush_lines.fill(0);
    };
    for(unsigned i=0;i<32;++i){
        reset(i);
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,cause,mask);NativeIosBinding binding(host);
        need(NativeIosBinding::write32(IosBus::IPC+HollywoodIrq::PPC_MASK,HollywoodIrq::IPC_PPC));
        need(NativeIosBinding::write32(IosBus::IPC+IpcMailbox::PPCCTRL,IpcMailbox::IY1|IpcMailbox::IY2));
        const auto hid=c.hid0,msr=c.msr;
        func_805222C0(c);
        need(c.pc==Back&&c.hid0==hid&&c.msr==msr&&c.srr0==Resume&&route->returned(c));
        need(scs==i+1&&vectors==i+1&&c.inst_count>7&&c.inst_count<256&&c.guest_flush_count==expected_lines&&host.serviced_steps()==0);
        need(c.mmu.read8(staging-1)==0xA5&&c.mmu.read8(staging+128)==0x5A);
        for(unsigned j=0;j<128;++j)need(c.mmu.read8(staging+j)==uint8_t(j^i));
    }
    for(unsigned fault=0;fault<10;++fault){
        reset(fault);fault_id=fault;
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,cause,mask);NativeIosBinding binding(host);
        need(NativeIosBinding::write32(IosBus::IPC+HollywoodIrq::PPC_MASK,HollywoodIrq::IPC_PPC));
        need(NativeIosBinding::write32(IosBus::IPC+IpcMailbox::PPCCTRL,IpcMailbox::IY1|IpcMailbox::IY2));
        if(fault==0)c.mmu.write8(Vector,installed[0]^1u);
        if(fault==1)c.msr&=~0x8000u;
        if(fault==2)c.dispatch_saved_ctx=0x80001234u;
        if(fault==3)c.mmu.write8(Route::Source,installed[0]^1u);
        if(fault==4)c.mmu.write32(Resume,0x60000000u);
        if(fault==5)suppress_arm=true;
        if(fault==8)cause.fetch_or(0x40u);
        if(fault==9)c.lr+=4;
        bool rejected=false;try{func_805222C0(c);}catch(const std::runtime_error& e){need(std::string_view(e.what())=="V637 open SC route rejected");rejected=true;}
        need(rejected&&scs==32&&vectors==32&&c.pc==Sc&&c.srr0==0&&c.srr1==0&&route->phase()==Route::Phase::Failed);
    }
    std::cout<<"V638_OPEN_SC owner="<<unsigned(owner)<<" trials=32 returned=32 vectors=32 ee_restored=32 refusal=10 serviced=0 fallback=0 boot_verified=0\n";
}
