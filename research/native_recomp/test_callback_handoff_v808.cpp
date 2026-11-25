#include "wii_callback_dispatch_device_v808.h"
#include "wii_callback_prefix_v800.h"
#include "wii_callback_identity_v796.h"
#include "wii_si_handler_return_v725.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
#include <stdexcept>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,C=0x80006000u,S=0x80008000u,Stack=0x80020000u;
constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,Bctrl=0x4e800421u,Call=0x48000101u;
constexpr uint32_t SaveCall=C+16u,Resume=C+20u,Branch=0x48000001u|((S-SaveCall)&0x03fffffcu);
constexpr std::array<uint32_t,6> prefix{0x9421ffc0u,0x7c0802a6u,0x90010044u,0x39610040u,Branch,Nop};
constexpr std::array<uint32_t,3> leaf{0x93cbfff8u,0x93ebfffcu,Blr};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.contains(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=R,msr=0x32u,srr0=0x80007000u,srr1=0x8032u,ctr=C,xer=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b){std::cerr<<"V808_ASSERT line="<<l.line()<<'\n';throw std::runtime_error("handoff");}
}
int main(){
    constexpr unsigned Control=SiController::Control,Status=SiController::Status,Buffer=SiController::Buffer;
    constexpr uint32_t Base=0xcd006400u,Other=0x100u,SI=SiController::PI_SI;
    unsigned pass=0,refused=0;
    for(unsigned t=0;t<13;++t){
        Cpu c;auto& tick=c.inst_count;
        for(unsigned i=0;i<32;++i)c.gpr[i]=0x1234567u*(i+1u);
        c.gpr[1]=Stack;c.mmu.words={{H,0x90030000u},{H+4,Call},{H+8,Call},{H+12,Bctrl},{H+16,Blr},{R,Nop}};
        for(unsigned i=0;i<prefix.size();++i)c.mmu.words[C+4*i]=prefix[i];
        for(unsigned i=0;i<leaf.size();++i)c.mmu.words[S+4*i]=leaf[i];
        for(uint32_t a=Stack-0x400u;a<Stack+0x100u;a+=4)c.mmu.words[a]=a^0xdeadbeefu;
        std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);
        using Port=SiTypeScheduler::Port;
        const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
        SiTypeScheduler scheduler(ctl,ports,8);
        ctl.write(Control,0xc0010301u);scheduler.advance(1);scheduler.advance(9);
        SiCompletionAckTrace ack;SiHandlerReturnWitness handler({H,H+20,H+4,R,Nop});
        need(handler.capture(c)&&ack.arm(ctl,cause,mask,tick,H,H+20));
        ++tick;need(ack.before(H,c.mmu.read32(H)));ack.write(ctl,Control,0xe0010300u);
        ++tick;need(ack.before(H+4,Call)&&ack.resume_after_ack(H+4,Call));
        c.pc=c.lr=H+4;
        need(handler.start(c,H+4,true)&&handler.before_authenticated(c,H+4,Call,true,4));
        PostAckTransferDevice device;
        need(device.begin(ctl,cause,mask,ack,tick,1,true,ports[1].type,8));
        const auto transfer_start=tick;
        using A=PostAckTransferDevice::Access;
        auto transfer=[&](A a=A::None,uint32_t addr=0){scheduler.advance(++tick);return device.before(tick,a,addr);};
        uint32_t value=0;
        need(transfer(A::Read,Base+Control)&&device.read(ctl,Control,value));
        need(transfer(A::Write,Base+Buffer)&&device.write(ctl,Buffer,0x00abcdefu));
        need(transfer(A::Write,Base+Status)&&device.write(ctl,Status,0x08000000u));
        need(transfer(A::Write,Base+Control)&&device.write(ctl,Control,0xc0010303u));
        if(t==1){ // in-flight cannot be admitted as a completed dispatch
            need(transfer()&&device.finish(tick,1)&&device.follow_stage()==2);
            ++tick;need(!observe_completed_callback_dispatch(device,tick)&&!device.failure());
            ++refused;continue;
        }
        for(unsigned i=0;i<9;++i)need(transfer());
        need(device.finish(tick,1)&&device.follow_stage()==3&&!device.pending()&&scheduler.completed()==2);
        c.pc=c.lr=H+8;
        need(handler.transfer_returned(c,H+8,unsigned(tick-transfer_start-1),device.held_now()));
        if(t==2){need(!handler.before_authenticated_indirect(c,H+8,Call,true,6)&&handler.failure()==8);++refused;continue;}
        need(handler.before_authenticated(c,H+8,Call,true,5));
        for(unsigned i=0;i<34;++i){scheduler.advance(++tick);need(device.after_return_at(tick));}
        c.pc=c.lr=H+12;
        need(handler.alarm_returned(c,H+12,33,device.held_now())&&handler.completed_calls()==24);
        if(t==3){need(!handler.before_authenticated_indirect(c,H+12,Bctrl,true,7)&&handler.failure()==8);++refused;continue;}
        if(t==4){need(!handler.before_authenticated(c,H+12,Bctrl,true,6)&&handler.failure()==8);++refused;continue;}
        if(t==5){need(!handler.before_authenticated_indirect(c,H+12,Bctrl,false,6)&&handler.failure()==3);++refused;continue;}
        need(handler.before_authenticated_indirect(c,H+12,Bctrl,device.held_now(),t==12?11u:6u));
        const auto ident=classify_callback_identity(c,H+12,Bctrl,6,2,C,prefix,std::array<uint32_t,2>{H+12,H+16});
        CallbackPrefixWitness<6,3> route(C,S,prefix,leaf);
        need(route.start_dispatch(c,H+12,Bctrl,ident==2,device.held_now()));
        c.pc=C;c.lr=H+16;
        need(route.dispatch_poll(c,device.held_now()));
        if(t==6)mask=0;
        if(t==7)ctl.write(Control,SiController::TC_INT);
        if(t==8)ctl.write(Buffer,0);
        if(t==9)++tick;
        ++tick;
        if(t==10){const uint64_t fake=tick;need(!observe_completed_callback_dispatch(device,fake)&&device.failure()==7);++refused;continue;}
        if(t>=6&&t<=9){need(!observe_completed_callback_dispatch(device,tick));++refused;continue;}
        const auto before=ctl.read(Control);
        const auto token=ctl.issued_tokens(),completed=scheduler.completed();
        need(observe_completed_callback_dispatch(device,tick)&&route.entry(c,C,device.held_now()));
        if(t==11){need(!observe_completed_callback_dispatch(device,tick)&&device.failure()==7);++refused;continue;}
        auto step=[&](uint32_t pc,uint32_t w){
            scheduler.advance(++tick);need(device.after_return_at(tick));
            return route.before(c,pc,w,device.held_now());
        };
        need(step(C,prefix[0]));c.mmu.words[Stack-64u]=Stack;c.gpr[1]=Stack-64u;
        need(step(C+4,prefix[1]));c.gpr[0]=c.lr;
        need(step(C+8,prefix[2]));c.mmu.words[Stack+4u]=c.gpr[0];
        need(step(C+12,prefix[3]));c.gpr[11]=Stack;
        need(step(SaveCall,Branch));c.lr=Resume;c.pc=S;need(route.entry(c,S,device.held_now()));
        need(step(S,leaf[0]));c.mmu.words[Stack-8u]=c.gpr[30];
        need(step(S+4,leaf[1]));c.mmu.words[Stack-4u]=c.gpr[31];
        need(step(S+8,Blr));c.pc=Resume;
        need(step(Resume,Nop)&&route.stage()==6&&route.writes()==4&&route.visits()==9);
        need(ctl.read(Control)==before&&ctl.issued_tokens()==token&&scheduler.completed()==completed&&device.held_now());
        ++pass;
    }
    need(pass==2&&refused==11);
    std::cout<<"V808_CALLBACK_HANDOFF synthetic=1 valid=2 refused=11 real_si=1 dispatcher_tick=1 original_execution=0\n";
}
