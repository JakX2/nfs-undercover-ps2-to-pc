#include "wii_post_ack_stm_join_v1239.h"
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
    uint32_t ctr=0,xer=0,srr0=0,srr1=0;
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
    unsigned valid=0,refused=0;
    for(unsigned lane=0;lane<=16;++lane){
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
        if(good){
            need(next.stage()==3u&&next.open_at(c)&&next.path_kind()==(lane==16?2u:1u)&&host.serviced_steps()==0);
            ++c.inst_count;need(!next.open_at(c));++valid;
        }else{need(next.failure()==2);++refused;}
    }
    need(valid==2&&refused==15);
    std::cout<<"V1239_IPC_STM_JOIN positive=2 refused=15 same_cpu=1 same_return_tick=1 both_paths=1 heap_preserved=1 serviced=0 original_execution=0 boot_verified=0\n";
}
