#include "wii_deferred_active_return.h"
#include <cassert>
#include <atomic>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=NativeIosBinding;using I=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
constexpr uint32_t Base=0x80000000u,Req=0x100u,Path=0x400u,Out=0x800u,Resume=Base+0x900u,
    Context=Base+0x1000u,en=M::IY1|M::IY2;
struct Mem{
    std::array<uint8_t,8192> ram{},ram2{};
    uint8_t* get_ptr(uint32_t a){
        if(a>=Base&&a-Base<ram.size())return ram.data()+a-Base;
        if(a>=0x90000000u&&a-0x90000000u<ram2.size())return ram2.data()+a-0x90000000u;
        return nullptr;
    }
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
constexpr uint32_t Wait=Base+0x1400u,Count=Base+0x1410u,Ring=Base+0x1500u,Credit=Base+0x1580u,
    P=Credit+4u,U=P+4u,A=Base+0x1600u,F=Base+0x1680u,Rfi=Base+0x1800u,Sp=Base+0x1e00u;
static void trial(unsigned first,unsigned fault){
    Cpu c;std::atomic<uint32_t> cause{0},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(c.mmu.ram,c.mmu.ram2,cause,mask);B bind(host);
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
    c.gpr[1]=Sp;c.gqr[3]=0x1234;c.cr[0].eq=true;
    const auto gp=c.gpr;const auto gqr=c.gqr;const auto cr=c.cr;const auto lr=c.lr,ctr=c.ctr,xer=c.xer,msr=c.msr;
    ExternalReturnWitness frame;
    assert(frame.capture(c,cause.load(),mask.load(),H::PI_HOLLYWOOD));
    for(unsigned i=0;i<32;++i)c.mmu.write32(Context+i*4,gp[i]);
    c.mmu.write32(Context+128,0x20000000u);c.mmu.write32(Context+132,lr);c.mmu.write32(Context+136,ctr);c.mmu.write32(Context+140,xer);
    c.mmu.write32(Context+408,Resume);c.mmu.write32(Context+412,msr);
    c.mmu.write32(Base+0xc0,Context&0x3fffffffu);c.mmu.write32(Base+0xd4,Context);c.mmu.write32(Base+0xe4,Context);
    c.mmu.write32(Context+712,2u<<16);c.mmu.write32(Count,1);c.mmu.write32(Rfi,0x4c000064u);
    c.msr&=~0x8000u;c.pc=Rfi;c.inst_count+=50;
    assert(gate.ack_write(I::IPC+M::PPCCTRL,en|M::Y2,0,true)&&gate.ack_write(I::IPC+H::PPC_FLAG,H::IPC_PPC,0,true));
    assert(mem.latch_cleared(c,true)&&mem.authorize(c,Credit,1,4,true));c.mmu.write32(Credit,1);
    assert(mem.authorize(c,U,0,4,true));c.mmu.write32(U,0);assert(mem.complete(c,true));
    DeferredActiveReturnJoin join;
    if(fault==2)c.mmu.write32(Context+712,4u<<16);
    if(fault==3)c.mmu.write32(Count,0);
    if(fault==4)c.gqr[3]^=1;
    const uint32_t wait=fault==15?0x90000101u:fault==16?0x90002000u:
        fault==17?0xd0000100u:fault==18?0x90001ffcu:fault>=13?0x90000100u:Wait;
    bool ok=join.begin(c,frame,gate,mem,Context,wait,Count,gqr,fault!=1);
    if(fault>=15&&fault<=18){assert(!ok&&join.detail()==12);return;}
    if(fault>=1&&fault<=4){
        constexpr unsigned details[]={0,1,7,9,5};
        assert(!ok&&join.failure()==1&&join.detail()==details[fault]);
        assert(join.gqr_mismatch_mask()==(fault==4?8u:0u));return;
    }assert(ok);
    if(fault==5||fault==14){c.mmu.write32(wait,Context);assert(!join.held(c,true));return;}
    if(fault==6){c.mmu.write32(Context+736,1);assert(!join.held(c,true));return;}
    if(fault==7){c.mmu.write32(Base+0xe4,Context+8);assert(!join.held(c,true));return;}
    if(fault==8){c.mmu.write32(Base+Req+60,1);assert(!join.held(c,true));return;}
    c.gpr=gp;c.gqr=gqr;c.cr=cr;c.lr=lr;c.ctr=ctr;c.xer=xer;c.srr0=Resume;c.srr1=msr;
    c.mmu.write32(Count,fault==9?1u:0u);++c.inst_count;
    assert(join.held(c,true)&&frame.before_rfi(c,Rfi,0x4c000064u,cause.load(),mask.load()));
    c.pc=Resume;c.msr=msr;
    assert(frame.poll(c,cause.load(),mask.load()));
    if(fault==10){assert(!join.finish(c,true));return;}
    assert(frame.poll(c,cause.load(),mask.load()));
    if(fault==11)c.gqr[3]^=1;
    ok=join.finish(c,true);
    if(fault==9||fault==11){assert(!ok);return;}assert(ok&&join.resumed(c,true));
    if(fault==12){++c.inst_count;assert(!join.resumed(c,true));}
    if(fault>=19){
        assert(!join.post_resume_storage_held(c,true,msr));
        c.mmu.write32(Resume,0x60000000u);c.inst_count+=2;
        assert(frame.resume(c,Resume,0x60000000u,cause.load(),mask.load()));
        assert(join.post_resume_storage_held(c,true,msr));
        c.msr&=~0x8000u;
        assert(!join.continuation_held(c,true)&&join.post_resume_storage_held(c,true,msr&~0x8000u));
        assert(!join.post_resume_storage_held(c,true,msr));
        if(fault==20){c.gqr[4]^=1;assert(!join.post_resume_storage_held(c,true,c.msr));}
        if(fault==21){c.mmu.write32(wait,Context);assert(!join.post_resume_storage_held(c,true,c.msr));}
        if(fault==22){c.mmu.write32(Count,1);assert(!join.post_resume_storage_held(c,true,c.msr));}
    }
}
int main(){for(unsigned first:{1u,2u})for(unsigned f=0;f<=22;++f)trial(first,f);
    std::cout<<"DEFERRED_ACTIVE_RETURN_TEST cases=46 original_execution=0\n";}
