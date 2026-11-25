#include "wii_gpr_restore_v736.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,L=0x80005000u,Frame=0x80010000u,Call=0x48001001u,Blr=0x4e800020u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=0x80006000u,msr=0x32u,srr0=0x80007000u,srr1=0x8032u,ctr=5,xer=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("V736 restore witness assertion");}
int main(){
    unsigned valid=0,rejected=0;
    for(unsigned trial=0;trial<20;++trial){
        Cpu c;const unsigned first=trial==1?14u:trial==2?31u:17u,base=trial==1?1u:11u;
        const int32_t disp=-4*int32_t(32u-first);
        for(unsigned i=0;i<32;++i)c.gpr[i]=i*13u+9u;
        c.gpr[base]=Frame;auto original=c.gpr;c.mmu.words[H]=Call;
        for(unsigned i=first;i<32;++i){
            original[i]^=0x12345678u;
            c.mmu.words[Frame+disp+4u*(i-first)]=original[i];
            c.mmu.words[L+4u*(i-first)]=(32u<<26)|(i<<21)|(base<<16)|(uint32_t(disp+4*int32_t(i-first))&0xffffu);
        }
        c.mmu.words[L+4u*(32u-first)]=Blr;
        GprRestoreExpectation e{H,L,Call,first,base,disp};
        if(trial==3)e.branch^=4u;
        if(trial==4)e.base=3;
        if(trial==5)c.mmu.words[Frame+disp]^=1u;
        if(trial==6)c.gpr[base]=0xcd000000u;
        GprRestoreWitness w(e);
        const bool started=w.start(c,H,Call,original);
        if(trial>=3&&trial<=6){need(!started);++rejected;continue;}
        need(started);
        c.pc=L;c.lr=H+4u;
        if(trial==7)c.lr^=4u;
        if(trial==8)++c.inst_count;
        if(trial==9)c.gpr[4]^=1u;
        const bool entered=w.entry(c,L);
        if(trial>=7&&trial<=9){need(!entered);++rejected;continue;}
        need(entered);
        bool refused=false;
        for(unsigned i=0;i<=32u-first;++i){
            ++c.inst_count;const uint32_t pc=L+4u*i;uint32_t word=c.mmu.read32(pc);
            if(i==1){
                if(trial==10)c.gpr[first]^=1u;
                if(trial==11)c.mmu.words[Frame+disp+4u]^=1u;
                if(trial==12)c.msr|=0x8000u;
                if(trial==13)c.cr[0].eq=true;
                if(trial==14)c.xer^=1u;
                if(trial==15)++c.inst_count;
                if(trial==16){word^=4u;c.mmu.words[pc]=word;}
            }
            const bool ok=w.before(c,pc,word);
            if(i==1&&trial>=10&&trial<=16){need(!ok);++rejected;refused=true;break;}
            need(ok);
            if(i<32u-first)c.gpr[first+i]=original[first+i]; // synthetic native-effect model
        }
        if(refused)continue;
        ++c.inst_count;c.pc=H+4u;
        if(trial==17)c.pc=H+8u;
        if(trial==18)c.gpr[31]^=1u;
        if(trial==19)++c.inst_count;
        const bool returned=w.returned(c,c.pc);
        if(trial>=17){need(!returned);++rejected;continue;}
        need(returned&&w.stage()==4&&w.visits()==33u-first);++valid;
    }
    need(valid==3&&rejected==17);
    std::cout<<"V736_GPR_RESTORE synthetic=1 valid=3 refused=17 original_execution=0\n";
}
