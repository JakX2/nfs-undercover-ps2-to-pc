#pragma once
#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <limits>
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

// Exact stack-relative identity, not a sampled arbitrary operand. The caller must
// have independently authenticated parent_sp as its still-live frame base.
// Accept only a non-record OR of an identical register into a volatile GPR.
inline std::optional<CallerIntegerEffect> predict_caller_stack_move(
    uint32_t w,const std::array<uint32_t,32>& gp,uint32_t cr,uint32_t parent_sp,int32_t offset=0){
    const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
    if(op!=31u||xo!=444u||(w&1u)||rs!=rb||ra==rs||
       !(ra==0u||(ra>=3u&&ra<=12u))||gp[1]!=parent_sp||
       parent_sp<0x80000000u||parent_sp>0x81800000u-704u||(parent_sp&7u)||
       offset<=-0x01800000||offset>=0x01800000)return {};
    const int64_t address=int64_t(parent_sp)+int64_t(offset);
    if(address<0x80000000ll||address>=0x81800000ll||gp[rs]!=uint32_t(address))return {};
    // Copy only. Being inside MEM1 does not authorize reading or writing it.
    return CallerIntegerEffect{ra,uint32_t(address),cr};
}
// Generic tagged stack operand. This predicts only register arithmetic,
// never guest memory access. Both input and result must resolve inside
// MEM1 without 32-bit wrap; the private symbolic plan supplies the offset.
inline std::optional<CallerIntegerEffect> predict_caller_stack_relative(
    uint32_t w,const std::array<uint32_t,32>& gp,uint32_t cr,
    uint32_t parent_sp,unsigned declared_src,int32_t offset){
    constexpr int64_t limit=0x01800000ll;
    if(declared_src>=32u||gp[1]!=parent_sp||parent_sp<0x80000000u||
       parent_sp>0x81800000u-704u||(parent_sp&7u)||offset<=-limit||offset>=limit)return {};
    const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
    unsigned src=0,dst=0;int64_t add=0;
    if((op==14u||op==15u)&&ra){
        src=ra;dst=rs;
        add=(int64_t(w&0xffffu)^0x8000ll)-0x8000ll;
        if(op==15u)add*=65536ll;
    }else if(op==31u&&xo==444u&&!(w&1u)&&rs==rb){
        src=rs;dst=ra;
    }else return {};
    if(src!=declared_src||!(dst==0u||(dst>=3u&&dst<=12u)))return {};
    const int64_t result_offset=int64_t(offset)+add;
    const int64_t input=int64_t(parent_sp)+offset,output=int64_t(parent_sp)+result_offset;
    if(result_offset<=-limit||result_offset>=limit||
       input<0x80000000ll||input>=0x81800000ll||
       output<0x80000000ll||output>=0x81800000ll||
       gp[src]!=uint32_t(input))return {};
    return CallerIntegerEffect{dst,uint32_t(output),cr};
}


// Read-only immediate-compare witness for a local translated instruction.
// The caller supplies the independently authenticated instruction, constant
// operand and next boundary. This does not execute or advance the guest.
class CallerImmediateCompareWitness {
public:
    unsigned stage() const { return stage_; }
    bool failed() const { return failed_; }

    template<class C>
    bool arm(C& c,uint32_t root,uint32_t label,uint32_t instruction,
             uint32_t next_word,CallerIntegerInput input) {
        const unsigned op=instruction>>26u;
        if(stage_||failed_||!safe(c)||c.pc!=root||root>label||
           (root&3u)||(label&3u)||label>0x817ffff8u||
           root<0x80000000u||!(op==10u||op==11u)||
           !word(c,label,instruction)||!word(c,label+4u,next_word)||
           c.inst_count==std::numeric_limits<uint64_t>::max())
            return reject();
        const std::array<CallerIntegerInput,1> operands{{input}};
        const auto expected=predict_caller_integer(instruction,c.gpr,pack(c),c.xer,operands);
        if(!expected||expected->reg)return reject();
        cpu_=&c;root_=root;label_=label;instruction_=instruction;next_word_=next_word;
        gpr_=c.gpr;gqr_=c.gqr;cr_=expected->cr;xer_=c.xer;
        lr_=c.lr;ctr_=c.ctr;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;
        count_=c.inst_count;stage_=1u;
        return true;
    }

    template<class C>
    bool observe(C& c,uint32_t label,uint32_t instruction) {
        if(stage_!=1u||failed_||cpu_!=&c||!safe(c)||c.pc!=root_||
           label!=label_+4u||instruction!=next_word_||
           c.inst_count!=count_+1u||c.gpr!=gpr_||c.gqr!=gqr_||
           pack(c)!=cr_||c.xer!=xer_||c.lr!=lr_||c.ctr!=ctr_||
           c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_||
           !word(c,label_,instruction_)||!word(c,label,next_word_))
            return reject();
        stage_=2u;
        return true;
    }

private:
    bool reject(){failed_=true;return false;}
    template<class C> static bool safe(C& c){
        return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;
    }
    template<class C> static uint32_t pack(C& c){
        uint32_t out=0;
        for(const auto& f:c.cr)
            out=(out<<4u)|(unsigned(f.lt)<<3u)|(unsigned(f.gt)<<2u)|
                (unsigned(f.eq)<<1u)|unsigned(f.so);
        return out;
    }
    template<class C> static bool word(C& c,uint32_t a,uint32_t expected){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto* first=c.mmu.get_ptr(a);
        auto* last=c.mmu.get_ptr(a+3u);
        return first&&last&&reinterpret_cast<uintptr_t>(last)==
            reinterpret_cast<uintptr_t>(first)+3u&&c.mmu.read32(a)==expected;
    }
    const void* cpu_=nullptr;
    std::array<uint32_t,32> gpr_{};
    std::array<uint32_t,8> gqr_{};
    uint32_t root_=0,label_=0,instruction_=0,next_word_=0,cr_=0,xer_=0;
    uint32_t lr_=0,ctr_=0,msr_=0,srr0_=0,srr1_=0;
    uint64_t count_=0;
    unsigned stage_=0;
    bool failed_=false;
};

}
