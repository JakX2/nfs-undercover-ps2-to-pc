#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
struct IpcEntryJoinExpectation {uint32_t call,root,branch,entry;};
// Read-only direct BL witness. The established IPC client witness separately
// checks the complete cold heap/mailbox/table prerequisites.
class IpcEntryJoinWitness {
public:
    explicit IpcEntryJoinWitness(IpcEntryJoinExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,bool leaf_verified,bool held){
        if(stage_||error_||!leaf_verified||!held||!safe(c)||pc!=e_.call||
           c.pc!=pc||c.lr!=pc||c.gpr[3]||w!=e_.branch||w>>26!=18u||(w&3u)!=1u||
           pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u)!=e_.root||
           !word(c,pc,w)||!word(c,e_.root,e_.entry))return fail(1);
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;cr_=pack(c);ctr_=c.ctr;xer_=c.xer;
        msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||error_||!held||cpu_!=&c||!safe(c)||pc!=e_.root||
           c.pc!=pc||c.lr!=e_.call+4u||c.inst_count!=tick_||!word(c,pc,e_.entry)||
           c.gpr!=gp_||c.gqr!=gqr_||pack(c)!=cr_||c.ctr!=ctr_||c.xer!=xer_||
           c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_)return fail(2);
        stage_=2;return true;
    }
private:
    IpcEntryJoinExpectation e_;const void* cpu_=nullptr;unsigned stage_=0,error_=0;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    uint32_t cr_=0,ctr_=0,xer_=0,msr_=0,srr0_=0,srr1_=0;uint64_t tick_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&(c.msr&0x8000u);}
    template<class C>static uint32_t pack(C& c){
        uint32_t r=0;for(auto f:c.cr)r=(r<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return r;
    }
    template<class C>static bool word(C& c,uint32_t pc,uint32_t w){
        return !(pc&3u)&&pc>=0x80000000u&&pc<=0x817ffffcu&&c.mmu.get_ptr(pc)&&c.mmu.get_ptr(pc+3u)&&c.mmu.read32(pc)==w;
    }
};
}
