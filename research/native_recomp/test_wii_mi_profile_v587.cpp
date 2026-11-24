#include "wii_irq_bank_binding_v481.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
using B=IrqBankBinding;
static void need(bool v,const std::source_location loc=std::source_location::current()){
    if(!v)throw std::runtime_error("V587 line "+std::to_string(loc.line()));
}
template<class F>void reject(F f){bool bad=false;try{f();}catch(const std::exception&){bad=true;}need(bad);}
int main(){
    std::atomic<uint32_t> pi{0x140};
    reject([]{B::enable_mi_boot();});need(!B::mi_boot_ready());
    for(uint32_t alias:{0u,0x80000000u,0xc0000000u}){
        WiiIrqBanks banks(pi);B b(banks);
        auto a=[&](uint32_t offset){return alias|0x0c004000u|offset;};
        need(!B::read16(a(0x10))&&!B::write16(a(0x20),0));
        B::enable_mi_boot();reject([]{B::enable_mi_boot();});
        need(!B::mi_boot_ready()&&!B::mi_boot_complete());
        reject([&]{B::write16(a(0x10),255);});
        reject([&]{B::write16(a(0x20),1);});
        reject([&]{B::write32(a(0x20),0);});
        reject([&]{B::check_cpu_access(a(0x10),1,true);});
        reject([&]{B::check_cpu_access(a(0x10),2,false);});
        reject([&]{B::read16(a(0x12));});
        reject([&]{B::read16(a(0x21));});
        reject([&]{B::write16(0x4c004020,0);});
        need(banks.mi_boot_stage()==0&&B::write16(a(0x20),0));
        reject([&]{B::write16(a(0x20),0);});
        reject([&]{B::write16(a(0x10),254);});
        need(banks.mi_boot_stage()==1&&B::write16(a(0x10),255));
        need(B::mi_boot_ready()&&!B::mi_boot_complete());
        need(B::read16(a(0x10))==255&&B::read16(a(0x20))==0);
        reject([&]{B::write16(a(0x10),255);});
        need(B::write16(a(0x1c),16)&&B::mi_boot_complete());
        banks.raise_mi(16);need(!B::mi_boot_complete()&&pi.load()==0x1c0);
        need(B::write16(a(0x1e),16)&&B::mi_boot_complete()&&pi.load()==0x140);
        need(!B::write16(0x0c006000,0));
    }
    need(!B::mi_boot_complete());
    std::cout<<"V587_MI_COLD aliases=3 ordered_writes=6 rejection_per_alias=11 irq_preserved=1 permissions=0\n";
}
