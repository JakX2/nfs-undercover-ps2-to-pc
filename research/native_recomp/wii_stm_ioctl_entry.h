#pragma once
#include "wii_open_return_v1351.h"
namespace undercover::wii {
struct StmIoctlEntryExpectation {
    uint32_t stm,resume,ioctl_call;
    VectorEdge disable,ioctl;
    std::span<const ReplyNativeWord> words;
    std::span<const uint32_t> stores;
    std::span<const AllocatorRange> text;
};
// Observe the original second-return corridor; no host writes or IOS service.
// The caller retains the selected thread, native mailbox and freed-heap guards.
class StmIoctlEntryWitness {
public:
    explicit StmIoctlEntryWitness(StmIoctlEntryExpectation e):e_(e){}
    unsigned stage()const{return stage_;} unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;} unsigned stores()const{return stores_;}
    uint32_t expected_msr()const{return disabled_?msr_&~0x8000u:msr_;}
    template<class C,class Prior>bool begin(C& c,Prior& prior,bool held,bool descriptor,unsigned first){
        if(stage_||error_||!held||!descriptor||!prior.returned(c,held,descriptor)||
           !safe(c)||c.pc!=e_.resume||c.lr!=c.pc||c.gpr[3]!=1u||!(c.msr&0x8000u)||
           (first!=1u&&first!=2u)||!known(c,e_.stm,e_.resume)||!direct(c,e_.disable)||
           !direct(c,e_.ioctl)||e_.ioctl.lr!=e_.ioctl_call+4u||e_.stores.empty()||
           e_.stores.size()>8u||e_.text.empty()||e_.text.size()>16u)return fail(1);
        cpu_=&c;msr_=c.msr;sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];first_=first;
        active_=e_.stm;next_=c.pc;last_=start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!live(c,held)||entry_due_||poll_due_||pc!=next_||
           c.inst_count-last_!=(resume_?2u:1u)||!known(c,active_,pc,w)||++visits_>128u||
           (resume_&&c.pc!=pc)||!settled(c))return fail(2);
        resume_=false;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rs=(w>>21)&31u;
        if(op==36u){
            if(active_!=e_.stm||std::count(e_.stores.begin(),e_.stores.end(),pc)!=1||
               (ra!=2u&&ra!=13u)||stores_>=e_.stores.size())return fail(3);
            int64_t ea=int64_t(c.gpr[ra])+int32_t((w&0xffffu)^0x8000u)-0x8000;
            if(ea<0x80000000ll||ea>0x817ffffcll||(ea&3)||!mapped(c,uint32_t(ea),4u)||
               (!stores_&&c.gpr[rs]!=1u))return fail(3);
            addr_=uint32_t(ea);value_=c.gpr[rs];pending_=true;++stores_;
        }else if((op>=37u&&op<=39u)||(op>=44u&&op<=45u)||op==47u||
                 (op>=52u&&op<=55u)||op==60u||op==61u||
                 (op==31u&&(xo==150u||xo==151u||xo==183u||xo==215u||xo==247u||xo==407u||xo==439u||
                   xo==661u||xo==725u||xo==662u||xo==918u||xo==663u||xo==695u||xo==727u||xo==759u||xo==983u||xo==1014u)))return fail(3);
        if(op==18u&&(w&1u)){
            const bool d=!disabled_&&pc+4u==e_.disable.lr&&w==e_.disable.branch_word;
            const bool i=disable_returned_&&pc==e_.ioctl_call&&w==e_.ioctl.branch_word;
            if(active_!=e_.stm||(!d&&!i))return fail(4);
            if(i&&(!stores_||!arguments(c)||!settled(c)))return fail(4);
            next_=d?e_.disable.pc:e_.ioctl.pc;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u||active_!=e_.disable.pc)return fail(4);
            if(!taken(c,w))return true;
            if(!disabled_||c.lr!=e_.disable.lr||c.gpr[3]!=1u||!helper_abi(c))return fail(4);
            disable_returned_=true;active_=e_.stm;next_=e_.disable.lr;return true;
        }
        if(op==31u&&xo==146u){
            if(active_!=e_.disable.pc||disabled_||c.gpr[rs]!=(msr_&~0x8000u))return fail(4);
            disabled_=true;return true;
        }
        if(op==17u||(op==19u&&(xo==50u||xo==528u))||(op==16u&&(w&1u)))return fail(4);
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            uint32_t dst=target(pc,w);
            if(!known(c,active_,dst))return fail(4);
            if(dst<=pc){poll_due_=true;poll_pc_=pc;}
            if(op==18u||taken(c,w)){
                if(active_==e_.stm&&dst>e_.ioctl_call)return fail(4);
                next_=dst;
            }
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||c.inst_count!=last_||!settled(c))return fail(5);
        if(pc==e_.disable.pc&&!disabled_&&c.lr==e_.disable.lr&&direct(c,e_.disable)){
            helper_=c.gpr;helper_cr_=pack(c)&0x00fff000u;active_=pc;entry_due_=false;return true;
        }
        if(pc==e_.ioctl.pc&&disable_returned_&&c.lr==e_.ioctl.lr&&direct(c,e_.ioctl)&&arguments(c)&&stores_){
            stage_=2;entry_due_=false;return true;
        }
        return fail(5);
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_||!settled(c))return fail(6);
        if(resume_&&!initial_poll_&&c.pc==e_.resume){initial_poll_=true;return true;}
        if(poll_due_&&c.pc==poll_pc_){poll_due_=false;return true;}
        return fail(6);
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&base(c,held)&&c.msr==expected_msr()&&c.pc==e_.ioctl.pc&&
            c.lr==e_.ioctl.lr&&c.inst_count==last_&&arguments(c)&&stores_&&settled(c);
    }
private:
    StmIoctlEntryExpectation e_;const void* cpu_=nullptr;
    uint32_t msr_=0,sp_=0,r2_=0,r13_=0,active_=0,next_=0,poll_pc_=0,addr_=0,value_=0,helper_cr_=0;
    uint64_t last_=0,start_=0;unsigned first_=0,stage_=0,error_=0,visits_=0,stores_=0;
    std::array<uint32_t,32> helper_{};
    std::array<std::pair<uint32_t,uint32_t>,8> written_{};unsigned cells_=0;
    bool disabled_=false,disable_returned_=false,entry_due_=false,resume_=true,poll_due_=false,initial_poll_=false,pending_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>bool base(C& c,bool held)const{
        return !error_&&cpu_==&c&&held&&safe(c)&&c.gpr[1]==sp_&&c.gpr[2]==r2_&&c.gpr[13]==r13_&&
            c.inst_count>=start_&&c.inst_count-start_<=256u;
    }
    template<class C>bool live(C& c,bool held)const{return stage_==1u&&base(c,held)&&c.msr==expected_msr();}
    template<class C>bool settled(C& c){
        if(pending_){
            if(!word(c,addr_,value_))return false;
            auto p=std::find_if(written_.begin(),written_.begin()+cells_,[&](auto x){return x.first==addr_;});
            if(p==written_.begin()+cells_){if(cells_==written_.size())return false;++cells_;}
            *p={addr_,value_};pending_=false;
        }
        for(unsigned i=0;i<cells_;++i)if(!word(c,written_[i].first,written_[i].second))return false;
        return true;
    }
    template<class C>bool arguments(C& c)const{
        return c.gpr[3]==(first_==2u?0u:1u)&&c.gpr[4]==StmIos::EventHook&&
            c.gpr[6]<=4096u&&(!c.gpr[6]||mapped(c,c.gpr[5],c.gpr[6]))&&
            c.gpr[8]>=4u&&c.gpr[8]<=4096u&&mapped(c,c.gpr[7],c.gpr[8])&&!(c.gpr[9]&3u)&&
            std::count_if(e_.text.begin(),e_.text.end(),[&](auto x){return x.contains(c.gpr[9],4u);})==1;
    }
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    template<class C>bool direct(C& c,VectorEdge e)const{return e.lr>=4u&&e.branch_word==branch(e.lr-4u,e.pc)&&word(c,e.lr-4u,e.branch_word)&&word(c,e.pc,e.entry_word)&&known(c,e.pc,e.pc);}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool helper_abi(C& c)const{
        if((pack(c)&0x00fff000u)!=helper_cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=helper_[i])return false;
        return true;
    }
    static uint32_t branch(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
};
}
