#include "wii_ipc_dispatch_v1261.h"
#include "wii_deferred_stm_irq_entry.h"
#include <cassert>
#include <iostream>
#include <vector>
#include <string_view>
using namespace undercover::wii;
using B=NativeIosBinding;using Bus=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
constexpr uint32_t Context=0x80006000u,Queue=0x80008000u,Table=0x80003040u,Global=0x80009000u,Counter=0x80009100u,
    Handler=0x80010000u,Resume=0x80005000u,Req=0x100u,Path=0x800u,Out=0xa00u,en=M::IY1|M::IY2;
constexpr SiDispatchExpectations Code{
    std::array<SiDispatchEdge,4>{{{0x80011000u,0x80012004u,1u,2u},{0x80013000u,0x80012008u,3u,4u},
        {0x80014000u,0x80013104u,5u,6u},{0x80015000u,0x80013108u,7u,8u}}},
    0x8001200cu,0x4e800421u,9u,10u};
struct Mmu{
    std::span<uint8_t> mem;WiiPhysicalRam& ram;
    uint8_t* get_ptr(uint32_t a){auto p=a&0x3fffffffu;return p<mem.size()?mem.data()+p:nullptr;}
    uint8_t read8(uint32_t a)const{return ram.read8(a&0x3fffffffu);}
    uint32_t read32(uint32_t a)const{return ram.read32(a&0x3fffffffu);}
    uint16_t read16(uint32_t a)const{return uint16_t((read8(a)<<8)|read8(a+1));}
    void write32(uint32_t a,uint32_t v){ram.write32(a&0x3fffffffu,v);}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=Resume+4,ctr=1,xer=2,msr=0x8032,srr0=3,srr1=4,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void wr(uint32_t off,uint32_t v){assert(B::write32(Bus::IPC+off,v));}
static void open(WiiPhysicalRam& ram,std::string_view path,unsigned fd){
    for(unsigned i=0;i<path.size();++i)ram.write8(Path+i,uint8_t(path[i]));
    ram.write8(Path+path.size(),0);ram.write32(Req,S::Open);ram.write32(Req+12,Path);ram.write32(Req+16,0);
    wr(M::PPCMSG,Req);wr(M::PPCCTRL,en|M::X1);
    auto a=B::service_at_guest_boundary(0);assert(a&&a->progress==S::Pump::Ack);
    wr(M::PPCCTRL,en|M::Y2);wr(H::PPC_FLAG,H::IPC_PPC);
    auto b=B::service_at_guest_boundary(0);assert(b&&b->progress==S::Pump::Replied&&ram.read32(Req+4)==fd);
    wr(M::PPCCTRL,en|M::Y1);wr(H::PPC_FLAG,H::IPC_PPC);
}
static void trial(unsigned first,unsigned fault){
    std::vector<uint8_t> one(0x600000u);std::array<uint8_t,4096> two{};
    std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);B bind(host);auto& ram=host.physical_ram();Cpu c{{one,ram}};
    wr(H::PPC_MASK,H::IPC_PPC);wr(M::PPCCTRL,en);
    open(ram,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    open(ram,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    const uint32_t fd=first==2?0u:1u;
    ram.write32(Req,S::Ioctl);ram.write32(Req+8,fd);ram.write32(Req+12,S::EventHook);
    ram.write32(Req+16,0);ram.write32(Req+20,0);ram.write32(Req+24,Out);ram.write32(Req+28,32);
    StmDeferredEventGate gate;
    assert(gate.begin({Req,fd,0,0,Out,32},first,true)&&gate.submit_write(Bus::IPC+M::PPCMSG,Req,0,true)&&
           gate.submit_write(Bus::IPC+M::PPCCTRL,en|M::X1,0,true)&&gate.accept(0,true));
    auto& m=c.mmu;
    m.write32(0x800000c0u,Context&0x3fffffffu);m.write32(0x800000d4u,Context);m.write32(0x800000e4u,Context);
    m.write32(Context+712,2u<<16);m.write32(Resume,0x60000000u);m.write32(ExternalVector,0x60000000u);
    std::array<uint8_t,4> vector{0x60,0,0,0};ExternalReturnWitness frame;
    assert(enter_deferred_stm_irq(c,host,gate,frame,vector,Req,Context,Resume,0x60000000u,true));
    // Synthetic vector save postcondition, not original vector execution.
    for(unsigned i=0;i<32;++i)m.write32(Context+4*i,c.gpr[i]);
    m.write32(Context+128,0);m.write32(Context+132,c.lr);m.write32(Context+136,c.ctr);m.write32(Context+140,c.xer);
    m.write32(Context+408,c.srr0);m.write32(Context+412,c.srr1);
    m.write32(Global,Table);m.write32(Table+27*4,Handler);m.write32(Counter,0);
    m.write32(SiDispatchWitness::Dispatcher,Code.dispatcher_word);
    m.write32(Code.indirect_pc,Code.indirect_word);m.write32(Handler,Code.handler_word);
    for(auto e:Code.edges){m.write32(e.pc,e.entry_word);m.write32(e.lr-4,e.branch_word);}
    c.pc=SiDispatchWitness::Dispatcher;c.gpr[3]=4;c.gpr[4]=Context;c.inst_count+=50;
    const auto snap=host.cold_ipc_snapshot();auto observed=snap;
    if(fault==1)m.write32(Context+712,4u<<16);
    if(fault==2)m.write32(Queue,Context);
    if(fault==3)m.write32(0x800000e4u,Context+8);
    if(fault==4)observed.event=false;
    if(fault==5)observed.replies=1;
    if(fault==11)observed.arm^=32u;
    IpcDispatchWitness w({Code,Handler,Context,Context,Table,Global,Counter},first);
    bool ok=w.begin_deferred(c,frame,observed,Queue,fault==6?Req+32:Req,gate,fault!=7);
    if((fault>=1&&fault<=7)||fault==11){assert(!ok&&w.failure()==1);return;}assert(ok&&w.deferred_mode()&&!w.reply_mode());
    if(fault==8){++c.inst_count;ram.write32(Req+60,1);assert(!w.before(c,c.pc,Code.dispatcher_word,false,snap,true));return;}
    ++c.inst_count;assert(w.before(c,c.pc,Code.dispatcher_word,false,snap,true));
    assert(w.read(Bus::PI_CAUSE,cause.load())&&w.read(Bus::PI_MASK,mask.load()));
    for(auto e:Code.edges){
        ++c.inst_count;assert(w.before(c,e.lr-4,e.branch_word,false,snap,true));c.pc=e.pc;c.lr=e.lr;
        assert(w.observe(c,c.pc,snap,true));++c.inst_count;assert(w.before(c,c.pc,e.entry_word,false,snap,true));
        assert(w.poll(c,snap,true));
    }
    m.write32(Counter,1);++c.inst_count;assert(w.before(c,Code.indirect_pc,Code.indirect_word,false,snap,true));
    assert(w.poll(c,snap,true));++c.inst_count;c.pc=Handler;c.lr=Code.indirect_pc+4;c.ctr=Handler;c.gpr[3]=27;c.gpr[4]=Context;
    if(fault==9)m.write32(Context+736,1);
    ok=w.observe(c,c.pc,snap,true);if(fault==9){assert(!ok);return;}assert(ok&&w.handler_ready(c,frame,snap,Queue,true));
    if(fault==10){m.write32(Context+140,0);assert(!w.handler_ready(c,frame,snap,Queue,true));return;}
    assert(host.serviced_steps()==5&&gate.deferred_held(true)&&host.services().event_pending()&&ram.read32(Req)==S::Ioctl);
}
int main(){for(unsigned first:{1u,2u})for(unsigned f=0;f<=11;++f)trial(first,f);
    std::cout<<"IPC_DEFERRED_ACTIVE_DISPATCH_TEST cases=24 original_execution=0\n";}
