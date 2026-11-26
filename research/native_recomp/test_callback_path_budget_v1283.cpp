#include "wii_held_pending_epilogue_v1149.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
int main(){
    static constexpr std::array<unsigned,3> good{71,73,79};
    static constexpr std::array<unsigned,2> duplicate{71,71},reverse{73,71},bad{71,257};
    constexpr CallbackVisitBudget legacy{71},verified{71,good};
    static_assert(legacy.valid()&&legacy.accepts(71)&&!legacy.accepts(72)&&legacy.maximum()==71);
    static_assert(verified.valid()&&verified.accepts(73)&&!verified.accepts(72)&&verified.maximum()==79);
    static_assert(!CallbackVisitBudget{71,duplicate}.valid()&&!CallbackVisitBudget{71,reverse}.valid()&&!CallbackVisitBudget{71,bad}.valid());
    constexpr uint32_t H=0x80004000u,S=H+0x20u,T=H+0x100u;
    constexpr uint32_t BL=0x48000001u|((T-S)&0x03fffffcu);
    static constexpr std::array<unsigned,2> nested_visits{82,84};
    constexpr CallbackNestedExpectation n{S,T,19,nested_visits};
    static_assert(n.valid());
    for(unsigned f=0;f<11;++f){
        CallbackNestedCensus gate;
        if(f==1){assert(!gate.before(n,H,H,S,BL,18,0,0,0,0));continue;}
        if(f==2){assert(!gate.before(n,H,H,S,BL^4,19,0,0,0,0));continue;}
        if(f==3){assert(!gate.before(n,H,T,T,0x60000000u,20,1,1,0,0));continue;}
        assert(gate.before(n,H,H,S,BL,19,0,0,0,0));
        if(f==4){assert(!gate.before(n,H,H,S,BL,21,0,1,1,0));continue;}
        if(f==5){assert(!gate.before(n,H,T,T,0x60000000u,20,0,1,0,0));continue;}
        if(f==6){assert(!gate.before(n,H,T,T,0x60000000u,20,1,5,0,0));continue;}
        assert(gate.before(n,H,T,T,0x60000000u,20,1,1,0,0));
        assert(gate.before(n,H,H,S+4,0x60000000u,80,1,4,3,2));
        assert(gate.finished(n, f==7?83:82, f==8?1:0,4,f==9?3:4,f==10?1:2)==(f==0));
    }
    CallbackNestedCensus old;
    assert(old.before({},H,H,H,0x60000000u,1,0,0,0,0)&&old.finished({},71,0,0,0,0));
    std::cout<<"V1333_NESTED_ADMISSION synthetic=1 valid=2 refused=10 exact_site=1 census=1 original_execution=0\n";
    std::cout<<"V1283_CALLBACK_PATH_BUDGET synthetic=1 exact_legacy=1 derived_lengths=1 invalid_lengths_refused=1 original_execution=0\n";
}
