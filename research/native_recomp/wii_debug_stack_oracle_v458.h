#pragma once
// Independent bounded verification oracle, not used by the game runtime.
#include <array>
#include <bit>
#include <cstdint>
#include <stdexcept>
#include <vector>
namespace undercover::wii {
struct DebugStackState {
    std::array<uint32_t,32> gpr{};
    std::array<double,32> fpr{};
    std::array<bool,32> cr{};
    std::array<uint8_t,512> stack{};
    uint32_t base=0;
    uint64_t ticks=0;
};
inline int32_t sign16(uint32_t w){return int32_t(w&0x7fffu)-int32_t(w&0x8000u);}
inline int32_t sign26(uint32_t w){return int32_t(w&0x01fffffcu)-int32_t(w&0x02000000u);}
inline DebugStackState reference_debug_stack(const std::vector<uint32_t>& words,DebugStackState s){
    auto require=[](bool b){if(!b)throw std::runtime_error("unsupported bounded debug oracle operation");};
    require(!words.empty()&&words.size()<=64&&words.back()==0x4e800020u);
    const uint32_t original_sp=s.gpr[1];
    require(uint64_t(s.base)+256u==original_sp);
    auto store=[&](uint32_t address,uint64_t value,unsigned n){
        require(address>=s.base&&uint64_t(address)+n<=uint64_t(s.base)+s.stack.size()&&address%n==0);
        for(unsigned j=0;j<n;++j)s.stack[address-s.base+j]=uint8_t(value>>(8u*(n-j-1u)));
    };
    size_t pc=0;
    while(pc<words.size()&&s.ticks<64){
        const uint32_t w=words[pc];const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u;
        const int32_t imm=sign16(w);++s.ticks;
        if(w==0x4e800020u){require(pc+1==words.size()&&s.gpr[1]==original_sp);return s;}
        if(w==0x60000000u){++pc;continue;}
        if(op==14){
            require(rs==1&&ra==1&&imm>=-256&&imm<=256&&imm%4==0);
            s.gpr[1]+=uint32_t(imm);
        }else if(op==36||op==37||op==54){
            require(ra==1&&imm>=-256&&imm<=256&&(op!=37||rs==1));
            const uint32_t ea=s.gpr[1]+uint32_t(imm);
            if(op==54)store(ea,std::bit_cast<uint64_t>(s.fpr[rs]),8);
            else store(ea,s.gpr[rs],4);
            if(op==37)s.gpr[1]=ea;
        }else if(op==16||op==18){
            require((w&3u)==0);
            const int32_t disp=op==16?sign16(w&0xfffcu):sign26(w);
            require(disp>0&&pc+size_t(disp/4)<words.size());
            bool take=true;
            if(op==16){
                const unsigned bo=rs,bi=ra;require((bo&4u)!=0);
                take=(bo&16u)||s.cr[bi]==bool(bo&8u);
            }
            pc+=take?size_t(disp/4):1u;continue;
        }else require(false);
        ++pc;
    }
    throw std::runtime_error("bounded debug oracle did not return");
}
}
