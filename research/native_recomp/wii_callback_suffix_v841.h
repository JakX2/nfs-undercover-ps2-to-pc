#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace undercover::wii {
struct CallbackSuffixWord{uint32_t pc,word;};
struct CallbackSuffixEdge{uint32_t site,target;unsigned ordinal;};
struct CallbackSuffixExpectation{
    uint32_t root,end,resume;
    std::span<const CallbackSuffixWord> words;
    std::array<CallbackSuffixEdge,2> edges;
};
// Read-only witness for the post-setter callback's indirect or restore boundary.
// All exact code identity is supplied privately by the installer.
// It verifies the executed store bytes at the following genuine label.
class CallbackSuffixWitness{
public:
    explicit CallbackSuffixWitness(CallbackSuffixExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned writes()const{return writes_;}
    unsigned ordinal()const{return ordinal_;}
    unsigned target_class()const{return target_class_;}
    unsigned polls()const{return polls_;}
    template<class C>bool poll(C& c,bool device){
        if(stage_!=1u||error_||ctx_!=&c||!device||!backward_||c.inst_count!=last_||++polls_>128u)return fail(2);
        backward_=false;return true;
    }
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,bool setter_return,bool device){
        if(stage_||error_||!setter_return||!device||!safe(c)||pc!=e_.resume||c.pc!=pc||c.lr!=pc||
           e_.root<0x80000000u||e_.end>0x81800000u||e_.root>=e_.end||e_.end-e_.root>4096u||
           ((e_.root|e_.end|e_.resume)&3u)||e_.words.empty()||e_.words.size()>64u||
           !find(pc)||find(pc)->word!=w||c.inst_count>UINT64_MAX-128u||
           c.gpr[1]<0x80000400u||c.gpr[1]>0x817fff00u||(c.gpr[1]&3u))return fail(1);
        uint32_t previous=0;
        for(auto row:e_.words){
            if(row.pc<=previous||row.pc<e_.root||row.pc>=e_.end||!match(c,row.pc,row.word))return fail(1);
            previous=row.pc;
        }
        unsigned mask=0;
        for(auto edge:e_.edges){
            const auto* row=find(edge.site);
            if(!row||(edge.ordinal!=4u&&edge.ordinal!=13u)||(mask&(1u<<edge.ordinal)))return fail(1);
            if(edge.ordinal==4u){
                if(row->word!=0x4e800421u||edge.target)return fail(1);
            }else if(row->word>>26!=18u||(row->word&3u)!=1u||target(edge.site,row->word)!=edge.target||
                     edge.target<0x80000000u||edge.target>0x817ffffcu||(edge.target&3u)||
                     (edge.target>=e_.root&&edge.target<e_.end))return fail(1);
            mask|=1u<<edge.ordinal;
        }
        if(mask!=((1u<<4)|(1u<<13)))return fail(1);
        ctx_=&c;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;
        next_=pc;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool device){
        if(stage_!=1||error_||backward_||!device||ctx_!=&c||!safe(c)||c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_||
           c.gpr[1]!=sp_||c.gpr[2]!=r2_||c.gpr[13]!=r13_||pc!=next_||
           c.inst_count-last_!=unsigned(visits_!=0)||++visits_>128u)return fail(2);
        const auto* row=find(pc);if(!row||row->word!=w||!match(c,pc,w))return fail(3);
        if(pending_){
            for(unsigned i=0;i<pending_;++i)
                if(!c.mmu.get_ptr(store_addr_+i)||c.mmu.read8(store_addr_+i)!=bytes_[i])return fail(4);
            pending_=0;
        }
        last_=c.inst_count;backward_=false;
        for(auto e:e_.edges)if(pc==e.site){
            ordinal_=e.ordinal;
            if(e.ordinal==4u){
                const uint32_t a=c.ctr;
                // Classify only; never execute or follow an arbitrary callback.
                target_class_=!a?1u:(a&3u)?2u:
                    (a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u))?3u:4u;
            }
            stage_=2;return true;
        }
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==17u||(op==19u&&(xo==16u||xo==50u||xo==528u))||(op==31u&&xo==146u))return fail(6);
        if(!memory(c,w))return fail(7);
        next_=pc+4u;
        if(op==16u||op==18u){
            if(w&3u)return fail(6);
            const auto dst=target(pc,w);
            if(!find(dst))return fail(6);
            // The pinned emitter polls before evaluating a local backward branch.
            // This includes its final, not-taken iteration; next_ remains conditional.
            backward_=dst<=pc;
            if(op==18u||taken(c,w))next_=dst;
        }
        return find(next_)?true:fail(6);
    }
private:
    CallbackSuffixExpectation e_;const void* ctx_=nullptr;
    unsigned stage_=0,error_=0,visits_=0,writes_=0,ordinal_=0,target_class_=0,polls_=0,pending_=0;
    bool backward_=false;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,srr0_=0,srr1_=0,next_=0,store_addr_=0;
    uint64_t last_=0;
    std::array<uint8_t,128> bytes_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    const CallbackSuffixWord* find(uint32_t pc)const{
        for(const auto& row:e_.words)if(row.pc==pc)return &row;
        return nullptr;
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>static bool match(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool short_branch=w>>26==16u;const uint32_t b=short_branch?0xfffcu:0x03fffffcu,s=short_branch?0x8000u:0x02000000u;
        return pc+(((w&b)^s)-s);
    }
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));
    }
    static bool within(uint32_t addr,unsigned n,uint32_t lo,uint32_t hi){
        return n&&addr>=lo&&uint64_t(addr)+n<=hi;
    }
    template<class C>bool memory(C& c,uint32_t w){
        const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u,rs=(w>>21)&31u;
        const uint32_t base=ra?c.gpr[ra]:0u;
        unsigned n=0;uint32_t a=0;bool write=false,reversed=false,multiple=false;
        if(op>=32u&&op<=47u){
            a=base+((w&0xffffu)^0x8000u)-0x8000u;
            n=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
            multiple=op==46u||op==47u;
            if(multiple)n=4u*(32u-rs);
            write=op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u;
            if(op==37u||op==39u||op==45u)return false; // no update of stack/base in this frontier
        }else if(op==31u){
            a=base+c.gpr[rb];
            switch(xo){
            case 23:case 55:case 534:n=4;break;
            case 87:case 119:n=1;break;
            case 279:case 311:case 343:case 375:case 790:n=2;break;
            case 151:n=4;write=true;break;
            case 215:n=1;write=true;break;
            case 407:n=2;write=true;break;
            case 662:n=4;write=true;reversed=true;break;
            case 918:n=2;write=true;reversed=true;break;
            case 183:case 247:case 439:case 20:case 150:case 533:case 597:case 661:case 725:
            case 535:case 567:case 599:case 631:case 663:case 695:case 727:case 759:case 983:
            case 54:case 86:case 246:case 278:case 470:case 982:case 1014:return false;
            default:break;
            }
        }else if(op>=48u||op==4u)return false;
        if(!n)return true;
        if(!within(a,n,0x80000000u,0x81800000u)||(n>1u&&(a&(n==2u?1u:3u))))return false;
        for(unsigned i=0;i<n;++i)if(!c.mmu.get_ptr(a+i))return false;
        if(!write)return true;
        if(++writes_>8u||n>bytes_.size()||
           !(within(a,n,sp_-0x400u,sp_+0x100u)||within(a,n,0x80619a60u,0x80619b60u)||
             within(a,n,0x806fe340u,0x806fe540u)||within(a,n,0x8070d000u,0x8070e900u))||
           (uint64_t(a)<e_.end&&e_.root<uint64_t(a)+n))return false;
        store_addr_=a;pending_=n;
        for(unsigned i=0;i<n;++i){
            const unsigned reg=rs+(multiple?i/4u:0u);
            const unsigned shift=multiple?8u*(3u-i%4u):8u*(reversed?i:n-1u-i);
            bytes_[i]=uint8_t(c.gpr[reg]>>shift);
        }
        return true;
    }
};
}
