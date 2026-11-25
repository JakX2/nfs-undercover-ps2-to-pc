#include "wii_handler_suffix_guard_v868.h"
#include <iostream>
#include <map>
#include <source_location>
#include <cstdlib>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,SP=0x80010000u,Nop=0x60000000u,Store=0x90610000u,Call=0x48000101u;
struct CPU{
    struct MMU{
        std::map<uint32_t,uint8_t> data;
        const uint8_t* get_ptr(uint32_t a)const{auto it=data.find(a);return it==data.end()?nullptr:&it->second;}
        uint8_t read8(uint32_t a)const{return data.at(a);}
        uint32_t read32(uint32_t a)const{uint32_t r=0;for(unsigned i=0;i<4;++i)r=(r<<8)|read8(a+i);return r;}
        void put(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)data[a+i]=uint8_t(v>>(24-8*i));}
    }mmu;
    std::array<uint32_t,32> gpr{};
    uint32_t pc=H;
    uint64_t inst_count=10;
};
static void need(bool ok,const std::source_location l=std::source_location::current()){
    if(!ok){std::cerr<<"V868_TEST line="<<l.line()<<'\n';std::exit(1);}
}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned t=0;t<10;++t){
        CPU c;c.gpr[1]=SP;c.gpr[3]=0x12345678u;c.mmu.put(H,Store);c.mmu.put(H+4,Nop);c.mmu.put(H+8,Call);c.mmu.put(SP,0);
        std::array<HandlerSuffixLabel,3> rows{{{H,Store,0,0},{H+4,Nop,0,0},{H+8,Call,7,1}}};
        HandlerSuffixGuard g;
        if(t==1)rows[1].word^=1;
        if(t==2)c.gpr[1]=0;
        bool ok=g.start(c,rows,H);
        if(t==1||t==2){need(!ok);++refused;continue;}
        need(ok);
        if(t==3)c.gpr[1]=0xcc006400u;
        if(t==4)c.gpr[1]=H;
        if(t==5)++c.inst_count;
        ok=g.before(c,H,Store,0,0);
        if(t>=3&&t<=5){need(!ok);++refused;continue;}
        need(ok);
        c.mmu.put(SP,c.gpr[3]^(t==6));++c.inst_count;
        if(t==7)c.mmu.put(H+4,Nop^1u);
        ok=g.before(c,H+4,Nop,0,0);
        if(t==6||t==7){need(!ok);++refused;continue;}
        need(ok);++c.inst_count;
        ok=g.before(c,H+8,Call,t==8?8u:7u,t==9?2u:1u);
        if(t==8||t==9){need(!ok);++refused;continue;}
        need(ok&&g.visits()==3&&g.writes()==1);++valid;
    }
    need(valid==1&&refused==9);
    std::cout<<"V868_HANDLER_GUARD valid=1 refused=9 original_execution=0\n";
    unsigned status_ok=0,status_bad=0;
    for(unsigned t=0;t<8;++t){
        CPU c;c.gpr[1]=SP;c.gpr[4]=t==2?0xcd006434u:t==3?0xcd006439u:t==4?0x4d006438u:t==5?SP:t==1?0xcd806438u:0xcd006438u;
        const uint32_t w=t==6?0x90640000u:t==7?0x88640000u:0x80640000u;
        c.mmu.put(H,w);c.mmu.put(SP,0);
        std::array<HandlerSuffixLabel,1> rows{{{H,w,0,0}}};HandlerSuffixGuard guard;
        need(guard.start(c,rows,H));
        if(t<2){need(guard.before(c,H,w,0,0,true));++status_ok;}
        else{need(!guard.before(c,H,w,0,0,true));++status_bad;}
    }
    need(status_ok==2&&status_bad==6);
    std::cout<<"V890_STATUS_GUARD valid=2 refused=6 original_execution=0\n";
    for(unsigned t=0;t<6;++t){
        CPU c;c.gpr[1]=SP;c.gpr[4]=t==2?0xcd006434u:t==3?0xcd006439u:t==4?0x4d006438u:t==1?0xcd806438u:0xcd006438u;
        const uint32_t w=t==5?0x80640000u:0x90640000u;
        c.mmu.put(H,w);std::array<HandlerSuffixLabel,1> rows{{{H,w,0,0}}};HandlerSuffixGuard guard;
        need(guard.start(c,rows,H));need(guard.before(c,H,w,0,0,false,true)==(t<2));
    }
    std::cout<<"V897_STATUS_W1C_GUARD valid=2 refused=4 original_execution=0\n";
}
