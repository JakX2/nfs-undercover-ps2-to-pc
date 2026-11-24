#include "wii_si_type_scheduler_v514.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI scheduler witness");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    using Port=SiTypeScheduler::Port;
    using Profile=SiTypeScheduler::Profile;
    constexpr auto C=SiController::Control,S=SiController::Status,B=SiController::Buffer;
    const Profile profile{Port::present({0x12,0x34,0x56}),Port::absent(),
                          Port::present({0x09,0x87,0x65}),Port::absent()};
    std::atomic<uint32_t> pi{0x4100};SiController si(pi);
    reject([&]{SiTypeScheduler invalid(si,profile,0);});
    reject([&]{SiTypeScheduler invalid(si,Profile{},8);});
    SiTypeScheduler sched(si,profile,8);
    uint64_t now=10;
    for(unsigned ch=0;ch<4;++ch){
        si.write(B,0x00abcdefu);si.write(C,0xc0010301u|(ch<<1));
        const auto req=*si.pending();
        need(req.channel==ch&&req.tx[0]==0);
        SiTickBinding::advance(now+1000);
        need(sched.completed()==ch&&si.pending()->token==req.token);
        {
            SiTickBinding binding(sched);
            reject([&]{SiTickBinding duplicate(sched);});
            SiTickBinding::advance(now);
            for(unsigned n=0;n<100;++n)need((si.read(C)&1)&&si.read(B)==0x00abcdefu);
            SiTickBinding::advance(now+7);SiTickBinding::advance(now+7);
            need(si.pending()->token==req.token&&sched.completed()==ch&&pi==0x4100u);
            reject([&]{SiTickBinding::advance(now+6);});
            SiTickBinding::advance(now+8);SiTickBinding::advance(now+8);
            need(!si.pending()&&sched.completed()==ch+1&&(si.read(C)&SiController::TC_INT));
            need(pi==(0x4100u|SiController::PI_SI));
            if(ch%2){
                const auto error=SiController::ERR_NOREP<<((3-ch)*8);
                need(si.read(S)==error&&si.read(B)==0x00abcdefu&&(si.read(C)&SiController::COM_ERR));
                si.write(S,error);need(si.read(S)==0);
            }else need(si.read(B)==(ch?0x098765efu:0x123456efu)&&!(si.read(C)&SiController::COM_ERR));
            si.write(C,SiController::TC_INT);need(pi==0x4100u);
        }
        need(!SiTickBinding::active());now+=20;
    }
    // Invalid command/geometry must not synthesize completion or change RAM.
    for(auto ctl:{0xc0020301u,0xc0010401u,0xc0010301u}){
        std::atomic<uint32_t> p{0x100};SiController c(p);SiTypeScheduler s(c,profile,8);
        c.write(B,ctl==0xc0010301u?0x01000000u:0u);c.write(C,ctl);
        auto q=*c.pending();reject([&]{s.advance(1);});
        need(c.pending()->token==q.token&&s.completed()==0&&p==0x100u);
    }
    // External completion followed immediately by a new token cannot inherit
    // the stale deadline; this also verifies token ownership is checked.
    si.write(B,0);si.write(C,0xc0010301u);sched.advance(now);
    auto old=*si.pending();si.complete(old.token,std::array<uint8_t,3>{1,2,3});
    si.write(B,0);si.write(C,0xc0010303u);sched.advance(now+7);
    sched.advance(now+8);need(si.pending()&&sched.completed()==4);
    sched.advance(now+15);need(!si.pending()&&sched.completed()==5);
    {
        std::atomic<uint32_t> p{0};SiController c(p);SiTypeScheduler s(c,profile,8);
        c.write(C,0xc0010301u);const auto q=*c.pending();
        reject([&]{s.advance(std::numeric_limits<uint64_t>::max()-7);});
        need(c.pending()->token==q.token&&s.completed()==0&&p==0);
        s.advance(1);s.advance(9);need(s.completed()==1);
    }
    std::cout<<"PASS: SI type endpoints, four channels, exact tick deadlines, stale tokens, explicit absence and negative controls\n";
}
