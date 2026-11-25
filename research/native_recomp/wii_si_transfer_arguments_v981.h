#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only admission of a queued SI type request at a native call boundary.
// Never fixes invalid packet fields or changes CPU/device state.
struct SiTransferArguments {
    unsigned channel=4;bool type=false,idle=false,queue_match=false,callback_known=false;
    std::array<uint32_t,8> packet{};
    bool admitted()const{return type&&idle&&queue_match&&callback_known;}
};
template<class C>SiTransferArguments inspect_si_transfer_arguments(C& c,uint32_t data,uint32_t slots,uint32_t callback){
    SiTransferArguments a;
    auto mapped=[&](uint32_t p,unsigned n){
        if(!n||p<0x80000000u||uint64_t(p)+n>0x81800000ull)return false;
        for(unsigned i=0;i<n;++i)if(!c.mmu.get_ptr(p+i))return false;
        return true;
    };
    if(c.gpr[3]>3u||data&3u||slots&3u||!mapped(data,20)||!mapped(slots,128))return a;
    a.channel=c.gpr[3];a.idle=c.mmu.read32(data)==0xffffffffu;
    for(unsigned i=0;i<8;++i)a.packet[i]=c.gpr[3+i];
    a.callback_known=c.gpr[8]==callback&&!(callback&3u)&&mapped(callback,4);
    a.type=c.gpr[5]==1u&&c.gpr[7]==3u&&mapped(c.gpr[4],1)&&mapped(c.gpr[6],3)&&
           !(c.gpr[8]&3u)&&mapped(c.gpr[8],4)&&c.mmu.read8(c.gpr[4])==0u;
    a.queue_match=true;
    for(unsigned i=0;i<8;++i)if(c.mmu.read32(slots+32u*a.channel+4u*i)!=a.packet[i])a.queue_match=false;
    return a;
}
}
