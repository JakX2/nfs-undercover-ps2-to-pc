#include "wii_exi_profile_v501.h"
#include "wii_physical_ram.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI profile");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    const std::string src="UNDERCOVER_EXI_PROFILE_V1\nid=ffffffff\ndi_config=00000001\nrtc_seconds=12345678\nlatency=00000008\nsram="+std::string(128,'a')+"\n";
    const auto p=ExiHostProfile::parse(src);
    need(p.id==0xffffffff&&p.di_config==1&&p.rtc_seconds==0x12345678&&p.latency==8&&p.sram[63]==0xaa);
    std::string crlf;for(char c:src){if(c=='\n')crlf+='\r';crlf+=c;}need(ExiHostProfile::parse(crlf).sram==p.sram);
    for(const std::string& bad:{src+"extra\n",src.substr(0,src.size()-1),std::string(513,'x')}){
        reject([&]{ExiHostProfile::parse(bad);});
    }
    for(const auto& [a,b]:std::array<std::pair<std::string,std::string>,5>{{
        {"ffffffff","fffffffff"},{"00000008","00000000"},{"00000008","00100000"},{"12345678","1234567z"},{"sram=","sramx="}}}){
        auto bad=src;bad.replace(bad.find(a),a.size(),b);reject([&]{ExiHostProfile::parse(bad);});
    }
    std::vector<uint8_t> m1(256),m2(256);WiiPhysicalRam ram(m1,m2);
    std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController exi(banks,&ram);
    need(!ExiDiConfigBinding::active()&&!ExiTickBinding::active());
    {
        ExiProfileSession session(exi,p);
        for(auto a:{0x0d006024u,0xcd006024u,0x8d006024u,0x0d806024u,0xcd806024u})need(ExiDiConfigBinding::read32(a)==1);
        need(!ExiDiConfigBinding::read32(0x0c006024u));
        reject([&]{ExiDiConfigBinding::read32(0x4d006024u);});
        reject([&]{ExiDiConfigBinding::check(0xcd006023u,2,true,false);});
        reject([&]{ExiDiConfigBinding::check(0xcd006024u,4,true,true);});
        reject([&]{ExiDiConfigBinding::check(0xcd006024u,4,false,false);});
        exi.write(0,0,0x234);exi.write(0,16,0);exi.write(0,12,0x15);
        for(unsigned i=0;i<=8;++i)ExiTickBinding::advance(i);
        need(session.completed()==1);
        exi.write(0,12,0x31);for(unsigned i=9;i<=17;++i)ExiTickBinding::advance(i);
        need(exi.read(0,16)==0xffffffff&&session.completed()==2&&!session.sram_dirty());
    }
    need(!ExiDiConfigBinding::active()&&!ExiTickBinding::active());
    std::cout<<"PASS: explicit EXI profile parser, configured ID, Wii DICFG aliases and read-only guards\n";
}
