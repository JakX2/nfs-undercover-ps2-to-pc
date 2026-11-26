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
    uint32_t pc=Resume,lr=H+0x2000u,ctr=17,xer=0x80000000u,msr=0x8032u,dispatch_saved_ctx=0,srr0=0x80005000u,srr1=0x8032u;
    bool is_running=true,in_callback=false;
    uint64_t read_timebase()const{return 0x100000020ull;}
};
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b){std::cerr<<"V997_ASSERT line="<<loc.line()<<std::endl;std::_Exit(125);}
}
int main(int argc,char** argv){
    need(argc==2);std::string_view mode=argv[1];
    const bool error_route=mode.starts_with("error-");if(error_route)mode.remove_prefix(6);
    if(mode=="default"){need(!v958::enabled()&&!v958::active());std::cout<<"V964_DEFAULT inactive=1\n";return 0;}
    need(v958::enabled()&&!v958::active());
    std::atomic<uint32_t> cause{Other},mask{SI};SiController ctl(cause);SiBinding binding(ctl);
    using Port=SiTypeScheduler::Port;
    const SiTypeScheduler::Profile ports{Port::absent(),error_route?Port::absent():Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
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
    const uint32_t shared_site=error_route?Completion+24:Completion+12;
    if(error_route){
        c.mmu.words[shared_site]=bl(shared_site,Nested);c.mmu.words[shared_site+4]=Nop;
        for(unsigned i=0;i<115u;++i)visit(Completion+16,Nop);
    }
    visit(shared_site,bl(shared_site,Nested),mode=="guard-shared");
    c.pc=Nested;c.lr=shared_site+4;v958::observe(c.pc,c);
    visit(Nested,bl(Nested,Disable));c.pc=mode=="wrong-leaf"?Time:Disable;c.lr=Nested+4;v958::observe(c.pc,c);
    c.gpr[3]=c.msr|(mode=="changed-msr"?0x8000u:0u);
    visit(Disable,Mtmsr);visit(Disable+4,Blr);
    visit(Nested+4,bl(Nested+4,Time));c.pc=Time;c.lr=Nested+8;v958::observe(c.pc,c);
    visit(Time,Nop);visit(Time+4,Blr);
    visit(Nested+8,bl(Nested+8,Restore));c.pc=Restore;c.lr=Nested+12;v958::observe(c.pc,c);
    c.gpr[3]=c.msr;visit(Restore,Mtmsr);
    visit(Restore+4,Blr);visit(Nested+12,Nop);
    c.lr=shared_site+4;visit(Nested+16,Blr);visit(shared_site+4,Nop);
    need(v958::shared_seen==!error_route&&v958::ack.postack_held());
    c.lr=H+8;visit(Completion+20,Blr);
    if(mode=="corrupt-abi")c.gpr[31]^=1u;
    visit(H+8,Nop);
    need(v958::post_seen&&v958::success_frontier_enabled()&&v958::ack.postack_held());
    for(unsigned i=0;i<v958::success_callback_words.size();++i)c.mmu.words[v958::transfer_callback+4*i]=v958::success_callback_words[i];
    if(mode.starts_with("callback")){
        if(error_route)for(unsigned i=0;i<70u;++i)visit(H+8,Nop);
        c.ctr=v958::transfer_callback;
        if(mode=="callback-unknown"){c.ctr+=0x100;c.mmu.words[c.ctr]=Nop;}
        if(mode=="callback-unmapped")c.ctr+=0x200;
        if(mode=="callback-corrupt")c.mmu.words[v958::transfer_callback+4]^=1u;
        if(mode=="callback-unaligned")c.ctr|=1u;
        if(mode=="callback-frame")c.mmu.words[v958::context+124]^=1u;
        const auto stack=c.gpr[1];
        for(uint32_t a=stack-0x400u;a<stack+0x100u;a+=4)c.mmu.words[a]=a^0x12345678u;
        for(unsigned i=0;i<v958::second_callback_save.size();++i)c.mmu.words[v958::second_callback_save_root+4*i]=v958::second_callback_save[i];
        c.gpr[3]=mode=="callback-channel"?4u:1u;
        visit(H+24,0x4e800421u,mode!="callback-unguarded");
        need(v958::callback_active());const auto target=v958::transfer_callback,save=v958::second_callback_save_root;
        c.pc=target;c.lr=H+28u;
        if(mode!="callback-no-poll")v958::poll(c);
        scheduler.advance(++tick);v958::observe(target,c);
        auto prefix=v958::second_callback_prefix;
        visit(target,prefix[0]);c.mmu.words[stack-64u]=stack;c.gpr[1]=stack-64u;
        if(mode=="callback-stack")c.mmu.words[stack-64u]^=1u;
        visit(target+4,prefix[1]);c.gpr[0]=c.lr;
        visit(target+8,prefix[2]);c.mmu.words[stack+4]=c.gpr[0];
        visit(target+12,prefix[3]);c.gpr[11]=stack;
        visit(target+16,prefix[4]);c.pc=save;c.lr=target+20u;v958::observe(save,c);
        for(unsigned i=0;i<6;++i){visit(save+4*i,v958::second_callback_save[i]);c.mmu.words[stack-24+4*i]=c.gpr[26+i];}
        if(mode=="callback-save-corrupt")c.mmu.words[stack-4]^=1u;
        visit(save+24,v958::second_callback_save[6]);
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
        if(mode.starts_with("callback-time")){
            auto put=[&](uint32_t base,const auto& words){for(auto word:words){c.mmu.words[base]=word;base+=4;}};
            put(v813::T,v813::system_words);put(v813::D,v813::disable);put(v813::U,v813::timebase);put(v813::R,v813::restore);
            if(mode!="callback-time-offset"){c.mmu.words[v813::Offset]=0;c.mmu.words[v813::Offset+4]=0x1234u;}
            visit(target+20,prefix[5]);
            need(v958::callback_time_active()&&v958::callback_time.visits()==1u&&v958::ack.postack_held());
            if(mode=="callback-time-frame")c.mmu.words[v958::context+124]^=1u;
            visit(target+24,v813::continuation[1]);
            c.pc=v813::T;c.lr=target+28;v958::observe(c.pc,c);
            for(unsigned i=0;i<25;++i){
                const uint32_t pc=v813::T+4*i;visit(pc,v813::system_words[i]);
                if(i==1||i==4||i==7){
                    const uint32_t leaf=i==1?v813::D:i==4?v813::U:v813::R;
                    const auto& words=i==1?v813::disable:i==4?v813::timebase:v813::restore;
                    c.pc=leaf;c.lr=pc+4;v958::observe(leaf,c);
                    for(unsigned j=0;j<words.size();++j){
                        visit(leaf+4*j,words[j]);
                        if(i==4){
                            if(j==0)c.gpr[3]=uint32_t(c.read_timebase()>>32);
                            if(j==1)c.gpr[4]=uint32_t(c.read_timebase());
                            if(j==2)c.gpr[5]=uint32_t(c.read_timebase()>>32);
                            if(j==3)v958::poll(c);
                        }else if(j==0){c.gpr[6]=c.msr;c.gpr[3]=0;}
                    }
                }
                if(i==5)c.gpr[3]=0;
                if(i==23){c.gpr[3]=1;c.gpr[4]=mode=="callback-time-result"?0x1255u:0x1254u;c.lr=target+28;}
            }
            visit(target+28,v813::continuation.back());need(false);
        }
#endif
        visit(target+20,prefix[5]);need(false);
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
