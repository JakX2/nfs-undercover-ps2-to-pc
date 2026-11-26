#include "wii_initialized_dol_data_v1264.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
struct Mmu{
    std::array<uint8_t,128> mem{};
    bool unmapped=false;
    uint8_t* get_ptr(uint32_t a){
        if(a<0x80004000u||a>=0x80004080u||(unmapped&&a>=0x80004040u))return nullptr;
        return mem.data()+a-0x80004000u;
    }
};
static void be(std::vector<uint8_t>& d,unsigned a,uint32_t v){
    for(unsigned i=0;i<4;++i)d.at(a+i)=uint8_t(v>>(24u-8u*i));
}
int main(){
    std::vector<uint8_t> d(288,0);
    auto set=[&](auto& raw,unsigned i,uint32_t f,uint32_t a,uint32_t n){
        be(raw,0x1c+4*i,f);be(raw,0x64+4*i,a);be(raw,0xac+4*i,n);
    };
    set(d,0,256,0x80004000,8);set(d,1,272,0x80004040,8);
    for(unsigned i=0;i<8;++i){d[256+i]=uint8_t(i+1);d[272+i]=uint8_t(i+9);}
    // Text is intentionally not loaded.
    be(d,0,280);be(d,0x48,0x80004020);be(d,0x90,8);d[280]=0xaa;
    Mmu m;seed_initialized_dol_data(m,d);
    assert(m.mem[0]==1&&m.mem[7]==8&&m.mem[64]==9&&m.mem[71]==16&&m.mem[32]==0);
    unsigned rejected=0;
    for(unsigned i=0;i<8;++i){
        auto bad=d;Mmu q;q.mem.fill(0x55);const auto old=q.mem;
        switch(i){
        case 0:bad.resize(255);break;
        case 1:set(bad,1,284,0x80004040,8);break;
        case 2:set(bad,1,272,0x80004004,8);break;
        case 3:set(bad,1,260,0x80004040,8);break;
        case 4:set(bad,1,272,0x817ffffc,8);break;
        case 5:set(bad,1,272,0x80000000,8);break;
        case 6:set(bad,0,0,0,0);set(bad,1,0,0,0);break;
        case 7:q.unmapped=true;break;
        }
        try{seed_initialized_dol_data(q,bad);assert(false);}
        catch(const std::runtime_error&){++rejected;assert(q.mem==old);}
    }
    assert(rejected==8);
    std::cout<<"V1264_DOL_DATA_TEST valid=1 refused=8 atomic=1 text_excluded=1\n";
}
