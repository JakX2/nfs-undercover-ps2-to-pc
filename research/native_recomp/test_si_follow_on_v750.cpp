#include "wii_si_follow_on_v750.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
static void need(bool ok){if(!ok)throw std::runtime_error("V750 follow-on assertion");}
int main(){
    using Port=SiTypeScheduler::Port;
    constexpr auto C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
    unsigned valid=0,rejected=0;
    for(unsigned trial=0;trial<24;++trial){
        std::atomic<uint32_t> cause{0x100u},mask{SI};
        SiController ctl(cause);
        const SiTypeScheduler::Profile profile{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler sched(ctl,profile,8);
        // Real first transaction and guest-style W1C, not a fabricated PI clear.
        ctl.write(C,0xc0010301u);sched.advance(1);sched.advance(9);
        need(cause==(0x100u|SI));ctl.write(C,0xe0010300u);need(cause==0x100u);
        for(unsigned i=0;i<32;++i)ctl.write(B+4*i,i?0x12345678u+i:0x00abcdefu);
        unsigned ch=trial%4;uint32_t v=0xc0010301u|(ch<<1);
        if(trial==4)v^=2u;
        if(trial==5)v^=0x10000u;
        if(trial==6)v^=SiController::TC_MASK;
        if(trial==7)ctl.write(B,0x01abcdefu);
        if(trial==8)mask=0;
        if(trial==9)cause|=SI;
        if(trial==10)v|=SiController::RDST_MASK;
        uint64_t tick=100;SiFollowOnWitness w;
        bool ok=w.arm(ctl,cause,mask,tick,v,ch,profile[ch].type,trial==11?0u:8u);
        if(trial>=4&&trial<=11){need(!ok&&w.failure()==1&&!ctl.pending());++rejected;continue;}need(ok);
        if(trial==12){need(!w.started(tick)&&w.failure()==2);++rejected;continue;}
        ctl.write(C,v);
        if(trial==13)++tick;
        if(trial==14)mask|=0x100u;
        if(trial==15)cause|=0x200u;
        ok=w.started(tick);
        if(trial>=13&&trial<=15){need(!ok&&w.failure()==2);++rejected;continue;}need(ok&&w.token()==2);
        if(trial==16){++tick;ctl.complete(w.token(),{},SiController::ERR_NOREP);need(!w.observe(tick)&&w.failure()==5);++rejected;continue;}
        if(trial==17){tick+=2;need(!w.observe(tick)&&w.failure()==3);++rejected;continue;}
        if(trial==18){++tick;cause|=SI;need(!w.observe(tick)&&w.failure()==4);++rejected;continue;}
        if(trial==19){++tick;ctl.write(C,v&~(SiController::TSTART|SiController::TC_MASK));need(!w.observe(tick)&&w.failure()==4);++rejected;continue;}
        for(unsigned i=1;i<=9;++i){
            ++tick;sched.advance(tick);
            if(i==9){
                if(trial==20)ctl.write(S,0x08000000u);
                if(trial==21)ctl.write(B+4,0u);
                if(trial==22)ctl.write(C,SiController::TC_INT);
                if(trial==23){ctl.write(B,0);ctl.write(C,v);}
            }
            ok=w.observe(tick);
            if(i==9&&trial>=20){need(!ok);++rejected;break;}
            need(ok&&w.stage()==(i==9?3u:2u)&&sched.completed()==(i==9?2u:1u));
        }
        if(trial<4){need(w.stage()==3&&w.failure()==0);++valid;}
    }
    need(valid==4&&rejected==20);
    std::cout<<"V750_SI_FOLLOW_ON synthetic=1 valid=4 refused=20 real_device=1 real_scheduler=1 original_execution=0\n";
}
