#pragma once
#include "wii_bounded_ack_call_route_v956.h"
#include "wii_postack_transfer_device_v771.h"
#include "wii_si_transfer_arguments_v981.h"
namespace undercover::wii {
// Read-only strict native call/return witness for a newly owned third device.
// The exact native labels and call geometry are authenticated privately.
class ThirdSiTransferRoute {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned entries()const{return route_.entries();}
    unsigned returns()const{return route_.returns();}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,const SiTransferArguments& a,
                                std::span<const AckCallSpan> spans,std::span<const AckCallEdge> edges,
                                std::span<const AckMsrSite> msr,uint32_t data){
        if(stage_||error_||!a.admitted()||a.channel>=4u||a.packet[0]!=a.channel||
           c.inst_count>UINT64_MAX-2048u||!word(c,pc,w)||
           !route_.begin(c,spans,edges,msr,true,pc)||!route_.before(c,pc,w))return fail(1);
        cpu_=&c;args_=a.packet;data_=data;site_=pc;start_=last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,PostAckTransferDevice& dev){
        if(stage_!=1u||error_||cpu_!=&c||dev.stage()!=1u||
           c.inst_count-last_!=1u||c.inst_count-start_>2048u||!word(c,pc,w)||++visits_>2048u)return fail(2);
        const auto a=PostAckTransferDevice::word_access(c,w);
        const auto off=PostAckTransferDevice::offset(a.address);
        if(a.kind!=PostAckTransferDevice::Access::None&&!off){
            const uint32_t p=a.address&0x3fffffffu;
            if((p<0x0d006500u&&uint64_t(p)+4u>0x0d006400u)||
               (p<0x0d806500u&&uint64_t(p)+4u>0x0d806400u))return fail(2);
        }
        if(!dev.before(c.inst_count,off?a.kind:PostAckTransferDevice::Access::None,off?a.address:0u,off?a.store:std::nullopt)||
           !route_.before(c,pc,w))return fail(3);
        last_=c.inst_count;
        if(pc==site_+4u){
            if(route_.depth()||route_.entries()!=route_.returns()||route_.entries()<4u||
               c.gpr[3]!=1u||!dev.finish(c.inst_count,c.gpr[3])||!dev.held_now()||
               dev.token()!=3u||dev.follow_stage()<2u||
               !c.mmu.get_ptr(data_)||!c.mmu.get_ptr(data_+19u)||
               c.mmu.read32(data_)!=args_[0]||c.mmu.read32(data_+8u)!=args_[4]||
               c.mmu.read32(data_+12u)!=args_[3]||c.mmu.read32(data_+16u)!=args_[5])return fail(4);
            stage_=2u;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,const PostAckTransferDevice& dev){
        return stage_==1u&&!error_&&cpu_==&c&&c.inst_count==last_&&dev.held_now()&&route_.entry(c,pc)?true:fail(5);
    }
    template<class C>bool poll(C& c,const PostAckTransferDevice& dev){
        return stage_==1u&&!error_&&cpu_==&c&&c.inst_count==last_&&dev.held_now()&&route_.can_poll()?true:fail(5);
    }
private:
    BoundedAckCallRoute route_;const void* cpu_=nullptr;
    std::array<uint32_t,8> args_{};
    uint32_t data_=0,site_=0;uint64_t start_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool word(C& c,uint32_t pc,uint32_t w){
        return !(pc&3u)&&pc>=0x80000000u&&pc<=0x817ffffcu&&c.mmu.get_ptr(pc)&&c.mmu.get_ptr(pc+3u)&&c.mmu.read32(pc)==w;
    }
};
}
