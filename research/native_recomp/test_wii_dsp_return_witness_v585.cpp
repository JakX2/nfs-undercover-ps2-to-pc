#include "wii_dsp_return_witness_v581.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V585 DSP witness line "+std::to_string(loc.line()));
}
struct Mmu {
    std::map<uint32_t,uint8_t> mem;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint8_t read8(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t w){for(unsigned i=0;i<4;++i)mem[a+i]=uint8_t(w>>(24-8*i));}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=2;
    bool is_running=true;uint64_t inst_count=100,tb=0;
    std::array<uint32_t,256> guest_flush_lines{};unsigned guest_flush_count=83;
    uint64_t read_timebase()const{return tb;}
};
// Only the read-only observer interface is modeled here. V580 separately
// tests the actual DSP control/ARAM backend with real byte copies.
struct BackendView {
    unsigned ack=1;bool complete=false,mem=true,aux=true;
    auto phase()const{return complete?DspBootProfile::Phase::Done:DspBootProfile::Phase::Dma2;}
    unsigned acks()const{return ack;}
    bool done()const{return complete;}
    bool memory()const{return mem;}
    bool aux_preserved()const{return aux;}
};
int main(){
    using W=DspStageWitness;using R=DspReturnWitness;
    constexpr uint32_t backup=0x816fff80u,sp=ThreadInitWitness::StackTop-104u;
    DspStageExpectations e{{{{0x80521d28,0x80522014,1,2},{0x80004338,0x80522024,3,4},
        {0x80004338,0x80522038,5,4},{0x805222c0,0x80522044,6,7}}},{},0x44000002u};
    DspReturnExpectations ret{{{{0x8052a83c,0x805220cc,0x11,0x22},{0x8052a83c,0x805220d4,0x33,0x22},
        {0x80521d28,0x8052218c,0x44,2},{0x80004338,0x805221a0,0x55,4}}},0x60000000};
    for(unsigned i=0;i<128;++i)e.image[i]=uint8_t(i*17+9);
    for(unsigned fault=0;fault<=16;++fault){
        Cpu c;auto& m=c.mmu;W w(e);R r(ret);BackendView p;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;c.lr=AudioResetWitness::Return;
        for(auto x:e.edges){m.write32(x.pc,x.entry_word);m.write32(x.lr-4,x.branch_word);}
        for(auto x:ret.edges){m.write32(x.pc,x.entry_word);m.write32(x.lr-4,x.branch_word);}
        m.write32(R::Return,ret.return_word);m.write32(W::Syscall,e.syscall_word);
        m.write32(c.gpr[13]-3472,0x81700000u);m.write32(0x800000e4u,ThreadInitWitness::Thread);
        std::array<uint8_t,128> initial{};
        for(unsigned i=0;i<128;++i){
            initial[i]=uint8_t(i*13+7);m.mem[W::Staging+i]=initial[i];
            m.mem[W::Source+i]=e.image[i];m.mem[backup+i]=0x5c;
        }
        for(auto a:{W::Staging,backup}){m.mem[a-1]=0xa1;m.mem[a+128]=0xb2;}
        need(w.begin(c));
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;c.inst_count+=10;};
        for(unsigned i=0;i<4;++i){
            enter(e.edges[i]);
            if(i==1){c.gpr[3]=backup;c.gpr[4]=W::Staging;c.gpr[5]=128;}
            if(i==2){for(unsigned j=0;j<128;++j)m.mem[backup+j]=initial[j];c.gpr[3]=W::Staging;c.gpr[4]=W::Source;c.gpr[5]=128;}
            if(i==3){for(unsigned j=0;j<128;++j)m.mem[W::Staging+j]=e.image[j];c.gpr[3]=W::Staging;c.gpr[4]=128;}
            need(w.observe(c.pc,c));
        }
        for(unsigned i=0;i<4;++i)c.guest_flush_lines[c.guest_flush_count++]=W::Staging+32*i;
        c.inst_count+=100;need(w.observe(W::Syscall,c));c.pc=c.lr=e.edges[3].lr;c.inst_count+=9;
        m.write32(c.pc,0x60000000);need(w.finish_sc(c.pc,c,0x60000000));
        // Fault 1: missing preserved staging at session activation.
        if(fault==1)m.mem[backup]^=1;
        need(r.begin(c,w)==(fault!=1));if(fault==1)continue;
        enter(ret.edges[0]);c.tb=0xfffffff0u;
        if(fault==2)p.ack=0;
        if(fault==3)c.lr^=4;
        need(r.observe(c.pc,c,w,p)==(fault!=2&&fault!=3));if(fault==2||fault==3)continue;
        enter(ret.edges[1]);c.tb+=1000;
        if(fault==4)c.tb-=1000;
        need(r.observe(c.pc,c,w,p)==(fault!=4));if(fault==4)continue;
        enter(ret.edges[1]);c.tb+=fault==5?100:1200;
        need(r.observe(c.pc,c,w,p));
        if(fault==6){enter(ret.edges[1]);c.tb+=1;need(!r.observe(c.pc,c,w,p));continue;}
        enter(ret.edges[2]);p.complete=fault!=7;p.ack=2;p.mem=fault!=8;
        if(fault==9)c.gpr[1]-=4;
        need(r.observe(c.pc,c,w,p)==!(fault==5||fault==7||fault==8||fault==9));
        if(fault==5||fault==7||fault==8||fault==9)continue;
        enter(ret.edges[3]);c.gpr[3]=W::Staging;c.gpr[4]=backup;c.gpr[5]=fault==10?96:128;
        if(fault==11)m.mem[W::Staging+31]^=1;
        need(r.observe(c.pc,c,w,p)==!(fault==10||fault==11));if(fault==10||fault==11)continue;
        for(unsigned i=0;i<128;++i)m.mem[W::Staging+i]=initial[i];
        c.pc=c.lr=R::Return;c.gpr[1]=sp+16;c.inst_count+=30;
        if(fault==12)c.gpr[1]-=4;
        if(fault==13)m.mem[W::Staging+127]^=1;
        if(fault==14)m.mem[backup+128]^=1;
        if(fault==15)p.aux=false;
        if(fault==16)m.write32(R::Return,0);
        need(r.observe(c.pc,c,w,p)==(fault==0));
        if(!fault){need(r.stage()==5&&w.stage()==8);need(!r.observe(c.pc,c,w,p));}
    }
    std::cout<<"V585_DSP_RETURN_WITNESS positive=1 refused=16 wrap=1 duplicate=1 firmware_executed=0\n";
}
