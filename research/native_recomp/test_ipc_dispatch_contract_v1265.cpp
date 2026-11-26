#include "wii_ipc_dispatch_v1261.h"
#include "wii_scheduler_reply_irq_v1268.h"
#ifdef UNDERCOVER_TEST_JOINED_ACK
#include "wii_joined_ipc_ack_v1266.h"
#include "wii_joined_ipc_reply_entry_v1273.h"
#ifdef UNDERCOVER_TEST_REPLY_PROCESSOR
#include "wii_reply_processor_v1280.h"
#ifdef UNDERCOVER_TEST_WAKE_READY
#include "wii_wake_ready_v1288.h"
#ifdef UNDERCOVER_TEST_NESTED_WAKE
#include "wii_nested_wake_return_v1291.h"
#ifdef UNDERCOVER_TEST_REPLY_COMPLETION
#include "wii_reply_completion_v1293.h"
#ifdef UNDERCOVER_TEST_REPLY_RETURN
#include "wii_reply_return_v1298.h"
#ifdef UNDERCOVER_TEST_READY_IDLE_RETURN
#include "wii_ready_idle_return_v1304.h"
#endif
#endif
#endif
#endif
#endif
#endif
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
    uint32_t guest_data_invalidate_count=300,guest_last_data_invalidate=0;
    bool is_running=true,in_callback=false;
};
static void trial(unsigned n,unsigned join_case=0,bool reply_lane=false,unsigned processor_case=0,unsigned wake_case=0,unsigned nested_case=0,unsigned finish_case=0,unsigned return_case=0,unsigned idle_case=0){
#ifndef UNDERCOVER_TEST_READY_IDLE_RETURN
    (void)idle_case;
#endif
#ifndef UNDERCOVER_TEST_REPLY_RETURN
    (void)return_case;
#endif
#ifndef UNDERCOVER_TEST_REPLY_COMPLETION
    (void)finish_case;
#endif
#ifndef UNDERCOVER_TEST_NESTED_WAKE
    (void)nested_case;
#endif
#ifndef UNDERCOVER_TEST_WAKE_READY
    (void)wake_case;
#endif
#ifndef UNDERCOVER_TEST_REPLY_PROCESSOR
    (void)processor_case;
#endif
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
#ifdef UNDERCOVER_TEST_REPLY_RETURN
        const auto handler_abi=ReplyReturnAbi::capture(c);
#endif
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
#ifdef UNDERCOVER_TEST_REPLY_PROCESSOR
        constexpr uint32_t Writer=0x8051906cu,Cache=0x80522294u,Wake=0x8052a51cu,
            Nop=0x60000000u,Blr=0x4e800020u,Lwz=0x80640000u,Stw=0x90640000u,
            Dcbi1=(31u<<26)|(3u<<11)|(470u<<1),Dcbi2=(31u<<26)|(3u<<16)|(5u<<11)|(470u<<1);
        constexpr auto bl=[](uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);};
        const std::array<ReplyNativeWord,14> words{{
            {Reply,Reply,Nop},{Reply,Reply+4u,bl(Reply+4u,Leaf)},
            {Reply,Reply+8u,bl(Reply+8u,Writer)},{Reply,Reply+12u,bl(Reply+12u,Leaf)},
            {Reply,Reply+16u,bl(Reply+16u,Cache)},{Reply,Reply+20u,bl(Reply+20u,Wake)},
            {Leaf,Leaf,Lwz},{Leaf,Leaf+4u,Blr},{Writer,Writer,Stw},{Writer,Writer+4u,Blr},
            {Cache,Cache,Dcbi1},{Cache,Cache+4u,Dcbi2},{Cache,Cache+8u,Blr},{Wake,Wake,Nop}}};
        const std::array<VectorEdge,5> calls{{
            {Leaf,Reply+8u,words[1].word,Lwz},{Writer,Reply+12u,words[2].word,Stw},
            {Leaf,Reply+16u,words[3].word,Lwz},{Cache,Reply+20u,words[4].word,Dcbi1},
            {Wake,Reply+24u,words[5].word,Nop}}};
        for(auto x:words)m.write32(x.pc,x.word);
#ifdef UNDERCOVER_TEST_REPLY_RETURN
        const auto processor_abi=ReplyReturnAbi::capture(c);
#endif
        ReplyProcessorWitness body({Reply,Leaf,Writer,Cache,Wake,Reply+24u,Context,Thread,words,calls});
        auto reject=[&](bool ok,unsigned reason){assert(!ok&&body.failure()==reason&&host.serviced_steps()==2u);};
        if(processor_case==1)++c.inst_count;
        ok=body.begin(c,j,frame,Queue,processor_case==2?Request+32u:Request,true);
        if(processor_case==1||processor_case==2){reject(ok,1);return;}assert(ok);
        assert(body.poll(c,true));++c.inst_count;assert(body.entry(c,Reply,true));
        auto step=[&](uint32_t pc){c.pc=pc;++c.inst_count;return body.before(c,pc,m.read32(pc),true);};
        auto call=[&](uint32_t pc,uint32_t lr){c.pc=pc;c.lr=lr;return body.entry(c,pc,true);};
        if(processor_case==3){reject(step(Reply+4u),5);return;}
        assert(step(Reply)&&step(Reply+4u));
        if(processor_case==4){reject(call(Leaf,Reply+12u),2);return;}
        c.gpr[4]=Bus::IPC+M::PPCCTRL;
        assert(call(Leaf,Reply+8u)&&step(Leaf));
        if(processor_case==5){assert(!body.read(c,Bus::IPC+M::PPCMSG,true));reject(false,8);return;}
        if(processor_case==12){reject(step(Leaf+4u),8);assert(body.mmio_reason()==9u);return;}
        if(processor_case==15){++c.inst_count;assert(!body.read(c,Bus::IPC+M::PPCCTRL,true));reject(false,8);assert(body.mmio_reason()==2u);return;}
        const auto control=body.read(c,Bus::IPC+M::PPCCTRL,true);assert(control);
        if(processor_case==13){c.gpr[3]=*control^1u;reject(step(Leaf+4u),8);assert(body.mmio_reason()==10u);return;}
        if(processor_case==14){assert(!body.read(c,Bus::IPC+M::PPCCTRL,true));reject(false,8);assert(body.mmio_reason()==7u);return;}
        c.gpr[3]=*control;c.gpr[4]=Bus::IPC+M::PPCCTRL;
        assert(step(Leaf+4u)&&step(Reply+8u)&&call(Writer,Reply+12u)&&step(Writer));
        if(processor_case==6){reject(body.write(c,Bus::IPC+M::PPCCTRL,*control|M::X1,true),8);return;}
        assert(body.write(c,Bus::IPC+M::PPCCTRL,*control,true)&&step(Writer+4u));
        c.gpr[4]=Bus::IPC+M::ARMMSG;
        assert(step(Reply+12u)&&call(Leaf,Reply+16u)&&step(Leaf));
        assert(body.read(c,Bus::IPC+M::ARMMSG,true)==Request);
        c.gpr[3]=Request;
        assert(step(Leaf+4u)&&step(Reply+16u));
        c.gpr[3]=Request|0x80000000u;c.gpr[4]=processor_case==7?8u:64u;c.gpr[5]=32u;
        ok=call(Cache,Reply+20u);
        if(processor_case==7){reject(ok,4);return;}assert(ok&&step(Cache));
        if(processor_case!=8){++c.guest_data_invalidate_count;c.guest_last_data_invalidate=c.gpr[3];}
        ok=step(Cache+4u);if(processor_case==8){reject(ok,4);return;}assert(ok);
        ++c.guest_data_invalidate_count;c.guest_last_data_invalidate=c.gpr[3]+(processor_case==9?0u:32u);
        ok=step(Cache+8u);if(processor_case==9){reject(ok,4);return;}assert(ok);
        if(processor_case==10)m.write32(Context+124u,0u);
        ok=step(Reply+20u);if(processor_case==10){reject(ok,5);return;}assert(ok);
        c.gpr[3]=processor_case==11?Queue+4u:Queue;ok=call(Wake,Reply+24u);
        if(processor_case==11){reject(ok,3);return;}
        assert(ok&&body.stage()==2u&&body.arm_reads()==1u&&body.invalidations()==2u&&
            host.serviced_steps()==2u&&m.read16(Thread+712u)==4u&&m.read32(Queue)==Thread);
#ifdef UNDERCOVER_TEST_WAKE_READY
        constexpr uint32_t Disable=0x805265acu,Select=0x80529718u,Ready=0x8000b000u;
        constexpr std::array<ReplyNativeWord,8> wake_words{{
            {Wake,Wake,Nop},{Wake,Wake+4u,bl(Wake+4u,Disable)},
            {Wake,Wake+8u,Nop},{Wake,Wake+12u,Nop},{Wake,Wake+16u,bl(Wake+16u,Select)},
            {Disable,Disable,Nop},{Disable,Disable+4u,Blr},{Select,Select,Nop}}};
        for(auto x:wake_words)m.write32(x.pc,x.word);
        WakeReadyWitness ready({Wake,Disable,Select,Context,Thread,
            {Disable,Wake+8u,wake_words[1].word,Nop},{Select,Wake+20u,wake_words[4].word,Nop},wake_words});
        const auto saved_sp=c.gpr[1];c.gpr[1]=0x8000c000u;
        if(wake_case==1)++c.inst_count;
        auto refuse_wake=[&](bool ok,unsigned reason){assert(!ok&&ready.failure()==reason&&host.serviced_steps()==2u);};
        ok=ready.begin(c,body,frame,Queue,true);
        if(wake_case==1){refuse_wake(ok,1);return;}assert(ok);
        assert(ready.poll(c,true));++c.inst_count;assert(ready.entry(c,Wake,true));
        auto ws=[&](uint32_t pc){c.pc=pc;++c.inst_count;return ready.before(c,pc,m.read32(pc),true);};
        auto we=[&](uint32_t pc,uint32_t lr){c.pc=pc;c.lr=lr;return ready.entry(c,pc,true);};
        if(wake_case==2){refuse_wake(ws(Wake+4u),5);return;}
        assert(ws(Wake)&&ws(Wake+4u));c.gpr[1]-=32u;
        if(wake_case==3){refuse_wake(we(Disable,Wake+12u),2);return;}
        assert(we(Disable,Wake+8u)&&ws(Disable)&&ws(Disable+4u));
        c.gpr[3]=wake_case==4?1u:0u;
        ok=ws(Wake+8u);if(wake_case==4){refuse_wake(ok,3);return;}assert(ok);
        if(wake_case==5){refuse_wake(ready.refuse_mmio(),8);return;}
        // Model only the guest's wake stores in the source-only test.
        m.write32(Thread+712u,1u<<16);
        m.write32(Queue,wake_case==6?Thread:0u);m.write32(Queue+4u,0u);
        m.write32(Thread+732u,wake_case==7?Queue:Ready);
        m.write32(Ready,Thread);m.write32(Ready+4u,wake_case==8?0u:Thread);
        if(wake_case==9)m.write32(Thread+4u,0x1234u);
        if(wake_case==11)m.write32(Thread+0x1c0u,m.read32(Thread+0x1c0u)^1u);
        if(wake_case==12)m.write32(Thread+0x2c4u,m.read32(Thread+0x2c4u)^1u);
        ok=ws(Wake+12u);if(wake_case==9||wake_case==11||wake_case==12){refuse_wake(ok,5);return;}assert(ok&&ws(Wake+16u));
        c.gpr[3]=wake_case==10?1u:0u;
        ok=we(Select,Wake+20u);
        if((wake_case>=6&&wake_case<=8)||wake_case==10){refuse_wake(ok,4);return;}
        assert(ok&&ready.stage()==2u&&ready.ready_queue()==Ready&&host.serviced_steps()==2u);
        (void)saved_sp;
#ifdef UNDERCOVER_TEST_NESTED_WAKE
        constexpr uint32_t Getter=0x80522928u,Restore=0x805265d4u;
        constexpr std::array<ReplyNativeWord,12> suffix{{
            {Select,Select,Nop},{Select,Select+4u,bl(Select+4u,Getter)},{Select,Select+8u,Nop},{Select,Select+12u,Blr},
            {Getter,Getter,Nop},{Getter,Getter+4u,Blr},
            {Wake,Wake+20u,Nop},{Wake,Wake+24u,bl(Wake+24u,Restore)},{Wake,Wake+28u,Nop},{Wake,Wake+32u,Blr},
            {Restore,Restore,Nop},{Restore,Restore+4u,Blr}}};
        for(auto x:suffix)m.write32(x.pc,x.word);
        m.write32(Counter,1u);
        NestedWakeReturnWitness nested({Wake,Select,Getter,Restore,Context,Counter,
            {Getter,Select+8u,suffix[1].word,Nop},{Restore,Wake+28u,suffix[7].word,Nop},suffix});
        auto nr=[&](bool ok,unsigned reason){assert(!ok&&nested.failure()==reason&&host.serviced_steps()==2u);};
        if(nested_case==1)++c.inst_count;
        if(nested_case==2)m.write32(Counter,0u);
        ok=nested.begin(c,ready,frame,Queue,true);
        if(nested_case==1||nested_case==2){nr(ok,1);return;}assert(ok);
        assert(nested.poll(c,true));++c.inst_count;assert(nested.entry(c,Select,true));
        auto ns=[&](uint32_t pc){c.pc=pc;++c.inst_count;return nested.before(c,pc,m.read32(pc),true);};
        auto ne=[&](uint32_t pc,uint32_t lr){c.pc=pc;c.lr=lr;return nested.entry(c,pc,true);};
        assert(ns(Select)&&ns(Select+4u));
        if(nested_case==3){nr(ne(Getter,Select+12u),2);return;}
        assert(ne(Getter,Select+8u)&&ns(Getter)&&ns(Getter+4u));
        c.gpr[3]=nested_case==4?Context+4u:Context;c.lr=Select+8u;
        // The real scheduler restores its caller LR before its final BLR.
        // Model a separate instruction for that restoration below.
        if(nested_case==4){nr(ns(Select+8u),3);return;}

        assert(ns(Select+8u));c.lr=Wake+20u;
        if(nested_case==5)c.gpr[31]^=1u;
        ok=ns(Select+12u);if(nested_case==5){nr(ok,5);return;}assert(ok);
        c.pc=Wake+20u;if(nested_case==6)++c.inst_count;
        ok=nested.poll(c,true);if(nested_case==6){nr(ok,7);return;}assert(ok);
        if(nested_case!=7)++c.inst_count;
        ok=ns(Wake+20u);if(nested_case==7){nr(ok,4);return;}assert(ok);
        assert(ns(Wake+24u));c.gpr[3]=nested_case==8?1u:0u;
        ok=ne(Restore,Wake+28u);if(nested_case==8){nr(ok,3);return;}assert(ok&&ns(Restore)&&ns(Restore+4u));
        if(nested_case==9)m.write32(Ready,0u);
        ok=ns(Wake+28u);if(nested_case==9){nr(ok,4);return;}assert(ok);
        c.gpr[1]=0x8000c000u;c.lr=Reply+24u;
        if(nested_case==10)c.gpr[1]-=4u;
        ok=ns(Wake+32u);if(nested_case==10){nr(ok,5);return;}assert(ok);
        c.pc=Reply+24u;
        if(nested_case==11)c.pc+=4u;
        ok=nested.poll(c,true);if(nested_case==11){nr(ok,7);return;}
        assert(ok&&nested.stage()==2u&&ready.ready_held(c,true)&&host.serviced_steps()==2u);
#ifdef UNDERCOVER_TEST_REPLY_COMPLETION
#ifdef UNDERCOVER_TEST_REPLY_RETURN
        if(return_case){
            constexpr uint32_t P=Reply+24u,Hret=Handler+12u,Dret=Code.indirect_pc+4u;
            const std::array<ReplyNativeWord,7> rw{{
                {Reply,P,bl(P,Writer)},{Reply,P+4u,Nop},{Reply,P+8u,Blr},
                {Writer,Writer,Stw},{Writer,Writer+4u,Blr},{Leaf,Leaf,Lwz},{Handler,Hret,Blr}}};
            const std::array<VectorEdge,1> re{{{Writer,P+4u,rw[0].word,Stw}}};
            for(auto x:rw)m.write32(x.pc,x.word);
            ReplyReturnWitness ret({Reply,Handler,Leaf,Writer,P,Hret,Dret,Counter,rw,re});
            auto no=[&](bool result,unsigned reason){assert(!result&&ret.failure()==reason&&host.serviced_steps()==2u);};
            if(return_case==2)++c.inst_count;
            ok=ret.begin(c,body,ready,nested,frame,Queue,Request,handler_abi,processor_abi,true);
            if(return_case==2){no(ok,1);return;}assert(ok);
            if(return_case==3)c.pc+=4u;
            ok=ret.poll(c,true);if(return_case==3){no(ok,6);return;}assert(ok);
            auto rs=[&](uint32_t pc){c.pc=pc;++c.inst_count;return ret.before(c,pc,m.read32(pc),true);};
            if(return_case!=4)++c.inst_count;
            ok=rs(P);if(return_case==4){no(ok,3);return;}assert(ok);
            c.lr=P+4u;c.pc=Writer;
            if(return_case==5)c.lr+=4u;
            ok=ret.entry(c,Writer,true);if(return_case==5){no(ok,2);return;}assert(ok);
            c.gpr[3]=H::IPC_PPC;c.gpr[4]=Bus::IPC+H::PPC_FLAG;
            assert(rs(Writer));
            if(return_case==6){no(ret.write(c,Bus::IPC+H::PPC_FLAG,0u,true),7);return;}
            if(return_case==7){no(rs(Writer+4u),7);return;}
            assert(ret.write(c,Bus::IPC+H::PPC_FLAG,H::IPC_PPC,true));
            if(return_case==8){no(ret.write(c,Bus::IPC+H::PPC_FLAG,H::IPC_PPC,true),7);return;}
            assert(rs(Writer+4u)&&rs(P+4u));
            c.gpr[1]=processor_abi.gp[1];c.lr=Hret;
            if(return_case==9)c.gpr[31]^=1u;
            ok=rs(P+8u);if(return_case==9){no(ok,5);return;}assert(ok);
            c.pc=Hret;
            if(return_case==10)c.mmu.write32(Counter,0u);
            ok=ret.poll(c,true);if(return_case==10){no(ok,6);return;}assert(ok);
            c.gpr[1]=handler_abi.gp[1];c.lr=Dret;++c.inst_count;
            if(return_case==11)c.gpr[14]^=1u;
            ok=rs(Hret);if(return_case==11){no(ok,5);return;}assert(ok);
            c.pc=Dret;if(return_case==12)++c.inst_count;
            ok=ret.poll(c,true);if(return_case==12){no(ok,6);return;}assert(ok);
            assert(return_case==1&&ret.returned(c,true)&&ret.writes()==1u&&cause.load()==Other&&host.serviced_steps()==2u);
#ifdef UNDERCOVER_TEST_READY_IDLE_RETURN
            if(idle_case){
                ReadyIdleReturnJoin join;
                if(idle_case==2)++c.inst_count;
                ok=join.begin(c,ret,ready,frame,true);
                if(idle_case==2){assert(!ok&&join.failure()==1u);return;}assert(ok);
                assert(join.boundary(c,true));
                if(idle_case==3){assert(!join.finish(c,true)&&join.failure()==2u);return;}
                if(idle_case==4)m.write32(Ready+4u,0u);
                if(idle_case==5)m.write32(Thread+0x2c4u,m.read32(Thread+0x2c4u)^1u);
                if(idle_case==6)cause.fetch_or(H::PI_HOLLYWOOD);
                if(idle_case==12)ram.write32(Request+4u,1u);
                if((idle_case>=4&&idle_case<=6)||idle_case==12){assert(!join.boundary(c,true));return;}
                // Model the native loader's final integer state in this
                // original-free test; the external return witness checks
                // it against its independent pre-exception capture.
                for(unsigned i=0;i<32;++i)c.gpr[i]=m.read32(Context+4u*i);
                c.lr=m.read32(Context+132u);c.ctr=m.read32(Context+136u);c.xer=m.read32(Context+140u);
                const uint32_t bits=m.read32(Context+128u);
                for(unsigned i=0;i<8;++i){
                    const unsigned f=(bits>>(28u-i*4u))&15u;
                    c.cr[i]={bool(f&8u),bool(f&4u),bool(f&2u),bool(f&1u)};
                }
                c.srr0=m.read32(Context+408u);c.srr1=m.read32(Context+412u);
                constexpr uint32_t Rfi=0x80020000u;c.pc=Rfi;m.write32(Rfi,0x4c000064u);++c.inst_count;
                assert(frame.before_rfi(c,Rfi,0x4c000064u,cause.load(),mask.load()));
                c.pc=c.srr0;c.msr=c.srr1;
                assert(frame.poll(c,cause.load(),mask.load()));
                if(idle_case==7){assert(!join.finish(c,true)&&join.failure()==2u);return;}
                assert(frame.poll(c,cause.load(),mask.load()));
                if(idle_case==8)++c.inst_count;
                if(idle_case==9)c.gpr[31]^=1u;
                if(idle_case==10)m.write32(0x800000d4u,Thread);
                ok=join.finish(c,true);
                if(idle_case>=8&&idle_case<=10){assert(!ok&&join.failure()==2u);return;}
                assert(ok&&join.resumed_idle(c,true));
                if(idle_case==11){++c.inst_count;assert(!join.resumed_idle(c,true));}
                else assert(idle_case==1);
                return;
            }
#endif
            return;
        }
#endif
        ReplyCompletionGate finish;
        if(finish_case==1)++c.inst_count;
        ok=finish.begin(c,body,ready,nested,frame,Queue,finish_case==2?Request+32u:Request,finish_case!=3);
        if(finish_case>=1&&finish_case<=3){assert(!ok&&finish.failure()==1u);return;}
        assert(ok&&finish.stage()==1u&&!finish.finished(c,true));
        if(finish_case==4){assert(!finish.read(c,Bus::IPC+M::PPCMSG,true)&&finish.failure()==2u);return;}
        if(finish_case==5){assert(!finish.write(c,Bus::IPC+M::PPCCTRL,M::IY1|M::IY2|M::X1,true)&&finish.failure()==3u&&finish.write_detail()==4u&&finish.write_register()==1u&&finish.write_control_bits()==49u);return;}
        if(finish_case==6){assert(!finish.write(c,Bus::IPC+H::PPC_FLAG,0,true)&&finish.failure()==3u&&finish.write_detail()==5u&&finish.write_register()==2u&&finish.write_value_class()==2u);return;}
        if(finish_case==7)c.msr|=0x8000u;
        if(finish_case==8)m.write32(Ready+4u,0u);
        if(finish_case==9)ram.write32(Request+4u,1u);
        if(finish_case==12)m.write32(Thread+0x1c0u,m.read32(Thread+0x1c0u)^1u);
        if(finish_case==13)m.write32(Thread+0x2c4u,m.read32(Thread+0x2c4u)^1u);
        if((finish_case>=7&&finish_case<=9)||finish_case==12||finish_case==13){assert(!finish.boundary(c,true));return;}
        assert(finish.read(c,Bus::MIRROR+M::PPCCTRL,true)==(M::IY1|M::IY2));
        assert(finish.read(c,Bus::IPC+H::PPC_FLAG,true)==H::IPC_PPC);
        assert(finish.write(c,Bus::MIRROR+H::PPC_FLAG,H::IPC_PPC,true));
        assert(finish.stage()==2u&&finish.writes()==1u&&cause.load()==Other&&
               finish.finished(c,true)&&ready.ready_context_held(c,true)&&host.serviced_steps()==2u);
        if(finish_case==10){assert(!finish.write(c,Bus::IPC+H::PPC_FLAG,H::IPC_PPC,true)&&finish.failure()==3u&&finish.write_detail()==1u);return;}
        if(finish_case==11){cause.fetch_or(H::PI_HOLLYWOOD);assert(!finish.finished(c,true));return;}
        assert(!finish.finished(c,false));
#endif
#endif
#endif
#endif
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
#ifdef UNDERCOVER_TEST_REPLY_PROCESSOR
    for(unsigned i=1;i<=15;++i)trial(0,0,true,i);
    std::cout<<"V1280_REPLY_BODY synthetic=1 valid=1 refused=15 native_mmio=1 modeled_instructions=1 wakeup=0 original_execution=0\n";
#ifdef UNDERCOVER_TEST_WAKE_READY
    for(unsigned i=1;i<=12;++i)trial(0,0,true,0,i);
    std::cout<<"V1288_WAKE_READY synthetic=1 valid=1 refused=12 ready_queue=1 modeled_stores=1 original_execution=0\n";
#ifdef UNDERCOVER_TEST_NESTED_WAKE
    for(unsigned i=1;i<=11;++i)trial(0,0,true,0,0,i);
    std::cout<<"V1291_NESTED_WAKE synthetic=1 valid=1 refused=11 no_switch=1 wake_return=1 original_execution=0\n";
#ifdef UNDERCOVER_TEST_REPLY_COMPLETION
    for(unsigned i=1;i<=13;++i)trial(0,0,true,0,0,0,i);
    std::cout<<"V1293_REPLY_COMPLETION synthetic=1 valid=1 refused=13 native_latch_w1c=1 ready=1 ios_steps=2 original_execution=0\n";
#ifdef UNDERCOVER_TEST_REPLY_RETURN
    for(unsigned i=1;i<=12;++i)trial(0,0,true,0,0,0,0,i);
    std::cout<<"V1298_REPLY_RETURN synthetic=1 valid=1 refused=11 abi_frames=2 native_latch_w1c=1 original_execution=0\n";
#ifdef UNDERCOVER_TEST_READY_IDLE_RETURN
    for(unsigned i=1;i<=12;++i)trial(0,0,true,0,0,0,0,1,i);
    std::cout<<"V1304_READY_IDLE_RETURN synthetic=1 valid=1 refused=11 full_context=1 ready_queue=1 original_execution=0\n";
#endif
#endif
#endif
#endif
#endif
#endif
#endif
}
