#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace undercover::wii {
struct HandlerSuffixLabel{uint32_t pc,word;unsigned ordinal,kind;};
class HandlerSuffixGuard{
public:
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned writes()const{return writes_;}
    template<class C>bool start(C& c,std::span<const HandlerSuffixLabel> rows,uint32_t resume,unsigned label_limit=64u,bool strict=false){
        if(ctx_||error_||rows.empty()||(label_limit!=64u&&label_limit!=256u)||rows.size()>label_limit||c.pc!=resume||
           c.gpr[1]<0x80000400u||c.gpr[1]>0x817fff00u||(c.gpr[1]&3u))return fail(1);
        rows_=rows;uint32_t previous=0;
        for(const auto& x:rows){
            if(x.pc<=previous||!mapped(c,x.pc,4u)||c.mmu.read32(x.pc)!=x.word||
               (x.ordinal==0)!=(x.kind==0)||x.kind>2u||x.ordinal>12u)return fail(1);
            previous=x.pc;
        }
        if(!find(resume))return fail(1);
        if(strict){if constexpr(!requires{c.ctr;c.cr[0].lt;c.cr[0].gt;c.cr[0].eq;c.cr[0].so;})return fail(1);}
        ctx_=&c;sp_=c.gpr[1];last_=c.inst_count;strict_=strict;next_=resume;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind,bool status_read=false,bool status_write=false){
        if(error_||ctx_!=&c||(strict_&&(terminal_||pc!=next_||c.gpr[1]!=sp_))||c.inst_count-last_!=unsigned(visits_!=0)||++visits_>128u)return fail(2);
        const auto* x=find(pc);
        if(!x||x->word!=w||x->ordinal!=ordinal||x->kind!=kind||!mapped(c,pc,4)||c.mmu.read32(pc)!=w)return fail(3);
        if(pending_){
            for(unsigned i=0;i<pending_;++i)if(!c.mmu.get_ptr(addr_+i)||c.mmu.read8(addr_+i)!=expected_[i])return fail(4);
            pending_=0;
        }
        last_=c.inst_count;
        if((status_read&&(kind||w>>26!=32u))||(status_write&&(kind||w>>26!=36u||status_read)))return fail(5);
        if(strict_){
            if(kind||w==0x4e800020u){terminal_=true;return true;}
            const unsigned op=w>>26,xo=(w>>1)&1023u;
            if(op==17u||(op==19u&&(xo==16u||xo==50u||xo==528u))||(op==31u&&xo==146u))return fail(6);
            next_=pc+4u;
            if(op==16u||op==18u){
                if(w&3u)return fail(6);
                const uint32_t mask=op==16u?0xfffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
                const uint32_t dest=pc+(((w&mask)^sign)-sign);
                if(!find(dest))return fail(6);
                if(op==18u||taken(c,w))next_=dest;
            }
            if(!find(next_))return fail(6);
        }
        return kind||w==0x4e800020u||memory(c,w,status_read,status_write)?true:fail(5);
    }
private:
    std::span<const HandlerSuffixLabel> rows_{};
    const void* ctx_=nullptr;uint64_t last_=0;
    uint32_t sp_=0,addr_=0,next_=0;bool strict_=false,terminal_=false;unsigned pending_=0,error_=0,visits_=0,writes_=0;
    std::array<uint8_t,128> expected_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    const HandlerSuffixLabel* find(uint32_t pc)const{for(const auto& x:rows_)if(x.pc==pc)return &x;return nullptr;}
    template<class C>static bool taken(C& c,uint32_t w){
        if constexpr(requires{c.ctr;c.cr[0].lt;c.cr[0].gt;c.cr[0].eq;c.cr[0].so;}){
            const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
            const bool bit=bi%4u==0?f.lt:bi%4u==1?f.gt:bi%4u==2?f.eq:f.so;
            return ((bo&4u)||(((uint32_t(c.ctr)-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
        }else return false;
    }
    static bool within(uint32_t a,unsigned n,uint32_t lo,uint32_t hi){return n&&a>=lo&&uint64_t(a)+n<=hi;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!within(a,n,0x80000000u,0x81800000u)||(n>1u&&(a&(n==2u?1u:3u))))return false;
        for(unsigned i=0;i<n;++i)if(!c.mmu.get_ptr(a+i))return false;
        return true;
    }
    template<class C>bool memory(C& c,uint32_t w,bool status_read,bool status_write){
        const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u,rs=(w>>21)&31u;
        const uint32_t base=ra?c.gpr[ra]:0u;
        uint32_t a=0;unsigned n=0;bool wr=false,multi=false,reverse=false;
        if(op>=32u&&op<=47u){
            a=base+((w&0xffffu)^0x8000u)-0x8000u;
            n=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
            multi=op==46u||op==47u;if(multi)n=4u*(32u-rs);
            wr=op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u;
        }else if(op==31u){
            a=base+c.gpr[rb];
            switch(xo){
            case 23:case 55:case 534:n=4;break;
            case 87:case 119:n=1;break;
            case 279:case 311:case 343:case 375:case 790:n=2;break;
            case 151:case 183:n=4;wr=true;break;
            case 215:case 247:n=1;wr=true;break;
            case 407:case 439:n=2;wr=true;break;
            case 662:n=4;wr=true;reverse=true;break;
            case 918:n=2;wr=true;reverse=true;break;
            case 20:case 150:case 533:case 597:case 661:case 725:
            case 535:case 567:case 599:case 631:case 663:case 695:case 727:case 759:case 983:
            case 54:case 86:case 246:case 278:case 470:case 982:case 1014:return false;
            default:break;
            }
        }else if(op>=48u||op==4u)return false;
        if(status_read||status_write)return wr==status_write&&n==4u&&op==(status_write?36u:32u)&&!(a&3u)&&(a&0xc0000000u)!=0x40000000u&&((a&0x3fffffffu)&~0x00800000u)==0x0d006438u;
        if(!n)return true;
        if(!mapped(c,a,n))return false;
        if(!wr)return true;
        if(++writes_>8u||n>expected_.size()||
           !(within(a,n,sp_-0x400u,sp_+0x100u)||within(a,n,0x80619a60u,0x80619b60u)||
             within(a,n,0x806fe340u,0x806fe540u)||within(a,n,0x8070d000u,0x8070e900u)))return false;
        for(const auto& x:rows_)if(uint64_t(a)<uint64_t(x.pc)+4u&&x.pc<uint64_t(a)+n)return false;
        addr_=a;pending_=n;
        for(unsigned i=0;i<n;++i){
            const unsigned reg=rs+(multi?i/4u:0u);
            const unsigned shift=multi?8u*(3u-i%4u):8u*(reverse?i:n-1u-i);
            expected_[i]=uint8_t(c.gpr[reg]>>shift);
        }
        return true;
    }
};
}
