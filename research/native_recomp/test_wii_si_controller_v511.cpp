#include "wii_si_controller_v511.h"
#include <iostream>
#include <vector>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI witness");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    std::atomic<uint32_t> pi{0x4100u|SiController::PI_SI};SiController si(pi);
    constexpr auto C=SiController::Control,P=SiController::Poll,S=SiController::Status,B=SiController::Buffer;
    need(pi==0x4100u&&si.read(C)==0&&si.read(P)==0&&si.read(S)==0&&!si.pending());
    si.write(P,0x000f0200u);need(si.read(P)==0x000f0200u);
    reject([&]{si.write(P,0x10u);});reject([&]{si.write(P,0x80000000u);});
    reject([&]{si.write(S,0x80000000u);});reject([&]{si.read(0x3c);});
    unsigned cases=0;
    for(unsigned ch=0;ch<4;++ch){
        for(unsigned n:{1u,3u,4u,127u,128u}){
            for(unsigned i=0;i<32;++i)si.write(B+i*4,0x12345678u+i);
            const unsigned len=n==128?0:n;
            const uint32_t ctl=0xc0000001u|(len<<16)|(len<<8)|(ch<<1);
            si.write(C,ctl);const auto q=*si.pending();
            need(q.channel==ch&&q.in_length==n&&q.out_length==n&&q.tx[0]==0x12&&q.tx[1]==0x34&&q.tx[127]==0x97);
            for(unsigned i=0;i<100;++i)need((si.read(C)&1u)&&si.pending()->token==q.token);
            reject([&]{si.write(C,ctl);});reject([&]{si.write(C,(ctl&~1u)^2u);});
            reject([&]{si.write(B,0);});reject([&]{si.complete(q.token+1,{});});
            std::vector<uint8_t> bytes(n,0xa5u);reject([&]{si.complete(q.token,std::span<const uint8_t>(bytes).first(n-1));});
            need(si.read(B)==0x12345678u&&(pi&SiController::PI_SI)==0);
            si.complete(q.token,bytes);
            need(!si.pending()&&!(si.read(C)&1u)&&(si.read(C)&SiController::TC_INT)&&(pi&SiController::PI_SI));
            const auto expected=n==1?0xa5345678u:n==3?0xa5a5a578u:0xa5a5a5a5u;
            need(si.read(B)==expected&&si.read(S)==0);
            si.write(C,si.read(C)&~(SiController::TC_MASK|SiController::TC_INT));
            need(!(pi&SiController::PI_SI)&&(si.read(C)&SiController::TC_INT));
            si.write(C,SiController::TC_MASK);need(pi&SiController::PI_SI);
            si.write(C,SiController::TC_INT);need(!(pi&SiController::PI_SI)&&!(si.read(C)&SiController::TC_INT));
            ++cases;
        }
        si.write(B,0x12345678u);si.write(C,0xc0010301u|(ch<<1));
        auto q=*si.pending();si.complete(q.token,{},SiController::ERR_NOREP);
        const uint32_t err=8u<<((3u-ch)*8u);
        need(si.read(S)==err&&si.read(B)==0x12345678u&&(si.read(C)&SiController::COM_ERR));
        si.write(S,err);need(si.read(S)==0);
        si.write(C,SiController::TC_INT);need(!(pi&SiController::PI_SI));
        ++cases;
    }
    need(pi==0x4100u);
    std::cout<<"PASS: native SI sampling, communication RAM, "<<cases<<" explicit channel transfers, W1C and shared PI IRQ\n";
}
