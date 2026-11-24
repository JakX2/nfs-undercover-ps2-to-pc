#include "wii_physical_ram.h"
#include <array>
#include <iostream>
#include <vector>
using namespace undercover::wii;
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
int main(){
    using R=WiiPhysicalRam;
    std::vector<uint8_t> one(std::size_t(R::MEM1_SIZE)+8u,0xa5u);
    std::vector<uint8_t> two(std::size_t(R::MEM2_SIZE)+8u,0x5au);
    R ram(one,two);
    need(ram.valid(0,1)&&ram.valid(R::MEM1_SIZE-4,4),"MEM1 range");
    need(ram.valid(R::MEM2_BASE,1)&&ram.valid(R::MEM2_BASE+R::MEM2_SIZE-4,4),"MEM2 range");
    for(uint32_t a:{R::MEM1_SIZE,R::MEM2_BASE+R::MEM2_SIZE,0x80000000u,0xc0000000u,0x90000000u,0x0d000000u,0xffffffffu})
        need(!ram.valid(a,1),"alias, MMIO or padding accepted");
    need(!ram.valid(0,0)&&!ram.valid(R::MEM1_SIZE-2,4)&&!ram.valid(R::MEM2_BASE+R::MEM2_SIZE-2,4)&&!ram.valid(4,0xffffffffu),"range overflow or empty span");
    ram.write32(0x100,0x12345678);ram.write32(R::MEM2_BASE+0x100,0xabcdef01);
    need(one[0x100]==0x12&&one[0x103]==0x78&&two[0x100]==0xab&&two[0x103]==0x01,"endian or region error");
    need(ram.read32(0x100)==0x12345678&&ram.read32(R::MEM2_BASE+0x100)==0xabcdef01,"readback error");
    bool rejected=false;try{ram.write8(R::MEM1_SIZE,0);}catch(const std::out_of_range&){rejected=true;}
    need(rejected&&one[R::MEM1_SIZE]==0xa5&&two[R::MEM2_SIZE]==0x5a,"padding write escaped");
    std::array<uint8_t,32> small{};R limited(small,{});
    need(limited.valid(28,4)&&!limited.valid(29,4)&&!limited.valid(R::MEM2_BASE,1),"short host backing ignored");
    std::cout<<"PASS: physical IOS RAM ranges, alias rejection, endian and padding\n";
}
