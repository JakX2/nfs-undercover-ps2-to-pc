#include "wii_transfer_prefix_v768.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,B=0x80005000u,S=0x80006000u,D=0x80008000u,Q=0x80009000u,Data=0x80010000u,Frame=0x80020000u;
constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,Store=0x90030000u,Li=0x38600000u,Mtmsr=0x7d400124u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
    uint8_t read8(uint32_t a){return uint8_t(read32(a&~3u)>>(24u-8u*(a&3u)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint64_t inst_count=100;
    uint32_t pc=H,lr=0x80030000u,msr=0x32u,dispatch_saved_ctx=0,ctr=4,srr0=0x80007000u,srr1=0x8032u,xer=0;
    bool is_running=true,in_callback=false;
};
static void need(bool b,unsigned line=0){if(!b){std::cerr<<"V769_ASSERT line="<<line<<"\n";throw std::runtime_error("prefix");}}
#define CHECK(x) need((x),__LINE__)
int main(){
    unsigned valid=0,rejected=0;
    for(unsigned trial=0;trial<13;++trial){
        std::atomic<uint32_t> cause{0x100u},mask{8u};SiController ctl(cause);
        ctl.write(SiController::Control,0xc0010301u);ctl.complete(ctl.pending()->token,{},SiController::ERR_NOREP);
        Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*123u+7u;
        c.gpr[1]=Frame;c.gpr[11]=Frame;c.gpr[3]=trial%4;c.gpr[4]=Data+4;c.gpr[5]=1;c.gpr[6]=Data+8;c.gpr[7]=3;c.gpr[8]=Q;c.gpr[9]=0xcd006434u;c.gpr[10]=c.msr;
        c.mmu.words={{Data,trial%2?0u:0xffffffffu},{Data+4,0},{B,bl(B,S)},{B+4,bl(B+4,D)},
                     {B+8,trial==1?0x90090000u:trial==2?bl(B+8,Q):0x80090000u},{D,Li},{D+4,Mtmsr},{D+8,Blr}};
        for(unsigned i=0;i<6;++i)c.mmu.words[S+4*i]=(36u<<26)|((26u+i)<<21)|(11u<<16)|(uint32_t(-24+int(i)*4)&0xffffu);
        c.mmu.words[S+24]=Blr;
        SiCompletionAckTrace ack;
        CHECK(ack.arm(ctl,cause,mask,c.inst_count,H,H+32));
        ++c.inst_count;CHECK(ack.before(H,Store));ack.write(ctl,SiController::Control,0xe0010300u);
        ++c.inst_count;CHECK(ack.before(H+4,Nop)&&ack.resume_after_ack(H+4,Nop));
        ++c.inst_count;CHECK(ack.before(H+8,bl(H+8,B)));
        TransferPrefixWitness w({H+8,B,B+12,bl(H+8,B),bl(B,S),
            {B,S,S+28,bl(B,S),26,11,-24},{B+4,D,D+12,bl(B+4,D),1},Data});
        if(trial==3)c.gpr[5]=2;
        if(trial==4)c.gpr[4]=0xcd006434u;
        if(trial==5)c.gpr[3]=4;
        const bool started=w.start(c,H+8,bl(H+8,B),ack);
        if(trial>=3&&trial<=5){CHECK(!started&&w.failure()==1);++rejected;continue;}CHECK(started);
        c.pc=B;c.lr=H+12;
        if(trial==6)c.lr^=4;
        const bool entered=w.entry(c,B,ack);
        if(trial==6){CHECK(!entered&&w.failure()==2);++rejected;continue;}CHECK(entered);
        ++c.inst_count;CHECK(w.before(c,B,bl(B,S),ack));
        c.pc=S;c.lr=B+4;CHECK(w.entry(c,S,ack));
        for(unsigned i=0;i<6;++i){
            ++c.inst_count;CHECK(w.save_before(c,S+4*i,c.mmu.words[S+4*i],ack));
            c.mmu.words[Frame-24+4*i]=c.gpr[26+i];
        }
        ++c.inst_count;CHECK(w.save_before(c,S+24,Blr,ack));
        c.pc=B+4;++c.inst_count;
        if(trial==7)c.mmu.words[Frame-4]^=1;
        const bool save=w.before(c,B+4,bl(B+4,D),ack);
        if(trial==7){CHECK(!save&&w.failure()==4);++rejected;continue;}CHECK(save&&w.save_done());
        c.pc=D;c.lr=B+8;CHECK(w.entry(c,D,ack));
        ++c.inst_count;CHECK(w.disable_before(c,D,Li,ack));c.gpr[3]=0;
        ++c.inst_count;if(trial==8)c.gpr[10]|=0x8000;
        const bool msr=w.disable_before(c,D+4,Mtmsr,ack);
        if(trial==8){CHECK(!msr&&w.failure()==4);++rejected;continue;}CHECK(msr);
        ++c.inst_count;CHECK(w.disable_before(c,D+8,Blr,ack));
        c.pc=B+8;++c.inst_count;
        if(trial==9)c.gpr[9]=0xcc003000u;
        if(trial==10)++c.inst_count;
        if(trial==11)c.msr|=0x8000u;
        if(trial==12)cause|=0x200u;
        const bool boundary=w.before(c,B+8,c.mmu.words[B+8],ack);
        if(trial>=9){CHECK(!boundary);++rejected;continue;}
        CHECK(boundary&&w.stage()==3&&w.save_done()&&w.disable_done()&&w.stop()==trial+1&&w.visits()==3);
        CHECK(!ctl.pending()&&ctl.issued_tokens()==1&&cause==0x100u&&mask==8u&&ack.postack_held());++valid;
    }
    CHECK(valid==3&&rejected==10);
    std::cout<<"V769_TRANSFER_PREFIX synthetic=1 valid=3 refused=10 actual_device=1 mmio_executed=0 original_execution=0\n";
}
