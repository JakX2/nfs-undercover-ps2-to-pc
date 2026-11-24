#include "wii_external_overlay_v662.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("V662 synthetic assertion");}
static void put(std::vector<uint8_t>& b,unsigned i,uint32_t w){for(unsigned n=0;n<4;++n)b.at(i+n)=uint8_t(w>>(24-8*n));}
static nwii::loader::Executable fixture(){
    nwii::loader::Executable exe;
    std::vector<uint8_t> text(IrqSize),table(60);
    for(unsigned i=0;i<IrqSize;i+=4)put(text,i,0x60000000u);
    put(text,0,0x48000008u);put(text,8,0x4bfffff8u);
    put(text,0x58,0x48000000u);put(text,0x68,0x38600000u);
    for(unsigned i=0;i<15;++i)put(table,4*i,0x100u*(i+1));
    exe.sections.push_back({IrqSource,IrqSize,text,true,false});
    exe.sections.push_back({IrqTable,60,table,false,false});return exe;
}
int main(){
    auto exe=fixture();const auto before=exe.sections[0].data;
    add_external_overlay(exe);need(exe.sections.size()==3&&exe.sections[0].data==before);
    const auto& v=exe.sections.back();need(v.address==IrqVector&&v.size==IrqSize&&v.is_text&&!v.is_bss);
    need(irq_word(v.data,0x58)==0x60000000u&&irq_word(v.data,0x68)==0x38600004u);
    need(irq_word(v.data,0)==0x48000008u&&irq_word(v.data,8)==0x4bfffff8u);
    for(unsigned n=0;n<8;++n){
        auto bad=fixture();
        switch(n){
        case 0:bad.sections.pop_back();break;
        case 1:put(bad.sections[1].data,16,0x600u);break;
        case 2:put(bad.sections[0].data,0,0x48000100u);break;
        case 3:bad.sections.push_back({IrqVector,4,{0,0,0,0},true,false});break;
        case 4:bad.sections.push_back(bad.sections[0]);break;
        case 5:bad.sections[0].data.pop_back();break;
        case 6:put(bad.sections[0].data,0,0x4bfffffcu);break;
        case 7:put(bad.sections[1].data,16,0x520u);break;
        }
        const auto count=bad.sections.size();bool rejected=false;
        try{add_external_overlay(bad);}catch(const std::runtime_error&){rejected=true;}
        need(rejected&&bad.sections.size()==count);
    }
    std::cout<<"V662_IRQ_OVERLAY synthetic=1 reject=8 runtime_delivery=0\n";
}
