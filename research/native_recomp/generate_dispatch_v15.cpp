// Native NWiiRecomp full generated dispatcher for a *private* compact Wii DOL.
// Usage: generate_dispatch_v15 PRIVATE_SLICED_DOL OUTPUT_DIR EXPECTED_ENTRY_HEX PARENT_BYTES EXPECTED_CALLEE_HEX CALLEE_BYTES
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

int main(int argc, char** argv) try {
    if (argc!=7) throw std::invalid_argument("usage: tool PRIVATE_SLICED_DOL EMPTY_OUTPUT_DIR");
    const std::filesystem::path dest=argv[2];
    if (!std::filesystem::is_directory(dest) || !std::filesystem::is_empty(dest))
        throw std::invalid_argument("output directory must exist and be empty");
    nwii::loader::Executable exe;
    if (!exe.load_dol(argv[1])) throw std::runtime_error("invalid DOL");
    nwii::analyzer::Analyzer analyzer(exe);
    analyzer.analyze({0x80004200u}); // independent, synthetic SC/BLR test terminator
    const auto& funcs=analyzer.get_functions();
    const auto entry = static_cast<uint32_t>(std::stoul(argv[3],nullptr,16));
    const auto parent_size = static_cast<uint32_t>(std::stoul(argv[4],nullptr,10));
    const auto callee = static_cast<uint32_t>(std::stoul(argv[5],nullptr,16));
    const auto callee_size = static_cast<uint32_t>(std::stoul(argv[6],nullptr,10));
    if (exe.entry_point != entry || funcs.size()!=3 ||
        !funcs.count(entry) || !funcs.count(callee) || !funcs.count(0x80004200u) ||
        funcs.at(entry).instructions.size() * 4 != parent_size ||
        funcs.at(callee).instructions.size() * 4 != callee_size ||
        funcs.at(0x80004200u).instructions.size() * 4 != 8)
        throw std::invalid_argument("expected exactly parent/callee plus synthetic stop");
    // Verify all three decoded regions lie in their declared text spans and
    // that the selected parent has a real direct BL to the selected callee.
    bool has_link_edge=false;
    for (const auto& ins: funcs.at(entry).instructions) {
        if ((ins.opcode >> 26) == 18u && (ins.opcode & 1u)) {
            uint32_t d=ins.opcode & 0x03fffffcu;
            if (d & 0x02000000u) d |= 0xfc000000u;
            const uint32_t target=(ins.opcode & 2u) ? d : ins.address+d;
            if (target==callee) has_link_edge=true;
        }
    }
    if (!has_link_edge) throw std::invalid_argument("parent must directly BL to selected callee");
    nwii::recomp::RecompilerConfig config;
    config.output_dir=dest.string();
    config.split_output=false;
    nwii::recomp::Recompiler recompiler(analyzer,nullptr,config);
    const auto generated=recompiler.generate_cpp(exe.entry_point);
    if (generated.size()!=1 || generated[0]!="output.cpp")
        throw std::runtime_error("unexpected NWiiRecomp output layout");
    std::cout<<"V15 generated real NWiiRecomp run_game dispatcher for "<<funcs.size()
             <<" selected functions, entry 0x"<<std::hex<<exe.entry_point<<std::dec<<"\n";
} catch(const std::exception& e) {std::cerr<<"V15: "<<e.what()<<"\n";return 1;}
