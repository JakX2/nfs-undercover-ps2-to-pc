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
    for(unsigned trial=0;trial<30;++trial){
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
        std::atomic<uint32_t> unrelated_cause{Other},unrelated_mask{SI};SiController unrelated(unrelated_cause);
        uint64_t fake_tick=tick;
        if(trial==25){CHECK(!w.begin(unrelated,cause,mask,ack,tick,ch,idle,ports[ch].type,8));++refused;continue;}
        if(trial==26){CHECK(!w.begin(ctl,unrelated_cause,mask,ack,tick,ch,idle,ports[ch].type,8));++refused;continue;}
        if(trial==27){CHECK(!w.begin(ctl,cause,unrelated_mask,ack,tick,ch,idle,ports[ch].type,8));++refused;continue;}
        if(trial==28){CHECK(!w.begin(ctl,cause,mask,ack,fake_tick,ch,idle,ports[ch].type,8));++refused;continue;}
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
        if(trial==29){scheduler.advance(++tick);CHECK(w.before(tick,Access::Write,Base+B,0x12345678u));CHECK(!w.write(ctl,B,0)&&ctl.read(B)==0);++refused;continue;}
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
        if(trial==0u||trial==1u){
            // After a real SI transfer completed, the same latched source
            // remains valid through more original-instruction ticks than
            // the 33-label Windows scheduler and interrupt-leaf window.
            for(unsigned native_tick=0;native_tick<48u;++native_tick){
                scheduler.advance(++tick);
                CHECK(w.after_return_at(tick)&&w.held_now());
            }
            if(trial==0u){
                // Even with the real device advanced, a skipped guest tick
                // is never a successful native continuation.
                tick+=2u;scheduler.advance(tick);
                CHECK(!w.after_return_at(tick)&&w.failure()==7u);
            }
        }

    }
    CHECK(valid==5&&refused==25);
    unsigned status_ok=0,status_bad=0;
    for(unsigned t=0;t<12;++t){
        std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler scheduler(ctl,ports,8);
        ctl.write(C,0xc0010301u);scheduler.advance(1);scheduler.advance(9);
        uint64_t tick=100;SiCompletionAckTrace ack;
        CHECK(ack.arm(ctl,cause,mask,tick,H,H+16));++tick;CHECK(ack.before(H,0x90030000u));
        ack.write(ctl,C,0xe0010300u);++tick;CHECK(ack.before(H+4,0x60000000u)&&ack.resume_after_ack(H+4,0x60000000u));
        PostAckTransferDevice w;const unsigned ch=t%4;
        CHECK(w.begin(ctl,cause,mask,ack,tick,ch,true,ports[ch].type,8));
        auto step=[&](Access a=Access::None,uint32_t addr=0){scheduler.advance(++tick);return w.before(tick,a,addr);};
        uint32_t result=0;
        CHECK(step(Access::Read,Base+C)&&w.read(ctl,C,result));
        CHECK(step(Access::Write,Base+B)&&w.write(ctl,B,0x00abcdefu));
        CHECK(step(Access::Write,Base+S)&&w.write(ctl,S,0x08000000u));
        CHECK(step(Access::Write,Base+C)&&w.write(ctl,C,0xc0010301u|(ch<<1)));
        for(unsigned i=0;i<(t==2?2u:9u);++i)CHECK(step());
        CHECK(w.finish(tick,1));
        if(t==2){CHECK(!w.arm_suffix_status_read(tick,Base+S));++status_bad;continue;}
        CHECK(w.follow_stage()==3u&&w.held_now());
        const auto original=ctl.read(S);const auto control=ctl.read(C);const auto tokens=ctl.issued_tokens();
        if(t==3){CHECK(!w.arm_suffix_status_read(tick,Base+C));++status_bad;continue;}
        if(t==4){const uint64_t copy=tick;CHECK(!w.arm_suffix_status_read(copy,Base+S));++status_bad;continue;}
        if(t==5){CHECK(!w.read(ctl,S,result));++status_bad;continue;}
        CHECK(w.arm_suffix_status_read(tick,t==1?Base+0x00800000u+S:Base+S)&&!w.held_now());
        if(t==6){CHECK(!w.read(ctl,C,result));++status_bad;continue;}
        if(t==7){++tick;CHECK(!w.after_return_at(tick));++status_bad;continue;}
        if(t==8){CHECK(!w.write(ctl,S,0));++status_bad;continue;}
        if(t==9){cause|=0x200u;CHECK(!w.read(ctl,S,result));++status_bad;continue;}
        CHECK(w.read(ctl,S,result)&&result==original&&w.suffix_status_value()==original&&w.held_now());
        if(t==10){CHECK(!w.read(ctl,S,result));++status_bad;continue;}
        if(t==11){CHECK(!w.arm_suffix_status_read(tick,Base+S));++status_bad;continue;}
        scheduler.advance(++tick);CHECK(w.after_return_at(tick)&&w.held_now()&&w.suffix_status_reads()==1u&&w.reads()==1u&&w.writes()==3u);
        CHECK(ctl.read(S)==original&&ctl.read(C)==control&&ctl.issued_tokens()==tokens&&cause==(Other|SI));
        ++status_ok;
    }
    CHECK(status_ok==2u&&status_bad==10u);
    std::cout<<"V890_STATUS_DEVICE valid=2 refused=10 real_scheduler=1 original_execution=0\n";
    unsigned w1c_ok=0,w1c_bad=0;
    for(unsigned t=0;t<12;++t){
        std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler scheduler(ctl,ports,8);
        ctl.write(C,0xc0010301u);scheduler.advance(1);scheduler.advance(9);
        uint64_t tick=100;SiCompletionAckTrace ack;
        CHECK(ack.arm(ctl,cause,mask,tick,H,H+16));++tick;CHECK(ack.before(H,0x90030000u));
        ack.write(ctl,C,0xe0010300u);++tick;CHECK(ack.before(H+4,0x60000000u)&&ack.resume_after_ack(H+4,0x60000000u));
        PostAckTransferDevice w;const unsigned ch=t%4;
        CHECK(w.begin(ctl,cause,mask,ack,tick,ch,true,ports[ch].type,8));
        auto step=[&](Access a=Access::None,uint32_t addr=0){scheduler.advance(++tick);return w.before(tick,a,addr);};
        uint32_t result=0;
        CHECK(step(Access::Read,Base+C)&&w.read(ctl,C,result));
        CHECK(step(Access::Write,Base+B)&&w.write(ctl,B,0x00abcdefu));
        CHECK(step(Access::Write,Base+S)&&w.write(ctl,S,0x08000000u));
        CHECK(step(Access::Write,Base+C)&&w.write(ctl,C,0xc0010301u|(ch<<1)));
        for(unsigned i=0;i<9;++i)CHECK(step());
        CHECK(w.finish(tick,1)&&w.follow_stage()==3u&&w.held_now());
        const auto original=ctl.read(S),control=ctl.read(C),buffer=ctl.read(B);
        const auto tokens=ctl.issued_tokens();
        const uint32_t value=0x0fu<<((3u-ch)*8u);
        if(t==4){CHECK(!w.arm_suffix_status_write(tick,Base+S,value));++w1c_bad;continue;}
        CHECK(w.arm_suffix_status_read(tick,Base+S)&&w.read(ctl,S,result)&&result==original);
        scheduler.advance(++tick);CHECK(w.after_return_at(tick));
        if(t==5){CHECK(!w.arm_suffix_status_write(tick,Base+C,value));++w1c_bad;continue;}
        if(t==6){CHECK(!w.arm_suffix_status_write(tick,Base+S,0x80000000u));++w1c_bad;continue;}
        if(t==7){CHECK(!w.write(ctl,S,value));++w1c_bad;continue;}
        CHECK(w.arm_suffix_status_write(tick,t==1?Base+0x00800000u+S:Base+S,value)&&!w.held_now());
        if(t==8){CHECK(!w.write(ctl,S,value^1u)&&ctl.read(S)==original);++w1c_bad;continue;}
        if(t==9){CHECK(!w.write(ctl,C,value)&&ctl.read(C)==control);++w1c_bad;continue;}
        if(t==10){++tick;CHECK(!w.after_return_at(tick));++w1c_bad;continue;}
        CHECK(w.write(ctl,S,value)&&w.suffix_status_writes()==1u&&w.held_now());
        CHECK(ctl.read(S)==(original&~value)&&ctl.read(C)==control&&ctl.read(B)==buffer&&ctl.issued_tokens()==tokens&&cause==(Other|SI));
        if(t==11){CHECK(!w.arm_suffix_status_write(tick,Base+S,value));++w1c_bad;continue;}
        scheduler.advance(++tick);CHECK(w.after_return_at(tick)&&w.held_now());
        ++w1c_ok;
    }
    CHECK(w1c_ok==4u&&w1c_bad==8u);
    std::cout<<"V897_STATUS_W1C_DEVICE valid=4 refused=8 real_scheduler=1 original_execution=0\n";
    struct Cpu{std::array<uint32_t,32> gpr{};} cpu;
    cpu.gpr[3]=Base;cpu.gpr[4]=0x12345678u;cpu.gpr[5]=C;
    auto a=PostAckTransferDevice::word_access(cpu,0x90830034u);CHECK(a.kind==Access::Write&&a.address==Base+C&&a.store==0x12345678u);
    a=PostAckTransferDevice::word_access(cpu,0x80830034u);CHECK(a.kind==Access::Read&&a.address==Base+C&&!a.store);
    a=PostAckTransferDevice::word_access(cpu,(31u<<26)|(4u<<21)|(3u<<16)|(5u<<11)|(662u<<1));CHECK(a.kind==Access::Write&&a.address==Base+C&&a.store==0x78563412u);
    a=PostAckTransferDevice::word_access(cpu,0x8083fffcu);CHECK(a.kind==Access::Read&&a.address==Base-4u);
    a=PostAckTransferDevice::word_access(cpu,0x60000000u);CHECK(a.kind==Access::None);
    std::cout<<"V771_POSTACK_TRANSFER_DEVICE synthetic=1 valid=5 refused=25 real_device=1 real_scheduler=1 original_execution=0\n";
}
