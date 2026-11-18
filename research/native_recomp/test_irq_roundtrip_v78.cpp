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
constexpr uint32_t Request=0x2000u,Path=0x2100u,Event=0x2200u,Output=0x2300u,State=0x2340u,FileOut=0x2380u,FileMeta=0x23c0u;
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
enum class EntryKind { Idle, Open, Hook, StateQuery, EventReply, FileOpen, FileRead, FileSeek, FileStats, Close };
static EntryKind kind=EntryKind::Idle;
static uint32_t expected_result=0,expected_slot=Request,expected_command=S::Open;
static unsigned expected_irqs=0;
static uint32_t expected_y(){
    return kind==EntryKind::EventReply||reads>0u?M::Y1:M::Y2;
}
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==Entry)return;
    assert(pc==Vector&&deliveries==entries+1u&&c.srr0==Resume&&!(c.msr&B::MSR_EE));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(!bus.external_exception_pending(c.msr))return false;
    assert(kind!=EntryKind::Idle&&deliveries<expected_irqs&&c.pc==Resume&&c.gpr[5]==0u&&c.gpr[6]==deliveries);
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
    assert(a==B::IPC+M::PPCCTRL&&kind!=EntryKind::Idle&&entries==reads+1u);
    const auto v=bus.read32(a).value();
    assert((v&(M::Y1|M::Y2))==expected_y());
    ++reads;return v;
}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    assert(kind!=EntryKind::Idle&&entries>0u&&ram.cpu&&!(ram.cpu->msr&B::MSR_EE));
    if(a==B::IPC+M::PPCCTRL){
        assert(controls+1u==entries&&v==(M::IY1|M::IY2|((kind==EntryKind::EventReply||controls>0u)?M::Y1:M::Y2)));
        assert(bus.write32(a,v));++controls;
        assert(bus.tick()==S::Pump::Busy); // IRQ latch still active
        return;
    }
    assert(a==B::IPC+H::PPC_FLAG&&v==H::IPC_PPC&&flags+1u==controls);
    assert(bus.write32(a,v)&&!bus.external_irq_level());++flags;
    if(flags==1u&&expected_irqs==2u){
        assert(bus.tick()==S::Pump::Replied&&bus.external_irq_level());
        assert(ram.read32(expected_slot)==S::Reply&&ram.read32(expected_slot+4u)==expected_result&&
               ram.read32(expected_slot+8u)==expected_command);
        assert(bus.read32(B::IPC+M::ARMMSG)==expected_slot);
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
    auto guest_files=std::make_shared<GuestFiles>();
    assert(guest_files->add("/shared2/sys/example.bin",{0x10,0x20,0x30,0x40,0x50}));
    assert(bus.services().mount_filesystem(guest_files));
    for(unsigned i=0;i<bytes.size();++i)ctx->mmu.write8(Vector+i,bytes[i]);
    std::ostringstream out,err;auto* old=std::cout.rdbuf(out.rdbuf());auto* olderr=std::cerr.rdbuf(err.rdbuf());
    unsigned total=0,pairs=0,invocations=0,deferred=0,completed=0;
    // Start a fresh test entry for each request, but preserve RAM, device
    // descriptors and interrupt latches between successive transactions.
    // The second open deliberately reuses both the mailbox slot and pathname
    // buffer. An extra idle entry detects stale interrupt notifications.
    auto run_entry=[&](EntryKind next,uint32_t fd,std::string_view path={},uint32_t event_code=0u){
        auto& c=*ctx;c.pc=Entry;c.lr=Stop;c.msr=c.srr0=c.srr1=0;c.is_running=true;
        c.gpr[5]=c.gpr[6]=0;c.gpr[10]=B::IPC;c.gpr[11]=H::IPC_PPC;
        entries=deliveries=acks=replies=controls=flags=reads=stops=0;
        kind=next;
        const bool opening=next==EntryKind::Open||next==EntryKind::FileOpen;
        expected_result=opening?fd:next==EntryKind::FileRead?event_code:next==EntryKind::FileSeek?1u:0u;
        expected_slot=(next==EntryKind::Hook||next==EntryKind::EventReply)?Event:Request;
        expected_command=opening?S::Open:next==EntryKind::FileRead?S::Read:
                         next==EntryKind::FileSeek?S::Seek:next==EntryKind::Close?S::Close:S::Ioctl;
        expected_irqs=next==EntryKind::Idle?0u:
                      (next==EntryKind::Hook||next==EntryKind::EventReply?1u:2u);
        assert(!bus.external_irq_level()&&bus.services().queued_replies()==0u);
        const bool send=next!=EntryKind::Idle&&next!=EntryKind::EventReply;
        if(send){
            for(unsigned i=0;i<64;++i)ram.write8(expected_slot+i,0u);
            if(opening){
                unsigned i=0;for(char ch:path)ram.write8(Path+i++,uint8_t(ch));
                ram.write8(Path+i,0);ram.write32(expected_slot,S::Open);ram.write32(expected_slot+12,Path);
                ram.write32(expected_slot+16u,next==EntryKind::FileOpen?1u:0u);
            }else if(next==EntryKind::FileRead||next==EntryKind::FileSeek||next==EntryKind::Close){
                ram.write32(expected_slot,expected_command);ram.write32(expected_slot+8u,fd);
                if(next==EntryKind::FileRead){ram.write32(expected_slot+12u,FileOut);ram.write32(expected_slot+16u,event_code);}
                if(next==EntryKind::FileSeek){ram.write32(expected_slot+12u,uint32_t(-2));ram.write32(expected_slot+16u,1u);}
            }else if(next==EntryKind::FileStats){
                ram.write32(expected_slot,S::Ioctl);ram.write32(expected_slot+8u,fd);
                ram.write32(expected_slot+12u,S::FileStats);ram.write32(expected_slot+24u,FileMeta);
                ram.write32(expected_slot+28u,8u);
            }else{
                ram.write32(expected_slot,S::Ioctl);ram.write32(expected_slot+8u,fd);
                ram.write32(expected_slot+12u,next==EntryKind::Hook?S::EventHook:S::GetState);
                ram.write32(expected_slot+24u,next==EntryKind::Hook?Output:State);
                ram.write32(expected_slot+28u,4u);
            }
            assert(bus.write32(B::IPC+H::PPC_MASK,H::IPC_PPC)&&bus.write32(B::PI_MASK,H::PI_HOLLYWOOD));
            assert(bus.write32(B::IPC+M::PPCMSG,expected_slot)&&bus.write32(B::IPC+M::PPCCTRL,M::IY1|M::IY2|M::X1));
            assert(bus.tick()==(next==EntryKind::Hook?S::Pump::Deferred:S::Pump::Ack));
            assert(bus.services().queued_replies()==(next==EntryKind::Hook?0u:1u));++acks;
        }else if(next==EntryKind::EventReply){
            assert(bus.services().event_pending()&&bus.services().signal_event(event_code));
            assert(!bus.external_irq_level()&&bus.tick()==S::Pump::Replied&&bus.external_irq_level());
        }
        run_game(c);
        const unsigned n=expected_irqs;
        assert(!c.is_running&&c.gpr[5]==1u&&c.gpr[6]==n&&c.msr==B::MSR_EE&&stops==1u);
        assert(entries==n&&deliveries==n&&reads==n&&controls==n&&flags==n&&
               acks==(send?1u:0u)&&replies==(n==2u?1u:0u));
        assert(!bus.external_irq_level()&&bus.services().queued_replies()==0u);
        assert((bus.read32(B::IPC+M::PPCCTRL).value()&(M::Y1|M::Y2|M::X1))==0u);
        assert((bus.read32(B::IPC+H::PPC_FLAG).value()&H::IPC_PPC)==0u);
        if(n==2u||next==EntryKind::EventReply){
            assert(ram.read32(expected_slot)==S::Reply&&ram.read32(expected_slot+4u)==expected_result&&
                   ram.read32(expected_slot+8u)==expected_command);
            assert(bus.read32(B::IPC+M::ARMMSG)==expected_slot);
            if(n==2u)++pairs;else ++completed;
        }
        if(next==EntryKind::Hook){
            assert(bus.services().event_pending()&&ram.read32(Event)==S::Ioctl);
            ++deferred;
        }
        if(next==EntryKind::EventReply)assert(!bus.services().event_pending()&&ram.read32(Output)==event_code);
        ++invocations;total+=deliveries;
    };
    for(unsigned trial=0;trial<32u;++trial){
        bus.reset();
        if((trial%2u)==0u){
            const bool reverse=(trial&2u)!=0u;
            const auto first=reverse?S::Device::Event:S::Device::Immediate;
            const auto second=reverse?S::Device::Immediate:S::Device::Event;
            const auto event_fd=reverse?0u:1u,immediate_fd=1u-event_fd;
            run_entry(EntryKind::Open,0u,reverse?"/dev/stm/eventhook":"/dev/stm/immediate");
            assert(bus.services().is_open(0u,first)&&!bus.services().is_open(1u,second));
            run_entry(EntryKind::Open,1u,reverse?"/dev/stm/immediate":"/dev/stm/eventhook");
            assert(bus.services().is_open(0u,first)&&bus.services().is_open(1u,second));
            // The ACK and deferred reply arrive in distinct native entries.
            // A synchronous command must complete while the event is pending.
            ram.write32(Output,0x11223344u);ram.write32(Output+4u,0x55667788u);
            ram.write32(State,0xffffffffu);
            run_entry(EntryKind::Hook,event_fd);
            run_entry(EntryKind::Idle,0u);
            assert(bus.services().event_pending()&&ram.read32(Output)==0x11223344u);
            run_entry(EntryKind::StateQuery,immediate_fd);
            assert(ram.read32(State)==0u&&bus.services().event_pending()&&ram.read32(Event)==S::Ioctl);
            // Real IOS file requests retain independent handles and cursor
            // state across separate generated native IRQ/RFI executions.
            run_entry(EntryKind::Open,2u,"/dev/fs");
            run_entry(EntryKind::FileOpen,3u,"/shared2/sys/example.bin");
            assert(bus.services().is_open(2u,S::Device::Fs)&&bus.services().is_open(3u,S::Device::File));
            ram.write32(FileOut,0xa5a5a5a5u);ram.write32(FileOut+4u,0xabcdef01u);
            run_entry(EntryKind::FileRead,3u,{},3u);
            assert(ram.read32(FileOut)==0x102030a5u);
            run_entry(EntryKind::FileSeek,3u);
            run_entry(EntryKind::FileStats,3u);
            assert(ram.read32(FileMeta)==5u&&ram.read32(FileMeta+4u)==1u);
            run_entry(EntryKind::FileRead,3u,{},4u);
            assert(ram.read32(FileOut)==0x20304050u&&ram.read32(FileOut+4u)==0xabcdef01u);
            run_entry(EntryKind::Close,3u);run_entry(EntryKind::Close,2u);
            assert(!bus.services().is_open(2u,S::Device::Fs)&&!bus.services().is_open(3u,S::Device::File));
            assert(bus.services().event_pending()&&ram.read32(Event)==S::Ioctl&&ram.read32(Output)==0x11223344u);
            run_entry(EntryKind::EventReply,event_fd,{},0x20000u+trial);
            assert(ram.read32(Output+4u)==0x55667788u);
            run_entry(EntryKind::Idle,0u);
            assert(bus.services().is_open(0u,first)&&bus.services().is_open(1u,second));
        }else{
            run_entry(EntryKind::Idle,0u);
            assert(!bus.services().is_open(0u,S::Device::Immediate)&&
                   !bus.services().is_open(0u,S::Device::Event));
        }
    }
    std::cout.rdbuf(old);std::cerr.rdbuf(olderr);
    assert(invocations==256u&&pairs==176u&&deferred==16u&&completed==16u&&total==384u&&err.str().find("Fallback dispatch")==std::string::npos&&err.str().find("UNKNOWN DISPATCH")==std::string::npos);
    std::cout<<"PASS: 256 synthetic native entries, 176 synchronous IOS pairs (including read-only filesystem transactions), 16 deferred event ACKs and 16 later event replies, 384 generated low-vector rfi returns, no fallback\n";
}
