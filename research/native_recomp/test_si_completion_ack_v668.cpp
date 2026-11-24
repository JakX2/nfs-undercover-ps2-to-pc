#include "wii_si_completion_ack_v668.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
using Trace=SiCompletionAckTrace;
constexpr uint32_t First=0x80004000u,Other=0x100u,SI=SiController::PI_SI;
constexpr uint32_t Store=0x90030000u,Nop=0x60000000u;
static void need(bool ok){if(!ok)throw std::runtime_error("V668 assertion");}
template<class F>static void reject(F f){bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}need(caught);}
int main(){
    using Port=SiTypeScheduler::Port;
    need(Trace::word_store(Store)&&Trace::word_store(0x94030004u)&&
         Trace::word_store((31u<<26)|(151u<<1))&&!Trace::word_store(Nop)&&
         !Trace::word_store(0x80030000u));
    for(unsigned trial=0;trial<14;++trial){
        std::atomic<uint32_t> cause{Other},mask{SI};
        SiController ctl(cause);SiTypeScheduler sched(ctl,{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
        ctl.write(SiController::Control,0xc0010301u);sched.advance(1);sched.advance(9);
        need(sched.completed()==1&&cause==(Other|SI)&&ctl.read(SiController::Control)==0xe0010300u);
        uint64_t tick=100;Trace w;
        if(trial==2)mask=SI|Other;
        if(trial==3)ctl.write(SiController::Status,0x08000000u);
        if(trial==4)tick=UINT64_MAX-2;
        bool armed=w.arm(ctl,cause,mask,tick,First,First+32u);
        if(trial>=2&&trial<=4){need(!armed&&w.failure()==1);continue;}need(armed);
        ++tick;
        if(trial==5){need(!w.before(First+32u,Store)&&w.failure()==2);continue;}
        if(trial==6)cause.fetch_or(0x200u);
        if(trial==6){need(!w.before(First,Store)&&w.failure()==4);continue;}
        need(w.before(First,trial==7?Nop:Store));
        if(trial==7){reject([&]{w.write(ctl,SiController::Control,0xe0010300u);});need(cause==(Other|SI));continue;}
        if(trial==8){++tick;reject([&]{w.write(ctl,SiController::Control,0xe0010300u);});need(cause==(Other|SI));continue;}
        if(trial==9){reject([&]{w.write(ctl,SiController::Control,0xe0010301u);});need(cause==(Other|SI));continue;}
        if(trial==10){reject([&]{w.write(ctl,SiController::Control,0x80010300u);});need(cause==(Other|SI));continue;}
        uint32_t pc=First;
        if(trial==0){
            w.write(ctl,SiController::Status,0x08000000u);
            need(ctl.read(SiController::Status)==0&&cause==(Other|SI));
            ++tick;pc+=4;need(w.before(pc,Store));
        }
        // This is the original-free test's explicit simulated guest store;
        // no host write to the PI cause is used to clear the source.
        w.write(ctl,SiController::Control,0xe0010300u);
        need(w.phase()==Trace::Phase::Acknowledged&&w.store_pc()==pc&&
             w.writes()==(trial==0?2u:1u)&&cause==Other&&mask==SI&&!ctl.pending());
        if(trial==11){++tick;need(!w.before(pc+8u,Nop)&&w.failure()==3);continue;}
        if(trial==12){tick+=2;need(!w.before(pc+4u,Nop)&&w.failure()==3);continue;}
        if(trial==13)cause.fetch_or(0x200u);
        ++tick;
        const bool ok=w.before(pc+4u,Nop);
        if(trial==13){need(!ok&&w.failure()==3);continue;}
        need(ok&&w.phase()==Trace::Phase::Complete);
        need(!(ctl.read(SiController::Control)&SiController::TC_INT));
        need(ctl.read(SiController::Status)==(trial==0?0u:0x08000000u));
    }
    // Default inactive observer delegates real MMIO without restrictions.
    std::atomic<uint32_t> cause{Other};SiController ctl(cause);Trace idle;
    idle.write(ctl,SiController::Buffer,0x12345678u);
    need(ctl.read(SiController::Buffer)==0x12345678u&&idle.phase()==Trace::Phase::Idle);
    std::cout<<"V668_SI_ACK synthetic=1 valid=2 rejects=12 actual_device=1 original_execution=0\n";
}
