#pragma once
#include "wii_ioctl_flush_tail_v1401.h"
namespace undercover::wii {
struct IoctlSubmitPrefixExpectation{
    VectorEdge submit,queue,flush;
    std::span<const ReplyNativeWord> words;
};
// Original async submit prefix, through the real queue initializer, to
// the request-header cache flush. The caller retains protected wire
// fields, buffers, outside-allocation heap, descriptors and device state.
class IoctlSubmitPrefixWitness{
public:
    explicit IoctlSubmitPrefixWitness(IoctlSubmitPrefixExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return fence_.stores();}
    unsigned request_stores()const{return fence_.heap_stores();}
    unsigned queue_stores()const{return unsigned(bool(queue_mask_&1u))+unsigned(bool(queue_mask_&2u));}
    unsigned store_failure()const{return fence_.failure();}
    unsigned range_failure()const{return fence_.range_failure();}
    unsigned ordinal()const{return ordinal_;}
    unsigned detail()const{return detail_;}
    unsigned queue_path()const{return queue_returned_?1u:queue_skipped_?2u:0u;}
    unsigned queue_class()const{return queue_class_;}
    uint32_t caller_sp()const{return sp0_;}
    template<class C>bool caller_abi(C& c)const{
        if(stage_!=2u||error_||cpu_!=&c||c.gpr[1]!=sp0_||c.lr!=e_.submit.lr||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||c.gpr[3]!=0u||pack(c)!=caller_cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=caller_gp_[i])return false;
        return true;
    }
    template<class C>bool begin(C& c,bool held,uint32_t request,uint32_t size,uint32_t callback=0){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.submit.pc||c.lr!=e_.submit.lr||
           canonical(c.gpr[3])!=request||(request&31u)||size<64u||size>4096u||
           c.gpr[1]<0x80000200u||c.gpr[1]>0x817fff70u||(c.gpr[1]&7u)||
           !known(c,e_.submit.pc,c.pc)||!edge(c,e_.submit)||!edge(c,e_.queue)||!edge(c,e_.flush))return fail(1);
        sp0_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;
        caller_gp_=c.gpr;caller_cr_=pack(c);
        stack_={sp0_-512u,520u};req_={request,size};callback_=callback;
        if(!fence_.begin(c,stack_,req_))return fail(1);
        for(unsigned i=0;i<size;++i)shadow_.push_back(c.mmu.read8(request+i));
        cpu_=&c;active_=next_=c.pc;last_=start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||due_||pc!=next_||c.inst_count-last_!=1u||
           !known(c,active_,pc)||c.mmu.read32(pc)!=w||++visits_>128u)return fail(2);
        if(!fence_.before(c,w)){ordinal_=(pc-active_)/4u+1u;return fail(3);}
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(active_==e_.queue.pc){
            if(w==0x4e800020u){
                if(c.lr!=e_.queue.lr||queue_mask_!=3u||!queue_zero(c))return fail(4);
                active_=e_.submit.pc;next_=e_.queue.lr;queue_returned_=true;return true;
            }
            if(op==36u){
                const unsigned rs=(w>>21)&31u,ra=(w>>16)&31u;
                const int64_t ea=int64_t(ra?c.gpr[ra]:0u)+int32_t((w&0xffffu)^0x8000u)-0x8000;
                if(c.gpr[rs]||ea<queue_||ea>int64_t(queue_)+4||((ea-queue_)&3))return fail(4);
                const unsigned bit=1u<<unsigned((ea-queue_)/4);
                if(queue_mask_&bit)return fail(4);
                queue_mask_|=bit;return true;
            }
            if(op==14u)return true;
            return fail(4);
        }
        if(op==18u&&(w&1u)){
            if(!queue_returned_&&!queue_skipped_&&pc+4u==e_.queue.lr&&w==e_.queue.branch_word){
                queue_=c.gpr[3];
                queue_class_=req_.contains(queue_,8u)?1u:stack_.contains(queue_,8u)?2u:
                    req_.contains(canonical(queue_),8u)?3u:queue_==0u?4u:5u;
                if((queue_&3u)||(!req_.contains(queue_,8u)&&!stack_.contains(queue_,8u)))return bad(pc,1);
                next_=e_.queue.pc;due_=true;return true;
            }
            if(pc+4u==e_.flush.lr&&w==e_.flush.branch_word){
                if(!queue_path())return bad(pc,2);
                if(!flush_args(c))return bad(pc,3);
                if(!finished(c))return bad(pc,4);
                next_=e_.flush.pc;due_=true;return true;
            }
            return bad(pc,5);
        }
        if(op==17u||(op==19u&&(xo==16u||xo==50u||xo==528u))||(op==31u&&xo==146u))return fail(6);
        if(op==16u||op==18u){
            if(w&3u)return fail(6);
            const auto dst=target(pc,w);
            if(dst<=pc)return fail(6);
            if(op==18u||taken(c,w))next_=dst;
            if(!known(c,active_,next_))return fail(6);
            // Only a taken, exact original forward edge crossing the
            // initializer call may bypass it. A synchronous request
            // (no authenticated callback) still requires initialization.
            if(pc<e_.queue.lr-4u&&next_>=e_.queue.lr&&!queue_path()){
                if(!callback_||(callback_&3u)||next_>e_.flush.lr-4u)return bad(pc,6);
                queue_skipped_=true;
            }
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!live(c,held)||!due_||c.pc!=pc||pc!=next_||
           c.inst_count!=last_||!fence_.settled(c))return fail(7);
        const auto e=queue_path()?e_.flush:e_.queue;
        if(pc!=e.pc||c.lr!=e.lr||!edge(c,e))return fail(7);
        due_=false;
        if(!queue_path()){
            if(c.gpr[3]!=queue_)return fail(7);
            active_=pc;return true;
        }
        if(!flush_args(c)||!finished(c))return fail(7);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&live(c,held)&&c.pc==e_.flush.pc&&c.lr==e_.flush.lr&&
            c.inst_count==last_&&queue_path()&&flush_args(c)&&finished(c);
    }
private:
    IoctlSubmitPrefixExpectation e_;AllocatorStoreFence fence_;AllocatorRange req_{},stack_{};
    std::vector<uint8_t> shadow_;const void* cpu_=nullptr;
    std::array<uint32_t,32> caller_gp_{};
    uint32_t caller_cr_=0;
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return v&0x00fff000u;
    }
    uint32_t sp0_=0,r2_=0,r13_=0,msr_=0,active_=0,next_=0,queue_=0,callback_=0;
    uint64_t last_=0,start_=0;unsigned stage_=0,error_=0,visits_=0,ordinal_=0,queue_mask_=0,detail_=0,queue_class_=0;
    bool due_=false,queue_returned_=false,queue_skipped_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool bad(uint32_t pc,unsigned n){ordinal_=(pc-active_)/4u+1u;detail_=n;return fail(5);}
    static uint32_t canonical(uint32_t a){return OpenCacheRangeTrace::canonical(a);}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.gpr[2]==r2_&&c.gpr[13]==r13_&&
            c.gpr[1]>=stack_.base&&c.gpr[1]<=sp0_&&!(c.gpr[1]&7u)&&c.inst_count>=start_&&c.inst_count-start_<=256u;
    }
    template<class C>bool queue_zero(C& c){return fence_.settled(c)&&!c.mmu.read32(queue_)&&!c.mmu.read32(queue_+4u);}
    template<class C>bool flush_args(C& c)const{return canonical(c.gpr[3])==req_.base&&c.gpr[4]>=32u&&c.gpr[4]<=req_.size;}
    template<class C>bool finished(C& c){
        if(!fence_.settled(c)||!fence_.stores()||!queue_path()||
           (queue_returned_&&(queue_mask_!=3u||!queue_zero(c)))||(queue_skipped_&&queue_mask_))return false;
        if(fence_.heap_stores())return fence_.finished(c);
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(req_.base+i)!=shadow_[i])return false;
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
            word(c,e.lr-4u,e.branch_word)&&word(c,e.pc,e.entry_word);
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
