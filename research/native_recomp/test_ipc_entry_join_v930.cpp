#include "wii_ipc_entry_join_v930.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t A=0x80004000u,B=0x80005000u,W=0x48001001u,E=0x60000000u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words{{A,W},{B,E}};uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=A,lr=A,msr=0x8032u,ctr=1,xer=2,srr0=3,srr1=4,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;uint64_t inst_count=100;
};
static void need(bool b){if(!b)throw std::runtime_error("V930 entry assertion");}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned trial=0;trial<22;++trial){
        Cpu c;IpcEntryJoinWitness join({A,B,W,E});
        c.gpr[1]=0x80020000u;c.gpr[14]=0x12345678u;c.cr[4].eq=true;c.gqr[7]=0x1234u;
        if(trial==1)c.gpr[3]=1;
        if(trial==2)c.msr&=~0x8000u;
        if(trial==3)c.mmu.words[B]^=1;
        if(trial==4)c.lr+=4;
        bool ok=join.start(c,A,W,trial!=5,trial!=6);
        if(trial>=1&&trial<=6){need(!ok&&join.failure()==1);++refused;continue;}need(ok);
        c.pc=B;c.lr=A+4;
        if(trial==7)++c.inst_count;
        if(trial==8)c.pc+=4;
        if(trial==9)c.lr+=4;
        if(trial==10)c.gpr[14]^=1;
        if(trial==11)c.gqr[7]^=1;
        if(trial==12)c.cr[4].eq=false;
        if(trial==13)c.ctr^=1;
        if(trial==14)c.xer^=1;
        if(trial==15)c.srr0^=1;
        if(trial==16)c.srr1^=1;
        if(trial==17)c.msr^=1;
        if(trial==18)c.mmu.words[B]^=1;
        if(trial==19)c.dispatch_saved_ctx=1;
        Cpu copy=c;ok=trial==20?join.entry(copy,B,true):join.entry(c,B,trial!=21);
        if(trial>=7){need(!ok&&join.failure()==2);++refused;continue;}
        need(ok&&join.stage()==2);++valid;
    }
    need(valid==1&&refused==21);
    std::cout<<"V930_IPC_ENTRY_JOIN synthetic=1 valid=1 refused=21 original_execution=0\n";
}
