#include "wii_dsp_stage_witness_v559.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("DSP staging line "+std::to_string(loc.line()));
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
    bool is_running=true;uint64_t inst_count=100;
    std::array<uint32_t,256> guest_flush_lines{};unsigned guest_flush_count=83;
};
int main(){
    using W=DspStageWitness;
    constexpr uint32_t backup=0x816fff80u,sp=ThreadInitWitness::StackTop-104u;
    DspStageExpectations e{{{{0x80521d28,0x80522014,1,2},{0x80004338,0x80522024,3,4},
        {0x80004338,0x80522038,5,4},{0x805222c0,0x80522044,6,7}}},{},0x44000002u};
    for(unsigned i=0;i<128;++i)e.image[i]=uint8_t(i*17+9);
    for(unsigned fault=0;fault<=30;++fault){
        Cpu c;auto& m=c.mmu;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;c.lr=AudioResetWitness::Return;
        for(auto x:e.edges){m.write32(x.pc,x.entry_word);m.write32(x.lr-4,x.branch_word);}
        m.write32(W::Syscall,e.syscall_word);m.write32(c.gpr[13]-3472,0x81700000u);
        m.write32(0x800000e4u,ThreadInitWitness::Thread);
        std::array<uint8_t,128> initial{};
        for(unsigned i=0;i<128;++i){
            initial[i]=uint8_t(i*13+7);m.mem[W::Staging+i]=initial[i];
            m.mem[W::Source+i]=e.image[i];m.mem[backup+i]=0x5c;
        }
        for(auto a:{W::Staging,backup}){m.mem[a-1]=0xa1;m.mem[a+128]=0xb2;}
        if(fault==1)m.mem[W::Source]^=1;
        if(fault==2)m.write32(c.gpr[13]-3472,0x81700020u);
        if(fault==3)c.guest_flush_count=253;
        W w(e);need(w.begin(c)==!(fault>=1&&fault<=3));
        if(fault>=1&&fault<=3)continue;
        bool rejected=false;
        for(unsigned i=0;i<4;++i){
            c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;c.inst_count+=10;
            bool bad=false;
            if(i==0){if(fault==4)c.lr^=4;bad=fault==4;}
            if(i==1){c.gpr[3]=backup;c.gpr[4]=W::Staging;c.gpr[5]=fault==5?64:128;bad=fault==5;}
            if(i==2){
                for(unsigned j=0;j<128;++j)m.mem[backup+j]=initial[j];
                if(fault==6)m.mem[backup+7]^=1;
                if(fault==7)m.mem[W::Staging-1]^=1;
                c.gpr[3]=W::Staging;c.gpr[4]=W::Source;c.gpr[5]=128;bad=fault==6||fault==7;
            }
            if(i==3){
                for(unsigned j=0;j<128;++j)m.mem[W::Staging+j]=e.image[j];
                if(fault==8)m.mem[W::Staging+127]^=1;
                c.gpr[3]=W::Staging;c.gpr[4]=fault==9?96:128;
                if(fault==10)++c.guest_flush_count;
                bad=fault>=8&&fault<=10;
            }
            need(w.observe(c.pc,c)==!bad);if(bad){rejected=true;break;}
        }
        if(rejected)continue;
        for(unsigned i=0;i<4;++i)c.guest_flush_lines[c.guest_flush_count++]=W::Staging+32*i;
        c.inst_count+=100;
        if(fault==11)c.guest_flush_lines[84]+=32;
        if(fault==12)--c.guest_flush_count;
        if(fault==13)m.mem[W::Source+7]^=1;
        if(fault==14)m.mem[backup+128]^=1;
        if(fault==15)c.gpr[1]-=4;
        if(fault==16)c.lr^=4;
        if(fault==17)m.write32(W::Syscall,0);
        need(w.observe(fault==18?W::Syscall+4:W::Syscall,c)==(fault==0||fault>18));
        if(fault>=1&&fault<=18)continue;
        need(w.stage()==6);
        c.pc=c.lr=e.edges[3].lr;c.inst_count+=9;
        const uint32_t ret=0x60000000u;m.write32(c.pc,ret);
        if(fault==19)c.pc+=4;
        if(fault==20)c.lr+=4;
        if(fault==21)c.inst_count++;
        if(fault==22)c.gpr[2]^=4;
        if(fault==23)c.gpr[13]^=4;
        if(fault==24)c.msr^=2;
        if(fault==25)m.mem[W::Staging+1]^=1;
        if(fault==26)m.mem[backup+1]^=1;
        if(fault==27)m.mem[backup-1]^=1;
        if(fault==28)++c.guest_flush_count;
        if(fault==29)m.write32(c.pc,0);
        if(fault==30)m.write32(0x800000e4u,0);
        need(w.finish_sc(e.edges[3].lr,c,ret)==(fault==0));
        if(!fault){need(w.stage()==7);need(!w.finish_sc(e.edges[3].lr,c,ret));}

    }
    std::cout<<"PASS: original-free DSP staging witness, 128-byte image and backup, four cache lines, 30 negative controls, original SC return boundary\n";
}
