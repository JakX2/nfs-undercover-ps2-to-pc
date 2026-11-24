#include "wii_exception_vector_witness_v457.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu {
    std::map<uint32_t,uint8_t> mem;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint8_t read8(uint32_t a) const {auto i=mem.find(a);return i==mem.end()?0:i->second;}
    uint32_t read32(uint32_t a) const {uint32_t w=0;for(unsigned i=0;i<4;++i)w=(w<<8)|read8(a+i);return w;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)mem[a+i]=uint8_t(v>>(24u-8u*i));}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80520bf4u,lr=0x805208acu,msr=0x2000u;
    uint64_t inst_count=100;bool is_running=true;
    uint32_t guest_flush_count=8,guest_invalidate_count=9,guest_sync_count=6,guest_isync_count=7;
    std::array<uint32_t,256> guest_flush_lines{},guest_invalidate_lines{};
};
static void need(bool b){if(!b)throw std::runtime_error("first-vector witness");}
int main(){
    constexpr uint32_t src=0x80520ec0u,table=0x8060bbe0u,sp=0x80751c68u,sda=0x8070e8e0u;
    for(unsigned mode=0;mode<2;++mode)for(unsigned fault=0;fault<18;++fault){
        VectorExpectations e{};
        e.count=5;e.edges[0]={0x805450e8u,0x80520c08u,1,2};
        e.edges[1]={0x804e50b8u,0x80520c48u,3,4};
        e.edges[2]={0x80004338u,0x80520d9cu,5,6};
        e.edges[3]={0x80522320u,0x80520da8u,7,8};
        e.edges[4]={0x80522378u,0x80520db8u,9,10};e.stop_word=11;
        const uint32_t dest=0x80000100u+mode*0x100u;
        Cpu c;c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        for(unsigned i=0;i<15;++i){e.offsets[i]=0x100u*(i+1+mode);c.mmu.write32(table+4u*i,e.offsets[i]);}
        for(unsigned i=0;i<152;++i){e.handler[i]=uint8_t(i^0x9du);c.mmu.mem[src+i]=e.handler[i];}
        for(unsigned i=0;i<e.count;++i){auto x=e.edges[i];c.mmu.write32(x.pc,x.entry_word);c.mmu.write32(x.lr-4u,x.branch_word);}
        c.mmu.write32(0x80520db8u,e.stop_word);
        c.mmu.write32(0x80000060u,mode);c.mmu.write32(sda-4160u,0x80000040u);
        c.mmu.write32(0x80000044u,0);c.mmu.mem[dest-1u]=0xa6;c.mmu.mem[dest+152u]=0xa7;
        if(fault==1)c.mmu.mem[src]++;
        if(fault==2)c.mmu.write32(table,0x101u);
        if(fault==3)c.msr|=0x8000u;
        FirstVectorWitness w(e);auto prior=c.mmu.mem;bool ok=w.begin(c);need(prior==c.mmu.mem);
        if(fault>=1&&fault<=3){need(!ok);continue;}
        need(ok&&w.debug_needed()==(mode==0));
        c.gpr[1]=sp-64u;
        auto edge=[&](unsigned i){
            c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;c.inst_count+=10;
            prior=c.mmu.mem;bool accepted=w.observe(c.pc,c);need(prior==c.mmu.mem);return accepted;
        };
        if(fault==4)c.gpr[1]-=4;
        ok=edge(0);if(fault==4){need(!ok);continue;}need(ok);
        if(mode==0)need(edge(1));
        c.mmu.write32(sp+4u,0x805208acu);c.mmu.write32(src+0x58u,0x60000000u);
        c.gpr[3]=dest;c.gpr[4]=src;c.gpr[5]=152u;c.gpr[29]=0;
        if(fault==5)c.gpr[3]+=32;
        if(fault==6)c.mmu.write32(0x80000044u,1);
        if(fault==7)c.mmu.mem[src+0x5b]++;
        if(fault==8)c.guest_flush_count=254;
        if(fault==9)c.gpr[29]=1;
        ok=edge(2);if(fault>=5&&fault<=9){need(!ok);continue;}need(ok&&w.stage()==1);
        for(unsigned i=0;i<152;++i)c.mmu.mem[dest+i]=c.mmu.read8(src+i);
        c.gpr[3]=dest;c.gpr[4]=152;
        if(fault==10)c.mmu.mem[dest+100u]++;
        if(fault==11)c.mmu.mem[dest+152u]++;
        if(fault==12)c.guest_sync_count++;
        ok=edge(3);if(fault>=10&&fault<=12){need(!ok);continue;}need(ok&&w.stage()==2);
        for(unsigned i=0;i<5;++i)c.guest_flush_lines[c.guest_flush_count++]=dest+32u*i;
        ++c.guest_sync_count;
        if(fault==13)c.guest_flush_lines[9]+=32;
        if(fault==14)c.guest_flush_count--;
        ok=edge(4);if(fault>=13&&fault<=14){need(!ok);continue;}need(ok&&w.stage()==3);
        for(unsigned i=0;i<5;++i)c.guest_invalidate_lines[c.guest_invalidate_count++]=dest+32u*i;
        ++c.guest_sync_count;++c.guest_isync_count;
        c.pc=c.lr=0x80520db8u;c.inst_count+=10;
        if(fault==15)c.guest_invalidate_lines[10]+=32;
        if(fault==16)c.guest_isync_count--;
        if(fault==17)c.mmu.mem[src+3]++;
        prior=c.mmu.mem;ok=w.observe(c.pc,c);need(prior==c.mmu.mem);
        need(ok==(fault==0));if(ok){need(w.stage()==4&&!w.active());need(!w.observe(c.pc,c));}
    }
    std::cout<<"PASS: two first-vector paths, 34 negative controls and duplicate stops\n";
}
