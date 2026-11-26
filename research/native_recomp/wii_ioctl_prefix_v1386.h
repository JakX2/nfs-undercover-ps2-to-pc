#pragma once
#include "wii_stm_ioctl_entry.h"
namespace undercover::wii {
struct IoctlPrefixExpectation {
    uint32_t root,save_call,save_root,alloc_call,alloc_root,save_count;
    std::span<const ReplyNativeWord> words;
};
// Original wrapper prefix only: stop before executing the allocator veneer.
// Predict stack stores from live PPC operands, check the entire stack shadow,
// and never write guest memory or service IOS from the observer.
class IoctlPrefixWitness {
public:
    explicit IoctlPrefixWitness(IoctlPrefixExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return stores_;}
    unsigned saved()const{return saved_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.root||(c.msr&0x8000u)||
           e_.save_count<1u||e_.save_count>18u||e_.words.size()>128u||
           !known(c,e_.root,e_.root)||!known(c,e_.save_root,e_.save_root)||
           !known(c,e_.alloc_root,e_.alloc_root)||c.gpr[1]<0x80000200u||
           c.gpr[1]>0x817ffff0u||(c.gpr[1]&7u))return fail(1);
        sp_=c.gpr[1];lo_=sp_-512u;gp_=c.gpr;msr_=c.msr;
        if(!mapped(c,lo_,shadow_.size()*4u))return fail(1);
        for(unsigned i=0;i<shadow_.size();++i)shadow_[i]=c.mmu.read32(lo_+4u*i);
        cpu_=&c;active_=next_=c.pc;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||entry_due_||pc!=next_||c.inst_count-last_!=1u||
           !known(c,active_,pc,w)||!settled(c)||++visits_>128u)return fail(2);
        last_=c.inst_count;last_pc_=pc;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rs=(w>>21)&31u;
        if(op==36u||op==37u){
            const int64_t ea=int64_t(ra?c.gpr[ra]:0u)+int32_t((w&0xffffu)^0x8000u)-0x8000;
            if(ea<lo_||ea+4>int64_t(lo_)+int64_t(shadow_.size()*4u)||(ea&3)||!ra||
               (op==37u&&(active_!=e_.root||ra!=1u||rs!=1u))||++stores_>32u)return fail(3);
            if(active_==e_.save_root){
                if(op!=36u||rs!=32u-e_.save_count+saved_||saved_>=e_.save_count||
                   c.gpr[rs]!=gp_[rs])return fail(3);
                ++saved_;
            }
            shadow_[(uint32_t(ea)-lo_)/4u]=c.gpr[rs];
            if(op==37u){sp_update_=true;new_sp_=uint32_t(ea);}
        }else if((op>=38u&&op<=39u)||(op>=44u&&op<=45u)||op==47u||
                 (op>=52u&&op<=55u)||op==60u||op==61u||
                 (op==31u&&(xo==150u||xo==151u||xo==183u||xo==215u||xo==247u||xo==407u||xo==439u||
                   xo==661u||xo==725u||xo==662u||xo==918u||xo==663u||xo==695u||xo==727u||xo==759u||xo==983u||xo==1014u)))return fail(3);
        if(op==18u&&(w&1u)){
            if(active_!=e_.root||(w&2u))return fail(4);
            const uint32_t dst=target(pc,w);
            if(!saved_return_&&pc==e_.save_call&&dst==e_.save_root){}
            else if(saved_return_&&pc==e_.alloc_call&&dst==e_.alloc_root){}
            else return fail(4);
            ret_=pc+4u;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w!=0x4e800020u||active_!=e_.save_root||saved_!=e_.save_count||c.lr!=ret_)return fail(4);
            active_=e_.root;next_=ret_;saved_return_=true;return true;
        }
        if(op==17u||(op==19u&&(xo==50u||xo==528u))||(op==31u&&xo==146u))return fail(4);
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            const auto dst=target(pc,w);
            if(active_!=e_.root||!known(c,active_,dst))return fail(4);
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||c.lr!=ret_||
           c.inst_count!=last_||!known(c,pc,pc)||!settled(c))return fail(5);
        entry_due_=false;
        if(pc==e_.save_root&&!saved_return_){active_=pc;return true;}
        if(pc==e_.alloc_root&&saved_return_&&saved_==e_.save_count&&
           c.gpr[1]<sp_&&sp_-c.gpr[1]<=512u&&c.gpr[4]>=64u&&c.gpr[4]<=4096u){
            stage_=2;return true;
        }
        return fail(5);
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_||++polls_>8u||
           (c.pc!=active_&&c.pc!=last_pc_&&c.pc!=next_)||!settled(c))return fail(6);
        return true;
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&base(c,held)&&c.pc==e_.alloc_root&&c.lr==e_.alloc_call+4u&&
               c.inst_count==last_&&saved_return_&&saved_==e_.save_count&&settled(c);
    }
private:
    IoctlPrefixExpectation e_;const void* cpu_=nullptr;std::array<uint32_t,32> gp_{};
    std::array<uint32_t,132> shadow_{};
    uint32_t sp_=0,lo_=0,msr_=0,active_=0,next_=0,last_pc_=0,ret_=0,new_sp_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0,saved_=0,polls_=0;
    bool entry_due_=false,saved_return_=false,sp_update_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{
        return !error_&&cpu_==&c&&held&&safe(c)&&c.msr==msr_&&c.gpr[2]==gp_[2]&&c.gpr[13]==gp_[13]&&
               c.gpr[1]>=lo_&&c.gpr[1]<=sp_&&!(c.gpr[1]&7u);
    }
    template<class C>bool live(C& c,bool held)const{return stage_==1u&&base(c,held);}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||a<0x80000000u||uint64_t(a)+n>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>bool settled(C& c){
        if(sp_update_){if(c.gpr[1]!=new_sp_)return false;sp_update_=false;}
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read32(lo_+4u*i)!=shadow_[i])return false;
        return true;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return !(pc&3u)&&mapped(c,pc,4u)&&std::count_if(e_.words.begin(),e_.words.end(),
            [&](auto x){return x.owner==owner&&x.pc==pc&&c.mmu.read32(pc)==x.word;})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&c.mmu.read32(pc)==w;}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
