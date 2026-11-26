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
    std::cout<<"V1283_CALLBACK_PATH_BUDGET synthetic=1 exact_legacy=1 derived_lengths=1 invalid_lengths_refused=1 original_execution=0\n";
}
