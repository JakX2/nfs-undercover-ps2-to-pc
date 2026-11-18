#include "wii_hollywood_irq.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
using H=HollywoodIrq;using M=IpcMailbox;
constexpr auto P=M::Side::Broadway,A=M::Side::Starlet;
int main(){
    H irq;M ipc;
    assert(!irq.broadway_asserted()&&!irq.starlet_asserted());
    // Pending sources survive a closed mask; masks never erase latches.
    for(unsigned n=0;n<32;++n){
        irq.reset();const uint32_t bit=1u<<n,other=1u<<((n+1)%32);
        irq.raise_ppc(bit|other);irq.raise_arm(bit|other);
        assert(!irq.broadway_asserted()&&!irq.starlet_asserted());
        irq.write(P,H::PPC_MASK,bit);irq.write(A,H::ARM_MASK,other);
        assert(irq.pi_cause_bits()==H::PI_HOLLYWOOD&&irq.starlet_asserted());
        irq.write(P,H::PPC_FLAG,bit);
        assert(irq.read(P,H::PPC_FLAG)==other&&!irq.broadway_asserted());
        irq.write(A,H::ARM_FLAG,bit);
        assert(irq.read(A,H::ARM_FLAG)==other&&irq.starlet_asserted());
        irq.write(P,H::PPC_MASK,other);assert(irq.broadway_asserted());
        irq.write(A,H::ARM_FLAG,other);assert(!irq.starlet_asserted());
        irq.write(P,H::PPC_MASK,0);assert(irq.read(P,H::PPC_FLAG)==other&&!irq.broadway_asserted());
    }
    irq.reset();irq.write(P,H::PPC_MASK,H::IPC_PPC);irq.write(A,H::ARM_MASK,H::IPC_ARM);
    ipc.write(P,M::PPCCTRL,M::IY1|M::IY2|M::X1);
    ipc.write(A,M::ARMCTRL,M::IX1);
    irq.sample_ipc(ipc);assert(irq.starlet_asserted()&&!irq.broadway_asserted());
    ipc.write(A,M::ARMCTRL,M::IX1|M::ARM_X1|M::ARM_Y2);
    irq.sample_ipc(ipc);assert(irq.starlet_asserted()&&irq.broadway_asserted());
    irq.write(A,H::ARM_FLAG,H::IPC_ARM);assert(!irq.starlet_asserted());
    ipc.write(P,M::PPCCTRL,M::IY1|M::IY2|M::Y2);irq.sample_ipc(ipc);
    assert(!ipc.broadway_irq_level()&&irq.broadway_asserted());
    irq.write(P,H::PPC_FLAG,H::IPC_PPC);assert(!irq.broadway_asserted());
    ipc.write(A,M::ARMCTRL,M::IX1|M::ARM_Y1);irq.sample_ipc(ipc);
    assert(irq.broadway_asserted());
    // W1C clears current latch; an asserted source can be sampled again.
    irq.write(P,H::PPC_FLAG,H::IPC_PPC);assert(!irq.broadway_asserted());
    irq.sample_ipc(ipc);assert(irq.broadway_asserted());
    ipc.write(P,M::PPCCTRL,M::IY1|M::IY2|M::Y1);
    irq.write(P,H::PPC_FLAG,H::IPC_PPC);irq.sample_ipc(ipc);
    assert(!irq.broadway_asserted()&&irq.pi_cause_bits()==0);
    for(uint32_t off:{0u,0x31u,H::ARM_FLAG,H::ARM_MASK,0xffffffffu}){
        bool rd=false,wr=false;
        try{(void)irq.read(P,off);}catch(const std::out_of_range&){rd=true;}
        try{irq.write(P,off,0xffffffffu);}catch(const std::out_of_range&){wr=true;}
        assert(rd&&wr&&!irq.broadway_asserted()&&!irq.starlet_asserted());
    }
    std::cout<<"PASS: Hollywood IRQ 32-source latches, masks, W1C, IPC ACK/reply and PI cause routing\n";
}
