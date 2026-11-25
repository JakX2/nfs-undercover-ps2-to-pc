#include "wii_si_handler_return_v725.h"
#include <iostream>
#include <map>
#include <stdexcept>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,Nop=0x60000000u,Blr=0x4e800020u,
    Call=0x48000101u,Indirect=0x4e800421u,Start=H+4u,Site=H+8u,Back=Site+4u;
struct Cpu {
    struct Cr{bool lt=false,gt=false,eq=false,so=false;};
    struct Mmu{
        std::map<uint32_t,uint32_t> words{{H,Nop},{Start,Call},{Site,Indirect},{Back,Nop},{H+16,Blr},{R,Nop}};
        uint8_t b=0;
        uint8_t* get_ptr(uint32_t a){return (a>=H&&a<H+20u)||(a>=R&&a<R+4u)?&b:nullptr;}
        uint32_t read32(uint32_t a){return words.at(a);}
    }mmu;
    std::array<uint32_t,32> gpr{};
    std::array<Cr,8> cr{};
    uint32_t pc=H,lr=R,msr=0x32,srr0=0x80006000,srr1=0x8032,ctr=0,xer=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false,dispatch_saved_ctx=false;
};
static void need(bool ok,const std::source_location l=std::source_location::current()){
    if(!ok){std::cerr<<"V865_ASSERT line="<<l.line()<<'\n';throw std::runtime_error("callback join");}
}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned trial=0;trial<20;++trial){
        Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*17u+7u;
        SiHandlerReturnWitness w({H,H+20u,Start,R,Nop});
        need(w.capture(c));
        c.pc=c.lr=Start;c.inst_count+=50;
        need(w.start(c,Start,true));
        need(w.before_authenticated(c,Start,Call,true,5u));
        c.pc=c.lr=Site;c.inst_count+=11;
        need(w.alarm_returned(c,Site,10,true)&&w.completed_calls()==16u);
        const unsigned slot=trial%2?6u:11u;
        if(trial==4){
            c.mmu.words[Site]=Call;
            need(w.before_authenticated(c,Site,Call,true,slot)&&!w.callback_pending());
            c.pc=c.lr=Back;c.inst_count+=200;
            need(!w.callback_returned(c,Back,c.inst_count-200,true,true,slot)&&w.failure()==8);
            ++refused;continue;
        }
        need(w.before_authenticated_indirect(c,Site,Indirect,true,slot)&&w.callback_pending()&&w.active_call()==slot);
        const uint64_t at=c.inst_count;
        c.pc=c.lr=Back;c.inst_count+=trial==0?14u:trial==1?16385u:trial==2?3500u:trial==3?4000u:200u;
        if(trial==5)c.inst_count=at+13u;
        if(trial==6)c.inst_count=at+16386u;
        if(trial==7)c.pc=Back+4u;
        if(trial==8)c.lr=Back+4u;
        if(trial==9)c.msr|=0x8000u;
        if(trial==10)c.srr0^=4u;
        if(trial==11){
            need(!w.helper_returned(c,Back,199u,true,slot)&&w.failure()==8);++refused;continue;
        }
        if(trial==12){
            need(!w.before(c,Back,Nop,true)&&w.failure()==3);++refused;continue;
        }
        const bool ok=w.callback_returned(c,trial==13?Back+4u:Back,at+unsigned(trial==14),trial!=15,trial!=16,trial==17?(slot==6?11u:6u):slot);
        if(trial>=5&&trial<=17){
            need(!ok&&w.failure()==8&&w.callback_pending()&&w.completed_calls()==16u);++refused;continue;
        }
        need(ok&&!w.callback_pending()&&!w.active_call()&&w.completed_calls()==(16u|(1u<<(slot-1u))));
        if(trial==18){need(!w.callback_returned(c,Back,at,true,true,slot)&&w.failure()==8);++refused;continue;}
        if(trial==19){++c.inst_count;need(!w.before(c,Back,Nop,true)&&w.failure()==3);++refused;continue;}
        // Caller label is still unexecuted and must be observed at the
        // exact same real tick. Its successor gets one further tick.
        need(w.before(c,Back,Nop,true));
        ++c.inst_count;c.pc=H+16;c.lr=R;
        need(w.before(c,H+16,Blr,true)&&w.stage()==3u);
        c.pc=R;need(w.poll(c,true));
        c.inst_count+=2;need(w.resumed(c,R,Nop,true)&&w.stage()==5u);
        ++valid;
    }
    need(valid==4&&refused==16);
    std::cout<<"V865_HANDLER_CALLBACK_JOIN valid="<<valid<<" refused="<<refused<<" both_slots=1 same_tick=1 original_execution=0\n";
}
