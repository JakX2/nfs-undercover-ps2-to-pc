#include "wii_second_completion_ack_v950.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t H=0x80004000u,Other=0x100u,Base=0xcd006400u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
constexpr uint32_t Load=0x80830034u,Store=0x90830034u,Nop=0x60000000u;
struct Mmu{
    std::map<uint32_t,uint32_t> words{{H,Load},{H+4,Store},{H+8,Nop},{H+12,Load}};
    uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint64_t inst_count=100;
    uint32_t msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;
};
static unsigned trial=0;
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(!ok){std::cerr<<"V969_ASSERT trial="<<trial<<" line="<<loc.line()<<std::endl;throw std::runtime_error("third token");}
}
int main(){
    unsigned valid=0,refused=0;
    for(trial=0;trial<20;++trial){
        const unsigned f=trial<8?0:trial-7,ch=trial%4;
        const bool idle=trial<4||f;
        std::atomic<uint32_t> cause{Other},mask{SI},foreign_cause{Other},foreign_mask{SI};SiController ctl(cause),foreign(foreign_cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler scheduler(ctl,ports,8);
        const uint32_t cfg=0x40010300u|(ch<<1);
        ctl.write(C,cfg|1u);scheduler.advance(1);scheduler.advance(9);
        ctl.write(C,cfg|SiController::TC_INT);ctl.write(C,cfg|1u);scheduler.advance(10);scheduler.advance(18);
        Cpu c;auto& tick=c.inst_count;SecondCompletionAck ack;PostAckTransferDevice third;
        c.gpr[3]=Base;need(ack.arm(ctl,cause,mask,tick,2,true));
        scheduler.advance(++tick);need(ack.before(c,H,Load,true));uint32_t v=0;
        need(ack.read(ctl,C,v));c.gpr[4]=v;
        scheduler.advance(++tick);need(ack.before(c,H+4,Store,true)&&ack.write(ctl,C,v));
        scheduler.advance(++tick);need(ack.before(c,H+8,Nop,true)&&ack.stage()==3);
        if(f!=1)need(ack.resume_after_ack(c,H+8,Nop));
        const uint64_t copy=tick;
        if(f==6)++tick;
        if(f==7)mask=0;
        if(f==8)ctl.write(B,0x12345678u);
        const auto initial=ctl.read(C),status=ctl.read(S),buffer=ctl.read(B);
        bool ok=ack.handoff_follow_on(third,f==2?foreign:ctl,f==3?foreign_cause:cause,
                  f==4?foreign_mask:mask,f==5?copy:tick,f==9?4u:ch,idle,ports[ch].type,f==10?0u:8u);
        if(f>=1&&f<=10){
            need(!ok&&ack.stage()!=5&&ctl.issued_tokens()==2&&ctl.read(C)==initial&&ctl.read(S)==status&&ctl.read(B)==buffer);
            ++refused;continue;
        }
        need(ok&&ack.stage()==5&&!ack.postack_held()&&third.stage()==1&&cause==Other&&ctl.issued_tokens()==2);
        need(!ack.handoff_follow_on(third,ctl,cause,mask,tick,ch,idle,ports[ch].type,8));
        auto step=[&](Access a=Access::None,uint32_t address=0,std::optional<uint32_t> value=std::nullopt){
            scheduler.advance(++tick);return third.before(tick,a,address,value);
        };
        if(!idle){
            need(step()&&third.finish(tick,0)&&third.held_now()&&ctl.issued_tokens()==2);
            ++valid;continue;
        }
        need(step(Access::Read,Base+C));
        if(f==11){++tick;need(!third.read(ctl,C,v)&&ctl.issued_tokens()==2);++refused;continue;}
        need(third.read(ctl,C,v)&&v==initial);
        need(step(Access::Write,Base+B,0u)&&third.write(ctl,B,0));
        need(step(Access::Write,Base+S,0x0f0f0f0fu)&&third.write(ctl,S,0x0f0f0f0fu));
        need(step(Access::Write,Base+C,cfg|1u));
        ok=third.write(ctl,C,(cfg|1u)^(f==12?2u:0u));
        if(f==12){need(!ok&&!ctl.pending()&&ctl.issued_tokens()==2);++refused;continue;}
        need(ok&&ctl.issued_tokens()==3&&third.token()==3);
        for(unsigned i=0;i<9;++i)need(step());
        need(third.finish(tick,1)&&third.held_now()&&third.follow_stage()==3&&scheduler.completed()==3&&cause==(Other|SI));
        ++valid;
    }
    need(valid==8&&refused==12);
    std::cout<<"V969_THIRD_TOKEN_HANDOFF valid=8 refused=12 real_scheduler=1 real_device=1 original_execution=0\n";
}
