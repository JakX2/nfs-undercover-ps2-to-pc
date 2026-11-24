#include "wii_exception_pack_v462.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu{
    std::map<uint32_t,uint8_t> mem;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint8_t read8(uint32_t a)const{auto p=mem.find(a);return p==mem.end()?0:p->second;}
    uint32_t read32(uint32_t a)const{uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)mem[a+i]=uint8_t(v>>(24u-8u*i));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80520bf4u,lr=0x805208acu,msr=0x2000u;
    uint64_t inst_count=100;bool is_running=true;
    uint32_t guest_flush_count=0,guest_invalidate_count=0,guest_sync_count=0,guest_isync_count=0;
    std::array<uint32_t,256> guest_flush_lines{},guest_invalidate_lines{};
};
static void need(bool b){if(!b)throw std::runtime_error("exception pack");}
int main(){
    constexpr uint32_t table=0x8060bbe0u,source=0x80520ec0u,sys=0x805290a8u,
      sda=0x8070e8e0u,sp=0x80751c68u,sd=0x80000c00u;
    for(unsigned mode=0;mode<2;++mode)for(unsigned fault=0;fault<22;++fault){
        ExceptionPackExpectations e{};Cpu c;c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        for(unsigned i=0;i<12;++i)c.gpr[20+i]=0x12340000u+i;
        for(unsigned i=0;i<15;++i){
            unsigned index=i;
            // Different table order, same nonoverlapping valid memory.
            if(mode&&i==3)index=11;else if(mode&&i==11)index=3;
            e.offsets[i]=0x100u*(index+1);c.mmu.write32(table+4u*i,e.offsets[i]);
            const uint32_t dest=0x80000000u+e.offsets[i];
            c.mmu.mem[dest-1]=0xa5;c.mmu.mem[dest+152]=0x5a;
            for(unsigned n=0;n<152;++n)c.mmu.mem[dest+n]=0xcc;
        }
        c.mmu.write32(table+60,0xdeadbeefu);c.mmu.write32(0x8000303c,0x76543210u);
        for(unsigned i=0;i<152;++i){e.handler[i]=uint8_t(i*3u+17u);c.mmu.mem[source+i]=e.handler[i];}
        for(unsigned i=0;i<28;++i){e.syscall[i]=uint8_t(0xc7u^i);c.mmu.mem[sys+i]=e.syscall[i];}
        for(unsigned i=153;i<255;++i)c.mmu.mem[sd+i]=uint8_t(i^0x99u);
        if(fault==1)c.mmu.write32(table+4,e.offsets[0]);
        if(fault==2)c.mmu.mem[sys]++;
        if(fault==3)c.mmu.mem[source+7]++;
        if(fault==4)c.msr|=0x8000u;
        ExceptionPackWitness w(e);auto prior=c.mmu.mem;bool ok=w.begin(c);need(prior==c.mmu.mem);
        if(fault>=1&&fault<=4){need(!ok);continue;}need(ok);
        c.pc=0x80004338u;c.lr=0x80520d9cu;c.gpr[1]=sp-64u;
        c.gpr[3]=0x80000000u+e.offsets[0];c.gpr[4]=source;c.gpr[5]=152u;c.gpr[29]=0;
        c.inst_count+=100;c.guest_flush_count=mode*11u;c.guest_invalidate_count=mode*13u;
        if(fault==5)c.gpr[5]--;
        if(fault==6)c.guest_flush_count=180;
        ok=w.first_copy(c);if(fault==5||fault==6){need(!ok);continue;}need(ok);
        c.mmu.write32(source+0x58,0x60000000u);c.mmu.write32(sda-3552u,0x80003000u);
        for(unsigned i=0;i<15;++i){
            const uint32_t dest=0x80000000u+e.offsets[i];
            for(unsigned n=0;n<152;++n)c.mmu.mem[dest+n]=c.mmu.read8(source+n);
            c.mmu.mem[dest+0x6b]=uint8_t(e.handler[0x6b]|i);
            c.mmu.write32(0x80003000u+4u*i,0x80520f5cu);
            for(unsigned n=0;n<5;++n){
                c.guest_flush_lines[c.guest_flush_count++]=dest+32u*n;
                c.guest_invalidate_lines[c.guest_invalidate_count++]=dest+32u*n;
            }
            c.guest_sync_count+=2;++c.guest_isync_count;
        }
        c.pc=0x805290c8u;c.lr=0x805208b0u;c.gpr[1]=sp;c.gpr[29]=0x12340009u;c.inst_count+=1000;
        if(fault==7)c.gpr[29]++;
        if(fault==8)c.guest_flush_lines[mode*11u+7]+=32;
        if(fault==9)c.guest_sync_count--;
        if(fault==10)c.mmu.mem[0x80000000u+e.offsets[4]+33u]++;
        if(fault==11)c.mmu.mem[0x80000000u+e.offsets[5]+0x6bu]^=0x80;
        if(fault==12)c.mmu.write32(0x80003010u,0x1234u);
        if(fault==13)c.mmu.mem[source+3]++;
        if(fault==14)c.mmu.mem[sd+180]++;
        if(fault==15)c.mmu.mem[0x80000000u+e.offsets[0]-1u]++;
        prior=c.mmu.mem;ok=w.syscall_entry(c);need(prior==c.mmu.mem);
        if(fault>=7&&fault<=15){need(!ok);continue;}need(ok);
        for(unsigned n=0;n<28;++n)c.mmu.mem[sd+n]=e.syscall[n];
        for(unsigned n=0;n<8;++n){
            c.guest_flush_lines[c.guest_flush_count++]=sd+32u*n;
            c.guest_invalidate_lines[c.guest_invalidate_count++]=sd+32u*n;
        }
        c.guest_sync_count+=2;++c.guest_isync_count;c.pc=0x805210ccu;c.lr=0x805208b4u;c.inst_count+=100;
        if(fault==16)c.mmu.mem[sd+7]++;
        if(fault==17)c.mmu.mem[sd+28]++;
        if(fault==18)c.mmu.mem[sd+200]++;
        if(fault==19)c.guest_invalidate_count--;
        if(fault==20)c.lr+=4;
        if(fault==21)c.mmu.write32(0x8000303c,0);
        prior=c.mmu.mem;ok=w.alarm_entry(c);need(prior==c.mmu.mem);
        need(ok==(fault==0));if(ok){need(w.phase()==4);need(!w.alarm_entry(c));}
    }
    std::cout<<"PASS: two complete vector-table configurations, 42 negative controls and duplicate stops\n";
}
