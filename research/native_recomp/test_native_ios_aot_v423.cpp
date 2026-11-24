#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_native_ios_aot_session.h"
#include "wii_v423_synthetic_program.h"
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>
using namespace undercover::wii;
using namespace undercover::wii::v423;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
namespace nw=nwii::runtime;
using Session=NativeIosAotSession<nw::CPUContext,VectorBytes.size()>;
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;
MMU* g_mmu=nullptr;
int g_ipc_interrupt_delay=0;
static Session* session=nullptr;
static unsigned stops=0,acks=0,replies=0;
static constexpr uint32_t req=0x100u;
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
namespace hw {
static unsigned legacy_calls=0;
void vi_trigger_interrupt(){}
extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){++legacy_calls;throw std::runtime_error("legacy IOS called");}
}
bool process_pending_callbacks(CPUContext& c){
    need(session!=nullptr,"no native session");
    const bool certified=c.pc==Entry||c.pc==Resume;
    const bool entered=session->poll(c,certified);
    if(entered){
        need(c.pc==Vector&&c.srr0==Resume&&c.srr1==B::MSR_EE&&!(c.msr&B::MSR_EE)&&c.gpr[5]==0u,"wrong IRQ resume or guest progress");
        const auto ctrl=c.mmu.read32(0xcd000004u);
        need(c.gpr[14]==0x12345678u,"handler scratch register leaked");
        if(ctrl&M::Y2){need(!(ctrl&M::Y1)&&c.gpr[6]==0u&&c.mmu.read32(0x80000000u+req)==S::Open,"ACK not distinct");++acks;}
        else {need((ctrl&M::Y1)&&c.gpr[6]==1u&&c.mmu.read32(0x80000000u+req)==S::Reply,"reply not distinct");++replies;}
    }
    return entered;
}
bool handle_syscall(CPUContext& c){need(c.pc==Stop&&c.gpr[5]==1u&&c.gpr[6]==2u&&session->returns()==2u&&!session->in_flight(),"guest stop before two real rfi returns");++stops;c.is_running=false;return true;}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
}
extern "C" void run_game(nw::CPUContext&);
int main(){
    for(unsigned trial=0;trial<2;++trial){
        auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
        nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
        auto& dispatcher=nw::MMIODispatcher::get();dispatcher.clear();nw::hw::register_ipc(dispatcher);nw::hw::register_pi(dispatcher);
        constexpr uint32_t other=1u<<8,path=0x400u;
        nw::hw::pi_intsr.store(other);nw::hw::pi_intmr.store(H::PI_HOLLYWOOD);
        NativeIosTransport transport(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
        for(std::size_t i=0;i<MainBytes.size();++i)c.mmu.write8(Entry+uint32_t(i),MainBytes[i]);
        for(std::size_t i=0;i<VectorBytes.size();++i)c.mmu.write8(Vector+uint32_t(i),VectorBytes[i]);
        const std::string_view device=trial==0?"/dev/stm/immediate":"/missing";
        for(std::size_t i=0;i<device.size();++i)c.mmu.write8(0x80000000u+path+uint32_t(i),uint8_t(device[i]));
        c.mmu.write32(0x80000000u+nw::req,S::Open);c.mmu.write32(0x80000000u+nw::req+12u,path);
        c.pc=Entry;c.lr=Stop;c.gpr[14]=0x12345678u;c.gpr[17]=0x87654321u;c.msr=0u;
        {
            Session lane(c,transport,VectorBytes);nw::session=&lane;
            std::ostringstream diagnostics;auto* old=std::cerr.rdbuf(diagnostics.rdbuf());
            try{run_game(c);}catch(...){std::cerr.rdbuf(old);throw;}
            std::cerr.rdbuf(old);
            need(diagnostics.str().find("Fallback dispatch")==std::string::npos&&diagnostics.str().find("UNKNOWN DISPATCH")==std::string::npos,"dispatcher fallback used");
            need(!c.is_running&&lane.entries()==2u&&lane.returns()==2u&&transport.serviced_steps()==2u&&c.gpr[5]==1u&&c.gpr[6]==2u&&c.gpr[14]==0x12345678u&&c.gpr[17]==0x87654321u&&c.msr==B::MSR_EE,"AOT session did not complete");
            need(c.mmu.read32(0x80000000u+nw::req+4u)==(trial==0?0u:uint32_t(S::NotFound))&&c.mmu.read32(0xcd800008u)==nw::req,"wrong actual IOS reply");
            need(nw::hw::pi_intsr.load()==other&&nw::hw::legacy_calls==0u&&nw::g_ipc_interrupt_delay==0&&!transport.service_at_guest_boundary(c.msr),"legacy or unsolicited IOS work");
            nw::session=nullptr;
        }
        need(!NativeIosBinding::active(),"native route leaked");nw::g_ctx_ptr=nullptr;nw::g_mmu=nullptr;
    }
    need(nw::acks==2u&&nw::replies==2u&&nw::stops==2u,"unexpected native interrupt counts");
    std::cout<<"PASS: V423 two generated AOT guest requests, four IRQ bodies and rfi returns, no interpreter or legacy IOS\n";
}
