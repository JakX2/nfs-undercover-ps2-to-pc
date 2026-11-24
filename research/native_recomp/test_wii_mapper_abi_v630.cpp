#include "wii_mapper_abi_v630.h"
#include <iostream>
#include <stdexcept>
#ifdef UNDERCOVER_V630_OWNER
#include "v630_private_mapper_prefix.h"
#endif
using namespace undercover::wii::v630;
constexpr uint32_t imm(unsigned op,unsigned rd,unsigned ra,int value){
    return op<<26|rd<<21|ra<<16|(uint32_t(value)&0xffffu);
}
constexpr uint32_t x(unsigned xo,unsigned rs,unsigned ra,unsigned rb){return 31u<<26|rs<<21|ra<<16|rb<<11|xo<<1;}
static void need(bool b){if(!b)throw std::runtime_error("V630 independent liveness control failed");}
int main(){
    constexpr uint32_t entry=0x80527568;
    constexpr std::array<uint32_t,5> good{imm(37,1,1,-16),x(339,0,8,0),imm(36,0,1,20),imm(15,3,0,0x8000),0x48000001};
    static_assert(dead_prefix(good)==4);
    constexpr std::array<uint32_t,2> load{imm(15,4,0,0x8000),imm(32,3,4,0x3100)};
    static_assert(dead_prefix(load)==2);
    constexpr std::array<uint32_t,1> logical{x(444,4,3,4)};
    static_assert(dead_prefix(logical)==1);
    constexpr std::array<uint32_t,1> spr{x(339,3,8,0)};
    static_assert(dead_prefix(spr)==1);
    constexpr uint32_t kill=imm(14,3,0,7);
    for(uint32_t bad:{imm(14,3,3,0),imm(32,3,3,0),imm(36,3,1,0),imm(36,4,3,0),
                      imm(37,1,3,-4),imm(33,3,3,0),imm(33,3,0,0),imm(20,4,3,0),
                      x(444,3,4,4),x(444,4,3,3),x(467,3,8,0),0x48000004u,0x41820004u,0u}){
        const std::array<uint32_t,2> seq{bad,kill};need(dead_prefix(seq)==0);
    }
    constexpr std::array<uint32_t,1> preserve{0x60000000};
    need(dead_prefix(preserve)==0);need(dead_prefix(std::array<uint32_t,17>{})==0);
    for(unsigned fault=0;fault<=4;++fault){
        const auto read=[&](uint32_t a)->std::optional<uint32_t>{
            if(a<entry||(a-entry)%4||(a-entry)/4>=good.size())return std::nullopt;
            const auto i=(a-entry)/4;
            if(fault==1&&i==1)return std::nullopt;
            return good[i]^uint32_t(fault==2&&i==2);
        };
        const bool valid=verify_dead_prefix(entry+(fault==3?1:0),fault==4?std::span<const uint32_t>(preserve):std::span<const uint32_t>(good),read);
        need(valid==(fault==0));
    }
    std::cout<<"V630_MAPPER_ABI synthetic=1 positive=4 refusal=20\n";
#ifdef UNDERCOVER_V630_OWNER
    const auto n=dead_prefix(owner_prefix);
    std::cout<<"V630_MAPPER_ABI owner=1 r3_dead="<<unsigned(n!=0)<<" prefix="<<n<<" exact_dol_elf=1\n";
#endif
}
