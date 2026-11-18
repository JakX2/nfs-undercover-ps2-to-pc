#include "synthetic_irq_roundtrip_v78.h"
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
using namespace synthetic_irq_roundtrip;
static std::vector<uint8_t> be(std::initializer_list<uint32_t> words_){
    std::vector<uint8_t> v;
    for(auto w:words_)for(unsigned sh:{24u,16u,8u,0u})v.push_back(uint8_t(w>>sh));
    return v;
}
int main(int argc,char**argv){
    assert(argc==3);
    nwii::loader::Executable exe;exe.entry_point=Entry;
    auto entry=be({0x38800000u,0x60848000u,(31u<<26)|(4u<<21)|(146u<<1),
                   0x38a50001u,0x44000002u,0x4e800020u});
    exe.sections.push_back({Entry,uint32_t(entry.size()),entry,true,false});
    exe.sections.push_back({Vector,uint32_t(bytes.size()),{bytes.begin(),bytes.end()},true,false});
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({Vector});
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=argv[1];cfg.split_output=std::string(argv[2])=="split";
    cfg.native_low_mem_entries.insert(Vector);
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    assert(!recomp.generate_cpp(Entry).empty());
    std::ifstream f(std::string(argv[1])+(cfg.split_output?"/main_output.cpp":"/output.cpp"));
    const std::string output((std::istreambuf_iterator<char>(f)),{});
    assert(output.find("case 0x8000400C: func_80004000(ctx); break;")!=std::string::npos);
    std::cout<<"PASS: original-free native low-vector IRQ round-trip generation\n";
}
