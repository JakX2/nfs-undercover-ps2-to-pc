#include "wii_si_transfer_arguments_v981.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t Data=0x80004000u,Slots=0x80005000u,Cmd=0x80006000u,Resp=0x80007000u,Callback=0x80008000u;
struct Mmu{
    std::map<uint32_t,uint8_t> mem;
    uint8_t* get_ptr(uint32_t p){auto i=mem.find(p);return i==mem.end()?nullptr:&i->second;}
    uint8_t read8(uint32_t p){return mem.at(p);}
    uint32_t read32(uint32_t p){uint32_t w=0;for(unsigned i=0;i<4;++i)w=(w<<8)|read8(p+i);return w;}
    void write(uint32_t p,uint32_t w){for(unsigned i=0;i<4;++i)mem[p+i]=uint8_t(w>>(24-8*i));}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};};
static void need(bool ok){if(!ok)throw std::runtime_error("V981 arguments");}
int main(){
    unsigned good=0,bad=0;
    for(unsigned f=0;f<16;++f){
        Cpu c;unsigned ch=f%4;
        for(unsigned i=0;i<5;++i)c.mmu.write(Data+4*i,0xffffffffu);
        for(unsigned i=0;i<32;++i)c.mmu.write(Slots+4*i,0);
        c.mmu.write(Cmd,0);c.mmu.write(Resp,0);c.mmu.write(Callback,0x60000000u);
        const std::array<uint32_t,8> request{ch,Cmd,1,Resp,3,Callback,0,3948};
        for(unsigned i=0;i<8;++i){c.gpr[3+i]=request[i];c.mmu.write(Slots+ch*32+4*i,request[i]);}
        if(f==4)c.gpr[3]=4;
        if(f==5)c.gpr[5]=2;
        if(f==6)c.gpr[7]=4;
        if(f==7)c.mmu.mem[Cmd]=1;
        if(f==8)c.mmu.mem.erase(Resp+2);
        if(f==9)c.mmu.write(Data,ch);
        if(f==10)c.gpr[8]=Callback+1;
        if(f==11)c.mmu.write(Slots+32*ch+28,3949);
        if(f==12)c.mmu.mem.erase(Slots+127);
        if(f==13)c.gpr[4]=0xffffffffu;
        if(f==14)c.mmu.mem.erase(Callback+3);
        if(f==15)c.gpr[10]=0;
        const auto before=c.mmu.mem;const auto gp=c.gpr;
        const auto a=inspect_si_transfer_arguments(c,Data,Slots,Callback);
        need(before==c.mmu.mem&&gp==c.gpr);
        if(f<4){need(a.admitted()&&a.channel==ch&&a.packet==request);++good;}
        else{need(!a.admitted());++bad;}
    }
    need(good==4&&bad==12);
    std::cout<<"V981_TRANSFER_ARGUMENTS valid=4 refused=12 read_only=1 original_execution=0\n";
}
