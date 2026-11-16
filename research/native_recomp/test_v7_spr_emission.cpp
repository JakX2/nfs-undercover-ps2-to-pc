// Synthetic PowerPC instruction-emission regression; no proprietary game code.
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
static uint32_t make_spr(uint32_t opcode, uint32_t gpr, uint32_t spr) {
    return (31u << 26) | (gpr << 21) | ((spr & 31u) << 16) |
           ((spr >> 5) << 11) | (opcode << 1);
}
static void require(bool value, const std::string& info) {
    if (!value) throw std::runtime_error(info);
}
int main() {
    nwii::loader::Executable empty;
    nwii::analyzer::Analyzer analyzer(empty);
    nwii::recomp::Recompiler recomp(analyzer);
    unsigned checks = 0;
    auto emit = [&](uint32_t opcode, uint32_t gpr, uint32_t spr) {
        nwii::analyzer::Function f{};
        f.start_address = 0x80010000;
        f.end_address = f.start_address + 4;
        f.instructions.push_back({f.start_address, make_spr(opcode, gpr, spr)});
        return recomp.generate_function_cpp(f);
    };
    for (uint32_t spr : {528u, 543u, 560u, 575u, 25u, 18u, 19u,
                         284u, 285u, 920u, 1008u, 1017u, 952u, 958u, 1020u}) {
        auto write = emit(467, 13, spr);
        require(write.find("ctx.write_unmodeled_spr(" + std::to_string(spr) + ", ctx.gpr[13])") != std::string::npos,
                "missing guest SPR write: " + std::to_string(spr)); ++checks;
        require(write.find("unhandled mtspr") == std::string::npos, "silent drop"); ++checks;
        auto read = emit(339, 14, spr);
        require(read.find("ctx.read_unmodeled_spr(" + std::to_string(spr) + ")") != std::string::npos,
                "missing guest SPR read: " + std::to_string(spr)); ++checks;
    }
    // Existing architected registers must stay on their existing paths.
    require(emit(467, 3, 8).find("ctx.lr = ctx.gpr[3]") != std::string::npos,"mtlr altered"); ++checks;
    require(emit(467, 4, 912).find("ctx.gqr[0] = ctx.gpr[4]") != std::string::npos,"GQR altered"); ++checks;
    require(emit(467, 5, 272).find("ctx.sprg[0] = ctx.gpr[5]") != std::string::npos,"SPRG altered"); ++checks;
    require(emit(339, 6, 287).find("mfspr PVR") != std::string::npos,"PVR altered"); ++checks;
    std::cout << "PASS: " << checks << " V7 synthetic emitted SPR checks\n";
}
