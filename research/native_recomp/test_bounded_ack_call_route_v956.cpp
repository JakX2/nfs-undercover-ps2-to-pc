#include "wii_bounded_ack_call_route_v956.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,S=H+0x100u,N=H+0x200u,BLR=0x4e800020u,NOP=0x60000000u;
constexpr std::array<AckCallSpan,3> spans{{{H,H+16},{S,S+16},{N,N+16}}};
constexpr std::array<AckCallEdge,2> edges{{{H,S},{S,N}}};
constexpr uint32_t bl(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
struct Cpu{uint32_t pc=H,lr=0,msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;std::array<uint32_t,32> gpr{};};
static void need(bool v){if(!v)throw std::runtime_error("V956 assertion");}
int main(){
    unsigned valid=0,bad=0;
    for(unsigned fault=0;fault<=14;++fault){
        Cpu c;BoundedAckCallRoute r;c.gpr[1]=0x80008000u;c.gpr[14]=123;
        auto ss=spans;auto ee=edges;
        if(fault==1)ss[1].root=H+4;
        if(fault==2)ee[0].target=S+4;
        if(fault==3)ee[1].site=H;
        if(fault==4)c.msr|=0x8000;
        const bool started=r.begin(c,ss,ee);
        if(fault>=1&&fault<=4){need(!started&&r.failure()==1);++bad;continue;}need(started);
        if(fault==5){need(!r.before(c,H+4,NOP));++bad;continue;}
        if(fault==6){need(!r.before(c,H,bl(H,N)));++bad;continue;}
        need(r.before(c,H,bl(H,S))&&!r.can_poll());
        c.pc=S;c.lr=H+4;
        if(fault==7)c.lr+=4;
        if(fault==8)c.pc=N;
        const bool entered=r.entry(c,S);
        if(fault==7||fault==8){need(!entered);++bad;continue;}need(entered&&r.depth()==1);
        need(r.before(c,S,bl(S,N)));
        c.pc=N;c.lr=S+4;need(r.entry(c,N)&&r.depth()==2);
        if(fault==9){need(!r.before(c,N,0x44000002u));++bad;continue;}
        if(fault==10)c.lr+=4;
        const bool ret=r.before(c,N,BLR);
        if(fault==10){need(!ret);++bad;continue;}need(ret&&!r.can_poll());
        if(fault==11)c.gpr[14]^=1;
        if(fault==12)c.gpr[1]+=4;
        const bool after=r.before(c,fault==13?S+8:S+4,NOP);
        if(fault>=11&&fault<=13){need(!after);++bad;continue;}need(after&&r.depth()==1&&r.returns()==1);
        c.lr=H+4;need(r.before(c,S+8,BLR));need(r.before(c,H+4,NOP));
        if(fault==14){need(!r.before(c,H+8,BLR));++bad;continue;}
        need(r.entries()==2&&r.returns()==2&&r.depth()==0&&r.can_poll());++valid;
    }
    need(valid==1&&bad==14);
    std::cout<<"V956_ACK_CALL_ROUTE valid=1 refused=14 original_execution=0\n";
}
