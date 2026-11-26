#include "wii_bounded_ack_call_route_v956.h"
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,L=H+0x100u,N=H+0x200u,Nop=0x60000000u,Blr=0x4e800020u;
constexpr std::array<AckCallSpan,2> spans{{{H,H+40},{L,L+24}}};
constexpr std::array<AckCallEdge,1> edges{{{H,L}}};
constexpr uint32_t bl(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
constexpr uint32_t bc(unsigned bo,unsigned bi,int disp){return 0x40000000u|(bo<<21)|(bi<<16)|(uint32_t(disp)&0xfffcu);}
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{uint32_t pc=H,lr=0,ctr=2,msr=0x32,dispatch_saved_ctx=0;bool is_running=true,in_callback=false;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};};
static void need(bool b){if(!b)throw std::runtime_error("V1000 strict route");}
int main(){
    unsigned good=0,bad=0;
    for(unsigned f=0;f<12;++f){
        Cpu c;BoundedAckCallRoute r;
        need(r.begin(c,spans,edges,{},true)&&r.before(c,H,bl(H,L)));
        c.pc=L;c.lr=H+4;need(r.entry(c,L)&&r.before(c,L,Nop));
        if(f==3){need(!r.before(c,L+8,Nop));++bad;continue;}
        c.cr[0].eq=f!=1;
        uint32_t branch=bc(12,2,8);
        if(f==4)branch=bc(12,2,32);
        if(f==5)branch|=2;
        bool ok=r.before(c,L+4,branch);
        if(f==4||f==5){need(!ok);++bad;continue;}need(ok);
        const uint32_t next=f==1?L+8:L+12;
        if(f==6){need(!r.before(c,L+8,Nop));++bad;continue;}
        need(r.before(c,next,Nop));
        if(f==1)need(r.before(c,L+12,Nop));
        // bdnz: use the pre-instruction CTR and check the actual next label.
        c.ctr=f==2?1u:2u;
        need(r.before(c,L+16,bc(16,0,-4)));
        --c.ctr;
        if(f==7){need(!r.before(c,L+20,Blr));++bad;continue;}
        if(f!=2){need(r.before(c,L+12,Nop)&&r.before(c,L+16,bc(16,0,-4)));--c.ctr;}
        need(r.before(c,L+20,Blr)&&r.before(c,H+4,Nop)&&r.depth()==0u);
        if(f==8){need(!r.stop_before_indirect(c,H+12,0x4e800421u));++bad;continue;}
        if(f==9){need(!r.stop_before_indirect(c,H+8,Blr));++bad;continue;}
        if(f==10){need(!r.stop_before_direct(c,H+12,bl(H+12,N)));++bad;continue;}
        if(f==11){need(!r.before(c,H+8,0x48000040u));++bad;continue;}
        need(r.stop_before_indirect(c,H+8,0x4e800421u));++good;
    }
    need(good==3&&bad==9);
    std::cout<<"V1000_STRICT_ROUTE valid=3 refused=9 conditional=1 backward=1 original_execution=0\n";
}
