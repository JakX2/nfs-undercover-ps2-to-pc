#include "wii_third_pending_reentry_v1067.h"
#include "wii_third_alarm_suffix_v1047.h"
#include "wii_held_pending_epilogue_v1149.h"
#include "wii_callback_prefix_v800.h"
#include "synthetic_callback_time_expectations_v1014.h"
#include "wii_callback_frontier_v829.h"
#include "wii_wireless_wrapper_v844.h"
#include "wii_callback_suffix_v841.h"
#include "wii_callback_return_v846.h"
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
    uint16_t read16(uint32_t a){return uint16_t((uint16_t(read8(a))<<8)|read8(a+1u));}
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
    unsigned return_valid=0,return_refused=0;
    unsigned handler_valid=0,handler_refused=0;
    unsigned handler_return_valid=0,handler_return_refused=0;
    unsigned ep_valid=0,ep_refused=0;
    unsigned rd_valid=0,rd_refused=0;
    unsigned held_valid=0,held_refused=0;
    unsigned held_return_valid=0,held_return_refused=0;
    unsigned held_ep_valid=0,held_ep_refused=0;
    unsigned held_vec_valid=0,held_vec_refused=0;
    unsigned held_disp_valid=0,held_disp_refused=0;
    {
        constexpr uint32_t P=0x80004000u,W=0x60000000u,O=0x80004000u;
        std::array<ThirdAckNativeLabel,2> rows{{{P,W,O,false},{P+4u,W,O,true}}};
        need(third_ack_native_owner(rows,P,W)==O);
        need(!third_ack_native_owner(rows,P+4u,W)&&!third_ack_native_owner(rows,P,W^1u)&&
             !third_ack_native_owner(rows,P+8u,W));
        rows[1]={P,W,O,false};need(!third_ack_native_owner(rows,P,W));
        rows[0].owner=0;need(!third_ack_native_owner(rows,P,W));
    }
    unsigned held_ack_valid=0,held_ack_refused=0;
    unsigned held_postack_valid=0,held_postack_refused=0;
    unsigned held_callback_valid=0,held_callback_refused=0;
    unsigned held_prefix_valid=0,held_prefix_refused=0;
    for(trial=0;trial<468;++trial){
        const unsigned rd_fault=trial>=276?trial-275u:0u;
        const unsigned ep_fault=trial>=268?0u:trial>=256?trial-255u:0u;
        const unsigned hr_fault=trial>=248?0u:trial>=236?trial-235u:0u;
        const unsigned handler_fault=trial>=228?0u:trial>=216?trial-215u:0u;
        const unsigned return_fault=trial>=208?0u:trial>=196?trial-195u:0u;
        const unsigned suffix_fault=trial>=188?0u:trial>=176?trial-175u:0u;
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
        if(trial>=288){c.gpr[1]=0x80035000u;c.gpr[20]=ch;}
        if(trial>=328){c.gpr[13]=0x80039000u;c.gpr[21]=Context;}
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
        if(trial>=288){
            const unsigned f=trial>=308?0u:trial>=296?trial-295u:0u;
            const unsigned hr=trial>=328?0u:trial>=316?trial-315u:0u;
            const unsigned he=trial>=348?0u:trial>=336?trial-335u:0u;
            const unsigned hv=trial>=368?0u:trial>=356?trial-355u:0u;
            const unsigned hd=trial>=388?0u:trial>=376?trial-375u:0u;
            const unsigned ha=trial>=408?0u:trial>=396?trial-395u:0u;
            const unsigned hp=trial>=428?0u:trial>=416?trial-415u:0u;
            const unsigned hc=trial>=448?0u:trial>=436?trial-435u:0u;
            const unsigned hprefix=trial>=456?trial-455u:0u;
            constexpr uint32_t A=0x80034000u,Table=0x80033000u,Rd=0x80830038u,Wr=0x90830038u;
            constexpr uint32_t Indexed=(31u<<26)|(5u<<21)|(3u<<16)|(4u<<11)|(23u<<1);
            constexpr uint32_t Compare=(10u<<26)|(5u<<16)|7u,Branch=(16u<<26)|(12u<<21)|(2u<<16)|12u;
            const HandlerIndexBranchExpectation ix{A,Indexed,Compare,Branch,A+64u,
                {Table,Table+4u,Table+8u,Table+12u},20u};
            std::array<HandlerSuffixLabel,16> rows{};
            for(unsigned i=0;i<14;++i)rows[i]={A+4u*i,Nop,0,0};
            rows[1].word=Rd;rows[2].word=Wr;rows[11].word=Indexed;rows[12].word=Compare;rows[13].word=Branch;
            rows[14]={A+56u,branch(A+56u,A+64u),0,0};
            rows[15]={A+64u,branch(A+64u,A+128u)|1u,12u,1u};
            for(auto x:rows)c.mmu.words[x.pc]=x.word;
            const uint32_t datum=(trial&4u)?9u:7u;
            for(unsigned i=0;i<4;++i)c.mmu.words[Table+4u*i]=i==ch?datum:13u;
            for(unsigned i=0;i<32;++i)c.mmu.words[Context+4u*i]=gp[i];
            c.mmu.words[Context+128]=0;c.mmu.words[Context+132]=lr;c.mmu.words[Context+136]=ctr;
            c.mmu.words[Context+140]=xer;c.mmu.words[Context+408]=H;c.mmu.words[Context+412]=0x8032u;
            constexpr uint32_t Root=A+128u,Call=A+64u,Dest=0x80038000u;
            constexpr auto restore=[]{
                std::array<uint32_t,16> out{};
                for(unsigned i=0;i<15;++i)out[i]=0x800b0000u|((17u+i)<<21)|((0xffc4u+4u*i)&0xffffu);
                out.back()=0x4e800020u;return out;
            }();
            constexpr std::array<uint32_t,4> tail{0x80010044u,0x7c0803a6u,0x38210040u,0x4e800020u};
            constexpr uint32_t En=0x8003b000u,Re=0x8003b100u,Di=0x8003b200u,Rs=0x8003b300u,Lo=0x8003b400u;
            const uint32_t dest_word=trial>=328?(branch(Dest,En)|1u):Nop;
            const HandlerReturnExpectation e{Call,Root,Dest,restore,tail,dest_word};
            HeldHandlerReturnWitness ret(e);
            const auto original=c.gpr;
            auto refused_return=[&](bool bad){
                need(bad&&ctl.issued_tokens()==3u&&cause==(Other|SI)&&dev.stage()==2u);++held_return_refused;
            };
            if(trial>=308){
                for(unsigned i=0;i<restore.size();++i)c.mmu.words[Root+4u*i]=restore[i];
                for(unsigned i=0;i<tail.size();++i)c.mmu.words[Call+4u+4u*i]=tail[i];
                c.mmu.words[Dest]=dest_word;
                c.pc=H;c.lr=hr==1?Dest+4u:Dest;
                bool ok=ret.capture(c,hr==2?H+4u:H,prior,Context);
                if(hr==1||hr==2){refused_return(!ok);continue;}need(ok);
                c.gpr[1]=original[1]-64u;c.gpr[11]=original[1];
                for(unsigned i=17;i<32;++i){
                    c.mmu.words[original[1]-4u*(32u-i)]=original[i];
                    if(i!=20u)c.gpr[i]^=0x1234u;
                }
                c.mmu.words[original[1]+4u]=Dest;
            }
            c.pc=A;
            HeldHandlerSuffixWitness held(ix);
            auto refused_held=[&](bool bad){
                need(bad&&ctl.issued_tokens()==3u&&cause==(Other|SI)&&dev.stage()==2u);++held_refused;
            };
            if(f==1)tick();
            if(f==2)c.mmu.words[Context+124]^=1u;
            if(f==3)c.mmu.words[A+44u]^=1u;
            bool ok=held.start(c,A,Nop,dev,prior,Context,rows,A+4u,A+8u);
            if(f>=1&&f<=3){refused_held(!ok);continue;}need(ok);
            auto at=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return held.before(c,pc,w);};
            c.gpr[3]=Base;
            if(f==4)c.gpr[3]+=4u;
            ok=at(A+4u,Rd);
            if(f==4){refused_held(!ok);continue;}need(ok);
            if(f!=5){need(dev.read(ctl,S,value));c.gpr[4]=value^(f==6?1u:0u);}
            ok=at(A+8u,Wr);
            if(f==5||f==6){refused_held(!ok);continue;}need(ok);
            if(f==7){refused_held(!dev.write(ctl,S,value^1u));continue;}
            if(f!=8)need(dev.write(ctl,S,value));
            ok=at(A+12u,Nop);
            if(f==8){refused_held(!ok);continue;}need(ok);
            for(unsigned i=4;i<11;++i)need(at(A+4u*i,Nop));
            c.gpr[3]=Table;c.gpr[4]=4u*ch;need(at(A+44u,Indexed));c.gpr[5]=datum^(f==9?1u:0u);
            ok=at(A+48u,Compare);
            if(f==9){refused_held(!ok);continue;}need(ok);
            c.cr[0]={false,datum>7u,datum==7u,false};
            if(f==10)c.cr[0].eq=!c.cr[0].eq;
            ok=at(A+52u,Branch);
            if(f==10){refused_held(!ok);continue;}need(ok);
            if(f==11){refused_held(!at(datum==7u?A+56u:A+64u,Nop));continue;}
            if(datum!=7u)need(at(A+56u,rows[14].word));
            if(f==12)tick();
            ok=at(A+64u,rows[15].word);
            if(f==12){refused_held(!ok);continue;}need(ok);
            need(held.stage()==2u&&held.taken()==(datum==7u)&&held.reads()==1u&&held.writes()==1u&&
                 dev.held_now()&&ctl.issued_tokens()==3u&&cause==(Other|SI));
            if(trial<308){++held_valid;continue;}
            if(hr==3)tick();
            if(hr==4)c.mmu.words[Root]^=1u;
            ok=ret.start(c,Call,rows.back().word,held,dev);
            if(hr==3||hr==4){refused_return(!ok);continue;}need(ok);
            c.pc=Root;c.lr=Call+4u;
            ok=ret.entry(c,hr==5?Root+4u:Root);
            if(hr==5){refused_return(!ok);continue;}need(ok);
            auto at_ret=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return ret.before(c,pc,w);};
            if(hr==6)c.mmu.words[original[1]-60u]^=1u;
            if(hr==7)c.mmu.words[Context+124u]^=1u;
            if(hr==8)mask=0;
            ok=at_ret(Root,restore[0]);
            if(hr>=6&&hr<=8){refused_return(!ok);continue;}need(ok);
            c.gpr[17]=original[17];
            for(unsigned i=1;i<15;++i){need(at_ret(Root+4u*i,restore[i]));c.gpr[17u+i]=original[17u+i];}
            need(at_ret(Root+60u,restore.back()));
            need(at_ret(Call+4u,tail[0]));c.gpr[0]=Dest;
            need(at_ret(Call+8u,tail[1]));c.lr=Dest;
            need(at_ret(Call+12u,tail[2]));c.gpr[1]=original[1];
            need(at_ret(Call+16u,tail[3]));c.pc=Dest;
            if(hr!=9)need(ret.poll(c));
            if(hr==10){refused_return(!ret.poll(c));continue;}
            tick();if(hr==11)tick();
            ok=ret.dispatch(c,Dest,dest_word);
            if(hr==9||hr==11){refused_return(!ok);continue;}need(ok);
            if(hr==12)c.gpr[31]^=1u;
            ok=at_ret(Dest,dest_word);
            if(hr==12){refused_return(!ok);continue;}need(ok);
            need(ret.stage()==3u&&ret.visits()==21u&&dev.held_now()&&ctl.issued_tokens()==3u&&cause==(Other|SI));
            if(trial<328){++held_return_valid;continue;}
            // Original-free effects; actual witness, device and scheduler.
            constexpr uint32_t Blr=0x4e800020u;
            const uint32_t counter=c.gpr[13]+4u,hint=c.gpr[13]+8u;
            c.mmu.words[counter]=2;c.mmu.words[hint]=0;
            for(unsigned i=0;i<8;++i)c.mmu.words[Context+0x1a4u+4*i]=0;
            c.mmu.words[Context+0x1a0u]=0;
            c.mmu.words[En]=branch(En,Di)|1u;c.mmu.words[En+4]=branch(En+4,Rs)|1u;
            c.mmu.words[En+8]=Blr;c.mmu.words[Di]=Blr;c.mmu.words[Rs]=Blr;c.mmu.words[Re]=Blr;
            c.mmu.words[Dest+4]=branch(Dest+4,Re)|1u;c.mmu.words[Dest+8]=Nop;
            c.mmu.words[Dest+12]=branch(Dest+12,Lo)|1u;c.mmu.words[Lo]=Rfi;
            HeldPendingEpilogueWitness ep({Dest,En,Re,Di,Rs,Lo,Lo+4,Context,4,8,21,255},{T,D,Context,Nop,Vec,Tramp});
            using Poll=HeldPendingEpilogueWitness::PollResult;
            auto refused_ep=[&](bool bad){
                need(bad&&ctl.issued_tokens()==3u&&cause==(Other|SI)&&dev.stage()==2u);++held_ep_refused;
            };
            if(he==1)tick();
            if(he==2)c.mmu.words[Context+124]^=1u;
            if(he==3)c.gpr[21]^=4u;
            ok=ep.begin(c,Dest,dest_word,ret,prior,dev,he==4?foreign:ctl,cause,mask);
            if(he>=1&&he<=4){refused_ep(!ok);continue;}need(ok);
            auto enter=[&](uint32_t pc,uint32_t link){c.pc=pc;c.lr=link;return ep.entry(c,pc);};
            auto at_ep=[&](uint32_t pc){c.pc=pc;tick();return ep.before(c,pc,c.mmu.words.at(pc));};
            ok=enter(he==5?Di:En,Dest+4);
            if(he==5){refused_ep(!ok);continue;}need(ok);
            if(he==6){refused_ep(!at_ep(En+4));continue;}
            need(at_ep(En)&&enter(Di,En+4)&&at_ep(Di));
            need(at_ep(En+4)&&enter(Rs,En+8)&&at_ep(Rs));
            c.lr=Dest+4;c.gpr[3]=2;c.mmu.words[counter]=1;
            need(at_ep(En+8)&&at_ep(Dest+4)&&enter(Re,Dest+8)&&at_ep(Re));
            need(at_ep(Dest+8));c.gpr[3]=Context;
            need(at_ep(Dest+12)&&enter(Lo,Dest+16));
            c.gpr=gp;c.lr=lr;c.ctr=ctr;c.xer=xer;c.cr.fill({});c.srr0=H;c.srr1=0x8032u;
            if(he==7)c.gpr[31]^=1u;
            ok=at_ep(Lo);
            if(he==7){refused_ep(!ok);continue;}need(ok&&ep.stage()==2u);
            c.pc=H;c.msr=c.srr1;
            if(he==8)c.gqr[0]^=1u;
            if(he==9)c.mmu.words[V]^=1u;
            if(he==10)tick();
            auto polled=ep.poll(c,Image);
            if(he>=8&&he<=10){refused_ep(polled==Poll::Rejected);continue;}
            need(polled==Poll::Entered&&ep.stage()==3u&&c.pc==V);
            if(he!=11)need(ep.poll(c,Image)==Poll::Continue);
            tick();if(he==12)tick();
            ok=ep.entry(c,V);
            if(he==11||he==12){refused_ep(!ok);continue;}
            need(ok&&ep.stage()==4u&&ep.next().stage()==3u&&dev.held_now());
            if(trial<348){++held_ep_valid;continue;}
            auto refused_vec=[&](bool bad){
                need(bad&&ep.failure()==5u&&ctl.issued_tokens()==3u&&cause==(Other|SI)&&dev.stage()==2u);++held_vec_refused;
            };
            if(hv==1)tick();
            if(hv==2)c.gqr[0]^=1u;
            tick();ok=ep.before(c,hv==3?V+4u:V,hv==4?Rfi:Vec[0]);
            if(hv>=1&&hv<=4){refused_vec(!ok);continue;}need(ok);
            for(unsigned i=3;i<=5;++i)c.mmu.words[Context+4*i]=gp[i];
            c.mmu.words[Context+132]=lr;c.mmu.words[Context+136]=ctr;c.mmu.words[Context+140]=xer;
            c.mmu.words[Context+408]=H;c.mmu.words[Context+412]=0x8032u;c.srr0=T;c.srr1=0x32u;
            c.pc=V+4;tick();need(ep.before(c,V+4,Rfi));
            c.pc=T;c.msr=c.srr1;c.gpr[3]=4;c.gpr[4]=Context;
            if(hv==5)c.gqr[7]^=1u;
            if(hv!=6){
                polled=ep.poll(c,Image);
                if(hv==5){refused_vec(polled==Poll::Rejected);continue;}need(polled==Poll::Continue);
            }
            if(hv!=7)tick();
            if(hv==8)c.mmu.words[Context+12]^=1u;
            ok=ep.entry(c,T);
            if(hv>=6&&hv<=8){refused_vec(!ok);continue;}need(ok);
            c.pc=T;tick();need(ep.before(c,T,Tramp[0]));
            c.pc=T+4;tick();need(ep.before(c,T+4,Tramp[1]));
            for(unsigned i=0;i<32;++i)c.mmu.words[Context+4*i]=gp[i];
            c.mmu.words[Context+128]=0;c.pc=D;
            need(ep.poll(c,Image)==Poll::Continue);tick();
            if(hv==9)c.mmu.words[Context+124]^=1u;
            if(hv==10)mask=0;
            if(hv==11)c.pc=D+4u;
            if(hv==12)tick();
            ok=ep.entry(c,D);
            if(hv>=9){refused_vec(!ok);continue;}need(ok);
            need(ep.stage()==5u&&ep.saved(c)&&ep.vector_visits()==2u&&ep.trampoline_visits()==2u&&
                 dev.held_now()&&ctl.issued_tokens()==3u&&sched.completed()==3u&&cause==(Other|SI));
            if(trial<368){++held_vec_valid;continue;}
            constexpr uint32_t Handler=SiDispatchWitness::Handler,Indirect=D+16u;
            SiDispatchExpectations ex{};
            constexpr uint32_t Helper=0x80009000u,Save=Helper+0x100u;
            constexpr uint32_t CallSave=branch(Handler,Save)|1u,AckCall=branch(Handler+4,Helper)|1u;
            ex.dispatcher_word=Nop;ex.handler_word=trial>=388?CallSave:Nop;ex.indirect_pc=Indirect;ex.indirect_word=0x4e800421u;
            for(unsigned i=0;i<4;++i){
                const uint32_t site=D+0x20u+4u*i,dst=0x80008000u+0x100u*i;
                ex.edges[i]={dst,site+4u,branch(site,dst)|1u,Nop};
                c.mmu.words[site]=ex.edges[i].branch_word;c.mmu.words[dst]=Nop;
            }
            c.mmu.words[Indirect]=ex.indirect_word;c.mmu.words[Handler]=ex.handler_word;
            c.mmu.words[0x80003090u]=Handler;c.mmu.words[0x800000d4u]=Context;c.mmu.words[0x800000e4u]=Context;
            auto refuse_disp=[&](bool bad){
                need(bad&&ctl.issued_tokens()==3u&&cause==(Other|SI)&&dev.stage()==2u);++held_disp_refused;
            };
            if(hd==1)c.mmu.words[0x80003090u]^=4u;
            ok=ep.begin_dispatch(c,ex);
            if(hd==1){refuse_disp(!ok);continue;}need(ok);
            if(hd==2){refuse_disp(!ep.begin_dispatch(c,ex));continue;}
            auto* witness=ep.dispatch_witness();need(witness);
            if(hd==3)tick();
            if(hd==4)c.mmu.words[Context+124]^=1u;
            tick();ok=ep.dispatch_before(c,D,hd==5?Rfi:Nop,hd==6);
            if(hd>=3&&hd<=6){refuse_disp(!ok);continue;}need(ok);
            witness->record(false,0x0c003000u,32,hd==7?cause.load()^SI:cause.load(),false);
            if(hd!=8)witness->record(false,0x0c003004u,32,mask.load(),false);
            if(hd==9)witness->record(false,0x0c003000u,32,cause.load(),false);
            if(hd==10)witness->record(false,0x0c003004u,32,mask.load(),true);
            for(unsigned i=0;i<4;++i){
                c.pc=ex.edges[i].lr-4u;tick();ok=ep.dispatch_before(c,c.pc,ex.edges[i].branch_word,false);
                if(i==0&&(hd==7||hd==10)){refuse_disp(!ok);break;}
                need(ok);c.pc=ex.edges[i].pc;c.lr=ex.edges[i].lr;
                ok=ep.entry(c,hd==11&&i==0?c.pc+4u:c.pc);
                if(hd==11&&i==0){refuse_disp(!ok);break;}need(ok);
                tick();need(ep.before(c,c.pc,Nop));
                need(ep.poll(c,Image)==Poll::Continue);
            }
            if(hd==7||hd==10||hd==11)continue;
            c.pc=Indirect;tick();need(ep.before(c,Indirect,ex.indirect_word));
            c.pc=Handler;c.ctr=Handler;c.lr=Indirect+4u;c.gpr[3]=hd==12?19u:20u;c.gpr[4]=Context;
            ok=ep.entry(c,Handler);
            if(hd==8||hd==9||hd==12){refuse_disp(!ok);continue;}need(ok);
            need(ep.stage()==7u&&ep.dispatch_saved(c)&&ep.dispatch_visits()==10u&&ep.dispatch_entries()==5u&&
                 ep.dispatch_reads()==2u&&ep.dispatch_polls()==4u&&dev.held_now()&&ctl.issued_tokens()==3u);
            if(trial<388){++held_disp_valid;continue;}
            // Original-free ACK instruction effects. The actual SI
            // controller and witness perform the guest W1C transaction.
            c.mmu.words[Handler+4]=AckCall;c.mmu.words[Handler+8]=Nop;c.mmu.words[Handler+12]=trial>=428?0x4e800421u:Blr;
            c.mmu.words[Save]=Blr;c.mmu.words[Helper]=Nop;c.mmu.words[Helper+4]=Load;
            c.mmu.words[Helper+8]=Nop;c.mmu.words[Helper+12]=Store;c.mmu.words[Helper+16]=Nop;c.mmu.words[Helper+20]=Blr;
            const std::array<AckCallSpan,3> spans{{{Handler,Handler+16},{Save,Save+4},{Helper,Helper+24}}};
            const std::array<AckCallEdge,2> edges{{{Handler,Save},{Handler+4,Helper}}};
            const auto control=ctl.read(C),status=ctl.read(S),buffer=ctl.read(B);
            auto refuse_ack=[&](bool bad,bool cleared=false){
                need(bad&&ctl.issued_tokens()==3u&&cause==(cleared?Other:(Other|SI))&&ctl.read(C)==(cleared?(control&~SiController::TC_INT):control));
                ++held_ack_refused;
            };
            if(ha==1)c.mmu.words[Context+124]^=1u;
            if(ha==2)tick();
            if(ha==3)c.lr^=4u;
            ok=ep.begin_ack(c,spans,edges);
            if(ha>=1&&ha<=3){refuse_ack(!ok);need(dev.stage()==2u);continue;}need(ok);
            need(dev.stage()==3u&&ep.stage()==8u&&ep.completion_ack().token()==3u&&
                 ep.completion_ack().no_response_verified()==!ports[ch].type.has_value());
            if(ha==4){refuse_ack(!ep.begin_ack(c,spans,edges));continue;}
            if(ha==5){refuse_ack(!ep.ack_read(ctl,C,value));continue;}
            auto at_ack=[&](uint32_t owner,uint32_t pc,uint32_t w,bool g=false){c.pc=pc;tick();return ep.ack_before(c,owner,pc,w,g);};
            ok=at_ack(Handler,Handler,CallSave,ha==6);
            if(ha==6){refuse_ack(!ok);continue;}need(ok);
            c.pc=Save;c.lr=Handler+4;
            ok=ep.entry(c,ha==7?Save+4:Save);
            if(ha==7){refuse_ack(!ok);continue;}need(ok);
            need(at_ack(Save,Save,Blr)&&at_ack(Handler,Handler+4,AckCall));
            c.pc=Helper;c.lr=Handler+8;need(ep.entry(c,Helper)&&at_ack(Helper,Helper,Nop));
            c.gpr[3]=Base;need(at_ack(Helper,Helper+4,Load));
            ok=ep.ack_read(ha==8?foreign:ctl,C,value);
            if(ha==8){refuse_ack(!ok);continue;}need(ok);
            c.gpr[4]=value^(ha==9?1u:0u);
            ok=at_ack(Helper,Helper+8,Nop);
            if(ha==9){refuse_ack(!ok);continue;}need(ok);
            if(ha==10)c.gpr[4]&=~SiController::TC_INT;
            need(at_ack(Helper,Helper+12,Store));
            ok=ep.ack_write(ctl,C,c.gpr[4]^(ha==11?2u:0u));
            if(ha==10||ha==11){refuse_ack(!ok);continue;}need(ok&&cause==Other);
            if(ha==12)c.mmu.words[Context+124]^=1u;
            ok=at_ack(Helper,Helper+16,Nop);
            if(ha==12){refuse_ack(!ok,true);continue;}need(ok);
            need(ep.stage()==9u&&ep.ack_saved(c)&&ep.ack_visits()==8u&&ep.completion_ack().reads()==1u&&
                 ep.completion_ack().writes()==1u&&ep.ack_calls().entries()==2u&&ep.ack_calls().returns()==1u&&
                 ctl.issued_tokens()==3u&&ctl.read(C)==(control&~SiController::TC_INT)&&ctl.read(S)==status&&ctl.read(B)==buffer&&
                 cause==Other&&dev.stage()==3u&&sched.completed()==3u);
            if(trial<408){++held_ack_valid;continue;}
            HeldAckHelperExpectation helper_expect{Handler+8u,Nop,2,2,2,0};
            auto refuse_post=[&](bool bad){
                need(bad&&cause==Other&&ctl.issued_tokens()==3u&&dev.stage()==3u&&
                     ctl.read(C)==(control&~SiController::TC_INT));++held_postack_refused;
            };
            if(hp==1)tick();
            if(hp==2)c.mmu.words[Context+124]^=1u;
            if(hp==5)helper_expect.entries=3;
            if(hp==6)helper_expect.visits=0;
            if(hp==7)helper_expect.pc+=4u;
            if(hp==8)helper_expect.word=Blr;
            const auto resume_tick=c.inst_count;
            ok=ep.resume_ack(c,Helper+16u+(hp==3?4u:0u),hp==4?Blr:Nop,helper_expect);
            if(hp>=1&&hp<=6){refuse_post(!ok);continue;}need(ok&&c.inst_count==resume_tick&&ep.stage()==10u);
            if(hp==9){refuse_post(!ep.resume_ack(c,Helper+16u,Nop,helper_expect));continue;}
            if(hp==10){refuse_post(!ep.ack_write(ctl,C,control));continue;}
            ok=at_ack(Helper,Helper+20u,Blr,hp==11);
            if(hp==11){refuse_post(!ok);continue;}need(ok);
            if(hp==12)c.gpr[31]^=1u;
            ok=at_ack(Handler,Handler+8u,Nop);
            if(hp==7||hp==8||hp==12){refuse_post(!ok);continue;}need(ok);
            need(ep.stage()==11u&&ep.helper_saved(c)&&ep.helper_visits()==2u&&
                 ep.ack_calls().entries()==2u&&ep.ack_calls().returns()==2u&&ep.ack_calls().msr_writes()==0u&&
                 ctl.issued_tokens()==3u&&cause==Other&&ctl.read(C)==(control&~SiController::TC_INT)&&dev.stage()==3u);
            if(trial<428){++held_postack_valid;continue;}
            {
                constexpr uint32_t Target=0x8003f000u,Site=Handler+12u,IndirectWord=0x4e800421u;
                constexpr uint32_t Leaf=Target+0x100u,Stack=0x80035000u;
                const std::array<uint32_t,6> words{0x9421ffc0u,0x7c0802a6u,0x90010044u,0x39610040u,branch(Target+16u,Leaf)|1u,Nop};
                const std::array<uint32_t,3> leaf{0x93cbfff8u,0x93ebfffcu,Blr};
                const std::array<uint32_t,2> sites{Site,Site+4u};
                for(unsigned i=0;i<words.size();++i)c.mmu.words[Target+4u*i]=words[i];
                HeldAckCallbackExpectation expectation{Site,IndirectWord,hc==5?2u:1u,hc==4?11u:6u};
                auto refuse_callback=[&](bool bad){
                    need(bad&&cause==Other&&ctl.issued_tokens()==3u&&dev.stage()==3u&&
                         ctl.read(C)==(control&~SiController::TC_INT));++held_callback_refused;
                };
                if(hc==1)tick();
                if(hc==2)c.mmu.words[Context+124]^=1u;
                const auto joined_tick=c.inst_count;
                ok=ep.resume_helper(c,Handler+8u+(hc==3?4u:0u),Nop,expectation);
                if(hc>=1&&hc<=4){refuse_callback(!ok);continue;}need(ok&&c.inst_count==joined_tick&&ep.stage()==12u);
                if(hc==6){refuse_callback(!ep.resume_helper(c,Handler+8u,Nop,expectation));continue;}
                c.ctr=Target+(hc==7?4u:0u);c.gpr[3]=hc==8?4u:ch;c.pc=Site;
                if(hc==9)c.mmu.words[Target+4u]^=1u;
                if(hc==10)c.mmu.words[Site]^=1u;
                if(hc==11)tick();
                tick();
                ok=ep.callback_frontier(c,hc==12?Helper:Handler,Site,IndirectWord,Target,words,sites);
                if(hc>=5){refuse_callback(!ok);continue;}need(ok);
                need(ep.stage()==13u&&ep.callback_saved(c)&&ep.callback_visits()==1u&&ep.helper_visits()==2u&&
                     ep.ack_calls().entries()==2u&&ep.ack_calls().returns()==2u&&ep.completion_ack().writes()==1u&&
                     c.pc==Site&&c.ctr==Target&&cause==Other&&ctl.issued_tokens()==3u&&dev.stage()==3u);
                if(trial<448){++held_callback_valid;continue;}
                for(unsigned i=0;i<leaf.size();++i)c.mmu.words[Leaf+4u*i]=leaf[i];
                c.gpr[1]=Stack;
                for(uint32_t a=Stack-0x400u;a<Stack+0x100u;a+=4u)c.mmu.words[a]=a^0xdeadbeefu;
                CallbackPrefixWitness<6,3> witness(Target,Leaf,words,leaf),foreign_witness(Target,Leaf,words,leaf);
                auto refuse_prefix=[&](bool bad){
                    need(bad&&cause==Other&&ctl.issued_tokens()==3u&&dev.stage()==3u&&
                        ctl.read(C)==(control&~SiController::TC_INT));++held_prefix_refused;
                };
                if(hprefix==1)tick();
                if(hprefix==2)c.mmu.words[Leaf]^=1u;
                ok=ep.begin_prefix(c,witness,Site+(hprefix==3?4u:0u),IndirectWord);
                if(hprefix>=1&&hprefix<=3){refuse_prefix(!ok);continue;}need(ok&&ep.stage()==14u);
                if(hprefix==4){refuse_prefix(!ep.begin_prefix(c,witness,Site,IndirectWord));continue;}
                c.pc=Target;c.lr=Site+4u;
                if(hprefix==5)c.mmu.words[Context+124]^=1u;
                if(hprefix==6){refuse_prefix(!ep.prefix_poll(c,foreign_witness));continue;}
                if(hprefix==7)tick();
                if(hprefix!=8){
                    ok=ep.prefix_poll(c,witness);
                    if(hprefix==5||hprefix==7){refuse_prefix(!ok);continue;}need(ok);
                }
                if(hprefix==9){refuse_prefix(!ep.prefix_poll(c,witness));continue;}
                tick();ok=ep.prefix_entry(c,witness,Target);
                if(hprefix==8){refuse_prefix(!ok);continue;}need(ok);
                auto prefix_at=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return ep.prefix_before(c,witness,pc,w,hprefix==10);};
                ok=prefix_at(Target,words[0]);
                if(hprefix==10){refuse_prefix(!ok);continue;}need(ok);
                c.gpr[1]=Stack-64u;c.mmu.words[Stack-64u]=Stack;
                if(hprefix==11)c.mmu.words[Stack-64u]^=1u;
                ok=prefix_at(Target+4u,words[1]);
                if(hprefix==11){refuse_prefix(!ok);continue;}need(ok);c.gpr[0]=c.lr;
                need(prefix_at(Target+8u,words[2]));c.mmu.words[Stack+4u]=c.gpr[0];
                need(prefix_at(Target+12u,words[3]));c.gpr[11]=Stack;
                need(prefix_at(Target+16u,words[4]));c.pc=Leaf;c.lr=Target+20u;need(ep.prefix_entry(c,witness,Leaf));
                need(prefix_at(Leaf,leaf[0]));c.mmu.words[Stack-8u]=c.gpr[30];
                need(prefix_at(Leaf+4u,leaf[1]));c.mmu.words[Stack-4u]=c.gpr[31];
                need(prefix_at(Leaf+8u,Blr));
                if(hprefix==12)c.mmu.words[Stack-8u]^=1u;
                ok=prefix_at(Target+20u,Nop);
                if(hprefix==12){refuse_prefix(!ok);continue;}need(ok);
                need(ep.stage()==15u&&ep.prefix_saved(c,witness)&&!ep.prefix_saved(c,foreign_witness)&&
                     witness.writes()==4u&&witness.visits()==9u&&ep.completion_ack().writes()==1u&&
                     cause==Other&&ctl.issued_tokens()==3u&&dev.stage()==3u);
                c.mmu.words[Context+124]^=1u;need(!ep.prefix_saved(c,witness));
                c.mmu.words[Context+124]^=1u;need(ep.prefix_saved(c,witness));
                ++held_prefix_valid;continue;
            }
        }
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
        if(trial>=228){c.gpr[20]=ch;c.gpr[1]=0x80034000u;}
        if(trial>=248){c.gpr[13]=0x80035000u;c.gpr[21]=Context;}
        const auto original_handler_gp=c.gpr;
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
        if(trial>=208)c.gpr[20]=ch;
        const auto original_callback_gp=c.gpr;
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
        if(trial<188){++suffix_valid;continue;}
        // Two-register independent restore fixture. The real owner route
        // uses the privately authenticated six-register compiler routine.
        constexpr uint32_t RestoreCall=Return+12u,Caller=Handler+16u;
        constexpr std::array<uint32_t,3> restore_words{0x83cbfff8u,0x83ebfffcu,Blr};
        constexpr std::array<uint32_t,4> tail{0x80010044u,0x7c0803a6u,0x38210040u,Blr};
        const NativeReturnExpectation<2> return_ex{RestoreCall,RestoreRoot,Caller,restore_words,tail,Nop};
        put(RestoreRoot,restore_words);put(RestoreCall+4u,tail);c.mmu.words[Caller]=Nop;
        NativeReturnWitness<2> ret(return_ex),foreign_ret(return_ex);
        auto refuse_return=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++return_refused;
        };
        if(return_fault==4)tick();
        if(return_fault==5)c.mmu.words[RestoreRoot]^=1u;
        if(return_fault==6)c.mmu.words[Context+124]^=1u;
        // Simulate independently authored callback volatile changes;
        // the original save slots must be read, not overwritten.
        c.gpr[30]^=0x55u;c.gpr[31]^=0xaau;c.gpr[11]=Stack;
        ok=route.begin_callback_return(c,return_fault==1?foreign_suffix:suffix,ret,
                        RestoreCall+(return_fault==2?4u:0u),return_fault==3?Nop:suffix_rows[3].word);
        if(return_fault>=1&&return_fault<=6){refuse_return(!ok,35);continue;}need(ok);
        c.pc=RestoreRoot;c.lr=RestoreCall+4u;
        ok=route.callback_return_entry(c,ret,return_fault==7?RestoreRoot+4u:RestoreRoot);
        if(return_fault==7){refuse_return(!ok,36);continue;}need(ok);
        auto at_return=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.callback_return_before(c,ret,pc,w);};
        if(return_fault==8)c.mmu.words[Stack-8u]^=1u;
        ok=at_return(RestoreRoot,restore_words[0]);
        if(return_fault==8){refuse_return(!ok,37);continue;}need(ok);
        c.gpr[30]=c.mmu.words[Stack-8u];
        need(at_return(RestoreRoot+4u,restore_words[1]));c.gpr[31]=c.mmu.words[Stack-4u];
        need(at_return(RestoreRoot+8u,Blr));
        need(at_return(RestoreCall+4u,tail[0]));c.gpr[0]=c.mmu.words[Stack+4u];
        need(at_return(RestoreCall+8u,tail[1]));c.lr=c.gpr[0];
        need(at_return(RestoreCall+12u,tail[2]));c.gpr[1]+=64u;
        need(at_return(RestoreCall+16u,tail[3]));c.pc=Caller;
        if(return_fault==9){tick();refuse_return(!route.callback_return_poll(c,ret),38);continue;}
        if(return_fault!=10)need(route.callback_return_poll(c,ret));
        tick();ok=route.callback_return_resume(c,ret,Caller,Nop);
        if(return_fault==10){refuse_return(!ok,39);continue;}need(ok);
        if(return_fault==11)c.gpr[30]^=1u;
        if(return_fault==12){tick();refuse_return(!route.callback_return_before(c,foreign_ret,Caller,Nop),37);continue;}
        ok=at_return(Caller,Nop);
        if(return_fault==11){refuse_return(!ok,37);continue;}need(ok);
        need(route.stage()==22u&&ret.stage()==5u&&ret.visits()==8u&&c.gpr[1]==original_callback_gp[1]&&
             c.gpr[30]==original_callback_gp[30]&&c.gpr[31]==original_callback_gp[31]&&
             route.completion_ack().postack_held()&&ctl.issued_tokens()==3u&&cause==Other);
        if(trial<208){++return_valid;continue;}
        constexpr uint32_t Table=0x80033000u,StatusLoad=0x80830038u,StatusStore=0x90830038u;
        constexpr uint32_t Indexed=(31u<<26)|(5u<<21)|(3u<<16)|(4u<<11)|(23u<<1);
        constexpr uint32_t Compare=(10u<<26)|(5u<<16)|7u,Branch=(16u<<26)|(12u<<21)|(2u<<16)|12u;
        const HandlerIndexBranchExpectation ix{Caller,Indexed,Compare,Branch,Caller+64u,
            {Table,Table+4u,Table+8u,Table+12u},20u};
        std::array<HandlerSuffixLabel,16> rows_handler{};
        for(unsigned i=0;i<14;++i)rows_handler[i]={Caller+4u*i,Nop,0,0};
        rows_handler[1].word=StatusLoad;rows_handler[2].word=StatusStore;
        rows_handler[11].word=Indexed;rows_handler[12].word=Compare;rows_handler[13].word=Branch;
        rows_handler[14]={Caller+56u,branch(Caller+56u,Caller+64u),0,0};
        rows_handler[15]={Caller+64u,branch(Caller+64u,RestoreRoot)|1u,12u,1u};
        for(const auto& row:rows_handler)c.mmu.words[row.pc]=row.word;
        for(unsigned i=0;i<4;++i)c.mmu.words[Table+4*i]=i==ch?7u:9u;
        auto refuse_handler=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++handler_refused;
        };
        if(handler_fault==4)tick();
        if(handler_fault==5)c.mmu.words[Caller+44u]^=1u;
        if(handler_fault==6)c.mmu.words[Context+124]^=1u;
        ok=route.begin_handler_suffix(c,handler_fault==1?foreign_ret:ret,
            Caller+(handler_fault==2?4u:0u),handler_fault==3?Blr:Nop,
            rows_handler,ix,Caller+4u,Caller+8u);
        if(handler_fault>=1&&handler_fault<=6){refuse_handler(!ok,40);continue;}need(ok);
        auto at_handler=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.handler_before(c,pc,w);};
        c.gpr[3]=Base;
        need(at_handler(Caller+4u,StatusLoad));
        if(handler_fault==7){refuse_handler(!route.handler_read(C,value),42);continue;}
        if(handler_fault!=8){need(route.handler_read(S,value));c.gpr[4]=value^(handler_fault==9?1u:0u);}
        ok=at_handler(Caller+8u,StatusStore);
        if(handler_fault==8||handler_fault==9){refuse_handler(!ok,41);continue;}need(ok);
        if(handler_fault==10){refuse_handler(!route.handler_write(S,value^1u),43);continue;}
        if(handler_fault!=11)need(route.handler_write(S,value));
        ok=at_handler(Caller+12u,Nop);
        if(handler_fault==11){refuse_handler(!ok,41);continue;}need(ok);
        for(unsigned i=4;i<11;++i)need(at_handler(Caller+4u*i,Nop));
        c.gpr[3]=Table;c.gpr[4]=4u*ch;need(at_handler(Caller+44u,Indexed));c.gpr[5]=7;
        need(at_handler(Caller+48u,Compare));c.cr[0]={false,false,true,false};
        if(handler_fault==12)c.cr[0].eq=false;
        ok=at_handler(Caller+52u,Branch);
        if(handler_fault==12){refuse_handler(!ok,41);continue;}need(ok);
        need(at_handler(Caller+64u,rows_handler.back().word));
        need(route.stage()==24u&&route.handler_ordinal()==12u&&route.handler_taken()&&route.handler_visits()==15u&&
             route.handler_reads()==1u&&route.handler_writes()==1u&&route.completion_ack().postack_held()&&
             ctl.issued_tokens()==3u&&cause==Other);
        if(trial<228){++handler_valid;continue;}
        constexpr uint32_t HandlerCall=Caller+64u,DispatcherResume=D+20u;
        // A separate synthetic handler restore, independent of callback ABI.
        // The original focused geometry uses fifteen restores.
        constexpr std::array<uint32_t,3> handler_restore{0x83cbfff8u,0x83ebfffcu,Blr};
        constexpr std::array<uint32_t,4> handler_tail{0x80010044u,0x7c0803a6u,0x38210040u,Blr};
        constexpr uint32_t Enable=0x80036000u,Reschedule=Enable+0x100u,Dis=Enable+0x200u,Rest=Enable+0x300u,Loader=Enable+0x400u;
        const uint32_t dispatcher_word=trial>=248?branch(DispatcherResume,Enable)|1u:Nop;
        const NativeReturnExpectation<2> he{HandlerCall,RestoreRoot,DispatcherResume,handler_restore,handler_tail,dispatcher_word};
        put(RestoreRoot,handler_restore);put(HandlerCall+4u,handler_tail);c.mmu.words[DispatcherResume]=dispatcher_word;
        const uint32_t old_sp=original_handler_gp[1];
        // This fixture previously used a small non-address r1 at handler
        // entry. A valid synthetic handler ABI is established before entry.
        c.gpr[1]=old_sp-64u;c.gpr[11]=old_sp;
        c.mmu.words[old_sp-8u]=original_handler_gp[30];
        c.mmu.words[old_sp-4u]=original_handler_gp[31];
        c.mmu.words[old_sp+4u]=DispatcherResume;
        c.gpr[30]^=0x123u;c.gpr[31]^=0x456u;
        NativeReturnWitness<2> hr(he),foreign_hr(he);
        auto refuse_hr=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++handler_return_refused;
        };
        if(hr_fault==4)tick();
        if(hr_fault==5)c.mmu.words[RestoreRoot]^=1u;
        if(hr_fault==6)c.mmu.words[Context+124]^=1u;
        // For a mismatched witness, use an otherwise valid expectation
        // with a different caller word.
        auto wrong=he;wrong.caller_word=Blr;NativeReturnWitness<2> wrong_hr(wrong);
        ok=route.begin_handler_return(c,hr_fault==1?wrong_hr:hr,HandlerCall+(hr_fault==2?4u:0u),
                                      hr_fault==3?Nop:rows_handler.back().word);
        if(hr_fault>=1&&hr_fault<=6){refuse_hr(!ok,44);continue;}need(ok);
        c.pc=RestoreRoot;c.lr=HandlerCall+4u;
        ok=route.handler_return_entry(c,hr,hr_fault==7?RestoreRoot+4u:RestoreRoot);
        if(hr_fault==7){refuse_hr(!ok,45);continue;}need(ok);
        auto at_hr=[&](uint32_t pc,uint32_t w){c.pc=pc;tick();return route.handler_return_before(c,hr,pc,w);};
        if(hr_fault==8)c.mmu.words[old_sp-8u]^=1u;
        ok=at_hr(RestoreRoot,handler_restore[0]);
        if(hr_fault==8){refuse_hr(!ok,46);continue;}need(ok);
        c.gpr[30]=c.mmu.words[old_sp-8u];need(at_hr(RestoreRoot+4u,handler_restore[1]));
        c.gpr[31]=c.mmu.words[old_sp-4u];need(at_hr(RestoreRoot+8u,Blr));
        need(at_hr(HandlerCall+4u,handler_tail[0]));c.gpr[0]=c.mmu.words[old_sp+4u];
        need(at_hr(HandlerCall+8u,handler_tail[1]));c.lr=c.gpr[0];
        need(at_hr(HandlerCall+12u,handler_tail[2]));c.gpr[1]+=64u;
        need(at_hr(HandlerCall+16u,Blr));c.pc=DispatcherResume;
        if(hr_fault==9){tick();refuse_hr(!route.handler_return_poll(c,hr),47);continue;}
        if(hr_fault!=10)need(route.handler_return_poll(c,hr));
        tick();ok=route.handler_return_resume(c,hr,DispatcherResume,dispatcher_word);
        if(hr_fault==10){refuse_hr(!ok,48);continue;}need(ok);
        if(hr_fault==11)c.gpr[31]^=1u;
        if(hr_fault==12){tick();refuse_hr(!route.handler_return_before(c,foreign_hr,DispatcherResume,Nop),46);continue;}
        ok=at_hr(DispatcherResume,dispatcher_word);
        if(hr_fault==11){refuse_hr(!ok,46);continue;}need(ok);
        need(route.stage()==26u&&hr.stage()==5u&&hr.visits()==8u&&c.gpr[1]==old_sp&&
             route.completion_ack().postack_held()&&ctl.issued_tokens()==3u&&cause==Other);
        if(trial<248){++handler_return_valid;continue;}
        // Synthetic effects only. Every admitted label and device tick
        // uses the same fresh-frame epilogue join as the original fixture.
        const uint32_t counter=c.gpr[13]+4u,hint=c.gpr[13]+8u;
        c.mmu.words[counter]=2;c.mmu.words[hint]=0;
        for(unsigned i=0;i<8;++i)c.mmu.words[Context+0x1a4u+4*i]=0;
        c.mmu.words[Context+0x1a0u]=0;
        c.mmu.words[Enable]=branch(Enable,Dis)|1u;c.mmu.words[Enable+4u]=branch(Enable+4u,Rest)|1u;
        c.mmu.words[Enable+8u]=Blr;c.mmu.words[Dis]=Blr;c.mmu.words[Rest]=Blr;c.mmu.words[Reschedule]=Blr;
        c.mmu.words[DispatcherResume+4u]=branch(DispatcherResume+4u,Reschedule)|1u;
        c.mmu.words[DispatcherResume+8u]=Nop;
        c.mmu.words[DispatcherResume+12u]=branch(DispatcherResume+12u,Loader)|1u;
        c.mmu.words[Loader]=Rfi;
        LiveEpilogueWitness ep({DispatcherResume,Enable,Reschedule,Dis,Rest,Loader,Loader+4u,Context,4,8,21,255});
        auto reject_ep=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++ep_refused;
        };
        if(ep_fault==4)tick();
        if(ep_fault==5)c.mmu.words[Context+124]^=1u;
        if(ep_fault==6)c.gpr[21]^=4u;
        ok=route.begin_epilogue(c,ep_fault==1?foreign_hr:hr,ep,DispatcherResume+(ep_fault==2?4u:0u),
                                ep_fault==3?Nop:dispatcher_word);
        if(ep_fault>=1&&ep_fault<=6){reject_ep(!ok,49);continue;}need(ok);
        auto enter_ep=[&](uint32_t root,uint32_t retpc){c.pc=root;c.lr=retpc;return route.epilogue_entry(c,root);};
        auto at_ep=[&](uint32_t pc){c.pc=pc;tick();return route.epilogue_before(c,pc,c.mmu.words.at(pc));};
        ok=enter_ep(ep_fault==7?Dis:Enable,DispatcherResume+4u);
        if(ep_fault==7){reject_ep(!ok,51);continue;}need(ok);
        if(ep_fault==8){reject_ep(!at_ep(Enable+4u),50);continue;}
        need(at_ep(Enable)&&enter_ep(Dis,Enable+4u)&&at_ep(Dis));
        need(at_ep(Enable+4u)&&enter_ep(Rest,Enable+8u)&&at_ep(Rest));
        c.lr=DispatcherResume+4u;c.gpr[3]=2;c.mmu.words[counter]=1;
        need(at_ep(Enable+8u)&&at_ep(DispatcherResume+4u)&&enter_ep(Reschedule,DispatcherResume+8u)&&at_ep(Reschedule));
        need(at_ep(DispatcherResume+8u));c.gpr[3]=Context;
        need(at_ep(DispatcherResume+12u)&&enter_ep(Loader,DispatcherResume+16u));
        c.gpr=gp;c.lr=lr;c.ctr=ctr;c.xer=xer;c.cr.fill({});c.srr0=H;c.srr1=0x8032u;
        if(ep_fault==9)c.gpr[31]^=1u;
        ok=at_ep(Loader);
        if(ep_fault==9){reject_ep(!ok,50);continue;}need(ok);
        c.pc=H;c.msr=c.srr1;
        if(ep_fault==10){if(ch&1u)c.gqr[0]^=1u;else c.gpr[31]^=1u;}
        if(ep_fault==11)tick();
        ok=route.epilogue_poll(c);
        if(ep_fault==10||ep_fault==11){reject_ep(!ok,52);continue;}need(ok);
        if(ep_fault==12)c.gqr[0]^=1u;
        ok=route.epilogue_poll(c);
        if(ep_fault==12){reject_ep(!ok,52);continue;}need(ok);
        need(route.stage()==28u&&ep.stage()==4u&&route.completion_ack().postack_held()&&ctl.issued_tokens()==3u&&cause==Other);
        if(trial<268){++ep_valid;continue;}
        auto reject_resume=[&](bool rejected,unsigned reason){
            need(rejected&&route.failure()==reason&&ctl.issued_tokens()==3u&&cause==Other&&dev.stage()==3u);++rd_refused;
        };
        const uint32_t resume_word=c.mmu.words.at(H);
        if(rd_fault==1){reject_resume(!route.epilogue_resume_dispatch(c,H),53);continue;}
        tick();
        if(rd_fault==2)tick();
        if(rd_fault==3)c.pc=H+4u;
        if(rd_fault==4)c.srr0=H+4u;
        if(rd_fault==5)mask=0;
        ok=route.epilogue_resume_dispatch(c,H);
        if(rd_fault>=2&&rd_fault<=5){reject_resume(!ok,53);continue;}
        need(ok);
        if(rd_fault==6){reject_resume(!route.epilogue_resume_dispatch(c,H),53);continue;}
        if(rd_fault!=7)tick();
        if(rd_fault==8)tick();
        if(rd_fault==9)c.gpr[31]^=1u;
        if(rd_fault==10)c.gqr[0]^=1u;
        if(rd_fault==11)c.mmu.words[H]^=1u;
        ok=route.epilogue_resume_label(c,rd_fault==12?H+4u:H,resume_word);
        if(rd_fault>=7){reject_resume(!ok,54);continue;}need(ok);
        need(route.stage()==30u&&ep.stage()==5u&&ctl.issued_tokens()==3u&&cause==Other);
        ++rd_valid;
    }
    need(valid==8&&refused==16&&dispatch_valid==8&&dispatch_refused==8&&ack_valid==8&&ack_refused==13&&
         resume_valid==8&&resume_refused==6&&frontier_valid==8&&frontier_refused==5&&callback_valid==8&&callback_refused==12&&time_valid==8&&time_refused==12&&post_valid==8&&post_refused==12&&wireless_valid==8&&wireless_refused==12&&suffix_valid==8&&suffix_refused==12&&return_valid==8&&return_refused==12&&handler_valid==8&&handler_refused==12&&handler_return_valid==8&&handler_return_refused==12&&ep_valid==8&&ep_refused==12&&rd_valid==8&&rd_refused==12&&held_valid==8&&held_refused==12&&held_return_valid==8&&held_return_refused==12&&held_ep_valid==8&&held_ep_refused==12&&held_vec_valid==8&&held_vec_refused==12&&held_disp_valid==8&&held_disp_refused==12&&held_ack_valid==8&&held_ack_refused==12&&held_postack_valid==8&&held_postack_refused==12&&held_callback_valid==8&&held_callback_refused==12&&held_prefix_valid==8&&held_prefix_refused==12);
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
    std::cout<<"V1117_THIRD_ACK_RETURN_JOIN valid=8 refused=12 dispatch_tick=1 original_abi=1 actual_device=1 original_execution=0\n";
    std::cout<<"V1122_THIRD_ACK_HANDLER_JOIN valid=8 refused=12 same_tick=1 status_read=1 status_w1c=1 original_execution=0\n";
    std::cout<<"V1126_THIRD_ACK_HANDLER_RETURN_JOIN valid=8 refused=12 dispatch_tick=1 original_abi=1 original_execution=0\n";
    std::cout<<"V1130_THIRD_ACK_RFI_JOIN valid=8 refused=12 fresh_context=1 two_polls=1 original_execution=0\n";
    std::cout<<"V1136_THIRD_ACK_RESUME_JOIN valid=8 refused=12 dispatch_ticks=2 resume_instruction_executed=0 original_execution=0\n";
    std::cout<<"V1138_HELD_HANDLER_SUFFIX valid=8 refused=12 actual_w1c=1 token_held=1 original_execution=0\n";
    std::cout<<"V1144_HELD_HANDLER_RETURN valid=8 refused=12 abi=15 dispatch_tick=1 token_held=1 original_execution=0\n";
    std::cout<<"V1149_HELD_PENDING_EPILOGUE valid=8 refused=12 native_rfi_model=1 same_token=1 third_vector_entry=1 original_execution=0\n";
    std::cout<<"V1150_HELD_VECTOR_JOIN valid=8 refused=12 vector_visits=2 trampoline_visits=2 saved_fields=38 token_held=1 original_execution=0\n";
    std::cout<<"V1157_HELD_DISPATCH_JOIN valid=8 refused=12 pi_reads=2 entries=5 token_held=1 original_execution=0\n";
    std::cout<<"V1164_HELD_THIRD_ACK_JOIN valid=8 refused=12 fresh_ack=1 actual_w1c=1 retired_transfer=1 pi_cleared=1 original_execution=0\n";
    std::cout<<"V1172_HELD_ACK_HELPER_RETURN valid=8 refused=12 same_tick=1 helper_return=1 pi_cleared=1 original_execution=0\n";
    std::cout<<"V1179_ACK_CALLBACK_FRONTIER valid=8 refused=12 same_tick=1 target_identity=1 call_executed=0 pi_cleared=1 original_execution=0\n";
    std::cout<<"V1183_ACK_CALLBACK_PREFIX valid=8 refused=12 indirect_dispatch=1 stack_proof=1 save_return=1 original_execution=0\n";
}
