#include "wii_si_profile_v518.h"
#include <iostream>
#include <string>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI profile witness");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    const std::string good="UNDERCOVER_SI_PROFILE_V1\nlatency=00000008\nport0=123456\nport1=absent\nport2=abcdef\nport3=absent\n";
    auto p=SiHostProfile::parse(good);
    need(p.latency==8&&p.ports[0].type==SiTypeScheduler::Type{0x12,0x34,0x56}&&!p.ports[1].type&&
         p.ports[2].type==SiTypeScheduler::Type{0xab,0xcd,0xef}&&!p.ports[3].type);
    std::string crlf;for(char c:good){if(c=='\n')crlf+='\r';crlf+=c;}
    need(SiHostProfile::parse(crlf).ports[2].type==p.ports[2].type);
    auto changed=[&](std::string_view from,std::string_view to){
        auto s=good;s.replace(s.find(from),from.size(),to);return s;};
    for(const auto& bad:{std::string{},good.substr(0,good.size()-1),good+"extra\n",std::string(257,'x'),
            changed("V1","V2"),changed("00000008","00000000"),changed("00000008","ffffffff"),
            changed("123456","12345"),changed("abcdef","abcdzz"),changed("absent","default"),
            changed("port2=","port1="),changed("port3=absent\n","")})
        reject([&]{SiHostProfile::parse(bad);});
    std::atomic<uint32_t> pi{0x100u};SiController ctl(pi);
    reject([&]{SiProfileSession s(ctl,p);});need(!SiTickBinding::active());
    {
        SiBinding mmio(ctl);
        {
            SiProfileSession s(ctl,p);
            reject([&]{SiProfileSession duplicate(ctl,p);});
            need(SiTickBinding::active());
            need(SiBinding::write32(0xcd006480u,0u)&&SiBinding::write32(0xcd006434u,0xc0010301u));
            SiTickBinding::advance(1);SiTickBinding::advance(8);need(s.completed()==0);
            SiTickBinding::advance(9);need(s.completed()==1&&SiBinding::read32(0xcd006480u)==0x12345600u);
        }
        need(!SiTickBinding::active()&&SiBinding::active());
    }
    need(!SiBinding::active()&&pi==(0x100u|SiController::PI_SI));
    std::cout<<"PASS: explicit SI profile, strict four-port geometry, no implicit defaults and scoped tick ownership\n";
}
