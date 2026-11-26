#pragma once
#include "wii_ioctl_allocation_v1387.h"
namespace undercover::wii {
struct IoctlConstructionExpectation {
    uint32_t wrapper,resume;
    VectorEdge input_flush,output_flush;
    std::span<const ReplyNativeWord> words;
};
// Original wrapper request writes between the verified allocation return
// and first native buffer flush. The callback location is not guessed:
// require its exact value at a unique aligned extension word.
class IoctlConstructionWitness {
public:
    explicit IoctlConstructionWitness(IoctlConstructionExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return fence_.stores();}
    unsigned request_stores()const{return fence_.heap_stores();}
    unsigned store_failure()const{return fence_.failure();}
    unsigned range_failure()const{return fence_.range_failure();}
    unsigned base_class()const{return fence_.base_class();}
    unsigned ordinal()const{return ordinal_;}
    unsigned flush_kind()const{return flush_kind_;}
    uint32_t request()const{return request_;}
    uint32_t callback()const{return callback_;}
    uint32_t allocated_size()const{return size_;}
    uint32_t output()const{return output_;}
    uint32_t output_size()const{return out_size_;}
    unsigned wire_failure()const{return wire_error_;}
    unsigned control_failure()const{return control_error_;}
    template<class C>bool capture(C& c,bool held,unsigned first){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.wrapper||(c.msr&0x8000u)||
           (first!=1u&&first!=2u)||c.gpr[3]!=(first==2u?0u:1u)||c.gpr[4]!=StmIos::EventHook||
           c.gpr[6]>4096u||c.gpr[8]<4u||c.gpr[8]>4096u||!c.gpr[9]||(c.gpr[9]&3u))return fail(1);
        fd_=c.gpr[3];input_=canonical(c.gpr[5]);in_size_=c.gpr[6];
        output_=canonical(c.gpr[7]);out_size_=c.gpr[8];callback_=c.gpr[9];
        if((in_size_&&!mapped(c,input_,in_size_))||!mapped(c,output_,out_size_))return fail(1);
        for(unsigned i=0;i<in_size_;++i)in_.push_back(c.mmu.read8(input_+i));
        for(unsigned i=0;i<out_size_;++i)out_.push_back(c.mmu.read8(output_+i));
        cpu_=&c;msr_=c.msr;sp0_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];stage_=1;return true;
    }
    template<class C>bool begin(C& c,bool held,uint32_t request,uint32_t size,AllocatorRange heap,AllocatorRange meta){
        if(stage_!=1u||!base(c,held)||c.pc!=e_.resume||c.lr!=c.pc||canonical(c.gpr[3])!=request||
           size<64u||size>4096u||(request&31u)||!heap.contains(request,size)||
           !mapped(c,heap.base,heap.size)||heap.size>0x10000u||!meta.size||meta.size>64u||!mapped(c,meta.base,meta.size)||
           overlap({request,size},{input_,in_size_})||overlap({request,size},{output_,out_size_})||
           c.gpr[1]>=sp0_||sp0_-c.gpr[1]>512u||c.gpr[1]<0x80000200u||!known(c,e_.resume)||
           !direct(c,e_.input_flush)||!direct(c,e_.output_flush)||
           !fence_.begin(c,{c.gpr[1],sp0_-c.gpr[1]},{request,size}))return fail(2);
        heap_=heap;meta_=meta;request_=request;size_=size;sp_=c.gpr[1];
        // The wrapper owns only its current frame. The caller linkage and
        // memory below the frame are no longer writable by this lane.
        for(unsigned i=0;i<heap.size;++i)heap_shadow_.push_back(c.mmu.read8(heap.base+i));
        for(unsigned i=0;i<meta.size;++i)metadata_.push_back(c.mmu.read8(meta.base+i));
        last_=c.inst_count;next_=c.pc;stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=2u||!live(c,held)||entry_due_||poll_due_||pc!=next_||
           c.inst_count-last_!=(first_?2u:1u)||!known(c,pc,w)||++visits_>128u||
           (first_&&c.pc!=pc))return fail(3);
        if(!fence_.before(c,w)){ordinal_=(pc-e_.wrapper)/4u+1u;return fail(4);}
        first_=false;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const bool input=pc+4u==e_.input_flush.lr&&w==e_.input_flush.branch_word;
            const bool output=pc+4u==e_.output_flush.lr&&w==e_.output_flush.branch_word;
            if(!input&&!output)return control(pc,1);
            if(output&&in_size_)return control(pc,2);
            flush_kind_=input?1u:2u;
            const auto addr=input?input_:output_;const auto n=input?in_size_:out_size_;
            if(canonical(c.gpr[3])!=addr||c.gpr[4]!=n)return control(pc,3);
            if(!wire(c))return control(pc,4);
            if(!storage(c))return control(pc,5);
            next_=input?e_.input_flush.pc:e_.output_flush.pc;entry_due_=true;return true;
        }
        if(op==17u||(op==19u&&(xo==16u||xo==50u||xo==528u))||(op==31u&&xo==146u))return control(pc,6);
        if(op==16u||op==18u){
            if(w&3u)return control(pc,7);
            auto dst=target(pc,w);
            const bool transfer=op==18u||taken(c,w);
            // Exact original branch word was authenticated above. An
            // untaken error/cleanup branch cannot escape the observed
            // lane; every actual successor must remain instrumented.
            if(!known(c,transfer?dst:pc+4u))return control(pc,8);
            if(dst<=pc){poll_due_=true;poll_pc_=pc;}
            if(transfer)next_=dst;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        const auto edge=flush_kind_==1u?e_.input_flush:e_.output_flush;
        if(stage_!=2u||!live(c,held)||!entry_due_||pc!=next_||c.pc!=pc||pc!=edge.pc||c.lr!=edge.lr||
           c.inst_count!=last_||!direct(c,edge)||!wire(c)||!storage(c))return fail(6);
        entry_due_=false;stage_=3;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=2u||!live(c,held)||c.inst_count!=last_||!fence_.settled(c)||++polls_>128u)return fail(7);
        if(poll_due_&&c.pc==poll_pc_){poll_due_=false;return true;}
        return fail(7);
    }
    template<class C>bool reached(C& c,bool held){
        const auto edge=flush_kind_==1u?e_.input_flush:e_.output_flush;
        return stage_==3u&&live(c,held)&&c.pc==edge.pc&&c.lr==edge.lr&&c.inst_count==last_&&wire(c)&&storage(c);
    }
    template<class C>bool preserved(C& c,bool held){return stage_==3u&&live(c,held)&&wire(c)&&storage(c);}
    // Once the original submit routine enters, a fresh store fence owns
    // the allocated block and the submit frame. Retain all other storage
    // and exact wire/callback identities; do not require the old SP.
    template<class C>bool identity_preserved(C& c,bool held){return stage_==3u&&base(c,held)&&wire(c)&&outside_storage(c);}
private:
    IoctlConstructionExpectation e_;AllocatorStoreFence fence_;AllocatorRange heap_{},meta_{};
    const void* cpu_=nullptr;std::vector<uint8_t> in_,out_,heap_shadow_,metadata_;
    uint32_t msr_=0,sp0_=0,sp_=0,r2_=0,r13_=0,fd_=0,input_=0,in_size_=0,output_=0,out_size_=0,callback_=0,
        request_=0,size_=0,next_=0,poll_pc_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,ordinal_=0,flush_kind_=0,polls_=0,wire_error_=0,control_error_=0,callback_offset_=0;
    bool first_=true,entry_due_=false,poll_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool control(uint32_t pc,unsigned n){ordinal_=(pc-e_.wrapper)/4u+1u;control_error_=n;return fail(5);}
    static uint32_t canonical(uint32_t a){return OpenCacheRangeTrace::canonical(a);}
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.size&&b.size&&a.base<b.end()&&b.base<a.end();}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{return !error_&&cpu_==&c&&held&&safe(c)&&c.msr==msr_&&c.gpr[2]==r2_&&c.gpr[13]==r13_;}
    template<class C>bool live(C& c,bool held)const{return base(c,held)&&c.gpr[1]==sp_;}
    template<class C>bool storage(C& c){return fence_.finished(c)&&outside_storage(c);}
    template<class C>bool outside_storage(C& c){
        for(unsigned i=0;i<heap_shadow_.size();++i)
            if(!AllocatorRange{request_,size_}.contains(heap_.base+i,1u)&&c.mmu.read8(heap_.base+i)!=heap_shadow_[i])return false;
        for(unsigned i=0;i<metadata_.size();++i)if(c.mmu.read8(meta_.base+i)!=metadata_[i])return false;
        for(unsigned i=0;i<in_.size();++i)if(c.mmu.read8(input_+i)!=in_[i])return false;
        for(unsigned i=0;i<out_.size();++i)if(c.mmu.read8(output_+i)!=out_[i])return false;
        return true;
    }
    template<class C>bool wire(C& c){
        const std::array<std::pair<unsigned,uint32_t>,7> fields{{{0,StmIos::Ioctl},{8,fd_},{12,StmIos::EventHook},
            {16,input_&0x3fffffffu},{20,in_size_},{24,output_&0x3fffffffu},{28,out_size_}}};
        unsigned n=0;
        for(auto f:fields){++n;if(c.mmu.read32(request_+f.first)!=f.second){wire_error_=n;return false;}}
        unsigned matches=0,match=0;
        for(unsigned off=32;off<64;off+=4)if(c.mmu.read32(request_+off)==callback_){++matches;match=off;}
        if(matches!=1u||(callback_offset_&&callback_offset_!=match)){wire_error_=8;return false;}
        callback_offset_=match;return true;
    }
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||!((a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull)||(a>=0x90000000u&&uint64_t(a)+n<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool equal(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==e_.wrapper&&x.pc==pc&&equal(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t pc,uint32_t w)const{return known(c,pc)&&equal(c,pc,w);}
    template<class C>bool direct(C& c,VectorEdge e)const{return e.lr>=4u&&target(e.lr-4u,e.branch_word)==e.pc&&
        e.branch_word>>26==18u&&(e.branch_word&3u)==1u&&equal(c,e.lr-4u,e.branch_word)&&equal(c,e.pc,e.entry_word)&&known(c,e.lr-4u);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
