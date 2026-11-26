#include "wii_post_ack_open_join_v1242.h"
#include <iostream>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=IpcClientWitness;using B=NativeIosBinding;using H=HollywoodIrq;using M=IpcMailbox;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V623 line "+std::to_string(l.line()));
}
struct Mmu {
    static constexpr uint32_t heap=0x93380000u;
    std::vector<uint8_t> mem1=std::vector<uint8_t>(24u*1024u*1024u);
    std::array<uint8_t,W::HeapLimit+2u> mem2{};
    uint8_t* get_ptr(uint32_t a){
        if(a>=0x80000000u&&a<0x81800000u)return mem1.data()+(a-0x80000000u);
        if(a>=heap-1u&&a<=heap+W::HeapLimit)return mem2.data()+(a-(heap-1u));
        return nullptr;
    }
    uint8_t read8(uint32_t a){auto* p=get_ptr(a);need(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto* p=get_ptr(a+i);need(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr {bool lt=false,gt=false,eq=false,so=false;};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0,lr=0,msr=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
    std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t ctr=0,xer=0,srr0=0,srr1=0,hid0=0x100;
    OpenCacheRangeTrace open_cache_range;
    uint32_t guest_flush_count=18000,guest_last_flush=0,guest_sync_count=0,guest_isync_count=0;
};
int main(){
    constexpr std::array<uint32_t,17> pc{
        W::Root,0x80518fc8,0x8052ae70,0x8052ae78,0x80519084,0x8051907c,0x8051aa04,
        0x805265ac,0x805265d4,0x8051908c,0x805265f8,0x805269bc,0x805265ac,
        0x805266e0,0x805265d4,0x8051906c,0x8051af28};
    constexpr std::array<uint32_t,17> lr{
        W::Return,0x805194f8,0x80518fe4,0x80518fec,0x805194fc,0x80519508,0x80519524,
        0x8051aa2c,0x8051ab14,0x80519530,0x80519540,0x80519548,0x805269dc,
        0x80526a0c,0x80526a1c,0x80519554,0x80519558};
    IpcClientExpectations e{};
    for(unsigned i=0;i<pc.size();++i)e.edges[i]={pc[i],lr[i],0x100u+i,pc[i]};
    e.edges[0].branch_word=0x48000001u|((W::Root-W::Call)&0x03fffffcu);
    e.handler=0x80519094u;e.handler_word=0x1234u;e.return_word=0x5678u;
    using S=StmPrefixWitness;
    StmPrefixExpectations stm{};
    stm.bridge.fill(0x60000000u);stm.bridge.back()=0x48000001u|((S::Stm-(S::Begin+24u))&0x03fffffcu);
    stm.stm={S::Stm,S::Begin+28u,stm.bridge.back(),0x60000000u};
    stm.open={S::Open,0x8052b090u,0x48000001u|((S::Open-0x8052b08cu)&0x03fffffcu),0x60000000u};
    stm.paths[0]={0x80601000u,1};stm.paths[1]={0x80602000u,2};
    stm.path_count=2;stm.irq_handler=e.handler;e.return_word=stm.bridge[0];
    using O=OpenRequestWitness;using R=OpenScRoute;
    OpenRequestExpectations op{stm.open,{O::Profile,0x8051998cu,3,4},
        {O::Disable,0x8051ab64u,5,6},{O::Restore,0x8051ad14u,7,8},
        {O::Flush,R::Caller,9,10},{O::Submit,0x80519a3cu,11,12},13,0x44000002u,14};
    // Synthetic cache vector fixture; native vector execution is a separate owner proof.
    const std::array<uint8_t,28> bytes{};
    unsigned valid=0,refused=0;
    for(unsigned test=0;test<=15;++test){
        const unsigned lane=test==15?16:0;
        constexpr unsigned fault=0;
        Cpu c;auto& m=c.mmu;std::atomic<uint32_t> cause{0},mask{0xf0};
        NativeIosTransport host(m.mem1,m.mem2,cause,mask);B binding(host);PostAckIpcJoin w(e,{W::Call,W::Root,e.edges[0].branch_word,e.edges[0].entry_word});
        m.mem2.fill(0x6b);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        c.pc=c.lr=W::Call;c.gpr[1]=W::Stack;c.gpr[13]=W::Sda;
        for(auto x:e.edges){m.write32(x.pc,x.entry_word);m.write32(x.lr-4u,x.branch_word);}
        m.write32(e.handler,e.handler_word);m.write32(W::Return,e.return_word);
        for(unsigned i=0;i<stm.bridge.size();++i)m.write32(S::Begin+4*i,stm.bridge[i]);
        for(auto edge:{stm.stm,stm.open}){m.write32(edge.pc,edge.entry_word);m.write32(edge.lr-4,edge.branch_word);}
        for(unsigned k=0;k<2;++k){
            const std::string_view path=k?"/dev/stm/eventhook":"/dev/stm/immediate";
            for(unsigned i=0;i<path.size();++i)*m.get_ptr(stm.paths[k].addr+i)=uint8_t(path[i]);
        }
        m.write32(W::Lo,Mmu::heap);m.write32(W::Hi,0x93400000u);
        m.write32(W::Sda-16336u,Mmu::heap);m.write32(W::Sda-3352u,0x93400000u);
        m.write32(W::MaskA,0xf7fff7f0u);m.write32(W::IrqGlobal,W::Table);
        if(fault==1)c.msr&=~0x8000u;
        if(fault==2)m.write32(W::Hi,Mmu::heap+16);
        if(fault==3)m.write32(W::Table+108u,1);
        if(fault==4)need(B::write32(IosBus::IPC+M::PPCCTRL,0x31));
        if(fault==18)m.write32(W::IrqGlobal,0);
        const bool bad_begin=(fault>=1&&fault<=4)||fault==18;
        need(w.pre_dispatch(c,W::Call,true,true)==!bad_begin);
        if(bad_begin){
            const uint32_t expected=fault==1?2u:fault==2?(2048u|4096u):fault==3?16384u:
                fault==4?(16u|32u):512u;
            need(w.cold_refusal()==expected);continue;
        }
        need(!w.cold_refusal());
        ++c.inst_count;
        need(w.before_call(c,W::Call,e.edges[0].branch_word,true,true));
        c.pc=W::Root;c.lr=W::Return;
        need(w.target_entry(c,c.pc,true)&&w.stage()==3u&&w.client_stage()==2u);
        if(fault==20){need(!w.continuation(c,c.pc,true)&&w.failure()==4u);continue;}
        if(fault==21){need(!w.continuation(c,c.pc,false)&&w.failure()==4u);continue;}
        bool stopped=false;
        for(unsigned i=1;i<17;++i){
            c.pc=pc[i];c.lr=lr[i];c.inst_count+=10;
            c.msr=(i==8||i==13||i==14)?0x32u:0x8032u;
            if(i==0)c.gpr[3]=0;
            if(i==5)c.gpr[3]=Mmu::heap;
            if(i==6){c.gpr[3]=Mmu::heap;c.gpr[4]=fault==6?33:64;}
            if(i==8||i==14)c.gpr[3]=1;
            if(i==9){
                c.gpr[3]=Mmu::heap+64;
                if(fault!=7)m.write32(Mmu::heap,0x12345678);
                if(fault==8)*m.get_ptr(Mmu::heap-1u)^=1;
                if(fault==9)*m.get_ptr(Mmu::heap+64u)^=1;
            }
            if(i==10){c.gpr[3]=27;c.gpr[4]=e.handler+(fault==10?4:0);}
            if(i==11){c.gpr[3]=0x10;m.write32(W::Table+108u,e.handler);}
            if(i==13)c.gpr[3]=0x10;
            if(i==15){
                mask.fetch_or(H::PI_HOLLYWOOD);
                m.write32(W::MaskA,0xf7fff7e0u);
                c.gpr[3]=1;c.gpr[4]=fault==11?0x31:0x36;
            }
            if(i==2&&fault==5)c.lr+=4;
            if(i==10&&fault==19)m.write32(W::IrqGlobal,W::Table+4);
            if(i==12&&fault==12)cause=0x10;
            if(i==16&&fault!=13){
                need(B::write32(IosBus::IPC+M::PPCCTRL,0x36));
                if(fault==14){bool refused=false;try{B::write32(IosBus::IPC+M::PPCCTRL,0x36);}catch(const std::runtime_error&){refused=true;}need(refused);}
            }
            const bool bad=(i==2&&fault==5)||(i==6&&fault==6)||(i==9&&fault>=7&&fault<=9)||
                (i==10&&(fault==10||fault==19))||(i==15&&fault==11)||(i==12&&fault==12)||(i==16&&(fault==13||fault==14));
            const bool denied=bad||(fault==22&&i==15);
            need(w.continuation(c,c.pc,!(fault==22&&i==15))==!denied);
            if(denied){need(w.failure()==4u);stopped=true;break;}
        }
        if(stopped)continue;
        c.pc=c.lr=W::Return;c.gpr[3]=0;c.msr=0x8032;c.inst_count+=10;
        if(fault==15)c.gpr[14]=1;
        if(fault==16)m.write32(W::Table+4,1);
        if(fault==17)m.write32(W::MaskA,0xf7fff7f0u);
        need(w.continuation(c,c.pc,fault!=23)==(fault==0));
        need(w.stage()==5u&&w.returned_at(c)&&w.heap_size()==64);
        PostAckStmJoin next(stm);
        if(lane==1)++c.inst_count;
        if(lane==2)c.in_callback=true;
        if(lane==3)c.mmu.write32(S::Begin+4u,0u);
        if(lane==4)c.mmu.write32(W::Table+108u,0u);
        if(lane==5){need(!next.begin(c,w,false)&&next.failure()==1);++refused;continue;}
        const bool bad_stm_begin=lane>=1&&lane<=4;
        need(next.begin(c,w,true)==!bad_stm_begin);
        if(bad_stm_begin){need(next.failure()==1);++refused;continue;}
        need(next.stage()==1u&&next.heap_size()==64u&&next.boundary(c,true));
        if(lane==6){need(!next.begin(c,w,true));++refused;continue;}
        c.pc=S::Stm;c.lr=stm.stm.lr;c.inst_count+=7;
        if(lane==7)c.lr+=4;
        if(lane==8)c.gpr[1]-=8;
        if(lane==9)c.mmu.write32(W::Table+4,1u);
        if(lane==10)cause.fetch_or(0x10000000u);
        const bool bad_root=lane>=7&&lane<=10;
        need(next.observe(c,c.pc,true)==!bad_root);
        if(bad_root){need(next.failure()==2);++refused;continue;}
        c.pc=S::Open;c.lr=stm.open.lr;c.inst_count+=22;
        c.gpr[1]-=32;c.gpr[3]=stm.paths[lane==16?1:0].addr;c.gpr[4]=0;
        if(lane==11)c.gpr[4]=1;
        if(lane==12)*m.get_ptr(c.gpr[3])=0;
        if(lane==13)c.in_callback=true;
        if(lane==14)++c.inst_count,c.inst_count+=8192u;
        const bool good=lane==0||lane==16;
        need(next.observe(c,c.pc,lane!=15)==good);
        need(good&&next.stage()==3u&&next.open_at(c)&&next.path_kind()==(lane==16?2u:1u)&&host.serviced_steps()==0);
        for(auto x:{op.profile,op.disable,op.restore,op.flush,op.submit}){
            m.write32(x.pc,x.entry_word);m.write32(x.lr-4u,x.branch_word);
        }
        m.write32(O::Alloc,op.alloc_word);m.write32(R::Call,op.sc_word);m.write32(R::Resume,0x4e800020u);m.write32(R::Caller,op.flush_return_word);
        PostAckOpenJoin open(op,bytes);
        const uint32_t path=c.gpr[3],req=Mmu::heap+32u;
        if(test==1)++c.inst_count;
        if(test==2)c.in_callback=true;
        if(test==3)c.gpr[4]=1;
        const bool denied_begin=test>=1&&test<=4;
        need(open.begin(c,next,test!=4)==!denied_begin);
        if(denied_begin){need(open.failure()==1);++refused;continue;}
        need(open.stage()==1u&&open.boundary(c,true));
        if(test==5){need(!open.begin(c,next,true));++refused;continue;}
        c.gpr[1]-=32u;
        auto enter=[&](VectorEdge edge){c.pc=edge.pc;c.lr=edge.lr;c.inst_count+=10;};
        enter(op.profile);
        if(test==6)c.lr+=4;
        need(open.observe(c,c.pc,test!=7)==(test!=6&&test!=7));
        if(test==6||test==7){++refused;continue;}
        c.pc=O::Alloc;++c.inst_count;c.gpr[4]=64u;need(open.observe(c,c.pc,true));
        enter(op.disable);need(open.observe(c,c.pc,true));
        enter(op.restore);c.msr&=~0x8000u;c.gpr[3]=1u;need(open.observe(c,c.pc,true));
        enter(op.flush);c.msr|=0x8000u;c.gpr[3]=path;c.gpr[4]=19u;need(open.observe(c,c.pc,true));
        c.open_cache_range.on_flush(path+(test==8?32u:0u));
        c.pc=R::Call;c.inst_count+=10;++c.guest_flush_count;c.guest_last_flush=path;
        need(open.observe(c,c.pc,true)==(test!=8));if(test==8){++refused;continue;}
        if(test==9){need(!open.vector_trace(c,R::Vector,true));++refused;continue;}
        ++c.inst_count;if(test==10)++c.inst_count;
        bool dispatched=open.dispatch(c,true,[&](Cpu& cpu){
            if(!open.vector_trace(cpu,R::Vector,true))throw std::runtime_error("vector");
            cpu.gpr[9]=cpu.hid0;cpu.gpr[10]=cpu.hid0|8u;
            cpu.inst_count+=7;cpu.pc=cpu.srr0;cpu.msr=cpu.srr1;
        },[](const Cpu&,const auto&,uint32_t){return true;});
        need(dispatched==(test!=10));if(test==10){++refused;continue;}
        c.pc=R::Caller;++c.inst_count;need(open.observe(c,c.pc,true));
        enter(op.submit);c.gpr[3]=req;
        m.write32(req,test==11?2u:1u);m.write32(req+12u,path&0x3fffffffu);m.write32(req+16u,0u);
        if(test==12)need(B::write32(IosBus::IPC+M::PPCMSG,0x100u));
        if(test==13)*m.get_ptr(Mmu::heap+64u)^=1u;
        if(test==14)c.in_callback=true;
        const bool valid_request=test==0||test==15;
        need(open.observe(c,c.pc,true)==valid_request);
        if(valid_request){
            need(open.stage()==9u&&open.submit_at(c,true)&&open.request()==req&&host.serviced_steps()==0);
            ++c.inst_count;need(!open.submit_at(c,true));++valid;
        }else ++refused;
    }
    need(valid==2&&refused==14);
    std::cout<<"V1242_STM_OPEN_JOIN positive=2 refused=14 calls=17 stm=3 open=9 vector=1 cache=1 request=1 submitted=0 serviced=0 original_execution=0 boot_verified=0\n";
}
