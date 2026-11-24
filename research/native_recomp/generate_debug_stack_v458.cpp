// Generate the authenticated stack-only routine without embedding owner instructions.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <stdexcept>
#include <string>
#include <vector>
int main(int argc,char** argv){
    if(argc!=4)throw std::runtime_error("DOL output mode");
    const std::filesystem::path dir=argv[2];const std::string mode=argv[3];
    if(!std::filesystem::is_directory(dir)||!std::filesystem::is_empty(dir)||(mode!="split"&&mode!="nonsplit"))
        throw std::runtime_error("output");
    nwii::loader::Executable exe;
    if(!exe.load_dol(argv[1])||exe.entry_point!=0x804e50b8u)throw std::runtime_error("entry");
    nwii::analyzer::Analyzer analyzer(exe);analyzer.analyze({});
    const auto& fs=analyzer.get_functions();
    if(fs.size()!=1||!fs.count(exe.entry_point))throw std::runtime_error("root");
    const auto& fn=fs.at(exe.entry_point);
    if(exe.sections.size()!=1||fn.instructions.empty()||fn.instructions.size()>64||fn.start_address!=exe.entry_point)
        throw std::runtime_error("body");
    const auto& data=exe.sections[0].data;
    if(data.size()!=4*fn.instructions.size())throw std::runtime_error("extent");
    std::vector<bool> seen(data.size()/4,false);
    for(const auto& inst:fn.instructions){
        if(inst.address<exe.entry_point||(inst.address-exe.entry_point)%4)throw std::runtime_error("geometry");
        const size_t at=inst.address-exe.entry_point;
        if(at+4>data.size()||seen[at/4])throw std::runtime_error("coverage");
        uint32_t word=0;for(unsigned n=0;n<4;++n)word=(word<<8)|data[at+n];
        if(word!=inst.opcode)throw std::runtime_error("original instruction mismatch");
        seen[at/4]=true;
    }
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("generation");
}
