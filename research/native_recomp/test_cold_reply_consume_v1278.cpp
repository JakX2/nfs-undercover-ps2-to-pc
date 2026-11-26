#include "wii_cold_reply_consume_v1278.h"
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Cpu{
    uint32_t msr=0x32u,guest_data_invalidate_count=300u,guest_last_data_invalidate=0u;
};
static void trial(unsigned lane,bool mem2){
    std::array<uint8_t,4096> m1{},m2{};
    constexpr uint32_t Path=0x800u,Other=0x100u,En=M::IY1|M::IY2;
    const uint32_t req=mem2?0x10000100u:0x100u,virt=req|0x80000000u;
    std::atomic<uint32_t> cause{Other},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(m1,m2,cause,mask);B binding(host);auto& ram=host.physical_ram();
    constexpr std::string_view name="/dev/stm/immediate";
    for(unsigned i=0;i<name.size();++i)ram.write8(Path+i,uint8_t(name[i]));
    ram.write8(Path+name.size(),0);ram.write32(req,S::Open);ram.write32(req+12u,Path);
    assert(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
    assert(B::write32(IosBus::IPC+M::PPCMSG,req));
    assert(B::write32(IosBus::IPC+M::PPCCTRL,En|M::X1));
    auto ack=B::service_at_guest_boundary(0u);assert(ack&&ack->progress==S::Pump::Ack);
    assert(B::write32(IosBus::IPC+M::PPCCTRL,En|M::Y2));
    assert(B::write32(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC));
    auto reply=B::service_at_guest_boundary(0u);assert(reply&&reply->progress==S::Pump::Replied);
    ColdReplyConsumeGate g;Cpu c;
    auto refuse=[&](bool ok,unsigned reason){assert(!ok&&g.failure()==reason&&host.serviced_steps()==2u);};
    if(lane==1){refuse(g.begin(req+32u,true),1);return;}
    if(lane==2){refuse(g.begin(req,false),1);return;}
    if(lane==3){ram.write32(req+4u,1u);refuse(g.begin(req,true),1);return;}
    assert(g.begin(req,true)&&g.boundary(true));
    if(lane==4){assert(!g.read(IosBus::IPC+M::PPCMSG,c.msr,true));refuse(false,2);return;}
    if(lane==5){assert(!g.read(IosBus::IPC+M::ARMMSG,0x8032u,true));refuse(false,2);return;}
    if(lane==6){refuse(g.write(IosBus::IPC+M::PPCCTRL,En|M::Y1,c.msr,true),3);return;}
    assert(g.read(IosBus::MIRROR+M::PPCCTRL,c.msr,true)==(En|M::Y1));
    if(lane==7){refuse(g.write(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC,c.msr,true),3);return;}
    if(lane==8){refuse(g.write(IosBus::IPC+M::PPCCTRL,En|M::Y1|M::X1,c.msr,true),3);return;}
    assert(g.write(IosBus::IPC+M::PPCCTRL,En|M::Y1,c.msr,true));
    assert(g.stage()==2u&&cause.load()==(Other|H::PI_HOLLYWOOD));
    if(lane==9){refuse(g.begin_invalidation(c,virt,32u,true),4);return;}
    assert(g.read(IosBus::IPC+M::ARMMSG,c.msr,true)==req);
    if(lane==10){refuse(g.begin_invalidation(c,virt+4u,32u,true),4);return;}
    if(lane==11){refuse(g.begin_invalidation(c,virt,8u,true),4);return;}
    if(lane==12){refuse(g.begin_invalidation(c,virt|0x40000000u,0x2000u,true),4);return;}
    assert(g.begin_invalidation(c,virt,64u,true));
    if(lane==13){refuse(g.invalidated(c,virt,true),5);return;}
    // Model native counter and effective-address observations only; V1276
    // separately executes the real synthetic PPC dcbi operations.
    ++c.guest_data_invalidate_count;c.guest_last_data_invalidate=virt;
    if(lane==14){refuse(g.invalidated(c,virt+32u,true),5);return;}
    if(lane==15){Cpu other=c;refuse(g.invalidated(other,virt,true),5);return;}
    if(lane==16){c.guest_last_data_invalidate^=32u;refuse(g.invalidated(c,virt,true),5);return;}
    assert(g.invalidated(c,virt,true));
    if(lane==17){refuse(g.finish_invalidation(c,true),6);return;}
    ++c.guest_data_invalidate_count;c.guest_last_data_invalidate=virt+32u;
    if(lane==18){ram.write32(req+8u,0);refuse(g.invalidated(c,virt+32u,true),5);return;}
    assert(g.invalidated(c,virt+32u,true)&&g.finish_invalidation(c,true));
    if(lane==19){++c.guest_data_invalidate_count;assert(!g.ready_for_wakeup(c,true));return;}
    if(lane==20){refuse(g.write(IosBus::IPC+H::PPC_FLAG,0u,c.msr,true),3);return;}
    if(lane==21){assert(g.write(IosBus::IPC+H::PPC_FLAG,H::IPC_PPC,c.msr,true));
        assert(cause.load()==Other&&g.stage()==3u);
    }else assert(lane==0&&cause.load()==(Other|H::PI_HOLLYWOOD));
    assert(g.arm_reads()==1u&&g.control_reads()==1u&&g.invalidations()==2u&&g.ready_for_wakeup(c,true));
    assert(!g.ready_for_wakeup(c,false)&&host.serviced_steps()==2u&&ram.read32(req)==S::Reply);
}
int main(){
    for(bool mem2:{false,true})for(unsigned lane=0;lane<=21;++lane)trial(lane,mem2);
    std::cout<<"V1278_REPLY_CONSUME synthetic=1 valid=4 refused=40 native_mmio=1 modeled_cache_observations=1 wakeup=0 original_execution=0\n";
}
