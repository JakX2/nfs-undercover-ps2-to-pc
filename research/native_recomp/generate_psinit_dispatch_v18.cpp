// Original-free native-dispatch harness: translates selected private DOL text
// through the real upstream NWiiRecomp analyzer and non-split C++ emitter.
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
constexpr uint32_t ENTRY=0x8000403cu, REGS=0x800041a8u, HW=0x800042e0u;
constexpr uint32_t PS=0x80520fb4u, HIDR=0x804b79dcu, HIDW=0x804b79e4u;
constexpr uint32_t IC=0x805223acu, FPR=0x8051fbb0u, CACHE=0x80522540u;
constexpr std::array<uint32_t,9> ADDRS {ENTRY,REGS,HW,PS,HIDR,HIDW,IC,FPR,CACHE};
void require(bool cond, const char* what) {if(!cond)throw std::invalid_argument(what);}
uint32_t bl_dest(const nwii::analyzer::Instruction& op) {
    const uint32_t w=op.opcode;
    require(w>>26==18 && (w&3)==1, "expected PPC BL relative instruction");
    uint32_t disp=w&0x03fffffcu;
    if(disp&0x02000000u)disp|=0xfc000000u;
    return op.address+disp;
}
uint32_t spr(const uint32_t w) {
    return (((w>>11)&31u)<<5) | ((w>>16)&31u);
}
void validate_spr(const nwii::analyzer::Instruction& op,int ext,uint32_t n) {
    const uint32_t w=op.opcode;
    require(w>>26==31 && ((w>>1)&1023u)==uint32_t(ext) && spr(w)==n,
            "unexpected original mfspr/mtspr instruction");
}
}
int main(int argc,char** argv)try{
    require(argc==4,"Usage: generate_psinit_dispatch_v18 PRIVATE_DOL EMPTY_DIR owner|synthetic");
    const std::string mode=argv[3];
    require(mode=="owner"||mode=="synthetic","invalid owner/synthetic selection");
    const bool owner=mode=="owner";
    const std::filesystem::path dir=argv[2];
    require(std::filesystem::is_directory(dir)&&std::filesystem::is_empty(dir),
            "output directory must exist and be empty");
    nwii::loader::Executable exe;
    require(exe.load_dol(argv[1]),"source DOL rejected by loader");
    require(exe.entry_point==ENTRY && exe.sections.size()==6,"unexpected DOL entry or section count");
    nwii::analyzer::Analyzer analyzer(exe);
    analyzer.analyze({FPR,CACHE});
    const auto& funcs=analyzer.get_functions();
    require(funcs.size()==ADDRS.size(),"analyzer did not recover exactly nine functions");
    for(uint32_t address:ADDRS)require(funcs.count(address)>0,"missing known Wii function in analyzer output");
    const auto& start=funcs.at(ENTRY).instructions;
    require(start.size()==4 && bl_dest(start.at(0))==REGS && bl_dest(start.at(1))==HW
            && start.at(2).opcode==0x44000002u && start.at(3).opcode==0x4e800020u,
            "unexpected startup call/stop sequence");
    const auto& regs=funcs.at(REGS).instructions;
    require(regs.size()==(owner?36u:3u)&&regs.back().opcode==0x4e800020u,
            "unexpected register init span");
    const auto& hw=funcs.at(HW).instructions;
    require(hw.size()==9 && hw.back().opcode==0x4e800020u,
            "hardware initialization span incomplete");
    for(size_t i=0;i<3;++i){
        const auto target=std::array<uint32_t,3>{PS,FPR,CACHE}[i];
        require(bl_dest(hw.at(4+i))==target,"hardware service target changed");
    }
    const auto& ps=funcs.at(PS).instructions;
    require(ps.size()==21 && ps.back().opcode==0x4e800020u,
            "real PSInit span must be complete, 21 instructions");
    for(size_t i=0;i<3;++i){
        const auto at=std::array<size_t,3>{3,5,6}[i];
        const auto target=std::array<uint32_t,3>{HIDR,HIDW,IC}[i];
        require(bl_dest(ps.at(at))==target,"PSInit indirect dependency differs");
    }
    require((ps.at(7).opcode>>26)==31 && ((ps.at(7).opcode>>1)&1023u)==598u,
            "PSInit lost cache synchronization");
    const uint32_t oris=ps.at(4).opcode;
    require(oris>>26==25 && ((oris>>21)&31u)==3u &&
            ((oris>>16)&31u)==3u && (oris&0xffffu)==0xa000u,
            "PSInit lost HID2 paired-single enable mask");
    require(ps.at(8).opcode==0x38600000u,"PSInit must zero r3 before GQR setup");
    for(size_t i=0;i<8;++i){
        validate_spr(ps.at(9+i),467,912+uint32_t(i));
        require(((ps.at(9+i).opcode>>21)&31u)==3u,"PSInit GQR must source zero from r3");
    }
    const auto& hidread=funcs.at(HIDR).instructions;
    const auto& hidwrite=funcs.at(HIDW).instructions;
    require(hidread.size()==2 && hidread.back().opcode==0x4e800020u,
            "HID2 read helper does not return");
    require(hidwrite.size()==2 && hidwrite.back().opcode==0x4e800020u,
            "HID2 write helper does not return");
    validate_spr(hidread.at(0),339,920);
    validate_spr(hidwrite.at(0),467,920);
    require(((hidread.at(0).opcode>>21)&31u)==3u &&
            ((hidwrite.at(0).opcode>>21)&31u)==3u,
            "HID2 read/write helpers must use ABI r3");
    const auto& ic=funcs.at(IC).instructions;
    require(ic.size()==4 && ic.back().opcode==0x4e800020u,
            "instruction-cache invalidation helper changed");
    validate_spr(ic.at(0),339,1008);
    validate_spr(ic.at(2),467,1008);
    const uint32_t ic_register=(ic.at(0).opcode>>21)&31u;
    const uint32_t ic_ori=ic.at(1).opcode;
    require(ic_register==((ic.at(2).opcode>>21)&31u) &&
            ic_ori>>26==24 && ((ic_ori>>21)&31u)==ic_register &&
            ((ic_ori>>16)&31u)==ic_register && (ic_ori&0xffffu)==0x0800u,
            "instruction-cache invalidate HID0 bit/register incorrect");
    for(uint32_t pc:{FPR,CACHE}){
        const auto& f=funcs.at(pc).instructions;
        require(f.size()==2 && f.front().opcode==0x44000002u &&
                f.back().opcode==0x4e800020u,
                "expected explicit synthetic FPR/cache service boundary");
    }
    nwii::recomp::RecompilerConfig cfg;
    cfg.output_dir=dir.string(); cfg.split_output=false;
    nwii::recomp::Recompiler recompiler(analyzer,nullptr,cfg);
    const auto outputs=recompiler.generate_cpp(ENTRY);
    require(outputs.size()==1 && outputs.at(0)=="output.cpp", "recompiler output unexpected");
    std::cout<<"PASS: genuine NWiiRecomp dispatch emits "<<funcs.size()
             <<" functions; owner="<<owner<<" original PSInit/HID/IC sequence verified\n";
    return 0;
}catch(const std::exception& e){std::cerr<<"V18 generator: "<<e.what()<<'\n';return 1;}
