#include "synthetic_irq_roundtrip_v78.h"
#include "native_external_irq.h"
#include "wii_ios_bus.h"
#include "runtime/cpu_context.h"
#include <cassert>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string_view>
using namespace synthetic_irq_roundtrip;
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
constexpr uint32_t Request=0x2000u,Path=0x2100u;
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
struct Ram final:IosMemory{
    CPUContext* cpu=nullptr;
    bool valid(uint32_t a,uint32_t n)const override{return cpu&&uint64_t(a)+n<=0x01800000u;}
    uint8_t read8(uint32_t a)const override{assert(valid(a,1));return cpu->mmu.mem1.at(a);}
    void write8(uint32_t a,uint8_t v)override{assert(valid(a,1));cpu->mmu.mem1.at(a)=v;}
};
static Ram ram;
static B bus(ram);
static unsigned entries=0,deliveries=0,acks=0,replies=0,controls=0,flags=0,reads=0,stops=0;
static bool transaction=false;
static uint32_t expected_fd=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==Entry)return;
    assert(pc==Vector&&deliveries==entries+1u&&c.srr0==Resume&&!(c.msr&B::MSR_EE));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(!bus.external_exception_pending(c.msr))return false;
    assert(transaction&&deliveries<2u&&c.pc==Resume&&c.gpr[5]==0u&&c.gpr[6]==deliveries);
    assert(c.srr0==0u||c.srr0==Resume);
    assert(enter_external_irq(c,bus,bytes,true)==ExternalEntry::Entered);
    assert(c.pc==Vector&&c.srr0==Resume&&c.srr1==B::MSR_EE);
    ++deliveries;return true;
}
bool handle_syscall(CPUContext& c){
    assert(c.pc==Stop);++stops;c.is_running=false;return true;
}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected halfword MMIO read");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected halfword MMIO write");}
uint32_t HW_Reg_Read32(uint32_t a){
    assert(a==B::IPC+M::PPCCTRL&&transaction&&entries==reads+1u);
    const auto v=bus.read32(a).value();
    assert((v&(M::Y1|M::Y2))==(reads==0u?M::Y2:M::Y1));
    ++reads;return v;
}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    assert(transaction&&entries>0u&&ram.cpu&&!(ram.cpu->msr&B::MSR_EE));
    if(a==B::IPC+M::PPCCTRL){
        assert(controls+1u==entries&&v==(M::IY1|M::IY2|(controls==0u?M::Y2:M::Y1)));
        assert(bus.write32(a,v));++controls;
        assert(bus.tick()==S::Pump::Busy); // IRQ latch still active
        return;
    }
    assert(a==B::IPC+H::PPC_FLAG&&v==H::IPC_PPC&&flags+1u==controls);
    assert(bus.write32(a,v)&&!bus.external_irq_level());++flags;
    if(flags==1u){
        assert(bus.tick()==S::Pump::Replied&&bus.external_irq_level());
        assert(ram.read32(Request)==S::Reply&&ram.read32(Request+4u)==expected_fd&&ram.read32(Request+8u)==S::Open);
        assert(bus.read32(B::IPC+M::ARMMSG)==Request);
        ++replies;
    }else{
        assert(bus.tick()==S::Pump::Idle&&!bus.external_irq_level());
    }
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    using namespace nwii::runtime;
    ram.cpu=ctx.get();
    for(unsigned i=0;i<bytes.size();++i)ctx->mmu.write8(Vector+i,bytes[i]);
    std::ostringstream out,err;auto* old=std::cout.rdbuf(out.rdbuf());auto* olderr=std::cerr.rdbuf(err.rdbuf());
    unsigned total=0,pairs=0,invocations=0;
    // Start a fresh test entry for each request, but preserve RAM, device
    // descriptors and interrupt latches between successive transactions.
    // The second open deliberately reuses both the mailbox slot and pathname
    // buffer. An extra idle entry detects stale interrupt notifications.
    auto run_entry=[&](bool send,uint32_t fd,std::string_view path){
        auto& c=*ctx;c.pc=Entry;c.lr=Stop;c.msr=c.srr0=c.srr1=0;c.is_running=true;
        c.gpr[5]=c.gpr[6]=0;c.gpr[10]=B::IPC;c.gpr[11]=H::IPC_PPC;
        entries=deliveries=acks=replies=controls=flags=reads=stops=0;
        transaction=send;expected_fd=fd;
        assert(!bus.external_irq_level()&&bus.services().queued_replies()==0u);
        if(send){
            for(unsigned i=0;i<64;++i)ram.write8(Request+i,0u);
            unsigned i=0;for(char ch:path)ram.write8(Path+i++,uint8_t(ch));
            ram.write8(Path+i,0);ram.write32(Request,S::Open);ram.write32(Request+12,Path);
            assert(bus.write32(B::IPC+H::PPC_MASK,H::IPC_PPC)&&bus.write32(B::PI_MASK,H::PI_HOLLYWOOD));
            assert(bus.write32(B::IPC+M::PPCMSG,Request)&&bus.write32(B::IPC+M::PPCCTRL,M::IY1|M::IY2|M::X1));
            assert(bus.tick()==S::Pump::Ack&&bus.services().queued_replies()==1u);++acks;
        }
        run_game(c);
        const unsigned n=send?2u:0u;
        assert(!c.is_running&&c.gpr[5]==1u&&c.gpr[6]==n&&c.msr==B::MSR_EE&&stops==1u);
        assert(entries==n&&deliveries==n&&reads==n&&controls==n&&flags==n&&
               acks==(send?1u:0u)&&replies==(send?1u:0u));
        assert(!bus.external_irq_level()&&bus.services().queued_replies()==0u);
        assert((bus.read32(B::IPC+M::PPCCTRL).value()&(M::Y1|M::Y2|M::X1))==0u);
        assert((bus.read32(B::IPC+H::PPC_FLAG).value()&H::IPC_PPC)==0u);
        if(send){
            assert(ram.read32(Request)==S::Reply&&ram.read32(Request+4u)==fd&&
                   ram.read32(Request+8u)==S::Open);
            ++pairs;
        }
        ++invocations;total+=deliveries;
    };
    for(unsigned trial=0;trial<32u;++trial){
        bus.reset();
        if((trial%2u)==0u){
            const bool reverse=(trial&2u)!=0u;
            const auto first=reverse?S::Device::Event:S::Device::Immediate;
            const auto second=reverse?S::Device::Immediate:S::Device::Event;
            run_entry(true,0u,reverse?"/dev/stm/eventhook":"/dev/stm/immediate");
            assert(bus.services().is_open(0u,first)&&!bus.services().is_open(1u,second));
            run_entry(true,1u,reverse?"/dev/stm/immediate":"/dev/stm/eventhook");
            assert(bus.services().is_open(0u,first)&&bus.services().is_open(1u,second));
            run_entry(false,0u,{});
            assert(bus.services().is_open(0u,first)&&bus.services().is_open(1u,second));
        }else{
            run_entry(false,0u,{});
            assert(!bus.services().is_open(0u,S::Device::Immediate)&&
                   !bus.services().is_open(0u,S::Device::Event));
        }
    }
    std::cout.rdbuf(old);std::cerr.rdbuf(olderr);
    assert(invocations==64u&&pairs==32u&&total==64u&&err.str().find("Fallback dispatch")==std::string::npos&&err.str().find("UNKNOWN DISPATCH")==std::string::npos);
    std::cout<<"PASS: 64 synthetic native entries, 32 IOS ACK/reply pairs (successive STM opens in both orders), 64 generated low-vector rfi returns, no fallback\n";
}
