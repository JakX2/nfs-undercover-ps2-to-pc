#pragma once
#include "wii_ipc_dispatch_execution.h"
namespace undercover::wii {
struct StmEventStore {uint32_t pc,address,width,reg;};
struct StmEventReturnExpectation {
    uint32_t stm,start;
    IpcDispatchEdge restore;
    std::span<const IpcDispatchWord> words;
    std::span<const StmEventStore> sites;
    AllocatorRange flag;
};
// The successful asynchronous return must mark the original STM event flag
// before reenabling interrupts. Observe exactly one genuine native write.
class StmEventReturnWitness {
public:
    explicit StmEventReturnWitness(StmEventReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned stores()const{return stores_;}
    unsigned ordinal()const{return ordinal_;}
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.start||c.gpr[3]!=0||
           e_.sites.size()!=2u||e_.flag.size<4u||e_.flag.size>4096u||!mapped(c,e_.flag)||
           !known(c,e_.start)||!known(c,e_.restore.call)||
           e_.restore.word>>26!=18u||(e_.restore.word&3u)!=1u||
           target(e_.restore.call,e_.restore.word)!=e_.restore.target||
           c.mmu.read32(e_.restore.call)!=e_.restore.word)return fail(1);
        for(auto s:e_.sites){
            if(s.width!=4u||s.reg>31u||!e_.flag.contains(s.address,4u)||!known(c,s.pc)||
               (s.address&3u)||c.mmu.read32(s.pc)>>26!=36u)return fail(1);
        }
        if(e_.sites[0].pc==e_.sites[1].pc||e_.sites[0].address!=e_.sites[1].address)return fail(1);
        for(unsigned i=0;i<e_.flag.size;++i)shadow_.push_back(c.mmu.read8(e_.flag.base+i));
        gp_=c.gpr;msr_=c.msr;cpu_=&c;next_=c.pc;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||due_||pc!=next_||c.inst_count-last_!=1u||
           !known(c,pc)||c.mmu.read32(pc)!=w||++visits_>32u||!settled(c))return fail(2);
        last_=c.inst_count;ordinal_=(pc-e_.stm)/4u+1u;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u;
        if(op==36u){
            auto s=std::find_if(e_.sites.begin(),e_.sites.end(),[&](auto x){return x.pc==pc;});
            const uint32_t a=c.gpr[ra]+uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
            if(stores_||s==e_.sites.end()||(ra!=2u&&ra!=13u)||rs!=s->reg||a!=s->address||
               c.gpr[rs]!=1u)return fail(3);
            const auto off=a-e_.flag.base;
            for(unsigned i=0;i<4;++i)shadow_[off+i]=uint8_t(c.gpr[rs]>>(24u-i*8u));
            ++stores_;
        }else if(op==18u&&(w&1u)){
            if(pc!=e_.restore.call||w!=e_.restore.word||stores_!=1u||c.gpr[3]!=1u)return fail(4);
            next_=e_.restore.target;due_=true;return true;
        }else if(op==16u||op==18u){
            if(w&3u||target(pc,w)<=pc||(op==16u&&!((w>>21)&4u)))return fail(4);
            if(op==18u||taken(c,w))next_=target(pc,w);
        }else if(!(op==10u||op==11u||op==14u||op==15u||op==20u||op==21u||op==23u||
                   (op>=24u&&op<=29u)||(op==31u&&(xo==0u||xo==32u||xo==28u||xo==444u||xo==266u||xo==316u))))return fail(4);
        if(!known(c,next_))return fail(4);
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!live(c,held)||!due_||pc!=e_.restore.target||c.pc!=pc||c.lr!=e_.restore.call+4u||
           c.inst_count!=last_||c.gpr[3]!=1u||stores_!=1u||!settled(c))return fail(5);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&live(c,held)&&c.pc==e_.restore.target&&c.lr==e_.restore.call+4u&&
            c.inst_count==last_&&c.gpr[3]==1u&&stores_==1u&&settled(c);
    }
    template<class C>bool flag_preserved(C& c){return stage_==2u&&!error_&&cpu_==&c&&settled(c);}
private:
    StmEventReturnExpectation e_;std::vector<uint8_t> shadow_;
    std::array<uint32_t,32> gp_{};const void* cpu_=nullptr;
    uint32_t msr_=0,next_=0;uint64_t last_=0;
    unsigned stage_=0,error_=0,visits_=0,stores_=0,ordinal_=0;bool due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&
        c.gpr[1]==gp_[1]&&c.gpr[2]==gp_[2]&&c.gpr[13]==gp_[13];}
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||a.base<0x80000000u||a.end()>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>bool settled(C& c){
        if(!mapped(c,e_.flag))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(e_.flag.base+i)!=shadow_[i])return false;
        return true;
    }
    template<class C>bool known(C& c,uint32_t pc)const{
        return !(pc&3u)&&mapped(c,{pc,4})&&std::count_if(e_.words.begin(),e_.words.end(),
            [&](auto x){return x.owner==e_.stm&&x.pc==pc&&c.mmu.read32(pc)==x.word;})==1;
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;return (bo&16u)||bit==bool(bo&8u);}
};
}
