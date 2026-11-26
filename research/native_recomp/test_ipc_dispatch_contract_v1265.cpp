#include "wii_ipc_dispatch_v1261.h"
#include "wii_scheduler_reply_irq_v1268.h"
#ifdef UNDERCOVER_TEST_JOINED_ACK
#include "wii_joined_ipc_ack_v1266.h"
#include "wii_joined_ipc_reply_entry_v1273.h"
#endif
#include <cassert>
#include <iostream>
#include <string_view>
#include <vector>
using namespace undercover::wii;
using H=HollywoodIrq;using M=IpcMailbox;using S=StmIos;using Bus=IosBus;
constexpr uint32_t Context=0x80004000u,Thread=0x80006000u,Queue=0x80008000u,
    Table=0x80003040u,Global=0x80009000u,Counter=0x80009100u,
    Handler=0x80010000u,Resume=0x80005000u,Request=0x100u,Path=0x800u,
    Other=0x100u,Mask=H::PI_HOLLYWOOD;
constexpr SiDispatchExpectations Code{
    std::array<SiDispatchEdge,4>{{
        {0x80011000u,0x80012004u,1u,2u},
        {0x80013000u,0x80012008u,3u,4u},
        {0x80014000u,0x80013104u,5u,6u},
        {0x80015000u,0x80013108u,7u,8u}}},
    0x8001200cu,0x4e800421u,9u,10u};
struct Mmu{
    std::span<uint8_t> mem;WiiPhysicalRam& ram;
    uint8_t* get_ptr(uint32_t a){
        const auto p=a&0x3fffffffu;
        return p<mem.size()?mem.data()+p:nullptr;
    }
    uint8_t read8(uint32_t a)const{return ram.read8(a&0x3fffffffu);}
    uint32_t read32(uint32_t a)const{return ram.read32(a&0x3fffffffu);}
    uint16_t read16(uint32_t a)const{return uint16_t((uint16_t(read8(a))<<8)|read8(a+1u));}
    void write32(uint32_t a,uint32_t v){ram.write32(a&0x3fffffffu,v);}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};
    std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=0x80005200u,ctr=17u,xer=0x80000000u,msr=0x8032u,
        srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
static void trial(unsigned n,unsigned join_case=0,bool reply_lane=false){
#ifndef UNDERCOVER_TEST_JOINED_ACK
    (void)join_case;
#endif
    std::vector<uint8_t> one(0x600000u);std::array<uint8_t,4096> two{};
    std::atomic<uint32_t> cause{Other},mask{Mask};
    NativeIosTransport host(one,two,cause,mask);auto& ram=host.physical_ram();
#ifdef UNDERCOVER_TEST_JOINED_ACK
    NativeIosBinding binding(host);
#endif
    Cpu c{{one,ram}};
    constexpr std::string_view name="/dev/stm/immediate";
    for(unsigned i=0;i<name.size();++i)ram.write8(Path+i,uint8_t(name[i]));
    ram.write8(Path+name.size(),0);ram.write32(Request,S::Open);ram.write32(Request+12u,Path);
    assert(host.write32(Bus::IPC+H::PPC_MASK,H::IPC_PPC));
    assert(host.write32(Bus::IPC+M::PPCMSG,Request));
    assert(host.write32(Bus::IPC+M::PPCCTRL,M::IY1|M::IY2|M::X1));
    const auto ack=host.service_at_guest_boundary(0);
    assert(ack&&ack->progress==S::Pump::Ack);
    for(unsigned i=0;i<32;++i)c.gpr[i]=i*17u+3u;
    c.cr[0].eq=true;
    ExternalReturnWitness frame;
    assert(frame.capture(c,cause.load(),mask.load(),H::PI_HOLLYWOOD));
    constexpr std::array<uint8_t,4> vector{0x60,0,0,0};
    for(unsigned i=0;i<vector.size();++i)ram.write8(0x500u+i,vector[i]);
    assert(enter_scheduler_ipc_irq(c,host,vector,Request));
    if(reply_lane){
        assert(host.write32(Bus::IPC+M::PPCCTRL,M::IY1|M::IY2|M::Y2));
        assert(host.write32(Bus::IPC+H::PPC_FLAG,H::IPC_PPC));
        const auto reply=host.service_at_guest_boundary(0);
        assert(reply&&reply->progress==S::Pump::Replied);
        constexpr uint32_t Rfi=0x80020000u;
        ram.write32(Rfi&0x3fffffffu,0x4c000064u);
        c.pc=Rfi;c.inst_count+=100u;
        assert(frame.before_pending_rfi(c,Rfi,0x4c000064u,cause.load(),mask.load()));
        c.pc=c.srr0;c.msr=c.srr1;
        assert(frame.pending_rfi_return(c,cause.load(),mask.load()));
        ExternalReturnWitness second;
        assert(enter_scheduler_reply_irq(c,host,frame,second,vector,Request));
        frame=second;
    }
    const auto snap=host.cold_ipc_snapshot();
    // Synthetic context stores explicitly model the vector postcondition;
    // the IRQ and pending ACK are real native transport operations.
    auto& m=c.mmu;
    for(unsigned i=0;i<32;++i)m.write32(Context+4u*i,c.gpr[i]);
    m.write32(Context+128u,0x20000000u);m.write32(Context+132u,c.lr);
    m.write32(Context+136u,c.ctr);m.write32(Context+140u,c.xer);
    m.write32(Context+408u,c.srr0);m.write32(Context+412u,c.srr1);
    m.write32(Thread+712u,4u<<16);m.write32(Thread+732u,Queue);
    m.write32(0x800000d4u,Context);m.write32(0x800000c0u,Context&0x3fffffffu);
    m.write32(Queue,Thread);m.write32(Queue+4u,Thread);
    m.write32(Global,Table);m.write32(Table+27u*4u,Handler);m.write32(Counter,0u);
    m.write32(SiDispatchWitness::Dispatcher,Code.dispatcher_word);
    m.write32(Code.indirect_pc,Code.indirect_word);m.write32(Handler,Code.handler_word);
    for(auto e:Code.edges){m.write32(e.pc,e.entry_word);m.write32(e.lr-4u,e.branch_word);}
    c.pc=SiDispatchWitness::Dispatcher;c.gpr[3]=4;c.gpr[4]=Context;c.msr=0x32u;c.inst_count+=50u;
    IpcDispatchWitness w({Code,Handler,Context,Thread,Table,Global,Counter});
    auto unchanged=[&]{
        assert(host.serviced_steps()==(reply_lane?2u:1u)&&ram.read32(Request)==(reply_lane?S::Reply:S::Open)&&
               same_scheduler_ipc_snapshot(snap,host.cold_ipc_snapshot()));
    };
    auto rejected=[&](bool ok,unsigned reason,unsigned detail=0){
        assert(!ok&&w.failure()==reason&&w.detail()==detail);unchanged();
    };
    auto observed=snap;
    if(n==1)c.gpr[4]=0;
    if(n==2)observed.control&=~(reply_lane?M::Y1:M::Y2);
    if(n==3)m.write32(Table+27u*4u,Handler+4u);
    if(n==4)m.write32(Context+124u,m.read32(Context+124u)^1u);
    // Wrong ARMMSG, wrong request address, stale phase, or a malformed
    // response must be rejected before any dispatcher instruction runs.
    if(reply_lane&&n==21)observed.arm+=32u;
    if(reply_lane&&n==22)observed.steps=1u;
    if(reply_lane&&n==23)ram.write32(Request+4u,1u);
    bool ok=reply_lane?w.begin_reply(c,frame,observed,Queue,n==24?Request+32u:Request,n!=5):
                       w.begin(c,frame,observed,Queue,n!=5);
    if(reply_lane&&n>=21&&n<=24){rejected(ok,1);return;}
    if(n>=1&&n<=5){rejected(ok,1);return;}
    assert(ok&&w.reply_mode()==reply_lane);
    if(reply_lane&&n==25){++c.inst_count;ram.write32(Request+8u,S::Reply);rejected(w.before(c,c.pc,Code.dispatcher_word,false,snap,true),4,10);return;}
    if(n==6){++c.inst_count;rejected(w.before(c,c.pc,Code.dispatcher_word,true,snap,true),4,1);return;}
    if(n==7){++c.inst_count;rejected(w.before(c,c.pc,Code.dispatcher_word,false,snap,false),4,2);return;}
    if(n==8){++c.inst_count;observed.control^=M::IY1;rejected(w.before(c,c.pc,Code.dispatcher_word,false,observed,true),4,3);return;}
    if(n==9){++c.inst_count;m.write32(Context+140u,0);rejected(w.before(c,c.pc,Code.dispatcher_word,false,snap,true),4,5);return;}
    if(n==10){++c.inst_count;m.write32(Queue+4u,0);rejected(w.before(c,c.pc,Code.dispatcher_word,false,snap,true),4,6);return;}
    if(n==11){++c.inst_count;rejected(w.before(c,c.pc,Code.dispatcher_word^1u,false,snap,true),4,7);return;}
    if(n==12){c.inst_count+=2;rejected(w.before(c,c.pc,Code.dispatcher_word,false,snap,true),4,8);return;}
    if(n==13){c.inst_count+=2;rejected(w.poll(c,snap,true),3);return;}
    ++c.inst_count;assert(w.before(c,c.pc,Code.dispatcher_word,false,snap,true));
    if(n==14){rejected(w.read(Bus::PI_CAUSE,cause.load()^Mask),2);return;}
    assert(w.read(Bus::PI_CAUSE,cause.load()));
    if(n!=15)assert(w.read(Bus::PI_MASK,mask.load()));
    for(unsigned i=0;i<Code.edges.size();++i){
        const auto e=Code.edges[i];
        ++c.inst_count;assert(w.before(c,e.lr-4u,e.branch_word,false,snap,true));
        c.pc=e.pc;c.lr=e.lr;
        if(n==16&&i==1){c.lr+=4;rejected(w.observe(c,c.pc,snap,true),5);return;}
        assert(w.observe(c,c.pc,snap,true));
        ++c.inst_count;assert(w.before(c,c.pc,e.entry_word,false,snap,true));
        assert(w.poll(c,snap,true));
    }
    if(n!=17)m.write32(Counter,1u);
    ++c.inst_count;assert(w.before(c,Code.indirect_pc,Code.indirect_word,false,snap,true));
    // Outer native dispatch adds one tick after the bctrl boundary.
    assert(w.poll(c,snap,true));++c.inst_count;
    c.pc=Handler;c.lr=Code.indirect_pc+4u;c.ctr=Handler;c.gpr[3]=27u;c.gpr[4]=Context;
    if(n==18)c.gpr[3]=20;
    if(n==19)c.ctr+=4;
    if(n==20)m.write32(Thread+732u,Queue+4u);
    ok=w.observe(c,c.pc,snap,true);
    if(n==15||n==17||n==18||n==19){rejected(ok,6);return;}
    if(n==20){rejected(ok,5);return;}
    assert(n==0&&ok&&w.stage()==6u&&w.cause_reads()==1u&&w.mask_reads()==1u);
    unchanged();
    if(reply_lane){
        assert(w.handler_ready(c,frame,snap,Queue,true));
#ifdef UNDERCOVER_TEST_JOINED_ACK
        constexpr uint32_t Leaf=0x8051905cu,Reply=0x805190c0u;
        constexpr VectorEdge reply_edge{Reply,Handler+12u,0x48000001u,0x60000000u};
        constexpr std::array<VectorEdge,2> edges{{{Leaf,Handler+8u,0x48000001u,0x4e800020u},reply_edge}};
        constexpr std::array<uint32_t,0> polls{};
        m.write32(Handler+4u,edges[0].branch_word);m.write32(Handler+8u,reply_edge.branch_word);
        m.write32(Leaf,edges[0].entry_word);m.write32(Reply,reply_edge.entry_word);
        JoinedIpcReplyEntry j(Handler,Leaf,reply_edge,Context,Thread,edges,polls);
        auto refuse=[&](bool ok,unsigned reason){assert(!ok&&j.failure()==reason);unchanged();};
        if(join_case==1)++c.inst_count;
        if(join_case==2)m.write32(Reply,0u);
        ok=j.begin(c,w,frame,Queue,join_case==3?Request+32u:Request,true);
        if(join_case>=1&&join_case<=3){refuse(ok,1);return;}
        assert(ok&&j.poll(c,true));++c.inst_count;assert(j.entry(c,Handler,true));
        ++c.inst_count;assert(j.before(c,Handler,Code.handler_word,false,true));
        if(join_case==4){refuse(j.write_refused(),7);return;}
        if(join_case==5){c.inst_count+=2;refuse(j.before(c,Handler+4u,edges[0].branch_word,false,true),4);return;}
        ++c.inst_count;assert(j.before(c,Handler+4u,edges[0].branch_word,false,true));
        c.pc=Leaf;c.lr=Handler+8u;
        if(join_case==6){c.lr+=4u;refuse(j.entry(c,Leaf,true),2);return;}
        assert(j.entry(c,Leaf,true));++c.inst_count;assert(j.before(c,Leaf,edges[0].entry_word,false,true));
        if(join_case==7){assert(!j.read(c,Bus::IPC+M::ARMMSG,true));refuse(false,6);return;}
        if(join_case!=8)assert(j.read(c,Bus::IPC+M::PPCCTRL,true));
        c.pc=Handler+8u;++c.inst_count;assert(j.before(c,c.pc,reply_edge.branch_word,false,true));
        c.pc=Reply;c.lr=reply_edge.lr;
        if(join_case==9)m.write32(Context+124u,0u);
        if(join_case==10)ram.write32(Request+4u,1u);
        ok=j.entry(c,Reply,true);
        if(join_case>=8){refuse(ok,join_case==8?3u:2u);return;}
        assert(ok&&j.stage()==2u&&j.reads()==1u&&j.visits()==4u);
        unchanged();
#endif
        return;
    }
#ifdef UNDERCOVER_TEST_JOINED_ACK
    // Synthetic handler observations; every MMIO write and IOS pump is
    // the real native transport. No owner game instructions here.
    constexpr uint32_t returned=Code.indirect_pc+4u,ret_word=0x60000000u,
        final_blr=Handler+0x40u,Leaf=0x8051905cu;
    m.write32(returned,ret_word);m.write32(final_blr,0x4e800020u);
    m.write32(Leaf,0x4e800020u);m.write32(Handler+4u,0x48000001u);
    constexpr std::array<VectorEdge,1> edges{{{Leaf,Handler+8u,0x48000001u,0x4e800020u}}};
    constexpr std::array<uint32_t,0> polls{};
    JoinedIpcAck j(Handler,returned,ret_word,final_blr,Context,Thread,edges,polls);
    auto refuse=[&](bool value,unsigned reason){
        assert(!value&&j.failure()==reason&&host.serviced_steps()==1u&&ram.read32(Request)==S::Open);
    };
    if(join_case==1)++c.inst_count;
    if(join_case==2)m.write32(returned,0);
    if(join_case==3)m.write32(final_blr,0);
    ok=j.begin(c,w,frame,Queue,Request,1u,true);
    if(join_case>=1&&join_case<=3){refuse(ok,1);return;}
    assert(ok&&j.poll(c,true));
    if(join_case==4){refuse(j.publish(c,true),8);return;}
    ++c.inst_count;assert(j.entry(c,Handler,true));
    ++c.inst_count;assert(j.before(c,Handler,Code.handler_word,false,true));
    if(join_case==5){c.inst_count+=2;refuse(j.before(c,Handler+4u,0x48000001u,false,true),3);return;}
    if(join_case==6){refuse(j.poll(c,true),4);return;}
    ++c.inst_count;assert(j.before(c,Handler+4u,0x48000001u,false,true));
    c.pc=Leaf;c.lr=Handler+8u;
    if(join_case==7){c.lr+=4;refuse(j.entry(c,Leaf,true),2);return;}
    assert(j.entry(c,Leaf,true));
    ++c.inst_count;assert(j.before(c,Leaf,0x4e800020u,false,true));
    c.pc=Handler+8u;c.lr=returned;
    const auto ctrl=j.read(c,Bus::IPC+M::PPCCTRL,true);assert(ctrl);
    if(join_case==8){refuse(j.write(c,Bus::IPC+H::PPC_FLAG,H::IPC_PPC,true),6);return;}
    assert(j.write(c,Bus::IPC+M::PPCCTRL,*ctrl,true));
    if(join_case==9){refuse(j.write(c,Bus::IPC+H::PPC_FLAG,0,true),6);return;}
    assert(j.write(c,Bus::IPC+H::PPC_FLAG,H::IPC_PPC,true));
    if(join_case==10){m.write32(Context+124u,0);refuse(j.poll(c,true),4);return;}
    if(join_case!=11){++c.inst_count;assert(j.before(c,final_blr,0x4e800020u,false,true));}
    c.pc=returned;
    if(join_case==12)c.gpr[31]^=1u;
    if(join_case==13)++c.inst_count;
    ok=j.finish(c,true);
    if(join_case>=11&&join_case<=13){refuse(ok,7);return;}
    assert(ok&&j.stage()==2u&&host.serviced_steps()==1u);
    assert(j.publish(c,true)&&j.stage()==3u&&host.serviced_steps()==2u);
    assert(ram.read32(Request)==S::Reply&&ram.read32(Request+4u)==0u&&ram.read32(Request+8u)==S::Open);
    assert(!j.publish(c,true)&&host.serviced_steps()==2u);
#endif
}
int main(){
    for(unsigned i=0;i<21;++i)trial(i);
    std::cout<<"V1265_IPC_DISPATCH_CONTRACT synthetic=1 valid=1 refused=20 native_ack=1 original_execution=0\n";
    for(unsigned i=0;i<=25;++i)trial(i,0,true);
    std::cout<<"V1272_REPLY_DISPATCH_CONTRACT synthetic=1 valid=1 refused=25 native_reply=1 original_execution=0\n";
#ifdef UNDERCOVER_TEST_JOINED_ACK
    for(unsigned i=1;i<=13;++i)trial(0,i);
    for(unsigned i=1;i<=10;++i)trial(0,i,true);
    std::cout<<"V1273_REPLY_ENTRY_CONTRACT synthetic=1 valid=1 refused=10 native_reply=1 wakeup=0 original_execution=0\n";
    std::cout<<"V1267_JOINED_ACK_CONTRACT synthetic=1 valid=1 refused=13 native_reply=1 original_execution=0\n";
#endif
}
