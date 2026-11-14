// Generic owner-local PowerPC callgraph extractor, no original game bytes.
// Usage: extractor PRIVATE_DOL OUTDIR START_HEX:SIZE_DEC [START_HEX:SIZE_DEC ...]
// Only emits source to caller-chosen local directory. Do not distribute game-derived output.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include "recompiler/symbols.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
namespace fs=std::filesystem;
using namespace nwii;
struct Span {uint32_t start,length;};
static uint32_t as_u32(const std::string& s, int base) {
    size_t pos=0;
    const auto val=std::stoull(s,&pos,base);
    if(pos!=s.size() || val>std::numeric_limits<uint32_t>::max()) throw std::invalid_argument("invalid number");
    return static_cast<uint32_t>(val);
}
static Span parse(const std::string& s) {
    const auto colon=s.find(':');
    if(colon==std::string::npos || s.find(':',colon+1)!=std::string::npos) throw std::invalid_argument("expected HEXADDR:DECSIZE");
    Span x{as_u32(s.substr(0,colon),16),as_u32(s.substr(colon+1),10)};
    if((x.start&3) || (x.length&3) || x.length<8 || x.length>16384 ||
       uint64_t(x.start)+x.length>UINT32_MAX) throw std::invalid_argument("invalid function alignment/size");
    return x;
}
static uint32_t branch_target(uint32_t opcode,uint32_t pc) {
    // PPC I-form LI is signed 26-bit byte displacement; AA selects absolute.
    uint32_t delta=opcode&0x03FFFFFCu;
    if(delta&0x02000000u) delta|=0xFC000000u;
    return (opcode&2u)?delta:pc+delta;
}
static uint32_t bc_target(uint32_t opcode,uint32_t pc) {
    // PPC B-form BD is signed 16-bit byte displacement.
    const auto delta=static_cast<int16_t>(opcode&0xFFFCu);
    return (opcode&2u)?static_cast<uint32_t>(static_cast<int32_t>(delta)):
        pc+static_cast<uint32_t>(static_cast<int32_t>(delta));
}
static std::string function_name(uint32_t addr) {
    std::ostringstream ss;
    ss<<"func_"<<std::uppercase<<std::hex<<std::setw(8)<<std::setfill('0')<<addr;
    return ss.str();
}
int main(int argc,char** argv) try {
    if(argc<5 || argc>19) throw std::invalid_argument("usage: extractor PRIVATE_DOL OUTDIR ADDR:SIZE ADDR:SIZE...");
    std::map<uint32_t,Span> spans;
    for(int i=3;i<argc;++i) {
        auto x=parse(argv[i]);
        if(!spans.emplace(x.start,x).second) throw std::invalid_argument("duplicate entry");
    }
    if(spans.size()<2) throw std::invalid_argument("requires at least two original functions");
    loader::Executable dol;
    if(!dol.load_dol(argv[1])) throw std::runtime_error("invalid input DOL");
    std::vector<analyzer::Function> funcs;
    std::set<std::pair<uint32_t,uint32_t>> edges;
    for(const auto& [addr,span]:spans) {
        for(const auto& [other,other_span]:spans) {
            if(addr!=other && uint64_t(addr)<uint64_t(other)+other_span.length &&
               uint64_t(other)<uint64_t(addr)+span.length) throw std::invalid_argument("overlapping function selections");
        }
        const loader::Section* section=nullptr;
        for(const auto& s:dol.sections) {
            if(s.is_text && addr>=s.address && uint64_t(addr)+span.length<=uint64_t(s.address)+s.size) {
                section=&s; break;
            }
        }
        if(!section) throw std::invalid_argument("span outside DOL text");
        analyzer::Function f{};
        f.start_address=addr;
        f.end_address=addr+span.length;
        for(uint32_t offset=0;offset<span.length;offset+=4) {
            const size_t at=size_t(addr-section->address)+offset;
            const auto& d=section->data;
            uint32_t word=(uint32_t(d[at])<<24)|(uint32_t(d[at+1])<<16)|
                          (uint32_t(d[at+2])<<8)|uint32_t(d[at+3]);
            f.instructions.push_back({addr+offset,word});
        }
        if(f.instructions.back().opcode!=0x4e800020u) throw std::invalid_argument("span must end with blr");
        for(const auto& ins:f.instructions) {
            const uint32_t op=ins.opcode>>26;
            const bool link=(ins.opcode&1u)!=0;
            if(op==16 && link) throw std::invalid_argument("linked conditional branch not supported");
            if(op==17) throw std::invalid_argument("syscall not allowed in isolated callgraph");
            if(op==19 && ins.opcode!=0x4e800020u) throw std::invalid_argument("indirect branch/control not allowed");
            if(op==16 || op==18) {
                const uint32_t target=op==16?bc_target(ins.opcode,ins.address):branch_target(ins.opcode,ins.address);
                const bool local=target>=addr&&uint64_t(target)<uint64_t(addr)+span.length;
                if(local) {
                    if(op==18 && link) throw std::invalid_argument("linked local branch unsupported");
                } else if(op==18 && link && spans.count(target)) {
                    edges.emplace(addr,target);
                } else {
                    throw std::invalid_argument("external branch without selected function");
                }
            }
        }
        funcs.push_back(std::move(f));
    }
    if(edges.empty()) throw std::invalid_argument("no inter-function BL edges in selection");
    // All validation completes before output files are created.
    const fs::path dest=argv[2];
    if(!fs::is_directory(dest)) throw std::invalid_argument("output directory must exist");
    for(const auto& [addr,span]:spans)
        if(fs::exists(dest/(function_name(addr)+".cpp"))) throw std::invalid_argument("output file exists, refusing overwrite");
    recomp::SymbolTable symbols;
    for(const auto& [addr,span]:spans) symbols.add_symbol(addr,function_name(addr));
    analyzer::Analyzer analyzer(dol);
    recomp::Recompiler recompiler(analyzer,&symbols);
    std::map<uint32_t,std::string> translated;
    for(const auto& f:funcs) {
        std::string cpp="#include \"runtime/cpu_context.h\"\nusing namespace nwii::runtime;\n";
        // Every selected function name declared regardless of definition TU.
        for(const auto& [addr,span]:spans) cpp+="void "+function_name(addr)+"(CPUContext& ctx);\n";
        cpp+=recompiler.generate_function_cpp(f);
        if(cpp.find("UNIMPLEMENTED OPCODE")!=std::string::npos ||
           cpp.find("std::exit(1)")!=std::string::npos)
            throw std::invalid_argument("generated function needs unsupported interpreter/opcode fallback");
        translated.emplace(f.start_address,std::move(cpp));
    }
    for(const auto& [addr,cpp]:translated) {
        std::ofstream out(dest/(function_name(addr)+".cpp"),std::ios::binary);
        if(!out || !(out<<cpp)) throw std::runtime_error("cannot write private generated output");
    }
    std::cout<<"PASS: "<<funcs.size()<<" selected PPC functions, "<<edges.size()<<" verified direct BL edges:";
    for(auto [a,b]:edges) std::cout<<" 0x"<<std::hex<<a<<"->0x"<<b;
    std::cout<<std::dec<<"\n";
} catch (const std::exception& e) { std::cerr<<"callgraph extractor: "<<e.what()<<"\n";return 1; }
