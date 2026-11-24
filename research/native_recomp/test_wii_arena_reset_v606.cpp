#include "wii_arena_reset_v606.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
using P=ArenaResetProfile;using B=ArenaResetBinding;
static void need(bool v,const std::source_location loc=std::source_location::current()){
    if(!v)throw std::runtime_error("V606 line "+std::to_string(loc.line()));
}
int main(){
    for(uint32_t alias:{0u,0x80000000u,0xc0000000u}){
        P p;
        need(!B::read32(P::Address));
        {
            B bind(p);
            need(!B::read32(0xcc003000u)&&!B::read32(0xcc003004u)&&!B::read32(0xcc00302cu));
            for(unsigned lane=1;lane<=2;++lane){
                need(p.arm(lane)&&p.armed()&&p.reads()==lane-1);
                need(B::read32(P::Address|alias)==P::ColdValue&&!p.armed()&&p.reads()==lane);
            }
            need(p.complete());
        }
        need(!B::read32(P::Address));
    }
    for(unsigned fault=0;fault<12;++fault){
        P p;B bind(p);bool rejected=false;
        try{
            if(fault==0){B::read32(P::Address);}
            else if(fault==1){rejected=!p.arm(2);}
            else{
                need(p.arm(1));
                switch(fault){
                case 2:rejected=!p.arm(1);break;
                case 3:B::check(P::Address,2,true,false);break;
                case 4:B::check(P::Address,4,true,true);break;
                case 5:B::check(P::Address,4,false,false);break;
                case 6:B::read32(P::Address|0x40000000u);break;
                case 7:B::check(P::Address-1,2,true,false);break;
                case 8:B::read32(P::Address+1);break;
                case 9:B::read32(P::Address);B::read32(P::Address);break;
                case 10:B::read32(P::Address);rejected=!p.arm(1);break;
                case 11:B::read32(P::Address);need(p.arm(2));B::read32(P::Address);rejected=!p.arm(3);break;
                }
            }
        }catch(const std::runtime_error&){rejected=true;}
        need(rejected&&p.failed()&&!p.complete());
    }
    std::cout<<"V606_ARENA_RESET aliases=3 lanes=6 reads=6 refusal=12 hardware_reset=0\n";
}
