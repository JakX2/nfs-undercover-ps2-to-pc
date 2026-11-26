#include "wii_third_pending_reentry_v1067.h"
#include "wii_second_completion_ack_v950.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t V=ExternalVector,T=0x80006000u,D=SiDispatchWitness::Dispatcher,H=0x80004000u,R=0x80004100u,Context=SiDispatchWitness::Thread,Other=0x100u,Base=0xcd006400u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
constexpr uint32_t Load=0x80830034u,Store=0x90830034u,Nop=0x60000000u,Rfi=0x4c000064u;
constexpr uint32_t branch(uint32_t a,uint32_t b){return 0x48000000u|((b-a)&0x03fffffcu);}
constexpr std::array<uint32_t,2> Vec{Nop,Rfi},Tramp{Nop,branch(T+4,D)};
constexpr std::array<uint8_t,8> Image{0x60,0,0,0,0x4c,0,0,0x64};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
    uint8_t read8(uint32_t a){return uint8_t(read32(a&~3u)>>(24u-8u*(a&3u)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=0x80007000u,ctr=17,xer=0x80000000u,msr=0x8032u,srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static unsigned trial=0;
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(!ok){std::cerr<<"V1067_ASSERT trial="<<trial<<" line="<<loc.line()<<'\n';throw std::runtime_error("third reentry");}
}
int main(){
    unsigned valid=0,refused=0,dispatch_valid=0,dispatch_refused=0,ack_valid=0,ack_refused=0;
    for(trial=0;trial<61;++trial){
        const unsigned fault=trial>=56?trial-23u:trial<8||(trial>=32&&trial<40)||trial>=48?0u:trial<32?trial-7u:trial-15u,ch=trial%4u;
        std::atomic<uint32_t> cause{Other},mask{SI},foreign_cause{Other|SI},foreign_mask{SI};
        SiController ctl(cause),foreign(foreign_cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler sched(ctl,ports,8);
        const uint32_t cfg=0x40010300u|(ch<<1);
        ctl.write(C,cfg|1u);sched.advance(1);sched.advance(9);
        ctl.write(C,cfg|SiController::TC_INT);ctl.write(B,0);ctl.write(C,cfg|1u);sched.advance(10);sched.advance(18);
        Cpu c;c.mmu.words={{H,Load},{H+4,Store},{H+8,Nop},{R,Rfi},{V,Vec[0]},{V+4,Vec[1]},{T,Tramp[0]},{T+4,Tramp[1]},{D,Nop}};
        for(unsigned i=0;i<32;++i)c.gpr[i]=17u*i+3u;
        c.gpr[3]=Base;
        const auto gp=c.gpr;const auto lr=c.lr,ctr=c.ctr,xer=c.xer;
        ExternalReturnWitness prior;need(prior.capture(c,cause,mask));
        c.msr=0x32u;c.srr0=H;c.srr1=0x8032u;
        SecondCompletionAck ack;PostAckTransferDevice dev;
        need(ack.arm(ctl,cause,mask,c.inst_count,2,true));
        auto tick=[&]{sched.advance(++c.inst_count);};
        tick();need(ack.before(c,H,Load,true));uint32_t value=0;
        need(ack.read(ctl,C,value));c.gpr[4]=value;
        tick();need(ack.before(c,H+4,Store,true)&&ack.write(ctl,C,value));
        tick();need(ack.before(c,H+8,Nop,true)&&ack.resume_after_ack(c,H+8,Nop));
        need(ack.handoff_follow_on(dev,ctl,cause,mask,c.inst_count,ch,true,ports[ch].type,8));
        auto step=[&](Access a=Access::None,uint32_t address=0,std::optional<uint32_t> v=std::nullopt){tick();need(dev.before(c.inst_count,a,address,v));};
        step(Access::Read,Base+C);need(dev.read(ctl,C,value));
        step(Access::Write,Base+B,0u);need(dev.write(ctl,B,0));
        step(Access::Write,Base+S,0x0f0f0f0fu);need(dev.write(ctl,S,0x0f0f0f0fu));
        step(Access::Write,Base+C,cfg|1u);need(dev.write(ctl,C,cfg|1u));
        for(unsigned i=0;i<9;++i)step();
        need(dev.finish(c.inst_count,1)&&dev.token()==3u&&dev.held_now());
        tick();need(dev.after_return_at(c.inst_count)&&dev.arm_suffix_status_read(c.inst_count,Base+S)&&dev.read(ctl,S,value));
        tick();need(dev.after_return_at(c.inst_count)&&dev.arm_suffix_status_write(c.inst_count,Base+S,value)&&dev.write(ctl,S,value));
        c.gpr=gp;c.pc=R;
        tick();need(dev.after_return_at(c.inst_count)&&prior.before_pending_rfi(c,R,Rfi,cause,mask));
        // Model native RFI effects in this original-free fixture only.
        c.pc=H;c.msr=c.srr1;
        if(fault!=1)need(prior.pending_rfi_return(c,cause,mask));
        ThirdPendingReentry route({T,D,Context,Nop,Vec,Tramp});
        const auto control=ctl.read(C),status=ctl.read(S),buffer=ctl.read(B);
        if(fault==5)c.gpr[31]^=1u;
        if(fault==6)c.mmu.words[V]^=1u;
        if(fault==7)tick();
        bool ok=route.enter(c,prior,dev,fault==2?foreign:ctl,fault==3?foreign_cause:cause,fault==4?foreign_mask:mask,Image);
        if(fault>=1&&fault<=7){need(!ok&&route.failure()==1u&&c.pc==H);++refused;continue;}need(ok);
        if(fault==8)tick();
        ok=route.outer_poll(c);
        if(fault==8){need(!ok&&route.failure()==2u);++refused;continue;}need(ok);
        if(fault!=9)tick();
        if(fault==10)c.gqr[0]^=1u;
        ok=route.vector_entry(c,V);
        if(fault==9||fault==10){need(!ok&&route.failure()==3u);++refused;continue;}need(ok);
        tick();ok=route.before(c,fault==11?V+4:V,Vec[0]);
        if(fault==11){need(!ok&&route.failure()==4u);++refused;continue;}need(ok);
        for(unsigned i=3;i<=5;++i)c.mmu.words[Context+4*i]=gp[i];
        c.mmu.words[Context+132]=lr;c.mmu.words[Context+136]=ctr;c.mmu.words[Context+140]=xer;
        c.mmu.words[Context+408]=H;c.mmu.words[Context+412]=0x8032u;c.srr0=T;c.srr1=0x32u;
        tick();need(route.before(c,V+4,Rfi));
        c.pc=T;c.msr=c.srr1;c.gpr[3]=4;c.gpr[4]=Context;
        if(fault==12)ctl.write(C,cfg|SiController::TC_INT);
        ok=route.poll(c);
        if(fault==12){need(!ok&&route.failure()==5u);++refused;continue;}need(ok);
        if(fault!=13)tick();
        if(fault==14)c.mmu.words[Context+12]^=1u;
        ok=route.entry(c,T);
        if(fault==13||fault==14){need(!ok&&route.failure()==6u);++refused;continue;}need(ok);
        tick();need(route.before(c,T,Tramp[0]));
        tick();need(route.before(c,T+4,Tramp[1]));
        for(unsigned i=0;i<32;++i)c.mmu.words[Context+4*i]=gp[i];
        c.mmu.words[Context+128]=0;c.pc=D;
        need(route.poll(c));tick();
        if(fault==15)c.mmu.words[Context+124]^=1u;
        if(fault==16)mask=0;
        ok=route.entry(c,D);
        if(fault==15||fault==16){need(!ok&&route.failure()==6u);++refused;continue;}need(ok);
        need(route.stage()==4u&&route.saved(c,Context)&&route.vector_visits()==2u&&route.trampoline_visits()==2u);
        need(dev.held_now()&&ack.stage()==5u&&ctl.issued_tokens()==3u&&sched.completed()==3u&&
             cause==(Other|SI)&&ctl.read(C)==control&&ctl.read(S)==status&&ctl.read(B)==buffer);
        if(trial<24){++valid;continue;}
        // Synthetic direct-leaf effects only; exercise the same production
        // device-bound dispatcher join used by the focused original runner.
        constexpr uint32_t Handler=SiDispatchWitness::Handler,Indirect=D+16u;
        SiDispatchExpectations ex{};
        ex.dispatcher_word=Nop;ex.handler_word=trial>=40?(branch(Handler,0x80009100u)|1u):Nop;ex.indirect_pc=Indirect;ex.indirect_word=0x4e800421u;
        for(unsigned i=0;i<4;++i){
            const uint32_t site=D+0x20u+4u*i,dst=0x80008000u+0x100u*i;
            ex.edges[i]={dst,site+4u,branch(site,dst)|1u,Nop};
            c.mmu.words[site]=ex.edges[i].branch_word;c.mmu.words[dst]=Nop;
        }
        c.mmu.words[Indirect]=ex.indirect_word;c.mmu.words[Handler]=ex.handler_word;
        c.mmu.words[0x80003090u]=Handler;c.mmu.words[0x800000d4u]=Context;c.mmu.words[0x800000e4u]=Context;
        SecondSiDispatchWitness dispatch(ex);
        auto reject=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason);++dispatch_refused;
        };
        if(fault==17)c.mmu.words[0x80003090u]^=4u;
        if(fault==18)c.mmu.words[Context+124]^=1u;
        ok=route.begin_dispatch(c,dispatch);
        if(fault==17||fault==18){reject(!ok,7);continue;}need(ok);
        if(fault==19)tick();
        if(fault==20)dispatch.record(false,0x0c003000u,32,cause.load()^SI,false);
        else dispatch.record(false,0x0c003000u,32,cause.load(),false);
        if(fault!=22)dispatch.record(false,0x0c003004u,32,mask.load(),false);
        tick();ok=route.dispatch_tick(c);
        if(fault==19||fault==20){reject(!ok,8);continue;}need(ok);
        c.pc=ex.edges[0].pc;c.lr=ex.edges[0].lr;
        ok=route.dispatch_entry(c,fault==21?ex.edges[1].pc:c.pc);
        if(fault==21){reject(!ok,9);continue;}need(ok);
        for(unsigned i=1;i<4;++i){
            need(route.dispatch_poll(c));tick();need(route.dispatch_tick(c));
            c.pc=ex.edges[i].pc;c.lr=ex.edges[i].lr;need(route.dispatch_entry(c,c.pc));
        }
        need(route.dispatch_poll(c));tick();
        if(fault==24)ctl.write(C,cfg|SiController::TC_INT);
        ok=route.dispatch_tick(c);
        if(fault==24){reject(!ok,8);continue;}need(ok);
        c.pc=Handler;c.ctr=Handler;c.lr=Indirect+4u;c.gpr[3]=fault==23?19u:20u;c.gpr[4]=Context;
        ok=route.dispatch_entry(c,Handler);
        if(fault==22||fault==23){reject(!ok,9);continue;}need(ok);
        need(route.stage()==6u&&dispatch.stage()==6u&&route.dispatch_saved(c,Context)&&
             dev.held_now()&&ack.stage()==5u&&ctl.issued_tokens()==3u&&sched.completed()==3u&&
             cause==(Other|SI)&&ctl.read(C)==control&&ctl.read(S)==status&&ctl.read(B)==buffer);
        if(trial<40){++dispatch_valid;continue;}
        // Synthetic authenticated handler and single native helper geometry.
        constexpr uint32_t Helper=0x80009000u,Save=Helper+0x100u,Blr=0x4e800020u;
        constexpr uint32_t CallSave=branch(Handler,Save)|1u,Call=branch(Handler+4,Helper)|1u;
        c.mmu.words[Handler]=CallSave;c.mmu.words[Handler+4]=Call;c.mmu.words[Handler+8]=Nop;
        c.mmu.words[Save]=Blr;
        const bool reversed=trial>=52&&trial<56;
        constexpr uint32_t Lwbrx=(31u<<26)|(4u<<21)|(3u<<16)|(534u<<1);
        const uint32_t load=reversed?Lwbrx:Load;
        c.mmu.words[Helper]=Nop;c.mmu.words[Helper+4]=load;c.mmu.words[Helper+8]=Nop;
        c.mmu.words[Helper+12]=Store;c.mmu.words[Helper+16]=Nop;
        const std::array<AckCallSpan,3> spans{{{Handler,Handler+12},{Save,Save+4},{Helper,Helper+20}}};
        const std::array<AckCallEdge,2> edges{{{Handler,Save},{Handler+4,Helper}}};
        auto ack_reject=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason);++ack_refused;
        };
        if(fault==25)c.mmu.words[Context+124]^=1u;
        if(fault==26)c.pc=Handler+4;
        if(fault==27)tick();
        if(fault==33)c.mmu.words[Handler]^=4u;
        if(fault==34)c.mmu.words[0x80003090u]^=4u;
        if(fault==35)c.lr^=4u;
        ok=route.begin_ack(c,spans,edges);
        if((fault>=25&&fault<=27)||(fault>=33&&fault<=35)){
            ack_reject(!ok,10);need(dev.stage()==2u&&ctl.read(C)==control&&cause==(Other|SI));continue;
        }
        need(ok&&dev.stage()==3u&&route.completion_ack().token()==3u&&
             route.completion_ack().no_response_verified()==!ports[ch].type.has_value()&&
             ctl.read(C)==control&&ctl.read(S)==status&&ctl.read(B)==buffer&&cause==(Other|SI));
        if(fault==28){ack_reject(!route.ack_read(C,value),14);continue;}
        tick();need(route.ack_before(c,Handler,Handler,CallSave));c.pc=Save;c.lr=Handler+4;
        need(route.ack_entry(c,Save));tick();need(route.ack_before(c,Save,Save,Blr));
        c.pc=Handler+4;tick();need(route.ack_before(c,Handler,Handler+4,Call));c.pc=Helper;c.lr=Handler+8;
        if(fault==29){ack_reject(!route.ack_entry(c,Helper+4),12);continue;}
        need(route.ack_entry(c,Helper));
        tick();need(route.ack_before(c,Helper,Helper,Nop));
        c.gpr[3]=Base;c.gpr[0]=0;tick();need(route.ack_before(c,Helper,Helper+4,load));
        if(fault==37){tick();ack_reject(!route.ack_before(c,Helper,Helper+8,Nop),16);need(cause==(Other|SI));continue;}
        need(route.ack_read(C,value));
        auto swap=[](uint32_t v){return (v>>24)|((v>>8)&0xff00u)|((v<<8)&0xff0000u)|(v<<24);};
        c.gpr[4]=reversed?swap(value):value;
        if(fault==36)c.gpr[4]^=1u;
        tick();ok=route.ack_before(c,Helper,Helper+8,Nop);
        if(fault==36){ack_reject(!ok,16);need(cause==(Other|SI));continue;}need(ok);
        // Model the independent fixture's register operations only after
        // the native load result was verified. Real guest code is unmodified.
        if(reversed)c.gpr[4]=swap(c.gpr[4]);
        if(fault==30)c.gpr[4]&=~SiController::TC_INT;
        tick();need(route.ack_before(c,Helper,Helper+12,Store));
        if(fault==30){ack_reject(!route.ack_write(C,c.gpr[4]),15);need(cause==(Other|SI));continue;}
        if(fault==31){ack_reject(!route.ack_write(C,c.gpr[4]^2u),15);need(cause==(Other|SI));continue;}
        need(route.ack_write(C,c.gpr[4])&&cause==Other);
        if(fault==32){c.mmu.words[Context+124]^=1u;tick();ack_reject(!route.ack_before(c,Helper,Helper+16,Nop),11);continue;}
        tick();need(route.ack_before(c,Helper,Helper+16,Nop)&&route.stage()==8u&&
                    route.completion_ack().stage()==3u&&route.completion_ack().reads()==1u&&route.completion_ack().writes()==1u&&
                    route.ack_calls().entries()==2u&&route.ack_calls().returns()==1u&&
                    ctl.issued_tokens()==3u&&ctl.read(C)==(control&~SiController::TC_INT)&&
                    ctl.read(S)==status&&ctl.read(B)==buffer&&sched.completed()==3u&&ack.stage()==5u);
        ++ack_valid;
    }
    need(valid==8&&refused==16&&dispatch_valid==8&&dispatch_refused==8&&ack_valid==8&&ack_refused==13);
    std::cout<<"V1067_THIRD_PENDING_REENTRY valid=8 refused=16 real_device=1 real_scheduler=1 original_execution=0\n";
    std::cout<<"V1077_THIRD_DISPATCH_JOIN valid=8 refused=8 actual_device=1 fresh_context=1 original_execution=0\n";
    std::cout<<"V1078_THIRD_ACK_JOIN valid=8 refused=13 actual_w1c=1 retired_transfer=1 original_execution=0\n";
}
