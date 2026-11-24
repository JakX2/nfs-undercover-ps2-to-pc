// Run only in the private build environment. Never print paths or game bytes.
#include "loader/loader.h"
#include "wii_dol_loader_v431.h"
#include "wii_dol_equivalence_v436.h"
#include <fstream>
#include <iostream>
using namespace undercover::wii;

int main(int argc,char** argv){
    if(argc!=2)return 2;
    nwii::loader::Executable strict,legacy;
    auto reload=[&](){
        std::ifstream input(argv[1],std::ios::binary);
        return input.is_open()&&load_strict_dol(input,strict.entry_point,strict.sections);
    };
    // Strict geometry first, before the old loader can allocate from a header.
    if(!reload())return 3;
    if(!legacy.load_dol(argv[1]))return 4;
    auto same=[&](){return compare_dol(legacy.entry_point,legacy.sections,
                        strict.entry_point,strict.sections)==DolMismatch::None;};
    if(!same())return 5;
    if(!reload()||!same())return 6;
    std::cout<<"V436_DOL_EQUIVALENCE verified=1 reload=1"<<std::endl;
    return 0;
}
