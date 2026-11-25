#include "wii_postack_transfer_device_v771.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t H=0x80004000u,Other=0x100u,Base=0xcd006400u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
static void need(bool ok,unsigned line){if(!ok){std::cerr<<"V771_ASSERT line="<<line<<'\n';throw std::runtime_error("device");}}
#define CHECK(x) need((x),__LINE__)
int main(){
    unsigned valid=0,refused=0;
    for(unsigned trial=0;trial<25;++trial){
        std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler scheduler(ctl,ports,8);
        ctl.write(C,0xc0010301u);scheduler.advance(1);scheduler.advance(9);
        uint64_t tick=100;SiCompletionAckTrace ack;
        CHECK(ack.arm(ctl,cause,mask,tick,H,H+16));++tick;CHECK(ack.before(H,0x90030000u));
        ack.write(ctl,C,0xe0010300u);++tick;CHECK(ack.before(H+4,0x60000000u)&&ack.resume_after_ack(H+4,0x60000000u));
        const unsigned ch=trial%4;
        PostAckTransferDevice w;
        const bool idle=trial!=4&&trial!=5;
        bool ok=w.begin(ctl,cause,mask,ack,tick,trial==6?4u:ch,idle,ports[ch].type,8);
        if(trial==6){CHECK(!ok&&w.failure()==1);++refused;continue;}CHECK(ok);
        auto before=[&](Access a=Access::None,uint32_t addr=0){scheduler.advance(++tick);return w.before(tick,a,addr);};
        if(!idle){
            ok=before(trial==5?Access::Read:Access::None,trial==5?Base+C:0);
            if(trial==5){CHECK(!ok);++refused;continue;}
            CHECK(ok&&w.finish(tick,0)&&w.stage()==2&&ctl.issued_tokens()==1);++valid;continue;
        }
        if(trial==7){tick+=2;scheduler.advance(tick);CHECK(!w.before(tick));++refused;continue;}
        if(trial==8){CHECK(!before(Access::Read,0xcc006434u));++refused;continue;}
        if(trial==9){CHECK(!before(Access::Read,Base+C+1));++refused;continue;}
        if(trial==10){CHECK(!before(Access::Read,0x4d006434u));++refused;continue;}
        if(trial==11){mask=0;CHECK(!before());++refused;continue;}
        CHECK(before(Access::Read,Base+C));
        uint32_t value=0;
        if(trial==12){CHECK(!w.read(ctl,S,value));++refused;continue;}
        if(trial==13){CHECK(!before());++refused;continue;}
        CHECK(w.read(ctl,C,value)&&value==0x60010300u);
        if(trial==14){CHECK(!w.read(ctl,C,value));++refused;continue;}
        CHECK(before(Access::Write,Base+B));
        CHECK(w.write(ctl,B,trial==15?0x01000000u:0x00abcdefu));
        CHECK(before(Access::Write,Base+S)&&w.write(ctl,S,0x08000000u));
        CHECK(before(Access::Write,Base+C));
        uint32_t control=0xc0010301u|(ch<<1);
        if(trial==16)control^=2u;
        if(trial==17)control|=SiController::RDST_MASK;
        ok=w.write(ctl,C,control);
        if(trial>=15&&trial<=17){CHECK(!ok&&!ctl.pending());++refused;continue;}CHECK(ok&&w.follow_stage()==2&&ctl.issued_tokens()==2);
        if(trial==18){CHECK(before(Access::Write,Base+B)&&!w.write(ctl,B,0));++refused;continue;}
        if(trial==19){++tick;ctl.complete(w.token(),{},SiController::ERR_NOREP);CHECK(!w.before(tick));++refused;continue;}
        // Return both while in flight and after completion, then observe
        // the same transaction without issuing another request.
        const bool early=trial%2==0;
        for(unsigned i=1;i<=(early?3u:9u);++i)CHECK(before());
        if(trial==20){CHECK(!w.finish(tick,0));++refused;continue;}
        CHECK(w.finish(tick,1)&&w.stage()==2);
        if(early)for(unsigned i=4;i<=9;++i){scheduler.advance(++tick);CHECK(w.after_return(tick));}
        CHECK(w.follow_stage()==3&&!ctl.pending()&&cause==(Other|SI)&&scheduler.completed()==2);
        if(trial==21)ctl.write(C,SiController::TC_INT);
        if(trial==22)ctl.write(B,0);
        if(trial==23)cause|=0x200u;
        if(trial==24)mask=0;
        scheduler.advance(++tick);ok=w.after_return(tick);
        if(trial>=21){CHECK(!ok);++refused;continue;}
        CHECK(ok&&ctl.issued_tokens()==2&&w.reads()==1&&w.writes()==3);++valid;
    }
    CHECK(valid==5&&refused==20);
    std::cout<<"V771_POSTACK_TRANSFER_DEVICE synthetic=1 valid=5 refused=20 real_device=1 real_scheduler=1 original_execution=0\n";
}
