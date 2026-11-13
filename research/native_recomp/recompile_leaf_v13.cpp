// Original-free private owner-DOL -> NWiiRecomp single-function emission.
// Usage: recompile_leaf_v13 ORIGINAL.DOL START_HEX SIZE_BYTES NAME OUTPUT.cpp
// Rejects untrusted ranges. Output may contain original game-derived code:
// DO NOT COMMIT OUTPUT.cpp or a proprietary original DOL.
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>

static uint32_t parse_u32(const std::string& value, int base) {
    size_t consumed=0;
    const auto num=std::stoull(value,&consumed,base);
    if(consumed!=value.size() || num > std::numeric_limits<uint32_t>::max())
        throw std::invalid_argument("invalid integer");
    return static_cast<uint32_t>(num);
}
static bool valid_symbol(const std::string& name) {
    if(name.empty() || name.size()>80 || (name[0]>='0' && name[0]<='9')) return false;
    for(char c:name)
        if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_')) return false;
    return true;
}
int main(int argc,char** argv) try {
    if(argc!=6){std::cerr<<"Usage: recompile_leaf_v13 DOL START_HEX SIZE_BYTES NAME OUTPUT.cpp\n";return 2;}
    const uint32_t start=parse_u32(argv[2],16), length=parse_u32(argv[3],10);
    const std::string function_name=argv[4];
    if(!valid_symbol(function_name)||length==0||length>4096||((start|length)&3u))
        throw std::invalid_argument("invalid function address, length, or exported symbol");
    nwii::loader::Executable exe;
    if(!exe.load_dol(argv[1])) throw std::runtime_error("DOL failed validation");
    const nwii::loader::Section* section=nullptr;
    for(const auto& candidate:exe.sections){
        const uint64_t lo=candidate.address,hi=lo+candidate.size;
        if(candidate.is_text && start>=lo && uint64_t(start)+length<=hi){
            section=&candidate;break;
        }
    }
    if(!section) throw std::invalid_argument("function range does not fit a DOL text section");
    nwii::analyzer::Function f{};
    f.start_address=start;
    f.end_address=start+length;
    for(uint32_t pos=0;pos<length;pos+=4){
        const size_t at=size_t(start-section->address)+pos;
        const auto& d=section->data;
        const uint32_t opcode=(uint32_t(d[at])<<24)|(uint32_t(d[at+1])<<16)|
                               (uint32_t(d[at+2])<<8)|d[at+3];
        f.instructions.push_back({start+pos,opcode});
    }
    // A deliberately narrow leaf-only extractor: refuse spans missing the
    // PowerPC unconditional return, rather than emitting an incomplete body.
    // The generated fragment can include local branches, but no BL/SC calls.
    if (f.instructions.back().opcode != 0x4e800020u)
        throw std::invalid_argument("audited leaf span must end in blr");
    for(const auto& ins : f.instructions) {
        const uint32_t op=ins.opcode >> 26;
        if(op==17 || (op==18 && (ins.opcode & 1u)) ||
           (op==16 && (ins.opcode & 1u)) ||
           (op==19 && ins.opcode!=0x4e800020u))
            throw std::invalid_argument("unsupported control flow in isolated PPC leaf");
        if(op==16 || op==18) {
            const int32_t displacement = op==16
                ? (static_cast<int32_t>(ins.opcode << 16) >> 16)
                : (static_cast<int32_t>((ins.opcode & 0x03fffffcu) << 6) >> 6);
            const uint32_t target = (ins.opcode & 2u)
                ? static_cast<uint32_t>(displacement)
                : ins.address + static_cast<uint32_t>(displacement);
            if(target < start || uint64_t(target) >= uint64_t(start)+length || (target&3u))
                throw std::invalid_argument("branch target exits isolated PPC leaf");
        }
    }
    nwii::analyzer::Analyzer analyzer(exe);
    nwii::recomp::Recompiler recomp(analyzer);
    auto emitted=recomp.generate_function_cpp(f);
    std::ostringstream oss;
    oss << "#include \"runtime/cpu_context.h\"\n"
        << "using namespace nwii::runtime;\n"
        << emitted << "\nextern \"C\" void " << function_name
        << "(nwii::runtime::CPUContext& ctx) { func_" << std::hex
        << std::uppercase << std::setw(8) << std::setfill('0') << start
        << "(ctx); }\n";
    std::ofstream out(argv[5],std::ios::binary|std::ios::trunc);
    if(!out) throw std::runtime_error("cannot open local output");
    out << oss.str();
    if(!out) throw std::runtime_error("failed writing local output");
    std::cout << "Locally generated " << f.instructions.size() << " original PPC instructions"
              << " for guest PC 0x" << std::hex << start << std::dec << "\n";
    return 0;
} catch(const std::exception& e){std::cerr<<"recompile_leaf_v13: "<<e.what()<<"\n";return 1;}
