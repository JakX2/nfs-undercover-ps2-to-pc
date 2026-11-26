#pragma once
#include "wii_ioctl_submit_prefix_v1403.h"
namespace undercover::wii {
struct IoctlSubmitQueueExpectation {
    uint32_t submit;
    VectorEdge disable,queue;
    std::span<const ReplyNativeWord> words;
};
// Stop at the original queue entry after a nested OSDisableInterrupts.
// The outer STM caller already has EE masked. Do not execute queue logic,
// widen the RAM fence, or authorize any MMIO or IOS service here.
class IoctlSubmitQueueWitness {
public:
    explicit IoctlSubmitQueueWitness(IoctlSubmitQueueExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned stores()const{return fence_.stores();}
    unsigned polls()const{return polls_;}
    unsigned ordinal()const{return ordinal_;}
    template<class C>bool begin(C& c,bool held,uint32_t request,uint32_t size,uint32_t caller_sp){
        const auto sp=c.gpr[1];
        if(stage_||error_||!held||!safe(c)||!e_.submit||e_.disable.lr<4u||
           c.pc!=e_.disable.lr-4u||c.lr!=c.pc||c.pc<e_.submit||
           e_.queue.lr<=e_.disable.lr||e_.queue.lr-c.pc>512u||
           (request&31u)||size<64u||size>4096u||sp<0x80000200u||
           caller_sp>0x817fff70u||caller_sp<=sp||caller_sp-sp>512u||
           (sp&7u)||(caller_sp&7u)||!known(c,e_.submit,c.pc)||
           !known(c,e_.disable.pc,e_.disable.pc)||!edge(c,e_.disable)||!edge(c,e_.queue)||
           !fence_.begin(c,{sp,caller_sp-sp+8u},{request,size}))return fail(1);
        gp_=c.gpr;msr_=c.msr;req_=request;size_=size;
        for(unsigned i=0;i<size;++i)shadow_.push_back(c.mmu.read8(request+i));
        cpu_=&c;active_=e_.submit;next_=c.pc;last_=start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||due_||pc!=next_||c.inst_count-last_!=1u||
           !known(c,active_,pc)||c.mmu.read32(pc)!=w||++visits_>256u)return fail(2);
        if(!fence_.before(c,w)||fence_.heap_stores()){ordinal_=(pc-active_)/4u+1u;return fail(3);}
        if(!unchanged(c))return fail(3);
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;polled_=false;poll_pc_=0;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            if(active_!=e_.submit)return fail(4);
            const bool d=!disable_returned_&&pc+4u==e_.disable.lr&&w==e_.disable.branch_word;
            const bool q=disable_returned_&&pc+4u==e_.queue.lr&&w==e_.queue.branch_word;
            if(!d&&!q)return fail(4);
            if(q&&!queue_arg(c))return fail(5);
            next_=d?e_.disable.pc:e_.queue.pc;due_=true;return true;
        }
        if(op==31u&&xo==146u){
            if(active_!=e_.disable.pc||masked_write_||c.gpr[(w>>21)&31u]!=msr_)return fail(4);
            masked_write_=true;poll_pc_=next_;return true;
        }
        if(op==19u&&xo==16u){
            if((w&1u)||active_!=e_.disable.pc)return fail(4);
            if(!taken(c,w))return true;
            if(!masked_write_||c.lr!=e_.disable.lr||c.gpr[3]!=0u||!helper_abi(c))return fail(4);
            disable_returned_=true;active_=e_.submit;next_=e_.disable.lr;return true;
        }
        if(op==17u||(op==19u&&(xo==50u||xo==528u)))return fail(4);
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            const uint32_t dst=target(pc,w);
            if(dst<=pc)poll_pc_=pc;
            if(op==18u||taken(c,w))next_=dst;
            if(!known(c,active_,next_)||
               (active_==e_.submit&&(next_<e_.disable.lr-4u||next_>=e_.queue.lr)))return fail(4);
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!due_||pc!=next_||c.pc!=pc||c.inst_count!=last_||
           !fence_.settled(c)||!unchanged(c))return fail(6);
        const auto x=disable_returned_?e_.queue:e_.disable;
        if(pc!=x.pc||c.lr!=x.lr||!edge(c,x))return fail(6);
        due_=false;
        if(!disable_returned_){active_=pc;helper_=c.gpr;helper_cr_=pack(c)&0x00fff000u;return true;}
        if(!queue_arg(c))return fail(5);
        stage_=2;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||!poll_pc_||polled_||c.pc!=poll_pc_||
           c.inst_count!=last_||!fence_.settled(c)||!unchanged(c)||++polls_>128u)return fail(7);
        polled_=true;return true;
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&base(c,held)&&disable_returned_&&masked_write_&&
           c.pc==e_.queue.pc&&c.lr==e_.queue.lr&&c.inst_count==last_&&
           queue_arg(c)&&fence_.settled(c)&&unchanged(c);
    }
private:
    IoctlSubmitQueueExpectation e_;AllocatorStoreFence fence_;
    std::vector<uint8_t> shadow_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{},helper_{};
    uint32_t msr_=0,req_=0,size_=0,active_=0,next_=0,last_pc_=0,poll_pc_=0,helper_cr_=0;
    uint64_t start_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0,polls_=0,ordinal_=0;
    bool due_=false,masked_write_=false,disable_returned_=false,polled_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool base(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.gpr[1]==gp_[1]&&
               c.gpr[2]==gp_[2]&&c.gpr[13]==gp_[13]&&c.inst_count>=start_&&c.inst_count-start_<=512u;
    }
    template<class C>bool live(C& c,bool held)const{return stage_==1u&&base(c,held);}
    template<class C>bool unchanged(C& c)const{
        for(unsigned i=0;i<size_;++i)if(c.mmu.read8(req_+i)!=shadow_[i])return false;
        return true;
    }
    template<class C>bool queue_arg(C& c)const{
        return OpenCacheRangeTrace::canonical(c.gpr[3])==req_;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool helper_abi(C& c)const{
        if(c.gpr[1]!=helper_[1]||c.gpr[2]!=helper_[2]||(pack(c)&0x00fff000u)!=helper_cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=helper_[i])return false;
        return true;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if(a&3u)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool edge(C& c,VectorEdge e)const{
        return e.lr>=4u&&e.branch_word>>26==18u&&(e.branch_word&3u)==1u&&target(e.lr-4u,e.branch_word)==e.pc&&
            word(c,e.lr-4u,e.branch_word)&&word(c,e.pc,e.entry_word)&&known(c,e_.submit,e.lr-4u);
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
