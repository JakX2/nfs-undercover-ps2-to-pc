#pragma once
#include "wii_post_stm_sc_report.h"
#include <array>
#include <cstdint>
#include <limits>
#include <optional>

namespace undercover::wii {

// A read-only post-execution observer for one authenticated PowerPC lbz/lbzx.
// The translated function, never this witness, must execute the guest load.
// A report-frame byte is accepted only through the existing report witness.
struct FormatterReportByteStep {
    uint32_t pc, word, next_pc, next_word, lr;
    uint32_t guest_address, child_sp, child_link, child_depth, extra_frame;
    uint8_t expected_byte;
};

class FormatterReportByteTransition {
public:
    unsigned stage() const { return stage_; }
    bool failed() const { return failed_; }

    template<class C, class Report>
    bool arm(C& c, Report& report, const FormatterReportByteStep& s, bool held) {
        if (stage_ || failed_ || !safe(c) || c.pc != s.pc || c.lr != s.lr ||
            s.pc > std::numeric_limits<uint32_t>::max() - 8u ||
            s.next_pc != s.pc + 4u || s.next_word == 0x44000002u ||
            !word(c,s.pc,s.word) || !word(c,s.next_pc,s.next_word))
            return reject();
        const unsigned op = s.word >> 26u;
        rt_ = (s.word >> 21u) & 31u;
        const unsigned ra = (s.word >> 16u) & 31u;
        const unsigned rb = (s.word >> 11u) & 31u;
        const unsigned xo = (s.word >> 1u) & 1023u;
        indexed_ = op == 31u && xo == 87u && !(s.word & 1u);
        if (!(op == 34u || indexed_) || !volatile_register(rt_))
            return reject();
        const uint32_t base = ra ? c.gpr[ra] : 0u;
        const uint32_t imm = uint32_t(int32_t((s.word & 0xffffu) ^ 0x8000u) - 0x8000);
        const uint32_t address = base + (indexed_ ? c.gpr[rb] : imm);
        if (address != s.guest_address ||
            address < 0x80000000u || address >= 0x81800000u)
            return reject();
        // One checked snapshot per boundary. The report witness owns all
        // live-frame, linkage and byte-provenance checks.
        const auto report_byte = report.observed_child_byte(
            c,held,s.child_sp,s.child_link,s.child_depth,address,s.extra_frame);
        if (!report_byte || *report_byte != s.expected_byte)
            return reject();

        cpu_ = &c;
        step_ = s;
        previous_ = c.gpr;
        gqr_ = c.gqr;
        msr_ = c.msr;
        cr_ = pack(c);
        ctr_ = c.ctr;
        xer_ = c.xer;
        srr0_ = c.srr0;
        srr1_ = c.srr1;
        start_ = c.inst_count;
        stage_ = 1u;
        return true;
    }

    // NWiiRecomp local instruction labels do not imply a new dispatch PC.
    // Keep the callee root in CPUContext::pc and authenticate the exact
    // successor label/word supplied by the generated native hook instead.
    // The guarded return and next unexecuted instruction must remain intact.
    template<class C, class Report>
    bool arm_native(C& c, Report& report, const FormatterReportByteStep& s, bool held,
                    std::optional<uint32_t> following_original = {},
                    std::optional<uint32_t> third_original = {},
                     std::optional<uint32_t> fourth_original = {},
                     std::optional<uint32_t> fifth_original = {},
                     std::optional<uint32_t> sixth_original = {}) {
        const uint32_t guard_offset = sixth_original ? 28u : fifth_original ? 24u : fourth_original ? 20u : third_original ? 16u : following_original ? 12u : 8u;
        if (s.pc > std::numeric_limits<uint32_t>::max() - guard_offset ||
            s.next_pc != s.pc + 4u || s.lr == s.pc || s.lr == s.next_pc ||
            (s.lr>=s.pc && s.lr<=s.pc+guard_offset) ||
            (sixth_original && (!fifth_original || s.lr == s.pc+24u ||
                 *sixth_original == 0x44000002u || !word(c,s.pc+24u,*sixth_original))) ||
            (fifth_original && (!fourth_original || s.lr == s.pc+20u ||
                 *fifth_original == 0x44000002u || !word(c,s.pc+20u,*fifth_original))) ||
            (fourth_original && (!third_original || s.lr == s.pc+16u ||
                 *fourth_original == 0x44000002u || !word(c,s.pc+16u,*fourth_original))) ||
             (third_original && (!following_original || s.lr == s.pc+12u ||
                *third_original == 0x44000002u || !word(c,s.pc+12u,*third_original))) ||
            (following_original &&
                (*following_original == 0x44000002u ||
                 !word(c,s.pc+8u,*following_original))) ||
            !word(c,s.pc+guard_offset,0x44000002u) ||
            !word(c,s.lr,0x44000002u))
            return reject();
        if (!arm(c,report,s,held)) return false;
        native_following_ = following_original;
        native_third_ = third_original;
        native_fourth_ = fourth_original;
        native_fifth_ = fifth_original;
        native_sixth_ = sixth_original;
        native_label_ = true;
        return true;
    }

    template<class C, class Report>
    bool observe_native_label(C& c, Report& report, uint32_t label_pc,
                              uint32_t label_word, bool held) {
        if (!native_label_ || label_pc != step_.next_pc ||
            label_word != step_.next_word ||
            !word(c,step_.pc+8u,native_following_.value_or(0x44000002u)) ||
            (native_following_&&!word(c,step_.pc+12u,native_third_.value_or(0x44000002u))) ||
            (native_third_&&!word(c,step_.pc+16u,native_fourth_.value_or(0x44000002u))) ||
             (native_fourth_&&!word(c,step_.pc+20u,native_fifth_.value_or(0x44000002u))) ||
             (native_fifth_&&!word(c,step_.pc+24u,native_sixth_.value_or(0x44000002u))) ||
            (native_sixth_&&!word(c,step_.pc+28u,0x44000002u)) ||
            !word(c,step_.lr,0x44000002u))
            return reject();
        return observe_effect(c,report,held,step_.pc);
    }

    template<class C, class Report>
    bool observe(C& c, Report& report, bool held) {
        if (native_label_) return reject();
        return observe_effect(c,report,held,step_.next_pc);
    }

private:
    template<class C, class Report>
    bool observe_effect(C& c, Report& report, bool held, uint32_t dispatch_pc) {
        if (stage_ != 1u || failed_ || cpu_ != &c || !safe(c) ||
            start_ == std::numeric_limits<uint64_t>::max() ||
            c.inst_count != start_ + 1u ||
            c.pc != dispatch_pc || c.lr != step_.lr ||
            c.gqr != gqr_ || c.msr != msr_ || pack(c) != cr_ ||
            c.ctr != ctr_ || c.xer != xer_ ||
            c.srr0 != srr0_ || c.srr1 != srr1_ ||
            !word(c,step_.pc,step_.word) ||
            !word(c,step_.next_pc,step_.next_word) ||
            c.gpr[rt_] != step_.expected_byte)
            return reject();
        for (unsigned r = 0; r < previous_.size(); ++r)
            if (r != rt_ && c.gpr[r] != previous_[r])
                return reject();
        const auto report_byte = report.observed_child_byte(
            c,held,step_.child_sp,step_.child_link,step_.child_depth,
            step_.guest_address,step_.extra_frame);
        if (!report_byte || *report_byte != step_.expected_byte)
            return reject();
        stage_ = 2u;
        return true;
    }

    bool reject() { failed_ = true; return false; }
    static bool volatile_register(unsigned r) {
        return r == 0u || (r >= 3u && r <= 12u);
    }
    template<class C> static bool safe(C& c) {
        return c.is_running && !c.in_callback && !c.dispatch_saved_ctx;
    }
    template<class C> static uint32_t pack(C& c) {
        uint32_t bits = 0;
        for (auto f : c.cr)
            bits = (bits << 4u) | (unsigned(f.lt) << 3u) |
                (unsigned(f.gt) << 2u) | (unsigned(f.eq) << 1u) | unsigned(f.so);
        return bits;
    }
    template<class C> static bool word(C& c,uint32_t addr,uint32_t expected) {
        if ((addr & 3u) || addr < 0x80000000u || addr > 0x81800000u - 4u)
            return false;
        auto* first = c.mmu.get_ptr(addr);
        auto* last = c.mmu.get_ptr(addr + 3u);
        return first && last && reinterpret_cast<uintptr_t>(last) ==
            reinterpret_cast<uintptr_t>(first) + 3u &&
            c.mmu.read32(addr) == expected;
    }
    const void* cpu_ = nullptr;
    FormatterReportByteStep step_{};
    std::array<uint32_t,32> previous_{};
    std::array<uint32_t,8> gqr_{};
    uint32_t msr_ = 0, cr_ = 0, ctr_ = 0, xer_ = 0, srr0_ = 0, srr1_ = 0;
    uint64_t start_ = 0;
    unsigned rt_ = 0, stage_ = 0;
    std::optional<uint32_t> native_following_{}, native_third_{}, native_fourth_{}, native_fifth_{}, native_sixth_{};
    bool indexed_ = false, failed_ = false, native_label_ = false;
};
} // namespace undercover::wii
