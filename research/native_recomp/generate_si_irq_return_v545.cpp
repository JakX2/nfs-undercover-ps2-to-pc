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
    auto spr=[](uint32_t n,uint32_t reg,bool write){
        const uint32_t field=((n&31u)<<5)|(n>>5);
        return (31u<<26)|(reg<<21)|(field<<11)|((write?467u:339u)<<1);
    };
    std::vector<uint8_t> vector;
    auto emit=[&](uint32_t word){auto b=be({word});vector.insert(vector.end(),b.begin(),b.end());};
    for(unsigned k=0;k<4;++k)emit(spr(272u+k,8u+k,true));
    for(unsigned k=0;k<4;++k)emit(spr(272u+k,12u+k,false));
    // Synthetic guest handler acknowledges the native SI device via MMIO.
    // r7 = SI COMCSR, r8 = channel-zero NOREP W1C then TC W1C.
    emit(0x3ce0cd00u);emit(0x60e76434u);
    emit(0x3d000800u);emit(0x91070004u);
    emit(0x3d00e001u);emit(0x61080300u);emit(0x91070000u);
    emit(0x38c60001u);emit(0x4c000064u);
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
