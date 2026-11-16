// Standalone, offline-only driver for the upstream NWiiRecomp analyzer/recompiler.
// Removes TOML/SDL GUI dependencies from the *build-time* translation step.
// It does not emulate Wii hardware or execute copyrighted game code.
#include <iostream>
#include <filesystem>
#include <string>
#include <vector>
#include <chrono>
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"

int main(int argc, char** argv) {
    if (argc != 4 && argc != 6) {
        std::cerr << "Usage: offline_recompiler_driver DOL SYMBOL_CSV OUTPUT_DIR [--generate UPSTREAM_RUNTIME_SRC]\n";
        return 2;
    }
    const auto start = std::chrono::steady_clock::now();
    const std::string dol = argv[1], csv = argv[2], out = argv[3];
    nwii::loader::Executable exec;
    if (!exec.load_dol(dol)) { std::cerr << "DOL load failed\n"; return 3; }
    std::cout << "DOL: " << std::hex << exec.entry_point << std::dec << " sections=" << exec.sections.size() << std::endl;
    nwii::recomp::SymbolTable symbols;
    if (!symbols.load_csv(csv)) { std::cerr << "Symbol import failed\n"; return 4; }
    std::vector<uint32_t> addrs;
    for (const auto& p : symbols.get_all_symbols()) addrs.push_back(p.first);
    std::cout << "Root symbols=" << addrs.size() << std::endl;
    nwii::analyzer::Analyzer analyzer(exec);
    analyzer.analyze(addrs);
    const auto& funcs = analyzer.get_functions();
    std::cout << "Discovered functions=" << funcs.size() << std::endl;
    uint64_t ninst = 0;
    for (const auto& [addr, fun] : funcs) ninst += fun.instructions.size();
    std::cout << "Analyzed instruction slots=" << ninst << std::endl;
    const auto dt = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    std::cout << "Analysis seconds=" << dt << std::endl;
    if (argc == 6) {
        if (std::string(argv[4]) != "--generate") return 2;
        nwii::recomp::RecompilerConfig cfg;
        cfg.project_name = "UndercoverWiiLocal";
        cfg.output_dir = out;
        cfg.runtime_source_dir = argv[5];
        cfg.split_output = true;
        cfg.instructions_per_file = 16000;
        nwii::recomp::Recompiler recomp(analyzer, &symbols, cfg);
        const bool ok = recomp.generate_cmake_project(exec.entry_point);
        std::cout << "Generated_project=" << ok << std::endl;
        if (!ok) return 5;
    }
    return 0;
}
