#include "wii_arena_clear_witness_v607.h"
#include "flat_cacheline_zero_v67.h"
#include <vector>
#include <iostream>
#include <source_location>
using namespace undercover::wii;
using W=ArenaClearWitness;using T=ArenaCacheRangeTrace;
static void need(bool v,const std::source_location l=std::source_location::current()){
    if(!v)throw std::runtime_error("V608 line "+std::to_string(l.line()));
}
constexpr uint32_t R13=0x8070e8e0u,Sp=0x80751c60u,Size=0x80000u;
constexpr std::array<uint32_t,2> Lo{0x81001000u,0x90001000u};
constexpr std::array<uint32_t,4> Off{16400,3472,16396,3468};
struct Mmu{
    std::vector<uint8_t> code=std::vector<uint8_t>(0x400000),m1=std::vector<uint8_t>(Size+2,0xa5),m2=std::vector<uint8_t>(Size+2,0x5a);
    uint8_t* get_ptr(uint32_t a){
        if(a>=0x80400000u&&a-0x80400000u<code.size())return code.data()+a-0x80400000u;
        if(a>=Lo[0]-1&&a-(Lo[0]-1)<m1.size())return m1.data()+a-(Lo[0]-1);
        if(a>=Lo[1]-1&&a-(Lo[1]-1)<m2.size())return m2.data()+a-(Lo[1]-1);
        return nullptr;
    }
    uint8_t read8(uint32_t a){auto* p=get_ptr(a);need(p!=nullptr);return *p;}
    uint32_t read32(uint32_t a){uint32_t w=0;for(unsigned i=0;i<4;++i)w=w<<8|read8(a+i);return w;}
    void write32(uint32_t a,uint32_t w){for(unsigned i=0;i<4;++i){auto* p=get_ptr(a+i);need(p!=nullptr);*p=uint8_t(w>>(24-8*i));}}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0,lr=0,msr=0x32,guest_flush_count=87,guest_last_flush=0;
    uint64_t inst_count=100;bool is_running=true;
    nwii::runtime::FlatCachelineZeroTrace guest_dcbz_trace;T arena_cache_range;
    void zero(uint32_t a){arena_cache_range.on_zero(a);guest_dcbz_trace.zero(mmu,a);}
    void flush(uint32_t a){arena_cache_range.on_flush(a);++guest_flush_count;guest_last_flush=a;}
};
// Independent test double for the V598 pair, already owner-verified in
// its generated native fixture. Cache and reset components here are real.
struct Pair{
    unsigned n=0;bool armed=false,returned=false;
    unsigned completed()const{return n;}
    void arm(uint32_t pc,Cpu& c,T& t){if(armed||pc!=W::Sc||!t.ready_sc(c))throw std::runtime_error("arm");armed=true;}
    bool finish(Cpu& c){if(!armed||!returned||!c.arena_cache_range.finish(c))return false;armed=returned=false;++n;return true;}
};
static ArenaClearEdge edge(uint32_t pc,uint32_t lr){return {pc,lr,0x48000001u|((pc-lr+4)&0x03fffffcu),0x60000000u};}
static ArenaClearExpectations expected(){
    ArenaClearExpectations e{};
    e.edges[0]={edge(0x8051ffc8,0x80520940),edge(0x805285d0,0x8051ffe0),edge(0x80521d28,0x8051ffec),edge(0x80521d40,0x8051fff4),edge(0x80521d40,0x8051fffc),edge(0x8052234c,0x80520020),edge(0x805222c0,0x8052002c)};
    e.edges[1]={edge(0x805201a4,0x80520944),edge(0x805285d0,0x805201bc),edge(0x80521d20,0x805201c8),edge(0x80521d38,0x805201d0),edge(0x80521d38,0x805201d8),edge(0x8052234c,0x805201fc),edge(0x805222c0,0x80520208)};
    e.begin_word=0x60000000;e.return_word=0x60000000;e.flush_resume_words.fill(0x60000000);return e;
}
struct Rejected{};
static void trial(unsigned fault){
    auto e=expected();W w(e);Cpu c;Pair pair;ArenaResetProfile reset;ArenaResetBinding binding(reset);
    c.pc=c.lr=W::Begin;c.gpr[1]=Sp;c.gpr[13]=R13;c.gpr[2]=0x80715ee0;
    auto put=[&](uint32_t a,uint32_t v){c.mmu.write32(a,v);};
    put(W::Begin,e.begin_word);put(W::Return,e.return_word);put(W::Sc,0x44000002);
    put(R13-3400,1);put(0x806f4f0c,0);
    for(unsigned i=0;i<2;++i){put(R13-Off[2*i],Lo[i]);put(R13-Off[2*i+1],Lo[i]+Size);
        for(auto a:e.edges[i]){put(a.pc,a.entry);put(a.lr-4,a.branch);}
        put(e.edges[i][6].lr,e.flush_resume_words[i]);}
    if(fault==1)put(0x806f4f0c,1);
    if(fault==2)put(R13-Off[0],Lo[0]+1);
    need(w.begin(c)==(fault!=1&&fault!=2));if(fault==1||fault==2)return;
    auto event=[&](uint32_t addr,unsigned f=0){c.inst_count+=10;bool ok=w.observe(addr,c,reset,pair);
        need(ok==(!f||fault!=f));if(!ok)throw Rejected{};};
    auto enter=[&](ArenaClearEdge a,unsigned f=0){c.pc=a.pc;c.lr=a.lr;event(c.pc,f);};
    bool rejected=false;
    try{
        for(unsigned i=0;i<2;++i){
            const auto& es=e.edges[i];const auto lo=Lo[i],hi=lo+Size;
            c.gpr[1]=Sp;
            if(i==1&&fault==3)*c.mmu.get_ptr(Lo[0]+55)=1;
            enter(es[0],i==1?3:0);
            c.gpr[1]=Sp-16;
            if(i==0&&fault==4)c.gpr[1]-=4;
            enter(es[1],i==0?4:0);
            if(i==0&&fault==5){enter(es[2],5);}
            need(ArenaResetBinding::read32(0xcc003024u)==ArenaResetProfile::ColdValue);
            if(i==0&&fault==6)enter(es[3],6);
            if(i==0&&fault==7)put(es[2].lr-4,0);
            enter(es[2],i==0?7:0);enter(es[3]);enter(es[4]);
            c.gpr[3]=lo;c.gpr[4]=Size;
            if(i==0&&fault==8)c.gpr[4]-=32;
            enter(es[5],i==0?8:0);
            for(uint32_t a=lo;a<hi;a+=32){if(i==0&&fault==9&&a==hi-32)break;c.zero(a);}
            if(i==0&&fault==10)*c.mmu.get_ptr(lo+22)=1;
            if(i==0&&fault==11)*c.mmu.get_ptr(hi)^=1;
            c.gpr[3]=hi-T::Tail;c.gpr[4]=T::Tail;
            if(i==0&&fault==12)c.gpr[3]-=32;
            enter(es[6],i==0&&fault>=9&&fault<=12?fault:0);
            for(uint32_t a=hi-T::Tail;a<hi;a+=32){if(i==0&&fault==13&&a==hi-32)break;c.flush(a);}
            c.pc=W::Sc;
            if(i==0&&fault==14)c.lr=e.edges[1][6].lr;
            event(W::Sc,i==0&&(fault==13||fault==14)?fault:0);
            pair.returned=!(i==0&&fault==15);c.pc=c.lr=es[6].lr;
            if(i==0&&fault==16)put(c.pc,0);
            event(c.pc,i==0&&(fault==15||fault==16)?fault:0);
        }
        c.gpr[1]=Sp;c.pc=c.lr=W::Return;
        if(fault==17)*c.mmu.get_ptr(Lo[1]+Size)^=1;
        if(fault==18)put(R13-Off[3],0);
        event(c.pc,fault>=17?fault:0);
    }catch(const Rejected&){rejected=true;}
    need(rejected==(fault!=0));
    if(!fault){need(w.stage()==20&&w.lines()==32768&&pair.n==2&&reset.complete()&&c.arena_cache_range.flushes()==16384);}
    else need(w.failure()!=0);
}
int main(){
    for(unsigned fault=0;fault<=18;++fault)trial(fault);
    std::cout<<"V608_ARENA_WITNESS stages=20 zero_lines=32768 flush_lines=16384 reset_reads=2 refusal=18 native_sc_fixture=separate boot_verified=0\n";
}
