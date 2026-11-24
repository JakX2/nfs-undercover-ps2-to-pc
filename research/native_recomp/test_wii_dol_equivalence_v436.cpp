#include "wii_dol_equivalence_v436.h"
#include <vector>
#include <stdexcept>
#include <iostream>
struct Section{uint32_t address,size;std::vector<uint8_t> data;bool is_text,is_bss;};
using namespace undercover::wii;
static void need(bool ok){if(!ok)throw std::runtime_error("DOL equivalence");}
int main(){
    const uint32_t entry=0x80004000u;
    const std::vector<Section> a{{entry,4,{1,2,3,4},true,false},{0x90001000u,3,{9,8,7},false,false},{0x90000ff0u,64,{},false,true}};
    need(compare_dol(entry,a,entry,a)==DolMismatch::None);
    for(unsigned n=0;n<9;++n){
        auto b=a;auto e=entry;DolMismatch want=DolMismatch::None;
        switch(n){
        case 0:e+=4;want=DolMismatch::Entry;break;
        case 1:b.pop_back();want=DolMismatch::Count;break;
        case 2:b[0].address+=4;want=DolMismatch::Geometry;break;
        case 3:b[2].size--;want=DolMismatch::Geometry;break;
        case 4:b[0].is_text=false;want=DolMismatch::Flags;break;
        case 5:b[2].is_bss=false;want=DolMismatch::Flags;break;
        case 6:b[1].data[2]^=1;want=DolMismatch::Payload;break;
        case 7:b[2].data.push_back(0);want=DolMismatch::Payload;break;
        case 8:std::swap(b[0],b[1]);want=DolMismatch::Geometry;break;
        }
        need(compare_dol(entry,a,e,b)==want);
    }
    std::cout<<"PASS: DOL section equivalence and nine mismatch controls\n";
}
