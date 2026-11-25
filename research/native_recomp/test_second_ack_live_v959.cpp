#include "wii_second_ack_live_v958.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
#include <source_location>
#include <string_view>
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t H=0x80004000u,Save=H+0x100u,Completion=H+0x200u,Resume=H+0x1000u,Other=0x100u,Base=0xcd006400u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
constexpr uint32_t Load=0x80830034u,Store=0x90830034u,Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t bl(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words{{H,bl(H,Save)},{H+4,bl(H+4,Completion)},{Save,Blr},{Completion,Load},{Completion+4,Store},{Completion+8,Nop}};
    uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint64_t inst_count=100;
    uint32_t pc=Resume,lr=H+0x2000u,ctr=17,xer=0x80000000u,msr=0x8032u,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;
};
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b){std::cerr<<"V959_ASSERT line="<<loc.line()<<std::endl;std::_Exit(125);}
}
int main(int argc,char** argv){
    need(argc==2);const std::string_view mode=argv[1];
    if(mode=="default"){need(!v958::enabled()&&!v958::active());std::cout<<"V959_DEFAULT inactive=1\n";return 0;}
    need(v958::enabled()&&!v958::active());
    std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);
    using Port=SiTypeScheduler::Port;
    const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
    SiTypeScheduler scheduler(ctl,ports,8);
    ctl.write(C,0xc0010301u);scheduler.advance(1);scheduler.advance(9);
    Cpu c;auto& tick=c.inst_count;SiCompletionAckTrace first;PostAckTransferDevice old;ExternalReturnWitness frame;
    need(first.arm(ctl,cause,mask,tick,H,H+16));++tick;need(first.before(H,0x90030000u));
    first.write(ctl,C,0xe0010300u);++tick;need(first.before(H+4,Nop)&&first.resume_after_ack(H+4,Nop));
    need(old.begin(ctl,cause,mask,first,tick,1,true,ports[1].type,8));
    auto step=[&](Access a=Access::None,uint32_t addr=0){scheduler.advance(++tick);return old.before(tick,a,addr);};
    uint32_t result=0;
    need(step(Access::Read,Base+C)&&old.read(ctl,C,result));
    need(step(Access::Write,Base+B)&&old.write(ctl,B,0x00abcdefu));
    need(step(Access::Write,Base+S)&&old.write(ctl,S,0x08000000u));
    need(step(Access::Write,Base+C)&&old.write(ctl,C,0xc0010303u));
    for(unsigned i=0;i<9;++i)need(step());
    need(old.finish(tick,1)&&old.held_now());
    for(unsigned i=0;i<32;++i)c.gpr[i]=i*17u;
    c.gpr[1]=0x8000b000u;c.gpr[3]=Base;
    need(frame.capture(c,cause.load(),mask.load()));
    for(unsigned i=0;i<32;++i)c.mmu.words[v958::context+4*i]=c.gpr[i];
    c.mmu.words[v958::context+128]=0;
    c.mmu.words[v958::context+132]=c.lr;c.mmu.words[v958::context+136]=c.ctr;c.mmu.words[v958::context+140]=c.xer;
    c.mmu.words[v958::context+408]=c.pc;c.mmu.words[v958::context+412]=c.msr;
    c.pc=H;c.msr=0x32u;
    scheduler.advance(++tick);need(old.after_return_at(tick));
    need(v958::start(c,frame)&&old.handoff_second_ack(v958::ack,ctl,cause,mask,tick));
    need(v958::active()&&old.stage()==3u);
    if(mode=="frame")c.mmu.words[v958::context+124]^=1u;
    auto visit=[&](uint32_t pc,uint32_t w,bool guard=false){scheduler.advance(++tick);c.pc=pc;v958::before(c,pc,w,guard);};
    visit(H,bl(H,Save),mode=="guard");
    c.pc=mode=="entry"?Completion:Save;c.lr=H+4;v958::observe(c.pc,c);
    visit(Save,Blr);
    if(mode=="return")c.gpr[14]^=1u;
    visit(H+4,bl(H+4,Completion));
    c.pc=Completion;c.lr=H+8;v958::observe(c.pc,c);
    visit(Completion,Load);
    if(!v958::ack.read(ctl,mode=="read"?S:C,result))v958::reject(5);
    c.gpr[4]=result|SiController::TC_INT;
    visit(Completion+4,Store);
    if(!v958::ack.write(ctl,C,mode=="write"?c.gpr[4]^2u:c.gpr[4]))v958::reject(6);
    need(ctl.issued_tokens()==2u&&cause==Other&&mask==SI&&scheduler.completed()==2u);
    visit(Completion+8,Nop);
    need(false);
}
