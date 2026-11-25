#include "wii_bounded_ack_call_route_v956.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,T=H+0x100u,S=H+0x200u,A=S+4u,R=H+0x300u,NOP=0x60000000u,BLR=0x4e800020u;
constexpr std::array<AckCallSpan,5> spans{{{H,H+16},{T,T+16},{S,S+12,1},{A,S+12,1},{R,R+8,0,31}}};
constexpr std::array<AckCallEdge,4> edges{{{H,S},{H+4,T},{T,A},{T+4,R}}};
constexpr uint32_t bl(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
struct Cpu{uint32_t pc=H,lr=0,msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;std::array<uint32_t,32> gpr{};};
static void need(bool ok){if(!ok)throw std::runtime_error("V971 alias route");}
int main(){
    unsigned good=0,bad=0;
    for(unsigned f=0;f<8;++f){
        Cpu c;BoundedAckCallRoute route;auto ss=spans;auto ee=edges;
        if(f==1)ss[3].save_suffix=0;
        if(f==2)ss[3].end+=4;
        if(f==3)ss[4].restore_first=30;
        bool ok=route.begin(c,ss,ee);
        if(f>=1&&f<=3){need(!ok);++bad;continue;}need(ok);
        need(route.before(c,H,bl(H,S),H));c.pc=S;c.lr=H+4;need(route.entry(c,S));
        need(route.before(c,S,NOP,S));
        ok=route.before(c,A,NOP,f==4?A:S);
        if(f==4){need(!ok);++bad;continue;}need(ok);
        need(route.before(c,S+8,BLR,S)&&route.before(c,H+4,bl(H+4,T),H));
        c.pc=T;c.lr=H+8;need(route.entry(c,T)&&route.before(c,T,bl(T,A),T));
        c.pc=A;c.lr=T+4;need(route.entry(c,A)&&route.before(c,A,NOP,A)&&route.before(c,S+8,BLR,A));
        need(route.before(c,T+4,bl(T+4,R),T));c.pc=R;c.lr=T+8;
        need(route.entry(c,R)&&route.before(c,R,NOP,R));
        c.gpr[31]=123;if(f==5)c.gpr[30]=1;
        need(route.before(c,R+4,BLR,R));
        ok=route.before(c,T+8,NOP,T);
        if(f==5){need(!ok);++bad;continue;}need(ok);
        if(f!=6)c.gpr[31]=0;
        c.lr=H+8;need(route.before(c,T+12,BLR,T));
        ok=route.before(c,H+8,NOP,f==7?T:H);
        if(f>=6){need(!ok);++bad;continue;}need(ok&&route.depth()==0&&route.entries()==4&&route.returns()==4);
        ++good;
    }
    need(good==1&&bad==7);
    std::cout<<"V971_ALIAS_ROUTE valid=1 refused=7 original_execution=0\n";
}
