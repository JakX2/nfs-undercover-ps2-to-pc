// Original-free driver: emit actual upstream NWiiRecomp run_game for a bounded
// three-function startup DOL. The private owner DOL slice itself is NEVER
// redistributed; output directory is owner-local and must start empty.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr uint32_t ENTRY=0x8000403Cu;
constexpr uint32_t REG_INIT=0x800041A8u;
constexpr uint32_t HARDWARE_BOUNDARY=0x800042E0u;

uint32_t linked_target(const nwii::analyzer::Instruction& instruction) {
    const uint32_t word=instruction.opcode;
    if ((word>>26)!=18u || !(word&1u) || (word&2u))
        throw std::invalid_argument("expected relative BL in startup entry");
    uint32_t delta=word&0x03FFFFFCu;
    if(delta&0x02000000u)delta|=0xFC000000u;
    return instruction.address+delta;
}
}

int main(int argc,char** argv) try {
    if(argc!=4 || (std::string(argv[3])!="owner" && std::string(argv[3])!="synthetic"))
        throw std::invalid_argument("usage: driver TEST_DOL EMPTY_OUTPUT_DIR owner|synthetic");
    const bool owner=std::string(argv[3])=="owner";
    const std::filesystem::path out=argv[2];
    if(!std::filesystem::is_directory(out) || !std::filesystem::is_empty(out))
        throw std::invalid_argument("output directory must exist and be empty");
    nwii::loader::Executable exe;
    if(!exe.load_dol(argv[1]))throw std::runtime_error("invalid DOL");
    if(exe.entry_point!=ENTRY || exe.sections.size()!=3)
        throw std::invalid_argument("unexpected entry or number of DOL sections");
    nwii::analyzer::Analyzer analyzer(exe);
    analyzer.analyze({HARDWARE_BOUNDARY});
    const auto& functions=analyzer.get_functions();
    if(functions.size()!=3 || !functions.count(ENTRY) || !functions.count(REG_INIT) ||
       !functions.count(HARDWARE_BOUNDARY))
        throw std::invalid_argument("startup path did not resolve three expected functions");
    const auto& entry=functions.at(ENTRY).instructions;
    const auto& regs=functions.at(REG_INIT).instructions;
    const auto& stop=functions.at(HARDWARE_BOUNDARY).instructions;
    if(entry.size()!=2 || entry[0].address!=ENTRY || entry[1].address!=ENTRY+4 ||
       linked_target(entry[0])!=REG_INIT || linked_target(entry[1])!=HARDWARE_BOUNDARY)
        throw std::invalid_argument("unexpected first two BLs in startup prefix");
    if(regs.size()!=(owner?36u:2u) || regs.front().address!=REG_INIT ||
       regs.back().opcode!=0x4E800020u)
        throw std::invalid_argument("unexpected register initializer length/return");
    for(size_t i=0;i+1<regs.size();++i){
        const uint32_t op=regs[i].opcode>>26;
        if(op==16u||op==17u||op==18u||op==19u)
            throw std::invalid_argument("register initializer contains unexpected control-flow");
    }
    if(stop.size()!=2 || stop.front().opcode!=0x44000002u ||
       stop.back().opcode!=0x4E800020u)
        throw std::invalid_argument("missing synthetic hardware-boundary stop");
    nwii::recomp::RecompilerConfig cfg;
    cfg.output_dir=out.string();
    cfg.split_output=false;
    nwii::recomp::Recompiler recompiler(analyzer,nullptr,cfg);
    const auto generated=recompiler.generate_cpp(ENTRY);
    if(generated.size()!=1 || generated.front()!="output.cpp")
        throw std::runtime_error("unexpected NWiiRecomp generated output files");
    std::cout<<"PASS: upstream run_game dispatcher emitted at first real startup address"
             <<" 0x"<<std::hex<<ENTRY<<std::dec<<", owner-prefix="<<owner
             <<", PPC instructions="<<entry.size()+regs.size()+stop.size()<<"\n";
    return 0;
} catch(const std::exception& ex) {
    std::cerr<<"V16 startup generator: "<<ex.what()<<"\n";
    return 1;
}
