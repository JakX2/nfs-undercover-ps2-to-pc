// Emit NWiiRecomp's ACTUAL non-split run_game for bounded six-function DOL.
// All original-derived generated code remains in owner-local private directory.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <array>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr uint32_t ENTRY = 0x8000403cu, REGS = 0x800041a8u, HW = 0x800042e0u;
constexpr std::array<uint32_t,3> OS{0x80520fb4u,0x8051fbb0u,0x80522540u};
uint32_t linked_target(const nwii::analyzer::Instruction& i) {
    const uint32_t w=i.opcode;
    if(w>>26!=18u || !(w&1u) || (w&2u))
        throw std::invalid_argument("expected relative BL opcode");
    uint32_t delta=w&0x03fffffcu;
    if(delta&0x02000000u)delta|=0xfc000000u;
    return i.address+delta;
}
void require(bool ok,const char* msg) {if(!ok)throw std::invalid_argument(msg);}
}

int main(int argc,char** argv)try{
    require(argc==4,"Usage: generator TEST_DOL EMPTY_OUTPUT_DIR owner|synthetic");
    const std::string mode=argv[3];
    require(mode=="owner"||mode=="synthetic","invalid generation mode");
    const bool owner=mode=="owner";
    const std::filesystem::path out=argv[2];
    require(std::filesystem::is_directory(out)&&std::filesystem::is_empty(out),
            "generated output directory must exist and be empty");
    nwii::loader::Executable exe;
    require(exe.load_dol(argv[1]),"invalid input DOL");
    require(exe.entry_point==ENTRY && exe.sections.size()==6,"unexpected DOL entry/section count");
    nwii::analyzer::Analyzer analyzer(exe);
    analyzer.analyze({OS[0],OS[1],OS[2]});
    const auto& funcs=analyzer.get_functions();
    require(funcs.size()==6 && funcs.count(ENTRY)&&funcs.count(REGS)&&funcs.count(HW)
            && funcs.count(OS[0])&&funcs.count(OS[1])&&funcs.count(OS[2]),
            "startup slice did not analyze exactly six functions");
    const auto& entry=funcs.at(ENTRY).instructions;
    const auto& regs=funcs.at(REGS).instructions;
    const auto& hw=funcs.at(HW).instructions;
    require(entry.size()==4 && entry[0].address==ENTRY && entry[1].address==ENTRY+4
            && linked_target(entry[0])==REGS && linked_target(entry[1])==HW
            && entry[2].opcode==0x44000002u && entry[3].opcode==0x4e800020u,
            "unexpected startup BL/stop/return layout");
    require(regs.size()==(owner?36u:2u) && regs[0].address==REGS
            && regs.back().opcode==0x4e800020u,"unexpected register initialization span");
    for(size_t i=0;i+1<regs.size();++i) {
        const uint32_t op=regs[i].opcode>>26;
        require(op!=16u&&op!=17u&&op!=18u&&op!=19u,"register initializer escaped selected span");
    }
    require(hw.size()==9 && hw[0].address==HW && hw[8].opcode==0x4e800020u,
            "unexpected hardware initializer length/return");
    // Source-backed privileged instruction sequence: mfmsr rX; ori rX,rX,0x2000;
    // mtmsr rX; mflr r31; three direct BL; mtlr r31; blr.
    const uint32_t msr_reg=(hw[0].opcode>>21)&31u;
    const uint32_t ori=hw[1].opcode;
    require((hw[0].opcode&0xfc1fffffu)==0x7c0000a6u &&
            (ori>>26)==24u && ((ori>>21)&31u)==msr_reg &&
            ((ori>>16)&31u)==msr_reg && (ori&0xffffu)==0x2000u &&
            (hw[2].opcode&0xfc1fffffu)==0x7c000124u &&
            ((hw[2].opcode>>21)&31u)==msr_reg &&
            hw[3].opcode==0x7fe802a6u && hw[7].opcode==0x7fe803a6u,
            "unrecognized original hardware MSR/LR instruction sequence");
    // No real Wii OS body is included, only explicit test-only boundaries.
    for(int i=0;i<3;++i)
        require(linked_target(hw[4+i])==OS[i],"unexpected hardware service BL target/order");
    for(auto target:OS) {
        const auto& f=funcs.at(target).instructions;
        require(f.size()==2 && f[0].opcode==0x44000002u && f[1].opcode==0x4e800020u,
                "missing synthetic test-only Wii OS service boundary");
    }
    nwii::recomp::RecompilerConfig cfg;
    cfg.output_dir=out.string(); cfg.split_output=false;
    nwii::recomp::Recompiler recompiler(analyzer,nullptr,cfg);
    const auto written=recompiler.generate_cpp(ENTRY);
    require(written.size()==1 && written.front()=="output.cpp","unexpected generated output");
    std::cout<<"PASS: NWiiRecomp emitted actual six-function dispatcher; original="<<owner
             <<" translated hardware instructions="<<hw.size()<<" startup entry=0x"
             <<std::hex<<ENTRY<<std::dec<<"\n";
    return 0;
}catch(const std::exception& e){std::cerr<<"V17 dispatch generator: "<<e.what()<<"\n";return 1;}
