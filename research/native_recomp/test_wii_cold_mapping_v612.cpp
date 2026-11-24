#include "wii_cold_mapping_v612.h"
#include <iostream>
#include <array>
#include <vector>
#include <source_location>
#include <stdexcept>
using P=undercover::wii::ColdMappingProfile;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V612 line "+std::to_string(l.line()));
}
struct Mmu {
    std::array<uint8_t,0x100> b{};unsigned writes=0;
    uint32_t hole=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80003100u&&a<0x80003200u&&a!=hole?b.data()+a-0x80003100u:nullptr;}
    uint32_t read32(uint32_t a){uint32_t w=0;for(unsigned i=0;i<4;++i){auto* p=get_ptr(a+i);need(p!=nullptr);w=w<<8|*p;}return w;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto* p=get_ptr(a+i);need(p!=nullptr);*p=uint8_t(v>>(24-8*i));}++writes;}
};
struct Sec{uint32_t address,size;bool is_bss;};
int main(){
    for(unsigned fault=0;fault<=14;++fault){
        Mmu m;for(auto f:P::Fields)m.write32(f.addr,f.prior);
        m.write32(0x8000310c,0x80754000);m.write32(0x80003138,0x1234);m.write32(0x80003158,0x23);
        std::vector<Sec> sections{{0x80004000,0x1000,false},{0x80003100,0x40,true}};
        if(fault>=1&&fault<=9){auto f=P::Fields[fault-1];m.write32(f.addr,f.prior^1);}
        if(fault==10)sections.push_back({0x800030ff,2,false});
        if(fault==11)sections.push_back({0x80003122,2,false});
        if(fault==12)m.hole=0x80003137;
        const auto before=m.b;const auto n=m.writes;
        const bool ok=P::install(m,sections,fault!=13,fault!=14);
        need(ok==(fault==0));
        if(ok){
            for(auto f:P::Fields)need(m.read32(f.addr)==f.value);
            need(m.writes==n+6&&m.read32(0x8000310c)==0x80754000&&m.read32(0x80003138)==0x1234&&m.read32(0x80003158)==0x23);
            need(!P::install(m,sections,true,true));
        }else need(m.b==before&&m.writes==n);
    }
    std::cout<<"V612_MAPPING_CONTROL fields=9 writes=6 refusal=14 adjacent=1 transactional=1 synthetic=1\n";
}
