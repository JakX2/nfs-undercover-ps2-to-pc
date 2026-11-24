#include "wii_sram_read_witness_v534.h"
#include "wii_exi_endpoint_scheduler_v495.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
static unsigned trial=0,checkpoint=0;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("SRAM read witness trial="+std::to_string(trial)+" step="+std::to_string(checkpoint)+" line="+std::to_string(loc.line()));
}
struct Ram final:IosMemory{
    std::map<uint32_t,uint8_t> mem;uint8_t dummy=0;
    bool valid(uint32_t a,uint32_t n)const override{return uint64_t(a)+n<=0x1800000ull;}
    uint8_t read8(uint32_t a)const override{auto i=mem.find(a);return i==mem.end()?0:i->second;}
    void write8(uint32_t a,uint8_t v)override{mem[a]=v;}
};
struct Mmu{
    Ram& ram;
    uint8_t* get_ptr(uint32_t a){return ram.valid(a&0x3fffffffu,1)?&ram.dummy:nullptr;}
    uint8_t read8(uint32_t a){return ram.read8(a&0x3fffffffu);}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)ram.write8((a+i)&0x3fffffffu,uint8_t(v>>(24-8*i)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;
    bool is_running=true;uint64_t inst_count=10000;
    std::array<uint32_t,256> guest_data_invalidate_lines{};
    unsigned guest_data_invalidate_count=3;
};
int main(){
    constexpr uint32_t sp=0x80751000,r13=0x8070e8e0,device_id=0xbeef0010,cmd=sp-64,meta=0x806f156cu;
    constexpr SramReadExpectations e{{0x80528754,0x805208d0,1,2},{{
        {0x80522294,0x80528788,3,4},{0x804efb80,0x80528798,5,6},
        {0x804ef3ec,0x805287b8,7,8},{0x804ee984,0x805287f4,9,10},
        {0x804eed9c,0x80528804,11,12},{0x804eeca4,0x80528828,13,14},
        {0x804eed9c,0x8052883c,11,16},{0x804ef51c,0x80528850,17,18},
        {0x804efc7c,0x80528864,19,20},{0x80528954,0x805288bc,21,22},
        {0x80528954,0x80528928,21,24}}},25};
    for(unsigned fault=0;fault<=18;++fault){
        trial=fault;checkpoint=0;exi_id_completion={};sram_completion={};
        need(exi_id_completion.begin(true));
        exi_id_completion.record({1,0,2,2,1,0},0);exi_id_completion.record({2,0,2,4,0,0},device_id);
        need(exi_id_completion.finish());
        Ram ram;Cpu c{{ram}};auto& m=c.mmu;c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;
        m.write32(r13-3824,device_id);m.write32(cmd,0x20000100);
        auto set_edge=[&](VectorEdge x){m.write32(x.pc,x.entry_word);m.write32(x.lr-4,x.branch_word);};
        set_edge(e.entry);for(auto x:e.edges)set_edge(x);m.write32(e.entry.lr,e.return_word);
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;c.inst_count+=100;};
        enter(e.entry);if(fault==1)m.write32(SramGuest,1);
        SramReadWitness w(e);need(w.begin(c,fault!=2)==(fault!=1&&fault!=2));
        if(fault==1||fault==2)continue;
        std::atomic<uint32_t> pi{0};WiiIrqBanks banks(pi);ExiController exi(banks,&ram);
        auto fixture=sram_read_fixture();if(fault==6)fixture[0]^=1;
        ExiMxDevice mx(fixture,[]{return 1u;});ExiIdEndpoint id(device_id);
        ExiEndpointScheduler sched(exi,mx,id,8);uint64_t tick=1;
        auto complete=[&](uint32_t ctrl){
            exi.write(0,12,ctrl);auto q=*exi.pending(0);sched.advance(tick);sched.advance(tick+7);
            need(exi.pending(0).has_value());tick+=8;sched.advance(tick++);need(!exi.pending(0));
            sram_completion.record(q,exi,mx);
        };
        bool stopped=false;
        for(unsigned step=1;step<=11;++step){
            checkpoint=step;enter(e.edges[step-1]);c.gpr[1]=sp-128;c.gpr[3]=c.gpr[4]=c.gpr[5]=c.gpr[6]=c.gpr[7]=0;
            bool bad=false;
            switch(step){
            case 1:c.gpr[3]=SramGuest;c.gpr[4]=fault==3?32:64;bad=fault==3;break;
            case 2:
                c.gpr[4]=1;c.guest_data_invalidate_count=5;
                c.guest_data_invalidate_lines[3]=SramGuest;c.guest_data_invalidate_lines[4]=SramGuest+(fault==4?64:32);
                bad=fault==4;break;
            case 3:c.gpr[4]=1;c.gpr[5]=3;m.write32(meta,0x10);break;
            case 4:
                c.gpr[4]=cmd;c.gpr[5]=4;c.gpr[6]=1;m.write32(meta,0x14);
                if(fault==5)m.write32(cmd,0);
                bad=fault==5;break;
            case 5:m.write32(meta,0x16);break;
            case 6:
                c.gpr[4]=SramGuest;c.gpr[5]=64;m.write32(meta,0x14);
                bad=fault==6||fault==7;if(fault==7)m.write32(SramGuest,1);break;
            case 7:m.write32(meta,0x15);break;
            case 8:
                m.write32(meta,0x14);if(fault==9)m.write32(SramGuest,0);
                bad=fault==8||fault==9;break;
            case 9:m.write32(meta,0x10);break;
            case 10:case 11:
                c.gpr[4]=20;m.write32(meta,0);m.write32(SramGuest+72,1);m.write32(SramGuest+76,1);
                if(fault==10&&step==10)c.gpr[3]=1;
                bad=fault==10&&step==10;break;
            }
            const bool passed=w.observe(c.pc,c);
            if(passed==bad)std::cerr<<"SRAM observer stage="<<w.stage()<<" reason="<<w.failure()<<" completed="<<sram_completion.count()<<'\n';
            need(passed==!bad);
            if(bad){stopped=true;break;}
            if(step==5){exi.write(0,0,0x130);exi.write(0,16,0x20000100);complete(0x35);}
            if(step==7){exi.write(0,4,SramGuest+(fault==8?32:0));exi.write(0,8,64);complete(3);}
            if(step==8)exi.write(0,0,8);
        }
        if(stopped)continue;
        checkpoint=12;c.pc=e.entry.lr;c.lr=e.entry.lr;c.gpr[1]=sp;c.inst_count+=100;
        m.write32(SramGuest+64,64);m.write32(SramGuest+68,0);m.write32(SramGuest+72,0);m.write32(SramGuest+76,1);
        m.write32(meta,0);m.write32(meta+4,0);m.write32(meta+8,cmd);m.write32(meta+12,1);
        if(fault==11)m.write32(SramGuest+64,32);
        if(fault==12)m.write32(SramGuest+72,1);
        if(fault==13)c.gpr[14]=1;
        if(fault==14)c.gpr[1]-=4;
        if(fault==15)m.write32(meta,0x10);
        if(fault==16)m.write32(meta+8,cmd+4);
        if(fault==17)m.write32(e.entry.lr,0);
        if(fault==18)c.guest_data_invalidate_count++;
        need(w.observe(c.pc,c)==(fault==0));
        if(!fault)need(w.stage()==13&&sched.completed()==2&&pi.load()==0);
    }
    std::cout<<"PASS: original-free SRAM read witness with actual EXI scheduler and DMA, 18 negative controls\n";
}
