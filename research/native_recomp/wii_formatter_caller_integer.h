#pragma once
#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <span>

namespace undercover::wii {
// Constant operands come from the private symbolic contract, not from
// unrestricted observation of unknown live guest registers.
struct CallerIntegerInput {unsigned reg;uint32_t value;};
struct CallerIntegerEffect {
    std::optional<unsigned> reg;
    uint32_t value=0,cr=0;
};
inline std::optional<CallerIntegerEffect> predict_caller_integer(
    uint32_t w,const std::array<uint32_t,32>& gp,uint32_t cr,uint32_t xer,
    std::span<const CallerIntegerInput> inputs,uint32_t saved_mask=0u){
    if(inputs.size()>3u||(saved_mask&0x3fffu))return {};
    uint32_t declared=0,used=0;
    for(auto x:inputs){
        if(x.reg>=32u||(declared&(uint32_t(1)<<x.reg))||gp[x.reg]!=x.value)return {};
        declared|=uint32_t(1)<<x.reg;
    }
    const auto read=[&](unsigned r){used|=uint32_t(1)<<r;return gp[r];};
    const auto writable=[&](unsigned r){return r==0u||(r>=3u&&r<=12u)||
        (r>=14u&&(saved_mask&(uint32_t(1)<<r)));};
    CallerIntegerEffect out;out.cr=cr;
    const auto compare=[&](unsigned f,bool lt,bool eq){
        const unsigned sh=28u-4u*f;
        out.cr=(out.cr&~(15u<<sh))|(((lt?8u:eq?2u:4u)|((xer>>31)&1u))<<sh);
    };
    const auto write=[&](unsigned r,uint32_t v,bool record){
        out.reg=r;out.value=v;
        if(record)compare(0u,(v&0x80000000u)!=0u,v==0u);
    };
    const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
    const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
    if(op==14u||op==15u){
        const uint32_t a=ra?read(ra):0u;
        write(rs,a+(op==15u?imm<<16u:imm),false);
    }else if(op==10u||op==11u){
        if(w&0x00600000u)return {}; // reserved bit and unsupported 64-bit L
        const uint32_t a=read(ra),b=op==10u?w&0xffffu:imm;
        compare((w>>23)&7u,op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
    }else if(op==31u&&(xo==0u||xo==32u)){
        if(w&0x00600001u)return {};
        const uint32_t a=read(ra),b=read(rb);
        compare((w>>23)&7u,xo==32u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
    }else if(op>=24u&&op<=29u){
        const uint32_t a=read(rs),n=(w&0xffffu)<<((op&1u)?16u:0u);
        write(ra,op<26u?a|n:op<28u?a^n:a&n,op>=28u);
    }else if(op==20u||op==21u||op==23u){
        const unsigned sh=op==23u?read(rb)&31u:rb,mb=(w>>6)&31u,me=(w>>1)&31u;
        uint32_t m=0;
        for(unsigned i=0;i<32u;++i)if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))m|=1u<<(31u-i);
        const uint32_t v=std::rotl(read(rs),int(sh))&m;
        write(ra,op==20u?(read(ra)&~m)|v:v,bool(w&1u));
    }else if(op==31u&&(xo==444u||xo==28u||xo==316u)){
        const uint32_t a=read(rs),b=read(rb);
        write(ra,xo==444u?a|b:xo==28u?a&b:a^b,bool(w&1u));
    }else if(op==31u&&(xo==922u||xo==954u)){
        if(rb)return {};
        const uint32_t m=xo==922u?0xffffu:0xffu,t=xo==922u?0x8000u:0x80u;
        write(ra,((read(rs)&m)^t)-t,bool(w&1u));
    }else if(op==31u&&(xo==266u||xo==40u)){
        const uint32_t a=read(ra),b=read(rb);
        write(rs,xo==266u?a+b:b-a,bool(w&1u));
    }else return {};
    if(used!=declared||(out.reg&&!writable(*out.reg)))return {};
    return out;
}
}
