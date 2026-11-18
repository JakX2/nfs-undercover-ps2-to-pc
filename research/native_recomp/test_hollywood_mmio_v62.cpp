// Original-free MMU aperture regression; no owner executable required.
#include "runtime/cpu_context.h"
#include <cassert>
#include <iostream>
#include <memory>
int main(){
    auto c=std::make_unique<nwii::runtime::CPUContext>();
    for(uint32_t a:{0x0c000000u,0x0c00ffffu,0x0d000000u,0x0d00ffffu,
                    0x0d800000u,0x0d800180u,0x0d80ffffu})assert(c->mmu.is_hw_reg(a));
    for(uint32_t a:{0x0bffffffu,0x0c010000u,0x0d010000u,0x0d7fffffu,0x0d810000u,
                    0x00000000u,0x10000000u})assert(!c->mmu.is_hw_reg(a));
    std::cout<<"PASS: Hollywood MMIO aperture and neighboring boundaries\n";
}
