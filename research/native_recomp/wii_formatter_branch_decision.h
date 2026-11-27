#pragma once
#include <cstdint>
#include <optional>

namespace undercover::wii {

// Pure, original-free PowerPC branch effect prediction. This function does
// not fetch, translate, dispatch or execute any guest instruction. Private
// owner fixtures must independently authenticate branch words and both
// possible native destinations before using the prediction as a witness.
struct FormatterBranchPrediction {
    enum class Kind { Direct, Conditional, LinkRegister, CountRegister };
    Kind kind{};
    uint32_t target=0, next_pc=0, ctr=0, lr=0;
    bool taken=false, cr_tested=false, ctr_decremented=false;
    bool linked=false, absolute=false;
};

inline std::optional<FormatterBranchPrediction> predict_formatter_branch(
    uint32_t word,uint32_t pc,uint32_t cr,uint32_t ctr,uint32_t lr) {
    if((pc&3u)||word==0x44000002u)return {};
    const unsigned op=word>>26u;
    FormatterBranchPrediction out;
    out.ctr=ctr;out.lr=lr;
    out.linked=bool(word&1u);
    out.absolute=bool(word&2u);
    bool conditional=false;
    if(op==18u) {
        out.kind=FormatterBranchPrediction::Kind::Direct;
    }else if(op==16u) {
        out.kind=FormatterBranchPrediction::Kind::Conditional;
        conditional=true;
    }else if(op==19u) {
        const unsigned xo=(word>>1u)&1023u;
        if(xo!=16u&&xo!=528u)return {};
        // XL-form bits 16..18 are reserved. PowerPC ISA 2.02
        // permits BH=01 for bclr (non-return target-history hint), but
        // reserves BH=01 for bcctr; BH=10 is reserved for both forms.
        // Hints do not alter the architectural LR/CTR/PC effects.
        if(word&0x0000e000u)return {};
        const unsigned bh=(word>>11u)&3u;
        if(bh==2u||(bh==1u&&xo==528u))return {};
        out.kind=xo==16u?FormatterBranchPrediction::Kind::LinkRegister:
                            FormatterBranchPrediction::Kind::CountRegister;
        if(xo==528u&&!(word&0x00800000u))return {}; // bcctr cannot decrement CTR
        out.absolute=false;
        conditional=true;
    }else return {};

    const unsigned bo=(word>>21u)&31u,bi=(word>>16u)&31u;
    if(conditional) {
        bool ctr_ok=true,cr_ok=true;
        out.cr_tested=!(bo&16u);
        out.ctr_decremented=!(bo&4u);
        if(out.ctr_decremented) {
            --out.ctr;
            ctr_ok=bool(out.ctr)!=bool(bo&2u);
        }
        if(out.cr_tested)
            cr_ok=bool((cr>>(31u-bi))&1u)==bool(bo&8u);
        out.taken=ctr_ok&&cr_ok;
    }else out.taken=true;

    if(op==19u) {
        // Indirect branch targets use *old* LR/CTR, even with LK set.
        out.target=(out.kind==FormatterBranchPrediction::Kind::LinkRegister?
                    lr:ctr)&~3u;
    }else {
        // Direct displacement is signed 16-bit (bc) or 26-bit (b).
        const uint32_t mask=op==16u?0x0000fffcu:0x03fffffcu;
        const uint32_t sign=op==16u?0x00008000u:0x02000000u;
        const uint32_t offset=((word&mask)^sign)-sign;
        out.target=out.absolute?offset:pc+offset;
    }
    out.next_pc=out.taken?out.target:pc+4u;
    if(out.linked)out.lr=pc+4u;
    return out;
}
} // namespace undercover::wii
