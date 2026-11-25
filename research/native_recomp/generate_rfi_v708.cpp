// Generate deliberately synthetic PPC entry/IRQ/stop functions.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <iostream>
#include <vector>
static std::vector<uint8_t> be(std::initializer_list<uint32_t> words){
    std::vector<uint8_t> v;
    for(auto w:words)for(unsigned shift:{24u,16u,8u,0u})v.push_back(uint8_t(w>>shift));
    return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    const std::filesystem::path dir=argv[1];
    const bool split=std::string(argv[2])=="split";
    constexpr uint32_t entry=0x80004000u,irq=0x80000500u;
    nwii::loader::Executable exe;exe.entry_point=entry;
    auto add=[&](uint32_t a,std::vector<uint8_t> v){
        exe.sections.push_back({a,uint32_t(v.size()),std::move(v),true,false});
    };
    add(entry,be({0x38800000u,0x60848000u,(31u<<26)|(4u<<21)|(146u<<1),
                  0x38a50001u,0x44000002u,0x4e800020u}));
    // Independent synthetic guest vector saves every register it uses,
    // modifies CR0, acknowledges the native device, restores CR and GPRs,
    // and executes actual rfi. No original code included.
    auto vector=be({0x90e1fffcu,0x9101fff8u,0x9121fff4u,0x7d200026u,0x9121fff0u,
                    0x2c070000u,0x3ce0cd00u,0x60e76434u,0x3d000800u,0x91070004u,
                    0x3d00e001u,0x61080300u,0x91070000u,0x8121fff0u,0x7d2ff120u,
                    0x8121fff4u,0x8101fff8u,0x80e1fffcu,0x4c000064u});
    add(irq,std::move(vector));
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({irq});
    nwii::recomp::RecompilerConfig config;config.output_dir=dir.string();config.split_output=split;
    // The pinned emitter deliberately defaults copied low-memory code to
    // interpretation; allow only this explicitly installed synthetic vector.
    config.native_low_mem_entries.insert(irq);
    nwii::recomp::Recompiler recomp(analyzer,nullptr,config);
    auto files=recomp.generate_cpp(entry);
    assert(!files.empty());
    std::ifstream file(dir/(split?"main_output.cpp":"output.cpp"));
    const std::string text((std::istreambuf_iterator<char>(file)),{});
    assert(text.find("case 0x8000400C: func_80004000(ctx); break;")!=std::string::npos);
    bool native_vector=false;
    for(const auto& f:std::filesystem::directory_iterator(dir))if(f.path().extension()==".cpp"){
        std::ifstream v(f.path());const std::string src((std::istreambuf_iterator<char>(v)),{});
        native_vector|=src.find("loc_80000500: ;")!=std::string::npos;
    }
    assert(native_vector);
    std::ofstream raw(dir/"vector.bin",std::ios::binary); // exact synthetic vector bytes for installed-memory authentication
    for(const auto& section:exe.sections)if(section.address==irq)raw.write(reinterpret_cast<const char*>(section.data.data()),section.data.size());
    assert(raw.good());
    std::cout<<"PASS: exact native mtmsr continuation case in "<<argv[2]<<" dispatcher\n";
}
