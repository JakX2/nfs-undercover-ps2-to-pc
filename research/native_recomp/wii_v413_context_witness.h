#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
// Read-only witness for the original OSLoadContext/RFI successor. The host
// never writes a guest register, context, PC, IRQ or IOS result here.
struct NandContextWitness {
    unsigned load=0, mapped=0, hit=0, regs=0, msr=0, coherent=0, interrupted=0;
    std::uint64_t entry_inst=0;
    std::uint32_t pc=0, expected_msr=0, lr=0, ctr=0, xer=0;
    std::array<std::uint32_t,32> gprs{};

    static bool context_range(std::uint32_t a) {
        return (a&3u)==0u && ((a>=0x80000000u && a<=0x81800000u-416u) ||
                             (a>=0x90000000u && a<=0x94000000u-416u));
    }
    template<class Cpu>
    bool capture(Cpu& c,std::uint32_t resume,std::uint32_t srr1,bool masked) {
        if(load) return false;
        load=1;
        const auto a=c.gpr[3];
        if(!masked || !context_range(a)) return true;
        // Check every word, not just the outer endpoints of a mapping.
        for(std::uint32_t off=0;off<416u;off+=4u)
            if(!c.mmu.get_ptr(a+off) || !c.mmu.get_ptr(a+off+3u)) return true;
        pc=c.mmu.read32(a+408u);
        if(!pc || (pc&3u) || !c.mmu.get_ptr(pc)) return true;
        expected_msr=c.mmu.read32(a+412u);
        lr=c.mmu.read32(a+132u);
        ctr=c.mmu.read32(a+136u);
        xer=c.mmu.read32(a+140u);
        for(unsigned i=0;i<32u;++i) gprs[i]=c.mmu.read32(a+4u*i);
        entry_inst=c.inst_count;
        mapped=1;
        interrupted=unsigned(pc==resume && expected_msr==srr1);
        return true;
    }
    template<class Cpu>
    bool observe(Cpu& c,bool irq_coherent) {
        if(!mapped || hit || c.pc!=pc || c.inst_count<=entry_inst) return false;
        hit=1;
        regs=unsigned(c.gpr==gprs && c.lr==lr && c.ctr==ctr && c.xer==xer);
        msr=unsigned(c.msr==expected_msr);
        coherent=unsigned(irq_coherent);
        return true;
    }
    bool restored() const { return mapped && hit && regs && msr && coherent; }
};
} // namespace undercover::wii
