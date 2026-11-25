#pragma once
#include "wii_handler_suffix_guard_v868.h"
namespace undercover::wii {
// Forward-only original SITransfer continuation; no linked call admitted.
class SiTransferChoice {
public:
    unsigned failure()const{return error_;}
    unsigned memory_failure()const{return mem_.failure();}
    unsigned visits()const{return mem_.visits();}
    unsigned writes()const{return mem_.writes();}
    unsigned boundary()const{return boundary_;}
    template<class C>bool start(C& c,std::span<const HandlerSuffixLabel> rows,uint32_t pc){
        if(cpu_||error_||!safe(c)||!mem_.start(c,rows,pc))return fail(1);
        cpu_=&c;rows_=rows;next_=pc;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];
        msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w){
        if(error_||boundary_||cpu_!=&c||!safe(c)||c.gpr[1]!=sp_||c.gpr[2]!=r2_||
           c.gpr[13]!=r13_||c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_||pc!=next_)return fail(2);
        const auto* row=find(pc);
        if(!row||row->word!=w||!mem_.before(c,pc,w,row->ordinal,row->kind))return fail(3);
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(row->kind){
            if(row->kind!=1||row->ordinal<3||row->ordinal>9||op!=18u||(w&3u)!=1u)return fail(4);
            boundary_=row->ordinal;return true;
        }
        if(op==17u||op==19u||(op==31u&&xo==146u))return fail(4);
        next_=pc+4u;
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            const uint32_t mask=op==16u?0xfffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
            const uint32_t dst=pc+(((w&mask)^sign)-sign);
            if(dst<=pc||!find(dst))return fail(4);
            if(op==18u||taken(c,w))next_=dst;
        }
        return find(next_)?true:fail(4);
    }
private:
    HandlerSuffixGuard mem_;std::span<const HandlerSuffixLabel> rows_{};
    const void* cpu_=nullptr;unsigned error_=0,boundary_=0;
    uint32_t next_=0,sp_=0,r2_=0,r13_=0,msr_=0,srr0_=0,srr1_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    const HandlerSuffixLabel* find(uint32_t pc)const{for(const auto& r:rows_)if(r.pc==pc)return &r;return nullptr;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>static bool taken(C& c,uint32_t w){
        uint32_t cr=0;for(auto f:c.cr)cr=(cr<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((cr>>(31u-bi))&1u)==bool(bo&8u));
    }
};
}
