#include "wii_open_sc_route_v637.h"
#include <array>
#include <atomic>
#include <iostream>
#include <map>
using namespace undercover::wii;
using R=OpenScRoute;using B=IosBus;using H=HollywoodIrq;using M=IpcMailbox;
struct Mem{
    std::map<uint32_t,uint8_t> bytes;
    uint8_t read8(uint32_t a){return bytes[a];}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(24-8*i));}
};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=R::Call,lr=R::Caller,msr=0x8032,ctr=7,hid0=0x100,srr0=0,srr1=0;
    uint32_t dispatch_saved_ctx=0,guest_sync_count=0,guest_isync_count=0;
    uint64_t inst_count=12;bool is_running=true;
};
static void need(bool ok){if(!ok)throw std::runtime_error("test assertion");}
int main(){
    // Synthetic bytes, not extracted original instructions. Mock translated
    // vector below tests the route contract; real native proof is separate.
    std::array<uint8_t,28> bytes{};
    unsigned good=0,bad=0;
    for(unsigned trial=0;trial<44;++trial){
        std::array<uint8_t,8192> one{},two{};
        std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
        NativeIosTransport host(one,two,cause,mask);NativeIosBinding bind(host);
        need(bind.write32(B::IPC+H::PPC_MASK,H::IPC_PPC));
        need(bind.write32(B::IPC+M::PPCCTRL,M::IY1|M::IY2));
        Cpu c;c.msr=0x8002u|((trial%4u)<<4);
        for(unsigned i=0;i<32;++i)c.gpr[i]=trial*33+i;
        c.mmu.write32(R::Call,0x44000002);c.mmu.write32(R::Resume,0x4e800020);
        R route(bytes);const unsigned fault=trial<32?0:trial-31;
        unsigned called=0;bool rejected=false;
        try{
            if(fault==1)c.msr&=~0x8000u;
            if(fault==2)cause.store(H::PI_HOLLYWOOD);
            if(fault==3)c.dispatch_saved_ctx=1;
            if(fault==4)c.lr+=4;
            if(fault!=5)route.arm(R::Call,c);
            ++c.inst_count;
            if(fault==6)c.mmu.bytes[R::Vector]=1;
            if(fault==7)c.mmu.bytes[R::Source]=1;
            if(fault==8)mask.store(0);
            if(fault==9)++c.inst_count;
            if(fault==10)bind.write32(B::IPC+M::PPCMSG,0x100);
            if(fault==11)c.gpr[1]++;
            need(route.dispatch(c,[&](Cpu& cpu){
                ++called;need(route.vector_trace(R::Vector,cpu));
                cpu.gpr[9]=cpu.hid0;cpu.gpr[10]=cpu.hid0|8;
                cpu.inst_count+=7;cpu.pc=cpu.srr0;cpu.msr=cpu.srr1;
                if(fault==12)cpu.msr^=0x8000;
            },[](const Cpu& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)
                    if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8):gp[i]))return false;
                return true;
            }));
            c.pc=R::Caller;need(route.returned(c));
        }catch(const std::runtime_error& e){
            if(std::string_view(e.what())!="V637 open SC route rejected")throw;
            rejected=true;
        }
        if(fault){
            need(rejected&&route.phase()==R::Phase::Failed&&called==(fault==12?1u:0u));
            ++bad;
        }else{need(!rejected&&called==1&&host.serviced_steps()==0);++good;}
    }
    std::cout<<"V637_OPEN_SC synthetic=1 returned="<<good<<" refusal="<<bad<<" ios_steps=0 original_vector=0\n";
}
