#pragma once
#include "v861_private_wireless_write.h"
#include "wii_wireless_profile_trace_v859.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v861 {
inline thread_local WirelessProfileTrace device;
inline thread_local unsigned locks=0,selects=0,imms=0,syncs=0,extendeds=0,deselects=0,unlocks=0,masks=0;
inline thread_local unsigned lock_returns=0,select_returns=0,imm_returns=0,sync_returns=0,extended_returns=0,deselect_returns=0,unlock_returns=0;
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V861_WIRELESS_WRITE");
    return v&&v[0]=='1'&&v[1]=='\0';
}
inline bool active(){return device.stage()!=0u;}
[[noreturn]]inline void reject(unsigned n){
    std::cout<<std::dec<<"V861_WIRELESS_WRITE_INVALID kind="<<n<<" device="<<device.stage()
        <<" reason="<<device.failure()<<" witness="<<device.witness_failure()
        <<" completed="<<device.completed()<<" bytes="<<device.bytes()<<std::endl;std::_Exit(126);
}
template<class C>ExiMxDevice::Sram payload(C& c){
    ExiMxDevice::Sram b{};
    for(unsigned i=0;i<b.size();++i){
        if(!c.mmu.get_ptr(sram+i))reject(1);
        b[i]=c.mmu.read8(sram+i);
    }
    return b;
}
template<class C>uint32_t state(C& c){
    const uint32_t a=extension.exi_state+12u;
    if(!c.mmu.get_ptr(a)||!c.mmu.get_ptr(a+3u))reject(1);
    return c.mmu.read32(a);
}
template<class C>void start(C& c,const WirelessWrapperWitness& route){
    if(!enabled()||!route.changed())return;
    if(route.ordinal()!=3u||c.gpr[4]>0xffffu||!device.begin(route.initial_payload(),route.channel(),uint16_t(c.gpr[4]),c.inst_count))reject(1);
}
template<class C>void entry(C& c,uint32_t pc){
    if(!active())return;
    if(pc==lock){
        if(++locks!=1u||state(c)!=0u||c.gpr[3]!=0u||c.gpr[4]!=1u)reject(2);
    }else if(pc==mask_helper){
        if(++masks>2u||c.gpr[3]!=0u||c.gpr[4]!=extension.exi_state)reject(2);
    }else if(pc==select){
        if(++selects!=1u||lock_returns!=1u||masks!=1u||state(c)!=0x10u||
           c.gpr[3]!=0u||c.gpr[4]!=1u||c.gpr[5]!=3u||
           !device.preselect(payload(c),c.inst_count))reject(2);
    }else if(pc==imm){
        if(select_returns!=1u||imms!=sync_returns||++imms>12u||state(c)!=0x14u||
           c.gpr[3]!=0u||c.gpr[5]!=4u||c.gpr[6]!=1u||c.gpr[7]!=0u||
           device.completed()!=imms-1u)reject(2);
        if(imms==1u){
            const uint32_t a=c.gpr[4];
            if(a<0x80000000u||a>0x817ffffcu||(a&3u)||!c.mmu.get_ptr(a)||!c.mmu.get_ptr(a+3u)||c.mmu.read32(a)!=0xa0000600u)reject(2);
        }else if(extendeds!=1u||c.gpr[4]!=sram+20u+4u*(imms-2u))reject(2);
    }else if(pc==sync){
        if(++syncs!=imm_returns||c.gpr[3]!=0u||state(c)!=0x16u)reject(2);
    }else if(pc==immex){
        if(++extendeds!=1u||sync_returns!=1u||device.completed()!=1u||
           c.gpr[3]!=0u||c.gpr[4]!=sram+20u||c.gpr[5]!=44u||c.gpr[6]!=1u)reject(2);
    }else if(pc==deselect){
        if(++deselects!=1u||extended_returns!=1u||device.stage()!=3u||device.completed()!=12u||c.gpr[3]!=0u)reject(2);
    }else if(pc==unlock){
        if(++unlocks!=1u||deselect_returns!=1u||state(c)!=0x10u||c.gpr[3]!=0u||device.stage()!=4u)reject(2);
    }
}
template<class C>void after(C& c,uint32_t old_root,const WirelessWrapperWitness& route){
    if(!active())return;
    if(old_root==lock){
        if(c.gpr[3]!=1u||state(c)!=0x10u||++lock_returns!=1u)reject(3);
    }else if(old_root==select){
        if(c.gpr[3]!=1u||state(c)!=0x14u||++select_returns!=1u)reject(3);
    }else if(old_root==imm){
        if(c.gpr[3]!=1u||state(c)!=0x16u||++imm_returns!=imms)reject(3);
    }else if(old_root==sync){
        if(c.gpr[3]!=1u||state(c)!=0x14u||++sync_returns!=syncs||device.completed()!=sync_returns)reject(3);
    }else if(old_root==immex){
        if(c.gpr[3]!=1u||++extended_returns!=1u||device.stage()!=3u||device.bytes()!=44u)reject(3);
    }else if(old_root==deselect){
        if(c.gpr[3]!=1u||++deselect_returns!=1u||state(c)!=0x10u||!device.deselected(payload(c),c.inst_count))reject(3);
    }else if(old_root==unlock){
        if(c.gpr[3]!=1u||state(c)!=0u||masks!=2u||++unlock_returns!=1u)reject(3);
    }
    if(route.stage()==2u){
        if(!route.extended()||!route.changed()||locks!=1u||selects!=1u||lock_returns!=1u||select_returns!=1u||
           imms!=12u||syncs!=12u||imm_returns!=12u||sync_returns!=12u||extendeds!=1u||extended_returns!=1u||
           deselects!=1u||deselect_returns!=1u||unlocks!=1u||unlock_returns!=1u||
           state(c)!=0u||!device.returned(payload(c),c.inst_count)||!device.held())reject(4);
        std::cout<<std::dec<<"V861_WIRELESS_WRITE_RESULT original_setter_return=1 original_unlock=1 transfers="<<device.completed()
            <<" bytes="<<device.bytes()<<" visits="<<route.visits()<<" polls="<<route.polls()<<" mmio="<<route.mmio()
            <<" payload=1 abi=1 callback_return=0 boot_verified=0"<<std::endl;std::_Exit(0);
    }
}
}
