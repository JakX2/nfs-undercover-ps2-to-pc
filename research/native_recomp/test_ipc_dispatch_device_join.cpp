#include "wii_ipc_dispatch_execution.h"
#include "wii_stm_deferred_event_gate.h"
#include <atomic>
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using Bind=NativeIosBinding;using Bus=IosBus;using Mail=IpcMailbox;using Irq=HollywoodIrq;using IOS=StmIos;
constexpr uint32_t B=0x80000000u,S=B+0x100u,W=B+0x200u,R=B+0x300u,
    Ring=B+0x400u,Credit=B+0x500u,Req=B+0x600u,Sp=B+0x700u,P=B+0x800u,A=B+0x900u,F=B+0xa00u,
    Path=B+0xb00u,Input=B+0xc00u,Output=B+0xd00u,OpenReq=B+0xe00u;
constexpr uint32_t ST=0x90830000u,LD=0x80630000u,Ret=0x4e800020u,N=0x60000000u;
constexpr uint32_t phys(uint32_t a){return a&0x3fffffffu;}
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
constexpr uint32_t en=Mail::IY1|Mail::IY2;
struct Mem{
    std::array<uint8_t,8192> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=S,lr=S,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void wr(uint32_t off,uint32_t value){assert(Bind::write32(Bus::IPC+off,value));}
static void open(Cpu& c,std::string_view path,unsigned fd){
    for(unsigned i=0;i<path.size();++i)*c.mmu.get_ptr(Path+i)=uint8_t(path[i]);
    *c.mmu.get_ptr(Path+uint32_t(path.size()))=0;
    c.mmu.write32(OpenReq,IOS::Open);c.mmu.write32(OpenReq+12,phys(Path));c.mmu.write32(OpenReq+16,0);
    wr(Mail::PPCMSG,phys(OpenReq));wr(Mail::PPCCTRL,en|Mail::X1);
    auto a=Bind::service_at_guest_boundary(0);assert(a&&a->progress==IOS::Pump::Ack);
    wr(Mail::PPCCTRL,en|Mail::Y2);wr(Irq::PPC_FLAG,Irq::IPC_PPC);
    auto b=Bind::service_at_guest_boundary(0);assert(b&&b->progress==IOS::Pump::Replied&&c.mmu.read32(OpenReq+4)==fd);
    wr(Mail::PPCCTRL,en|Mail::Y1);wr(Irq::PPC_FLAG,Irq::IPC_PPC);
}
static void trial(unsigned first,bool input,unsigned fault){
    Cpu c;std::array<uint8_t,8192> two{};
    std::atomic<uint32_t> cause{0},mask{Irq::PI_HOLLYWOOD};
    NativeIosTransport host(c.mmu.ram,two,cause,mask);Bind binding(host);
    wr(Irq::PPC_MASK,Irq::IPC_PPC);wr(Mail::PPCCTRL,en);
    open(c,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    open(c,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    assert(host.serviced_steps()==4u);
    const uint32_t fd=first==2u?0u:1u;
    c.mmu.write32(Req,IOS::Ioctl);c.mmu.write32(Req+8,fd);c.mmu.write32(Req+12,IOS::EventHook);
    c.mmu.write32(Req+16,input?phys(Input):0u);c.mmu.write32(Req+20,input?32u:0u);
    c.mmu.write32(Req+24,phys(Output));c.mmu.write32(Req+28,32);
    for(unsigned i=0;i<32;++i){*c.mmu.get_ptr(Input+i)=0x5a;*c.mmu.get_ptr(Output+i)=0xa5;}
    const std::array<IpcDispatchWord,12> words{{
        {S,S,N},{S,S+4,bl(S+4,W)},{S,S+8,ST},{S,S+12,ST},{S,S+16,ST},
        {S,S+20,bl(S+20,R)},{S,S+24,bl(S+24,W)},{S,S+28,N},
        {W,W,ST},{W,W+4,Ret},{R,R,LD},{R,R+4,Ret}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Ring+4,1);c.mmu.write32(Ring+12,1);c.mmu.write32(Ring+16,Req);c.mmu.write32(Credit,1);
    c.gpr[1]=Sp;
    StmDeferredEventGate gate;
    assert(gate.begin({phys(Req),fd,input?phys(Input):0u,input?32u:0u,phys(Output),32u},first,true));
    IpcDispatchExecution w({S,S,S+28,{{{S+4,W,bl(S+4,W)},{S+20,R,bl(S+20,R)},{S+24,W,bl(S+24,W)}}},
        words,{Ring,80},{Credit,4},16,{{P,4},{P+4,4},{A,8},{F,8}}});
    auto held=[&]{return gate.submission_held(true);};
    assert(w.begin(c,held(),{Req,64},{Sp,64}));
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,held());};
    assert(step(S,N)&&step(S+4,bl(S+4,W)));c.pc=W;c.lr=S+8;assert(w.entry(c,W,held()));
    c.gpr[3]=Bus::IPC+Mail::PPCMSG;c.gpr[4]=phys(Req);
    assert(step(W,ST));
    if(fault==1){assert(!w.write_allowed(c,c.gpr[3]+4,c.gpr[4],held()));return;}
    assert(w.write_allowed(c,c.gpr[3],c.gpr[4],held()));
    assert(gate.submit_write(c.gpr[3],c.gpr[4],c.msr,true)&&w.write_done(c,c.gpr[3],c.gpr[4],held()));
    assert(host.serviced_steps()==4u&&!host.services().event_pending());
    assert(step(W+4,Ret));c.pc=S+8;assert(w.returned(c,c.pc,held()));
    for(unsigned i=0;i<3;++i){
        c.gpr[3]=i==0?Ring+8:i==1?Ring:Credit;c.gpr[4]=i==2?0u:1u;
        assert(step(S+8+4*i,ST));c.mmu.write32(c.gpr[3],c.gpr[4]);
    }
    assert(step(S+20,bl(S+20,R)));c.pc=R;c.lr=S+24;assert(w.entry(c,R,held()));
    c.gpr[3]=Bus::IPC+Mail::PPCCTRL;assert(step(R,LD));
    assert(w.read_allowed(c,c.gpr[3],held()));
    auto ctrl=gate.read_submission_control(c.gpr[3],c.msr,true);
    assert(ctrl&&*ctrl==en&&w.read_done(c,*ctrl,held()));
    c.gpr[3]=*ctrl;assert(step(R+4,Ret));c.pc=S+24;assert(w.returned(c,c.pc,held()));
    assert(step(S+24,bl(S+24,W)));c.pc=W;c.lr=S+28;assert(w.entry(c,W,held()));
    c.gpr[3]=Bus::IPC+Mail::PPCCTRL;c.gpr[4]=fault==2?Mail::X1:en|Mail::X1;
    assert(step(W,ST)&&w.write_allowed(c,c.gpr[3],c.gpr[4],held()));
    const bool submitted=gate.submit_write(c.gpr[3],c.gpr[4],c.msr,true);
    if(fault==2){assert(!submitted&&host.serviced_steps()==4u);return;}
    assert(submitted&&w.write_done(c,c.gpr[3],c.gpr[4],held()));
    assert(step(W+4,Ret));c.pc=S+28;
    if(fault==3){c.mmu.write32(Ring,0);assert(!w.returned(c,c.pc,held()));return;}
    assert(w.returned(c,c.pc,held())&&w.reached(c,held()));
    auto before=host.cold_ipc_snapshot();
    assert(before.steps==4u&&before.queued&&!before.event&&!before.replies&&(before.control&Mail::X1));
    if(fault==4){*c.mmu.get_ptr(Output+5)=0;assert(!gate.accept(c.msr,true)&&host.serviced_steps()==4u);return;}
    if(fault==5){assert(!gate.accept(c.msr|Bus::MSR_EE,true)&&host.serviced_steps()==4u);return;}
    assert(gate.accept(c.msr,w.reached(c,held())));
    assert(gate.deferred_held(true)&&w.reached(c,gate.deferred_held(true)));
    auto after=host.cold_ipc_snapshot();
    assert(after.steps==5u&&!after.queued&&after.event&&!after.replies&&(after.control&Mail::Y2)&&!(after.control&Mail::X1));
    assert((cause.load()&mask.load())==Irq::PI_HOLLYWOOD&&host.services().event_pending());
    assert(c.mmu.read32(Req)==IOS::Ioctl&&c.mmu.read32(Ring)==1u&&c.mmu.read32(Credit)==0u);
    for(unsigned i=0;i<32;++i)assert(c.mmu.read8(Output+i)==0xa5);
    // No implicit callback, reply or acknowledgment has been manufactured.
    if(fault==6){c.mmu.write32(F,1);assert(!w.reached(c,gate.deferred_held(true)));}
}
int main(){for(unsigned first:{1u,2u})for(bool input:{false,true})for(unsigned f=0;f<=6;++f)trial(first,input,f);
    std::cout<<"IPC_DISPATCH_DEVICE_JOIN_TEST cases=28 original_execution=0\n";}
