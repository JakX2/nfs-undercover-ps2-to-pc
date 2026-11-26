#include "wii_si_binding_v512.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
#include <source_location>
#include <string_view>
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t H=0x80004000u,Save=H+0x100u,Completion=H+0x200u,Resume=H+0x1000u,Other=0x100u,Base=0xcd006400u,Mirror=0xcd806400u;
constexpr uint32_t Nested=H+0x300u,Disable=H+0x400u,Time=H+0x500u,Restore=H+0x600u,Mtmsr=0x7c600124u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer,SI=SiController::PI_SI;
constexpr uint32_t Load=0x80830034u,Store=0x90830034u,Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t bl(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words{{H,bl(H,Save)},{H+4,bl(H+4,Completion)},{Save,Blr},{Completion,Load},{Completion+4,Store},{Completion+8,Nop},{Completion+12,bl(Completion+12,Nested)},{Completion+16,Nop},{Completion+20,Blr},{H+8,Nop},{H+12,bl(H+12,Nested)},{H+16,Nop},{H+20,0x480006edu},{H+24,0x4e800421u},
        {Nested,bl(Nested,Disable)},{Nested+4,bl(Nested+4,Time)},{Nested+8,bl(Nested+8,Restore)},{Nested+12,Nop},{Nested+16,Blr},
        {Disable,Mtmsr},{Disable+4,Blr},{Time,Nop},{Time+4,Blr},{Restore,Mtmsr},{Restore+4,Blr}};
    uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
    uint8_t read8(uint32_t a){return uint8_t(words.at(a&~3u)>>(24u-8u*(a&3u)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint64_t inst_count=100;
    uint32_t pc=Resume,lr=H+0x2000u,ctr=17,xer=0x80000000u,msr=0x8032u,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;
};
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b){std::cerr<<"V997_ASSERT line="<<loc.line()<<std::endl;std::_Exit(125);}
}
int main(int argc,char** argv){
    need(argc==2);const std::string_view mode=argv[1];
    if(mode=="default"){need(!v958::enabled()&&!v958::active());std::cout<<"V964_DEFAULT inactive=1\n";return 0;}
    need(v958::enabled()&&!v958::active());
    std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);SiBinding binding(ctl);
    using Port=SiTypeScheduler::Port;
    const SiTypeScheduler::Profile ports{Port::absent(),Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
    SiTypeScheduler scheduler(ctl,ports,8);
    SiTickBinding ticks(scheduler);
    need(SiBinding::write32(Base+C,0xc0010301u));scheduler.advance(1);scheduler.advance(9);
    Cpu c;auto& tick=c.inst_count;auto& first=si_completion_ack_trace;auto& old=si_transfer_device;ExternalReturnWitness frame;
    need(first.arm(ctl,cause,mask,tick,H,H+16));++tick;need(first.before(H,0x90030000u));
    need(SiBinding::write32(Base+C,0xe0010300u));++tick;need(first.before(H+4,Nop)&&first.resume_after_ack(H+4,Nop));
    scheduler.advance(tick);need(SiBinding::begin_transfer_device(cause,mask,tick,1,true));
    auto step=[&](Access a=Access::None,uint32_t addr=0){scheduler.advance(++tick);return old.before(tick,a,addr);};
    uint32_t result=0;
    need(step(Access::Read,Base+C));auto read=SiBinding::read32(Base+C);need(read.has_value());result=*read;
    need(step(Access::Write,Base+B)&&SiBinding::write32(Base+B,0x00abcdefu));
    need(step(Access::Write,Base+S)&&SiBinding::write32(Base+S,0x08000000u));
    need(step(Access::Write,Base+C)&&SiBinding::write32(Base+C,0xc0010303u));
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
    need(v958::start(c,frame)&&SiBinding::handoff_second_ack(cause,mask,tick));
    need(v958::active()&&old.stage()==3u);
    if(mode=="frame")c.mmu.words[v958::context+124]^=1u;
    auto visit=[&](uint32_t pc,uint32_t w,bool guard=false){scheduler.advance(++tick);c.pc=pc;v958::before(c,pc,w,guard);};
    visit(H,bl(H,Save),mode=="guard");
    c.pc=mode=="entry"?Completion:Save;c.lr=H+4;v958::observe(c.pc,c);
    visit(Save,Blr);
    if(mode=="return")c.gpr[14]^=1u;
    visit(H+4,bl(H+4,Completion));
    c.pc=Completion;c.lr=H+8;v958::observe(c.pc,c);
    if(mode=="mirror")c.gpr[3]=Mirror;
    visit(Completion,Load);
    if(mode=="width")SiBinding::check(Base+C,2u,true);
    if(mode=="offset")SiBinding::check(Base+8u,4u,true);
    read=SiBinding::read32((mode=="mirror"?Mirror:Base)+(mode=="read"?S:C));need(read.has_value());result=*read;
    c.gpr[4]=result|SiController::TC_INT;
    visit(Completion+4,Store);
    need(SiBinding::write32((mode=="mirror"?Mirror:Base)+C,mode=="write"?c.gpr[4]^2u:c.gpr[4]));
    need(ctl.issued_tokens()==2u&&cause==Other&&mask==SI&&scheduler.completed()==2u);
    visit(Completion+8,Nop);
    need(v958::post_enabled()&&v958::ack.stage()==4u);
    if(mode=="missing-shared"){
        visit(Completion+20,Blr);visit(H+8,Nop);need(false);
    }
    if(mode=="frame-after-ack")c.mmu.words[v958::context+124]^=1u;
    visit(Completion+12,bl(Completion+12,Nested),mode=="guard-shared");
    c.pc=Nested;c.lr=Completion+16;v958::observe(c.pc,c);
    visit(Nested,bl(Nested,Disable));c.pc=mode=="wrong-leaf"?Time:Disable;c.lr=Nested+4;v958::observe(c.pc,c);
    c.gpr[3]=c.msr|(mode=="changed-msr"?0x8000u:0u);
    visit(Disable,Mtmsr);visit(Disable+4,Blr);
    visit(Nested+4,bl(Nested+4,Time));c.pc=Time;c.lr=Nested+8;v958::observe(c.pc,c);
    visit(Time,Nop);visit(Time+4,Blr);
    visit(Nested+8,bl(Nested+8,Restore));c.pc=Restore;c.lr=Nested+12;v958::observe(c.pc,c);
    c.gpr[3]=c.msr;visit(Restore,Mtmsr);
    visit(Restore+4,Blr);visit(Nested+12,Nop);
    c.lr=Completion+16;visit(Nested+16,Blr);visit(Completion+16,Nop);
    need(v958::shared_seen&&v958::ack.postack_held());
    c.lr=H+8;visit(Completion+20,Blr);
    if(mode=="corrupt-abi")c.gpr[31]^=1u;
    visit(H+8,Nop);
    need(v958::post_seen&&v958::success_frontier_enabled()&&v958::ack.postack_held());
    for(unsigned i=0;i<v958::success_callback_words.size();++i)c.mmu.words[v958::transfer_callback+4*i]=v958::success_callback_words[i];
    if(mode.starts_with("callback")){
        c.ctr=v958::transfer_callback;
        if(mode=="callback-unknown"){c.ctr+=0x100;c.mmu.words[c.ctr]=Nop;}
        if(mode=="callback-unmapped")c.ctr+=0x200;
        if(mode=="callback-corrupt")c.mmu.words[v958::transfer_callback+4]^=1u;
        if(mode=="callback-unaligned")c.ctr|=1u;
        if(mode=="callback-frame")c.mmu.words[v958::context+124]^=1u;
        visit(H+24,0x4e800421u,mode!="callback-unguarded");need(false);
    }
    visit(H+12,bl(H+12,Nested));c.pc=Nested;c.lr=H+16;v958::observe(c.pc,c);
    visit(Nested,bl(Nested,Disable));c.pc=Disable;c.lr=Nested+4;v958::observe(c.pc,c);
    c.gpr[3]=c.msr;visit(Disable,Mtmsr);visit(Disable+4,Blr);
    visit(Nested+4,bl(Nested+4,Time));c.pc=Time;c.lr=Nested+8;v958::observe(c.pc,c);
    visit(Time,Nop);visit(Time+4,Blr);
    visit(Nested+8,bl(Nested+8,Restore));c.pc=Restore;c.lr=Nested+12;v958::observe(c.pc,c);
    c.gpr[3]=c.msr;visit(Restore,Mtmsr);visit(Restore+4,Blr);visit(Nested+12,Nop);
    c.lr=H+16;visit(Nested+16,Blr);visit(H+16,Nop);
    constexpr uint32_t Cmd=0x8000d100u,Resp=0x8000d200u;
    for(unsigned i=0;i<32;++i)c.mmu.words[v958::transfer_slots+4*i]=0;
    for(unsigned i=0;i<5;++i)c.mmu.words[v958::transfer_data+4*i]=0xffffffffu;
    c.mmu.words[Cmd]=0;c.mmu.words[Resp]=0;
    const std::array<uint32_t,8> args{2,Cmd,1,Resp,3,v958::transfer_callback,0,3948};
    for(unsigned i=0;i<8;++i){c.gpr[3+i]=args[i];c.mmu.words[v958::transfer_slots+64+4*i]=args[i];}
    if(mode=="direct-mismatch")c.mmu.words[v958::transfer_slots+64+28]^=1;
    visit(H+20,v958::transfer_branch,true);need(false);
}
