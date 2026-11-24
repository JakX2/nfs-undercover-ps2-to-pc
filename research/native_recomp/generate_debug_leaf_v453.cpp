// Generate the authenticated leaf without embedding owner instructions.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <filesystem>
#include <stdexcept>
#include <string>
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
    if(fn.instructions.empty()||fn.instructions.size()>32||fn.start_address!=exe.entry_point||
       fn.instructions.back().opcode!=0x4e800020u)throw std::runtime_error("body");
    for(size_t i=0;i+1<fn.instructions.size();++i)
        if(fn.instructions[i].opcode!=0x60000000u)throw std::runtime_error("not leaf");
    nwii::recomp::RecompilerConfig cfg;cfg.output_dir=dir.string();cfg.split_output=mode=="split";
    nwii::recomp::Recompiler recomp(analyzer,nullptr,cfg);
    if(recomp.generate_cpp(exe.entry_point).empty())throw std::runtime_error("generation");
}
