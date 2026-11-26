#include "wii_second_completion_ack_v950.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t H=0x80004000u,Other=0x100u,Base=0xcd006400u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
constexpr uint32_t Load=0x80830034u,Store=0x90830034u,Nop=0x60000000u;
struct Mmu{
    std::map<uint32_t,uint32_t> words{{H,Load},{H+4,Store},{H+8,Nop}};uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint64_t inst_count=100;
    uint32_t msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;
};
static void need(bool ok,unsigned line){if(!ok){std::cerr<<"V957_ASSERT line="<<line<<'\n';throw std::runtime_error("handoff");}}
#define CHECK(x) need((x),__LINE__)
int main(){
    unsigned valid=0,refused=0;
    for(unsigned t=0;t<20;++t){
        const unsigned fault=t<8?0:t-7,ch=t%4;
        std::atomic<uint32_t> cause{Other},mask{SI},other_cause{Other},other_mask{SI};
        SiController ctl(cause),other_ctl(other_cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler scheduler(ctl,ports,8);
        ctl.write(C,0xc0010301u);scheduler.advance(1);scheduler.advance(9);
        Cpu c;auto& tick=c.inst_count;SiCompletionAckTrace first;PostAckTransferDevice old;SecondCompletionAck next;
        CHECK(first.arm(ctl,cause,mask,tick,H,H+16));++tick;CHECK(first.before(H,0x90030000u));
        first.write(ctl,C,0xe0010300u);++tick;CHECK(first.before(H+4,Nop)&&first.resume_after_ack(H+4,Nop));
        CHECK(old.begin(ctl,cause,mask,first,tick,ch,true,ports[ch].type,8));
        auto step=[&](Access a=Access::None,uint32_t addr=0){scheduler.advance(++tick);return old.before(tick,a,addr);};
        uint32_t result=0;
        CHECK(step(Access::Read,Base+C)&&old.read(ctl,C,result));
        CHECK(step(Access::Write,Base+B)&&old.write(ctl,B,0x00abcdefu));
        CHECK(step(Access::Write,Base+S)&&old.write(ctl,S,0x08000000u));
        CHECK(step(Access::Write,Base+C)&&old.write(ctl,C,0xc0010301u|(ch<<1)));
        for(unsigned i=0;i<(fault==5?2u:9u);++i)CHECK(step());
        if(fault!=6)CHECK(old.finish(tick,1));
        const auto snapshot=ctl.read(C),status=ctl.read(S),buffer=ctl.read(B);
        const uint64_t copied=tick;
        if(fault==7)++tick;
        if(fault==8)mask=0;
        if(fault==9)cause|=0x200u;
        if(fault==10)CHECK(next.arm(ctl,cause,mask,tick,2,true));
        if(fault==11)CHECK(old.arm_suffix_status_read(tick,Base+S));
        if(fault==12)CHECK(old.arm_suffix_status_read(tick,Base+S)&&old.read(ctl,S,result)&&old.arm_suffix_status_write(tick,Base+S,0));
        const bool ok=old.handoff_second_ack(next,fault==1?other_ctl:ctl,fault==2?other_cause:cause,
                         fault==3?other_mask:mask,fault==4?copied:tick);
        if(fault){
            CHECK(!ok&&old.stage()!=3&&ctl.issued_tokens()==2&&ctl.read(C)==snapshot&&ctl.read(S)==status&&ctl.read(B)==buffer);
            ++refused;continue;
        }
        CHECK(ok&&old.stage()==3&&!old.held_now()&&next.stage()==1&&next.token()==2);
        CHECK(next.response_class_verified()&&next.no_response_verified()==!ports[ch].type.has_value());
        CHECK(!old.handoff_second_ack(next,ctl,cause,mask,tick)&&ctl.read(C)==snapshot&&cause==(Other|SI));
        c.gpr[3]=Base;
        scheduler.advance(++tick);CHECK(next.before(c,H,Load,true)&&next.read(ctl,C,result)&&result==snapshot);
        c.gpr[4]=result|SiController::TC_INT;
        scheduler.advance(++tick);CHECK(next.before(c,H+4,Store,true)&&next.write(ctl,C,c.gpr[4]));
        scheduler.advance(++tick);CHECK(next.before(c,H+8,Nop,true)&&next.stage()==3);
        CHECK(cause==Other&&mask==SI&&ctl.issued_tokens()==2&&scheduler.completed()==2&&ctl.read(B)==buffer&&ctl.read(S)==status);
        CHECK(next.response_class_verified()&&next.no_response_verified()==!ports[ch].type.has_value());
        ++valid;
    }
    CHECK(valid==8&&refused==12);
    std::cout<<"V957_SECOND_ACK_HANDOFF valid=8 refused=12 real_scheduler=1 real_device=1 original_execution=0\n";
}
