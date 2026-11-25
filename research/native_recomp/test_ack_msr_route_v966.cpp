#include "wii_bounded_ack_call_route_v956.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,L=H+0x100u,MT=0x7c600124u,NOP=0x60000000u,BLR=0x4e800020u;
constexpr std::array<AckCallSpan,2> spans{{{H,H+16},{L,L+16}}};
constexpr std::array<AckCallEdge,1> edges{{{H,L}}};
constexpr std::array<AckMsrSite,1> msr{{{L,MT}}};
struct Cpu{uint32_t pc=H,lr=0,msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;std::array<uint32_t,32> gpr{};};
static void need(bool ok){if(!ok)throw std::runtime_error("V966 assertion");}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned f=0;f<8;++f){
        Cpu c;BoundedAckCallRoute r;auto sites=msr;
        if(f==1)sites[0].pc=L+12;
        if(f==2)sites[0].word=NOP;
        bool ok=r.begin(c,spans,edges,f==3?std::span<const AckMsrSite>{}:std::span<const AckMsrSite>{sites});
        if(f==1||f==2){need(!ok&&r.failure()==1);++refused;continue;}need(ok);
        need(r.before(c,H,0x48000101u));c.pc=L;c.lr=H+4;need(r.entry(c,L));
        c.gpr[3]=c.msr;if(f==4)c.gpr[3]|=0x8000u;
        ok=r.before(c,L,f==5?MT^(1u<<21):MT);
        if(f>=3&&f<=5){need(!ok&&r.failure()==4);++refused;continue;}
        need(ok&&!r.can_poll()&&r.msr_writes()==1);
        if(f==6)c.msr^=0x10;
        ok=r.before(c,f==7?L+8:L+4,NOP);
        if(f>=6){need(!ok&&r.failure()==2);++refused;continue;}
        need(ok&&r.can_poll()&&r.before(c,L+8,BLR)&&r.before(c,H+4,NOP)&&r.returns()==1);
        ++valid;
    }
    need(valid==1&&refused==7);
    std::cout<<"V966_MSR_ROUTE valid=1 refused=7 original_execution=0\n";
}
