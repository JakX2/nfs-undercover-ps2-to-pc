#include "wii_third_pending_reentry_v1067.h"
#include "wii_callback_prefix_v800.h"
#include "synthetic_callback_time_expectations_v1014.h"
#include "wii_callback_frontier_v829.h"
#include "wii_wireless_wrapper_v844.h"
#include "wii_callback_suffix_v841.h"
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
    uint64_t read_timebase()const{return 0x100000020ull;}
};
static unsigned trial=0;
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(!ok){std::cerr<<"V1067_ASSERT trial="<<trial<<" line="<<loc.line()<<'\n';throw std::runtime_error("third reentry");}
}
int main(){
    unsigned valid=0,refused=0,dispatch_valid=0,dispatch_refused=0,ack_valid=0,ack_refused=0,resume_valid=0,resume_refused=0,frontier_valid=0,frontier_refused=0,callback_valid=0,callback_refused=0;
    unsigned time_valid=0,time_refused=0;
    unsigned post_valid=0,post_refused=0;
    unsigned wireless_valid=0,wireless_refused=0;
    unsigned suffix_valid=0,suffix_refused=0;
    for(trial=0;trial<188;++trial){
        const unsigned suffix_fault=trial>=176?trial-175u:0u;
        const unsigned wireless_fault=trial>=168?0u:trial>=156?trial-155u:0u;
        const unsigned post_fault=trial>=148?0u:trial>=136?trial-135u:0u;
        const unsigned time_fault=trial>=128?0u:trial>=116?trial-115u:0u;
        const unsigned fault=trial>=108?0u:trial>=96?trial-47u:trial>=88?0u:trial>=83?trial-39u:trial>=75?0u:trial>=69?trial-31u:trial>=61?0u:trial>=56?trial-23u:trial<8||(trial>=32&&trial<40)||trial>=48?0u:trial<32?trial-7u:trial-15u,ch=trial%4u;
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
        c.mmu.words[Handler]=CallSave;c.mmu.words[Handler+4]=Call;c.mmu.words[Handler+8]=Nop;c.mmu.words[Handler+12]=trial>=75?0x4e800421u:Blr;
        c.mmu.words[Save]=Blr;
        const bool reversed=trial>=52&&trial<56;
        constexpr uint32_t Lwbrx=(31u<<26)|(4u<<21)|(3u<<16)|(534u<<1);
        const uint32_t load=reversed?Lwbrx:Load;
        c.mmu.words[Helper]=Nop;c.mmu.words[Helper+4]=load;c.mmu.words[Helper+8]=Nop;
        c.mmu.words[Helper+12]=Store;c.mmu.words[Helper+16]=Nop;c.mmu.words[Helper+20]=Blr;
        const std::array<AckCallSpan,3> spans{{{Handler,Handler+16},{Save,Save+4},{Helper,Helper+24}}};
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
        c.gpr[3]=Base;c.gpr[0]=C;tick();need(route.ack_before(c,Helper,Helper+4,load));
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
        tick();ok=route.ack_before(c,Helper,Helper+16,Nop);
        if(!ok)std::cerr<<"V1083_ACK_REFUSAL route="<<route.failure()<<" ack="<<route.completion_ack().failure()
                         <<" calls="<<route.ack_calls().failure()<<" stage="<<route.stage()<<'\n';
        need(ok&&route.stage()==8u);
        need(route.completion_ack().stage()==3u&&route.completion_ack().reads()==1u&&route.completion_ack().writes()==1u);
        need(route.ack_calls().entries()==2u&&route.ack_calls().returns()==1u);
        need(ctl.issued_tokens()==3u&&ctl.read(C)==(control&~SiController::TC_INT)&&
             ctl.read(S)==status&&ctl.read(B)==buffer&&sched.completed()==3u&&ack.stage()==5u);
        if(trial<61){++ack_valid;continue;}
        // The same-tick successor must execute at most once. Its native
        // call-route label was already consumed by ack_before above.
        auto resume_reject=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&cause==Other&&ctl.issued_tokens()==3u);++resume_refused;
        };
        const auto resume_tick=c.inst_count;
        if(fault==38)tick();
        if(fault==39)c.mmu.words[Context+124]^=1u;
        ok=route.resume_ack(c,Helper+16+(fault==40?4u:0u),fault==41?Blr:Nop);
        if(fault>=38&&fault<=41){resume_reject(!ok,17);continue;}need(ok);
        need(c.inst_count==resume_tick&&route.stage()==9u&&route.postack_held(c));
        if(fault==42){resume_reject(!route.resume_ack(c,Helper+16,Nop),17);continue;}
        if(fault==43){resume_reject(!route.ack_before(c,Helper,Helper+16,Nop),11);continue;}
        tick();need(route.ack_before(c,Helper,Helper+20,Blr));
        c.pc=Handler+8;tick();
        // Handler terminal label itself has an unexecuted continuation.
        // The original helper return must account for both calls.
        need(route.ack_before(c,Handler,Handler+8,Nop)&&route.postack_held(c)&&
             route.ack_calls().depth()==0u&&route.ack_calls().entries()==2u&&route.ack_calls().returns()==2u&&
             route.completion_ack().writes()==1u&&ctl.issued_tokens()==3u&&cause==Other);
        if(trial<75){++resume_valid;continue;}
        constexpr uint32_t IndirectCall=0x4e800421u;
        if(fault==44)c.mmu.words[Context+124]^=1u;
        if(fault!=45)tick();
        if(fault==46)c.mmu.words[Handler+12]=Blr;
        const unsigned owner=fault==47?Helper:Handler;
        ok=route.stop_before_callback(c,owner,Handler+12+(fault==48?4u:0u),IndirectCall);
        if(fault>=44&&fault<=48){
            need(!ok&&route.failure()==18u&&ctl.issued_tokens()==3u&&cause==Other);++frontier_refused;continue;
        }
        need(ok&&route.stage()==10u&&route.ack_calls().depth()==0u&&route.completion_ack().writes()==1u&&
             ctl.issued_tokens()==3u&&cause==Other);
        if(trial<88){++frontier_valid;continue;}
        constexpr uint32_t Root=0x8000a000u,Leaf=Root+0x100u,Stack=0x80020000u,
                           CallSite=Root+16u,Resume=Root+20u,SaveBranch=branch(CallSite,Leaf)|1u;
        constexpr std::array<uint32_t,6> prefix{0x9421ffc0u,0x7c0802a6u,0x90010044u,0x39610040u,SaveBranch,Nop};
        constexpr std::array<uint32_t,3> leaf{0x93cbfff8u,0x93ebfffcu,Blr};
        // Independently authored fixture stack, registers and instruction effects.
        // Preserve the actual third completion ACK and captured context.
        for(unsigned i=0;i<prefix.size();++i)c.mmu.words[Root+4u*i]=prefix[i];
        for(unsigned i=0;i<leaf.size();++i)c.mmu.words[Leaf+4u*i]=leaf[i];
        for(uint32_t a=Stack-0x400u;a<Stack+0x100u;a+=4u)c.mmu.words[a]=a^0xdeadbeefu;
        c.gpr[1]=Stack;c.ctr=Root;
        if(trial>=128)c.gpr[3]=ch;
        CallbackPrefixWitness<6,3> witness(Root,Leaf,prefix,leaf),foreign_witness(Root,Leaf,prefix,leaf);
        auto callback_reject=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++callback_refused;
        };
        if(fault==49)c.ctr|=3u;
        if(fault==50)c.mmu.words[Root+4u]^=1u;
        if(fault==51)tick();
        ok=route.begin_callback(c,witness,Handler+12,IndirectCall,fault!=52);
        if(fault>=49&&fault<=52){callback_reject(!ok,19);continue;}need(ok);
        c.pc=Root;c.lr=Handler+16;
        if(fault==53)c.mmu.words[Context+124]^=1u;
        if(fault==54){callback_reject(!route.callback_poll(c,foreign_witness),20);continue;}
        if(fault==55)tick();
        if(fault!=56){
            ok=route.callback_poll(c,witness);
            if(fault==53||fault==55){callback_reject(!ok,20);continue;}need(ok);
        }
        if(fault==57){callback_reject(!route.callback_poll(c,witness),20);continue;}
        tick();ok=route.callback_entry(c,witness,Root);
        if(fault==56){callback_reject(!ok,21);continue;}need(ok);
        auto step_callback=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.callback_before(c,witness,pc,w);};
        need(step_callback(Root,prefix[0]));
        c.mmu.words[Stack-64u]=Stack;c.gpr[1]=Stack-64u;
        if(fault==58)c.mmu.words[Stack-64u]^=1u;
        ok=step_callback(Root+4,prefix[1]);
        if(fault==58){callback_reject(!ok,22);continue;}need(ok);c.gpr[0]=c.lr;
        need(step_callback(Root+8,prefix[2]));c.mmu.words[Stack+4u]=c.gpr[0];
        need(step_callback(Root+12,prefix[3]));c.gpr[11]=Stack;
        need(step_callback(CallSite,SaveBranch));c.pc=Leaf;c.lr=Resume;
        if(fault==59)c.lr^=4u;
        ok=route.callback_entry(c,witness,Leaf);
        if(fault==59){callback_reject(!ok,21);continue;}need(ok);
        need(step_callback(Leaf,leaf[0]));c.mmu.words[Stack-8u]=c.gpr[30];
        need(step_callback(Leaf+4,leaf[1]));c.mmu.words[Stack-4u]=c.gpr[31];
        need(step_callback(Leaf+8,Blr));
        if(fault==60)c.mmu.words[Stack-8u]^=1u;
        ok=step_callback(Resume,Nop);
        if(fault==60){callback_reject(!ok,22);continue;}
        need(ok&&route.stage()==12u&&witness.stage()==6u&&witness.visits()==9u&&witness.writes()==4u&&
             route.completion_ack().postack_held()&&route.completion_ack().writes()==1u&&
             ctl.issued_tokens()==3u&&sched.completed()==3u&&cause==Other&&ack.stage()==5u&&dev.stage()==3u);
        if(trial<108){++callback_valid;continue;}
        constexpr std::array<uint32_t,3> continuation{Nop,branch(Resume+4,v813::T)|1u,Nop};
        auto e=v813::expected;e.callback=Root;e.callback_end=Root+688u;e.resume=Resume;e.time_site=Resume+4u;e.continuation=continuation;
        CallbackTimeWitness time(e),foreign_time(e);
        auto put=[&](uint32_t base,const auto& words){for(auto word:words){c.mmu.words[base]=word;base+=4;}};
        put(Resume,continuation);put(v813::T,v813::system_words);put(v813::D,v813::disable);
        put(v813::U,v813::timebase);put(v813::R,v813::restore);
        if(time_fault!=5){c.mmu.words[v813::Offset]=0;c.mmu.words[v813::Offset+4]=0x1234u;}
        auto reject_time=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++time_refused;
        };
        if(time_fault==4)tick();
        ok=route.begin_callback_time(c,time_fault==1?foreign_witness:witness,time,
                                    Resume+(time_fault==2?4u:0u),time_fault==3?Blr:Nop);
        if(time_fault>=1&&time_fault<=5){reject_time(!ok,23);continue;}need(ok);
        need(route.stage()==13u&&time.visits()==1u&&route.completion_ack().postack_held());
        if(time_fault==7)c.mmu.words[Context+124]^=1u;
        if(time_fault==12)mask=0;
        auto at_time=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.callback_time_before(c,time,pc,w);};
        if(time_fault==6){tick();reject_time(!route.callback_time_before(c,foreign_time,Resume+4,continuation[1]),24);continue;}
        ok=at_time(Resume+4,continuation[1]);
        if(time_fault==7||time_fault==12){reject_time(!ok,24);continue;}need(ok);
        c.pc=v813::T;c.lr=Resume+8;
        ok=route.callback_time_entry(c,time,time_fault==8?v813::D:c.pc);
        if(time_fault==8){reject_time(!ok,25);continue;}need(ok);
        bool missing_poll=false;
        for(unsigned i=0;i<25&&!missing_poll;++i){
            const uint32_t pc=v813::T+4*i;need(at_time(pc,v813::system_words[i]));
            if(i==1||i==4||i==7){
                const uint32_t root=i==1?v813::D:i==4?v813::U:v813::R;
                const auto& words=i==1?v813::disable:i==4?v813::timebase:v813::restore;
                c.pc=root;c.lr=pc+4;need(route.callback_time_entry(c,time,root));
                for(unsigned j=0;j<words.size();++j){
                    ok=at_time(root+4*j,words[j]);
                    if(time_fault==9&&i==4&&j==4){reject_time(!ok,24);missing_poll=true;break;}need(ok);
                    if(i==4){
                        if(j==0)c.gpr[3]=uint32_t(c.read_timebase()>>32);
                        if(j==1)c.gpr[4]=uint32_t(c.read_timebase());
                        if(j==2)c.gpr[5]=uint32_t(c.read_timebase()>>32);
                        if(j==3&&time_fault!=9)need(route.callback_time_poll(c,time));
                    }else if(j==0){c.gpr[6]=c.msr;c.gpr[3]=0;}
                }
            }
            if(i==5)c.gpr[3]=0;
            if(i==23){c.gpr[3]=1;c.gpr[4]=time_fault==10?0x1255u:0x1254u;c.lr=Resume+8;}
        }
        if(missing_poll)continue;
        if(time_fault==11)c.mmu.words[v813::Offset+4]^=1u;
        ok=at_time(Resume+8,Nop);
        if(time_fault==10||time_fault==11){reject_time(!ok,24);continue;}need(ok);
        need(route.stage()==14u&&time.stage()==5u&&time.cursor()==3u&&time.time_visits()==25u&&
             time.leaf_visits()==18u&&time.polls()==1u&&time.reads()==3u&&
             route.completion_ack().postack_held()&&route.completion_ack().writes()==1u&&
             ctl.issued_tokens()==3u&&sched.completed()==3u&&cause==Other&&dev.stage()==3u);
        if(trial<128){++time_valid;continue;}
        constexpr uint32_t P=Resume+8u,A=0x8000b000u,B=0x8000b100u;
        const uint32_t getter_site=P+(trial>=168?40u:16u);
        const std::array<CallbackFrontierWord,5> rows{{{P,Nop},{P+4u,0x38600000u|ch},
            {P+8u,0x90810008u},{P+12u,branch(P+12u,A)|1u},{getter_site,branch(getter_site,B)|1u}}};
        const CallbackFrontierExpectation post_expectation{Root,Root+688u,P,rows,
            {{{P+12u,A,3},{getter_site,B,5}}}};
        CallbackFrontierWitness frontier(post_expectation),foreign_frontier(post_expectation);
        for(const auto& row:rows)c.mmu.words[row.pc]=row.word;
        auto reject_post=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++post_refused;
        };
        if(post_fault==4)tick();
        if(post_fault==5)c.mmu.words[P+8u]^=1u;
        if(post_fault==6)c.mmu.words[Context+124]^=1u;
        ok=route.begin_callback_frontier(c,post_fault==1?foreign_time:time,frontier,
                                        P+(post_fault==2?4u:0u),post_fault==3?Blr:Nop);
        if(post_fault>=1&&post_fault<=6){reject_post(!ok,27);continue;}need(ok);
        need(route.stage()==15u&&frontier.visits()==1u&&route.completion_ack().postack_held());
        auto at_post=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.callback_frontier_before(c,frontier,pc,w);};
        if(post_fault==7){tick();reject_post(!route.callback_frontier_before(c,foreign_frontier,P+4u,rows[1].word),28);continue;}
        if(post_fault==8)tick();
        if(post_fault==9)mask=0;
        ok=at_post(P+4u,rows[1].word);
        if(post_fault==8||post_fault==9){reject_post(!ok,28);continue;}need(ok);
        c.gpr[3]=post_fault==12?((ch+1u)%4u):ch;c.gpr[4]=0;
        need(at_post(P+8u,rows[2].word));
        if(post_fault!=10)c.mmu.words[c.gpr[1]+8u]=0;
        if(post_fault==11)c.mmu.words[Context+124]^=1u;
        ok=at_post(P+12u,rows[3].word);
        if(post_fault>=10){reject_post(!ok,28);continue;}need(ok);
        need(route.stage()==16u&&frontier.stage()==2u&&frontier.ordinal()==3u&&frontier.zero_id()==1u&&
             frontier.visits()==4u&&frontier.writes()==1u&&route.completion_ack().postack_held()&&
             ctl.issued_tokens()==3u&&sched.completed()==3u&&cause==Other&&dev.stage()==3u);
        if(trial<148){++post_valid;continue;}
        // Source-only synthetic wrapper: retain the real ACK, use distinct
        // authored functions with the same ABI contract and metadata.
        constexpr uint32_t U=0x8000c000u,DI=0x8000c400u,RI=0x8000c500u,L=0x8000c600u,
                           SRAM=0x80030000u,Return=P+16u;
        std::array<uint32_t,39> setter;setter.fill(Nop);
        std::array<uint32_t,30> getter;getter.fill(Nop);
        std::array<uint32_t,184> unlock;unlock.fill(Nop);
        std::array<uint32_t,5> disable;disable.fill(Nop);
        std::array<uint32_t,9> restore;restore.fill(Nop);
        setter[0]=branch(A,U)|1u;setter[1]=Nop;setter[2]=Blr;getter[0]=Blr;
        unlock[0]=branch(U,DI)|1u;unlock[1]=0x90850048u;
        unlock[2]=branch(U+8u,RI)|1u;unlock[3]=Nop;unlock[4]=Blr;
        disable[0]=Blr;restore[0]=Blr;
        put(A,setter);put(B,getter);put(U,unlock);put(DI,disable);put(RI,restore);
        c.mmu.words[L]=Nop;
        for(unsigned i=0;i<20;++i)c.mmu.words[SRAM+4u*i]=0;
        c.mmu.words[SRAM+64u]=64u;c.mmu.words[SRAM+76u]=1u;
        const uint32_t return_word=trial>=168?Nop:rows[4].word;
        const WirelessExpectation wireless_ex{{{{A,setter},{B,getter},{U,unlock},{DI,disable},{RI,restore}}},
            {{{P+12u,rows[3].word,return_word,3},{getter_site,rows[4].word,Nop,5}}},L,Nop,SRAM};
        c.mmu.words[Return]=return_word;c.mmu.words[getter_site+4u]=Nop;
        WirelessWrapperWitness wrapper(wireless_ex),foreign_wrapper(wireless_ex);
        auto refuse_wireless=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++wireless_refused;
        };
        if(wireless_fault==4)tick();
        if(wireless_fault==5)c.mmu.words[SRAM+48u]=0x01000100u,c.mmu.words[SRAM+52u]=0x01000100u;
        if(wireless_fault==6)c.mmu.words[SRAM+72u]=1u;
        if(wireless_fault==7)c.gpr[3]=(ch+1u)%4u;
        ok=route.begin_wireless(c,wireless_fault==1?foreign_frontier:frontier,wrapper,
                                P+12u+(wireless_fault==2?4u:0u),wireless_fault==3?Nop:rows[3].word);
        if(wireless_fault>=1&&wireless_fault<=7){refuse_wireless(!ok,29);continue;}need(ok);
        need(route.stage()==17u&&wrapper.stage()==1u&&!wrapper.changed());
        c.pc=A;c.lr=Return;
        ok=route.wireless_entry(c,wrapper,wireless_fault==8?B:A);
        if(wireless_fault==8){refuse_wireless(!ok,31);continue;}need(ok);
        auto at_wireless=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.wireless_before(c,wrapper,pc,w);};
        if(wireless_fault==9)c.mmu.words[Context+124]^=1u;
        if(wireless_fault==10){tick();refuse_wireless(!route.wireless_before(c,foreign_wrapper,A,setter[0]),30);continue;}
        ok=at_wireless(A,setter[0]);
        if(wireless_fault==9){refuse_wireless(!ok,30);continue;}need(ok);
        c.gpr[3]=0;c.gpr[4]=20;c.gpr[5]=SRAM;c.mmu.words[SRAM+72u]=1u;
        c.pc=U;c.lr=A+4u;need(route.wireless_entry(c,wrapper,U));
        need(at_wireless(U,unlock[0]));c.pc=DI;c.lr=U+4u;need(route.wireless_entry(c,wrapper,DI));
        need(at_wireless(DI,Blr));c.gpr[4]=0;need(at_wireless(U+4u,unlock[1]));
        c.mmu.words[SRAM+72u]=0u;
        if(wireless_fault==11)c.mmu.words[SRAM+72u]^=1u;
        ok=at_wireless(U+8u,unlock[2]);
        if(wireless_fault==11){refuse_wireless(!ok,30);continue;}need(ok);
        c.pc=RI;c.lr=U+12u;need(route.wireless_entry(c,wrapper,RI));
        need(at_wireless(RI,Blr));need(at_wireless(U+12u,Nop));c.lr=A+4u;
        need(at_wireless(U+16u,Blr));need(at_wireless(A+4u,Nop));c.lr=Return;
        if(wireless_fault==12)c.gpr[31]^=1u;
        need(at_wireless(A+8u,Blr));ok=at_wireless(Return,return_word);
        if(wireless_fault==12){refuse_wireless(!ok,30);continue;}need(ok);
        need(route.stage()==18u&&wrapper.stage()==2u&&wrapper.visits()==11u&&wrapper.writes()==1u&&
             route.completion_ack().postack_held()&&ctl.issued_tokens()==3u&&cause==Other);
        if(trial<168){++wireless_valid;continue;}
        constexpr uint32_t RestoreRoot=0x8000c700u;
        // NOP, verified stack store, not-taken backward branch (one poll),
        // and a direct compiler restore call. An indirect alternative is
        // present in the exact private geometry but never executed.
        const std::array<CallbackSuffixWord,5> suffix_rows{{{Return,Nop},{Return+4u,0x90810008u},
            {Return+8u,0x4182fffcu},{Return+12u,branch(Return+12u,RestoreRoot)|1u},
            {Return+16u,IndirectCall}}};
        const CallbackSuffixExpectation sx{Root,Root+688u,Return,suffix_rows,
            {{{Return+16u,0u,4u},{Return+12u,RestoreRoot,13u}}}};
        for(const auto& row:suffix_rows)c.mmu.words[row.pc]=row.word;
        CallbackSuffixWitness suffix(sx),foreign_suffix(sx);
        auto refuse_suffix=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++suffix_refused;
        };
        if(suffix_fault==4)tick();
        if(suffix_fault==5)c.mmu.words[Return+8u]^=1u;
        if(suffix_fault==6)c.mmu.words[Context+124]^=1u;
        ok=route.begin_callback_suffix(c,suffix_fault==1?foreign_wrapper:wrapper,suffix,
                                        Return+(suffix_fault==2?4u:0u),suffix_fault==3?Blr:Nop);
        if(suffix_fault>=1&&suffix_fault<=6){refuse_suffix(!ok,32);continue;}need(ok);
        need(route.stage()==19u&&suffix.visits()==1u&&route.completion_ack().postack_held());
        auto at_suffix=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.callback_suffix_before(c,suffix,pc,w);};
        if(suffix_fault==7){tick();refuse_suffix(!route.callback_suffix_before(c,foreign_suffix,Return+4u,suffix_rows[1].word),33);continue;}
        if(suffix_fault==8)mask=0;
        c.gpr[4]=0x12345678u;
        ok=at_suffix(Return+4u,suffix_rows[1].word);
        if(suffix_fault==8){refuse_suffix(!ok,33);continue;}need(ok);
        if(suffix_fault!=9)c.mmu.words[c.gpr[1]+8u]=c.gpr[4];
        c.cr[0].eq=false;
        ok=at_suffix(Return+8u,suffix_rows[2].word);
        if(suffix_fault==9){refuse_suffix(!ok,33);continue;}need(ok);
        if(suffix_fault==10){tick();refuse_suffix(!route.callback_suffix_poll(c,suffix),34);continue;}
        if(suffix_fault!=11)need(route.callback_suffix_poll(c,suffix));
        if(suffix_fault==12)c.mmu.words[Context+124]^=1u;
        ok=at_suffix(Return+12u,suffix_rows[3].word);
        if(suffix_fault>=11){refuse_suffix(!ok,33);continue;}need(ok);
        need(route.stage()==20u&&suffix.stage()==2u&&suffix.ordinal()==13u&&suffix.target_class()==0u&&
             suffix.visits()==4u&&suffix.writes()==1u&&suffix.polls()==1u&&route.completion_ack().postack_held()&&
             ctl.issued_tokens()==3u&&cause==Other);
        ++suffix_valid;
    }
    need(valid==8&&refused==16&&dispatch_valid==8&&dispatch_refused==8&&ack_valid==8&&ack_refused==13&&
         resume_valid==8&&resume_refused==6&&frontier_valid==8&&frontier_refused==5&&callback_valid==8&&callback_refused==12&&time_valid==8&&time_refused==12&&post_valid==8&&post_refused==12&&wireless_valid==8&&wireless_refused==12&&suffix_valid==8&&suffix_refused==12);
    std::cout<<"V1067_THIRD_PENDING_REENTRY valid=8 refused=16 real_device=1 real_scheduler=1 original_execution=0\n";
    std::cout<<"V1077_THIRD_DISPATCH_JOIN valid=8 refused=8 actual_device=1 fresh_context=1 original_execution=0\n";
    std::cout<<"V1078_THIRD_ACK_JOIN valid=8 refused=13 actual_w1c=1 retired_transfer=1 original_execution=0\n";
    std::cout<<"V1085_THIRD_ACK_RESUME valid=8 refused=6 same_tick=1 no_w1c_replay=1 helper_return=1 original_execution=0\n";
    std::cout<<"V1088_THIRD_CALLBACK_STOP valid=8 refused=5 original_call_executed=0 original_execution=0\n";
    std::cout<<"V1093_THIRD_ACK_CALLBACK_JOIN valid=8 refused=12 actual_device=1 fresh_witness=1 original_execution=0\n";
    std::cout<<"V1104_THIRD_ACK_TIME_JOIN valid=8 refused=12 same_tick=1 actual_device=1 original_execution=0\n";
    std::cout<<"V1108_THIRD_ACK_FRONTIER_JOIN valid=8 refused=12 same_tick=1 actual_device=1 original_execution=0\n";
    std::cout<<"V1112_THIRD_ACK_WIRELESS_JOIN valid=8 refused=12 same_tick=1 actual_device=1 original_execution=0\n";
    std::cout<<"V1115_THIRD_ACK_SUFFIX_JOIN valid=8 refused=12 same_tick=1 actual_device=1 original_execution=0\n";
}
