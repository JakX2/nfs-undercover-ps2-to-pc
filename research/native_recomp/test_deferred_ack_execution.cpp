#include "wii_deferred_ack_execution.h"
#include <cassert>
#include <atomic>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=NativeIosBinding;using I=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
constexpr uint32_t Base=0x80000000u,Req=0x100u,Path=0x400u,Out=0x800u,Resume=Base+0x900u,
    Context=Base+0x1000u,en=M::IY1|M::IY2;
struct Mem{
    std::array<uint8_t,8192> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=Base&&a-Base<ram.size()?ram.data()+a-Base:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint16_t read16(uint32_t a){return uint16_t((read8(a)<<8)|read8(a+1));}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=Resume+4,ctr=1,xer=2,msr=0x8032,srr0=3,srr1=4,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void wr(uint32_t off,uint32_t v){assert(B::write32(I::IPC+off,v));}
static void open(Cpu& c,std::string_view path,unsigned fd){
    for(unsigned i=0;i<path.size();++i)*c.mmu.get_ptr(Base+Path+i)=uint8_t(path[i]);
    *c.mmu.get_ptr(Base+Path+uint32_t(path.size()))=0;
    c.mmu.write32(Base+Req,S::Open);c.mmu.write32(Base+Req+12,Path);c.mmu.write32(Base+Req+16,0);
    wr(M::PPCMSG,Req);wr(M::PPCCTRL,en|M::X1);
    auto a=B::service_at_guest_boundary(0);assert(a&&a->progress==S::Pump::Ack);
    wr(M::PPCCTRL,en|M::Y2);wr(H::PPC_FLAG,H::IPC_PPC);
    auto b=B::service_at_guest_boundary(0);assert(b&&b->progress==S::Pump::Replied&&c.mmu.read32(Base+Req+4)==fd);
    wr(M::PPCCTRL,en|M::Y1);wr(H::PPC_FLAG,H::IPC_PPC);
}
constexpr uint32_t Handler=Base+0x1400u,Read=Base+0x1500u,Write=Base+0x1520u,Prof=Base+0x1600u,
    Caller=Base+0x1700u,Sp=Base+0x1e00u,Ring=Base+0x1100u,Credit=Base+0x1180u,
    U=Credit+4u,P=Credit+8u,A=Base+0x1200u,F=Base+0x1280u;
constexpr uint32_t Ret=0x4e800020u,N=0x60000000u,Stack=0x9421ffe0u,Unstack=0x38210020u,
    Ld=0x80630000u,St=0x90830000u,Inc=0x908d0000u,Dec=0x908d0004u,LR=0x7c0803a6u;
constexpr uint32_t bl(uint32_t p,uint32_t d){return 0x48000001u|((d-p)&0x03fffffcu);}
static void trial(unsigned first,unsigned fault){
    Cpu c;std::array<uint8_t,8192> two{};std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(c.mmu.ram,two,cause,mask);B bind(host);
    wr(H::PPC_MASK,H::IPC_PPC);wr(M::PPCCTRL,en);
    open(c,first==1?"/dev/stm/immediate":"/dev/stm/eventhook",0);
    open(c,first==1?"/dev/stm/eventhook":"/dev/stm/immediate",1);
    uint32_t fd=first==2?0u:1u;
    c.mmu.write32(Base+Req,S::Ioctl);c.mmu.write32(Base+Req+8,fd);c.mmu.write32(Base+Req+12,S::EventHook);
    c.mmu.write32(Base+Req+16,0);c.mmu.write32(Base+Req+20,0);c.mmu.write32(Base+Req+24,Out);c.mmu.write32(Base+Req+28,32);
    StmDeferredEventGate gate;
    assert(gate.begin({Req,fd,0,0,Out,32},first,true)&&gate.submit_write(I::IPC+M::PPCMSG,Req,0,true)&&
           gate.submit_write(I::IPC+M::PPCCTRL,en|M::X1,0,true)&&gate.accept(0,true));
    c.mmu.write32(Ring+16+15*4,Base+Req);c.mmu.write32(P,1);c.mmu.write32(U,1);
    c.mmu.write32(A,Base+Req);c.mmu.write32(F,fd);
    IpcDeferredAckMemory mem;
    assert(mem.begin(c,{Ring,80},{Credit,4},{{P,4},{U,4},{A,128},{F,128}},
                     {Base+Req,64},{Sp-512,520},16,fd,true,0));
    std::array<IpcDispatchWord,16> words{{
        {Handler,Handler,Stack},{Handler,Handler+4,bl(Handler+4,Read)},
        {Handler,Handler+8,bl(Handler+8,Write)},{Handler,Handler+12,bl(Handler+12,Write)},
        {Handler,Handler+16,Inc},{Handler,Handler+20,bl(Handler+20,Prof)},
        {Handler,Handler+24,Unstack},{Handler,Handler+28,LR},{Handler,Handler+32,Ret},
        {Read,Read,Ld},{Read,Read+4,Ret},{Write,Write,St},{Write,Write+4,Ret},
        {Prof,Prof,Dec},{Prof,Prof+4,Ret},{Caller,Caller,N}}};
    if(fault==3)words[0].word=0x900d0000u;
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    const std::array<IpcDispatchEdge,4> edges{{{Handler+4,Read,words[1].word},
        {Handler+8,Write,words[2].word},{Handler+12,Write,words[3].word},{Handler+20,Prof,words[5].word}}};
    c.pc=Handler;c.lr=Caller;c.msr=0x32;c.gpr[1]=Sp;c.gpr[13]=Credit;c.gpr[0]=Caller;
    DeferredAckExecution w({Handler,Caller,N,Handler+32,Read,Write,Prof,Handler+16,Prof,words,edges});
    bool ok=w.begin(c,gate,mem,fault!=1);if(fault==1){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,true);};
    ok=step(Handler,fault==2?N:words[0].word);
    if(fault==2||fault==3){assert(!ok);return;}assert(ok);
    c.mmu.write32(Sp-32,Sp);c.gpr[1]=Sp-32;
    if(fault==4)c.mmu.write32(Sp-28,1);
    ok=step(Handler+4,words[1].word);if(fault==4){assert(!ok);return;}assert(ok);
    c.pc=Read;c.lr=fault==5?Caller:Handler+8;c.gpr[3]=I::IPC+M::PPCCTRL;
    ok=w.entry(c,Read,true);if(fault==5){assert(!ok);return;}assert(ok);
    assert(step(Read,Ld));
    auto v=w.read(c,fault==6?I::IPC+M::PPCMSG:c.gpr[3],true);
    if(fault==6){assert(!v);return;}assert(v);
    c.gpr[3]=fault==7?0u:*v;
    ok=step(Read+4,Ret);if(fault==7){assert(!ok);return;}assert(ok);
    for(unsigned i=0;i<2;++i){
        const auto call=Handler+8+i*4;
        c.gpr[3]=I::IPC+(i?H::PPC_FLAG:M::PPCCTRL);c.gpr[4]=i?H::IPC_PPC:en|M::Y2;
        assert(step(call,bl(call,Write)));c.pc=Write;c.lr=call+4;assert(w.entry(c,Write,true));
        assert(step(Write,St));ok=w.write(c,c.gpr[3],fault==8&&i==0?0u:c.gpr[4],true);
        if(fault==8){assert(!ok);return;}assert(ok);
        assert(step(Write+4,Ret));
    }
    c.gpr[4]=fault==9?0u:1u;
    ok=step(Handler+16,Inc);if(fault==9){assert(!ok);return;}assert(ok);
    c.mmu.write32(Credit,fault==10?0u:1u);
    ok=step(Handler+20,words[5].word);if(fault==10){assert(!ok);return;}assert(ok);
    c.pc=Prof;c.lr=Handler+24;c.gpr[4]=fault==11?1u:0u;assert(w.entry(c,Prof,true));
    ok=step(Prof,Dec);if(fault==11){assert(!ok);return;}assert(ok);
    c.mmu.write32(U,0);
    if(fault==12)c.mmu.write32(P,0);
    ok=step(Prof+4,Ret);if(fault==12){assert(!ok);return;}assert(ok);
    assert(step(Handler+24,Unstack));c.gpr[1]=Sp;
    assert(step(Handler+28,LR));c.lr=Caller;
    if(fault==13)c.gpr[31]=1;
    ok=step(Handler+32,Ret);if(fault==13){assert(!ok);return;}assert(ok);
    c.pc=fault==14?Caller+4:Caller;
    ok=w.poll(c,true);if(fault==14){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.reads()==1&&w.writes()==2&&w.calls()==4&&w.stack_stores()==1&&
           host.serviced_steps()==5&&host.services().event_pending()&&mem.preserved(c));
}
int main(){for(unsigned first:{1u,2u})for(unsigned f=0;f<=14;++f)trial(first,f);
    std::cout<<"DEFERRED_ACK_EXECUTION_TEST cases=30 original_execution=0\n";}
