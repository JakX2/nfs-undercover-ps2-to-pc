#include "wii_private_expansion_seed_v1323.h"
#include <cassert>
#include <iostream>
#include <map>
#include <vector>
using namespace undercover::wii;
constexpr uint32_t A=0x80010000u,Nop=0x60000000u,Blr=0x4e800020u;
struct Row{uint32_t owner,pc,word;};
struct Mmu{
    std::map<uint32_t,uint32_t> ram;unsigned writes=0;uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return ram.count(a&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return ram.at(a);}
    void write32(uint32_t a,uint32_t v){ram.at(a)=v;++writes;}
};
int main(){
    for(unsigned f=0;f<9;++f){
        Mmu m;m.ram={{A,Nop},{A+4,0},{A+8,0},{A+12,0x12345678u}};
        std::vector<Row> rows{{A,A,Nop},{A,A+4,Nop},{A,A+8,Blr},{A+12,A+12,0x12345678u}};
        unsigned n=3;
        if(f==1)rows.erase(rows.begin()+1);
        if(f==2)rows[1].pc=A;
        if(f==3)rows[1].pc=A+12;
        if(f==4)m.ram[A]=Blr;
        if(f==5)m.ram.erase(A+4);
        if(f==6)rows[1].owner=A+4;
        if(f==7)n=257;
        if(f==8)rows.push_back({A+12,A+4,Blr});
        auto before=m.ram;bool ok=seed_private_expansion(m,rows,A,n);
        if(f){assert(!ok&&m.writes==0&&m.ram==before);}
        else {
            assert(ok&&m.writes==3&&m.read32(A+4)==Nop&&m.read32(A+8)==Blr&&m.read32(A+12)==0x12345678u);
            assert(verify_private_words(m,rows));
            m.ram[A+8]^=1;assert(!verify_private_words(m,rows));m.ram[A+8]^=1;
            m.ram.erase(A+4);assert(!verify_private_words(m,rows));
            assert(m.writes==3);
        }
    }
    std::cout<<"V1323_PRIVATE_SEED synthetic=1 valid=1 refused=8 atomic_preflight=1 original_execution=0\n";
}
