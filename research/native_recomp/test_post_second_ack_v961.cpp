#include "wii_second_completion_ack_v950.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t A=0x80004000u,Other=0x100u,SI=8u,Base=0xcd006400u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer;
constexpr uint32_t Load=0x80830034u,Store=0x90830034u,Status=0x90830038u,Buffer=0x90830080u,Nop=0x60000000u;
struct Mmu{
    std::map<uint32_t,uint32_t> words{{A,Load},{A+4,Store},{A+8,Status},{A+12,Buffer},{A+16,Load},{A+20,Nop},{A+24,Store}};
    uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint64_t inst_count=100;
    uint32_t msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;
};
static unsigned trial=0;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b){std::cerr<<"V961_ASSERT trial="<<trial<<" line="<<loc.line()<<std::endl;throw std::runtime_error("post ACK");}
}
int main(){
    unsigned valid=0,refused=0,additional=0;
    for(trial=0;trial<22;++trial){
        const unsigned fault=trial<8?0:trial-7,ch=trial%4;
        std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);SecondCompletionAck w;Cpu c;
        const uint32_t cfg=SiController::TC_MASK|0x00010300u|(ch<<1);
        const std::array<uint8_t,3> response{9,0,0};
        ctl.write(C,cfg|SiController::TSTART);ctl.complete(ctl.pending()->token,response);
        ctl.write(C,cfg|SiController::TC_INT);
        ctl.write(C,cfg|SiController::TSTART);
        if(trial&4u)ctl.complete(ctl.pending()->token,{},SiController::ERR_NOREP);else ctl.complete(ctl.pending()->token,response);
        c.gpr[3]=Base;need(w.arm(ctl,cause,mask,c.inst_count,2,true));
        uint32_t v=0;
        auto step=[&](uint32_t pc,uint32_t word){++c.inst_count;return w.before(c,pc,word,true);};
        need(step(A,Load)&&w.read(ctl,C,v));c.gpr[4]=v;
        need(step(A+4,Store)&&w.write(ctl,C,v)&&w.stage()==2);
        need(step(A+8,Status)&&w.stage()==3&&cause==Other);
        c.gpr[4]=0xfu<<((3u-ch)*8u);
        if(fault==1)++c.inst_count;
        if(fault==2)c.msr|=0x8000u;
        if(fault==3)mask=0;
        if(fault==4)ctl.write(B,0x12345678u);
        if(fault==13)c.mmu.words[A+8]=Nop;
        bool ok=w.resume_after_ack(c,fault==5?A+12:A+8,(fault==6||fault==13)?Nop:Status);
        if(fault==13){need(!ok&&w.failure()==5&&w.stage()==3&&ctl.issued_tokens()==2&&cause==Other);++additional;continue;}
        if(fault>=1&&fault<=6){need(!ok&&w.failure()==5);++refused;continue;}
        need(ok&&w.stage()==4&&!w.postack_held());
        if(fault==7){need(!w.resume_after_ack(c,A+8,Status));++refused;continue;}
        const auto status=ctl.read(S);
        ok=w.write(ctl,S,c.gpr[4]^(fault==8?1u:0u));
        if(fault==8){need(!ok&&ctl.read(S)==status);++refused;continue;}
        need(ok&&ctl.read(S)==(status&~c.gpr[4])&&w.postack_held());
        c.gpr[4]=0x12345678u;
        need(step(A+12,Buffer));
        if(fault==9){need(!step(A+16,Load));++refused;continue;}
        ok=w.write(ctl,B,c.gpr[4]^(fault==10?1u:0u));
        if(fault==10){need(!ok);++refused;continue;}need(ok&&ctl.read(B)==c.gpr[4]);
        need(step(A+16,Load)&&w.read(ctl,C,v)&&v==ctl.read(C)&&!(v&SiController::TC_INT));
        if(fault==11)cause|=0x200u;
        ok=step(A+20,Nop);
        if(fault==11){need(!ok);++refused;continue;}need(ok&&w.postack_held());
        if(fault==12){
            c.gpr[4]=v|SiController::TSTART;
            need(step(A+24,Store)&&!w.write(ctl,C,c.gpr[4])&&!ctl.pending()&&ctl.issued_tokens()==2);
            ++refused;continue;
        }
        need(w.reads()==2u&&w.writes()==3u&&w.token()==2u&&cause==Other&&mask==SI&&w.poll(c.inst_count));
        if(fault==14){const auto tick=c.inst_count;++c.inst_count;need(!w.poll(tick)&&!w.postack_held());++additional;continue;}
        ++valid;
    }
    need(valid==8&&refused==12&&additional==2);
    std::cout<<"V961_POST_SECOND_ACK valid=8 refused=12 real_device=1 original_execution=0\n";
    std::cout<<"V993_SUCCESSOR_BINDING changed_word_refused=1 stale_poll_refused=1 original_execution=0\n";
}
