#include "wii_si_binding_v512.h"
#include "wii_si_type_scheduler_v514.h"
#include "wii_third_si_transfer_v1028.h"
#include "wii_third_alarm_suffix_v1047.h"
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
    uint32_t pc=Resume,lr=H+0x2000u,ctr=17,xer=0x80000000u,msr=0x8032u,dispatch_saved_ctx=0,srr0=Resume,srr1=0x8032u;
    bool is_running=true,in_callback=false,dec_irq_pending=true;
    uint32_t dec_value=300;uint64_t dec_written_tb=50;
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
    const bool error=mode.starts_with("error-")&&mode!="error-success";
    const SiTypeScheduler::Profile ports{Port::absent(),error?Port::absent():Port::present({1,2,3}),Port::absent(),Port::present({4,5,6})};
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
    const bool abi_probe=mode.starts_with("error-abi");
    constexpr uint32_t Cmd=0x8000d100u,Resp=0x8000d200u;
    const std::array<uint32_t,8> args{2,Cmd,1,Resp,3,v958::transfer_callback,0,3948};
    if(abi_probe){
        for(unsigned i=0;i<32;++i)c.mmu.words[v958::transfer_slots+4*i]=0;
        for(unsigned i=0;i<8;++i)c.mmu.words[v958::transfer_slots+64+4*i]=args[i];
        if(mode=="error-abi-core"||mode=="error-abi-live-core")c.mmu.words[v958::transfer_slots+64+4]^=4u;
    }
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
    const bool error_route=mode.starts_with("error-")&&mode!="error-success";
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
    if(mode.starts_with("callback")||mode.starts_with("error-callback")){
        if(error_route)for(unsigned i=0;i<(mode=="error-callback-short"?69u:70u);++i)visit(H+8,Nop);
        c.ctr=v958::transfer_callback;
        if(mode=="callback-unknown"){c.ctr+=0x100;c.mmu.words[c.ctr]=Nop;}
        if(mode=="callback-unmapped")c.ctr+=0x200;
        if(mode=="callback-corrupt")c.mmu.words[v958::transfer_callback+4]^=1u;
        if(mode=="callback-unaligned")c.ctr|=1u;
        if(mode=="callback-frame")c.mmu.words[v958::context+124]^=1u;
        visit(H+24,0x4e800421u,mode!="callback-unguarded");need(false);
    }
    if(error_route)for(unsigned i=0;i<64u;++i)visit(H+8,Nop);
    visit(H+12,bl(H+12,Nested));c.pc=Nested;c.lr=H+16;v958::observe(c.pc,c);
    visit(Nested,bl(Nested,Disable));c.pc=Disable;c.lr=Nested+4;v958::observe(c.pc,c);
    c.gpr[3]=c.msr;visit(Disable,Mtmsr);visit(Disable+4,Blr);
    visit(Nested+4,bl(Nested+4,Time));c.pc=Time;c.lr=Nested+8;v958::observe(c.pc,c);
    visit(Time,Nop);visit(Time+4,Blr);
    visit(Nested+8,bl(Nested+8,Restore));c.pc=Restore;c.lr=Nested+12;v958::observe(c.pc,c);
    c.gpr[3]=c.msr;visit(Restore,Mtmsr);visit(Restore+4,Blr);visit(Nested+12,Nop);
    c.lr=H+16;visit(Nested+16,Blr);visit(H+16,Nop);
    if(!abi_probe)for(unsigned i=0;i<32;++i)c.mmu.words[v958::transfer_slots+4*i]=0;
    for(unsigned i=0;i<5;++i)c.mmu.words[v958::transfer_data+4*i]=0xffffffffu;
    c.mmu.words[Cmd]=0;c.mmu.words[Resp]=0;
    for(unsigned i=0;i<8;++i){c.gpr[3+i]=args[i];if(!abi_probe)c.mmu.words[v958::transfer_slots+64+4*i]=args[i];}
    if(abi_probe&&mode!="error-abi-exact"&&mode!="error-abi-live-exact")c.gpr[10]=0u;
    if(mode=="error-abi-changed"||mode=="error-abi-live-changed")c.mmu.words[v958::transfer_slots+64+28]^=1u;
    if(mode=="direct-mismatch")c.mmu.words[v958::transfer_slots+64+28]^=1;
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
    if(mode.starts_with("error-abi-live")){
        // Use exactly the production handoff and observer functions; only
        // the instruction effects and mapped labels are synthetic.
        constexpr uint32_t Root=H+0x700u,L1=H+0x800u,L2=H+0x900u,L3=H+0xa00u;
        c.mmu.words[H+24]=Nop;
        for(auto e:v958::third_edges)c.mmu.words[e.site]=bl(e.site,e.target);
        for(auto leaf:{L1,L2,L3})c.mmu.words[leaf]=Blr;
        c.mmu.words[Root+12]=Load;
        c.mmu.words[Root+16]=0x90830000u|B;
        c.mmu.words[Root+20]=0x90830000u|S;
        c.mmu.words[Root+24]=Store;
        for(unsigned i=0;i<9;++i)c.mmu.words[Root+28+4*i]=Nop;
        c.mmu.words[Root+64]=Blr;
        visit(H+20,v958::transfer_branch,true);
        need(v958::third_ready&&v958::third_admission==(mode=="error-abi-live-exact"?1u:2u));
        const auto ctrl=ctl.read(C),status=ctl.read(S),buffer=ctl.read(B);
        const bool tamper=mode=="error-abi-live-tamper"||mode=="error-abi-live-reg"||mode=="error-abi-live-tick";
        if(mode=="error-abi-live-tamper")c.mmu.words[v958::transfer_slots+64+28]^=1u;
        if(mode=="error-abi-live-reg")c.gpr[10]^=1u;
        if(mode=="error-abi-live-tick")scheduler.advance(++tick);
        const bool admitted=SiBinding::handoff_second_transfer(c,cause,mask,H+20);
        need(admitted!=tamper&&ctl.read(C)==ctrl&&ctl.read(S)==status&&ctl.read(B)==buffer&&ctl.issued_tokens()==2u);
        if(tamper){
            need(v958::ack.stage()==4u&&!v958::next_device.stage()&&!v958::third_route.stage());
            std::cout<<"V1043_LIVE_HANDOFF refused=1 unchanged_device=1 original_execution=0"<<std::endl;return 0;
        }
        need(v958::third_active()&&v958::ack.stage()==5u&&v958::next_device.stage()==1u);
        need(!SiBinding::handoff_second_transfer(c,cause,mask,H+20));
        c.pc=Root;c.lr=H+24;v958::observe(c.pc,c);
        for(unsigned i=1;i<v958::third_edges.size();++i){
            const auto e=v958::third_edges[i];visit(e.site,c.mmu.words[e.site]);
            c.pc=e.target;c.lr=e.site+4;v958::observe(c.pc,c);visit(e.target,Blr);
        }
        c.gpr[3]=Base;visit(Root+12,Load);read=SiBinding::read32(Base+C);need(read&&*read==ctrl);
        c.gpr[4]=0;visit(Root+16,c.mmu.words[Root+16]);need(SiBinding::write32(Base+B,0));
        c.gpr[4]=0x00000800u;visit(Root+20,c.mmu.words[Root+20]);need(SiBinding::write32(Base+S,c.gpr[4]));
        c.gpr[4]=0xc0010305u;visit(Root+24,Store);need(SiBinding::write32(Base+C,c.gpr[4]));
        for(unsigned i=0;i<9;++i){visit(Root+28+4*i,Nop);need(!v958::poll(c));}
        c.gpr[3]=1;c.lr=H+24;
        c.mmu.words[v958::transfer_data]=2u;c.mmu.words[v958::transfer_data+8]=3u;
        c.mmu.words[v958::transfer_data+12]=Resp;c.mmu.words[v958::transfer_data+16]=v958::transfer_callback;
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
        const bool alarm_mode=mode.starts_with("error-abi-live-alarm");
        if(alarm_mode){
            constexpr uint32_t A=H+0xb00u,D=H+0xc00u,Q=H+0xd00u,Head=0x8000e000u,Tail=Head+4,Node=Head+0x100u;
            constexpr uint32_t Rd=0x80830038u,Wr=0x90830038u,Site=H+36;
            c.mmu.words[H+28]=Rd;c.mmu.words[H+32]=Wr;c.mmu.words[Site]=bl(Site,A);c.mmu.words[Site+4]=Nop;
            c.mmu.words[A]=bl(A,D);c.mmu.words[A+4]=Nop;c.mmu.words[A+8]=bl(A+8,Q);c.mmu.words[A+12]=Nop;c.mmu.words[A+16]=Blr;
            c.mmu.words[D]=Mtmsr;c.mmu.words[D+4]=Blr;c.mmu.words[Q]=Mtmsr;c.mmu.words[Q+4]=Blr;
            c.mmu.words[Head]=c.mmu.words[Tail]=0;for(unsigned i=0;i<10;++i)c.mmu.words[Node+4*i]=0;
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
            if(mode.starts_with("error-abi-live-alarm-callback")){
                c.mmu.words[Site+8]=0x4e800421u;
                for(unsigned i=0;i<v958::third_postalarm_prefix.size();++i)c.mmu.words[v958::transfer_callback+4u*i]=v958::third_postalarm_prefix[i];
                for(unsigned i=0;i<v958::third_postalarm_save.size();++i)c.mmu.words[v958::third_postalarm_save_root+4u*i]=v958::third_postalarm_save[i];
                constexpr uint32_t Stack=0x8000b000u;
                need(c.gpr[1]==Stack);
                for(uint32_t p=Stack-0x400u;p<Stack+0x100u;p+=4u)c.mmu.words[p]=p^0xdeadbeefu;
            }
#endif
            if(mode=="error-abi-live-alarm-label")c.mmu.words[H+32]^=1u;
        }
#endif
        visit(Root+64,Blr);visit(H+24,Nop);
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
        if(alarm_mode){
            constexpr uint32_t A=H+0xb00u,D=H+0xc00u,Q=H+0xd00u,Head=0x8000e000u,Node=Head+0x100u;
            constexpr uint32_t Rd=0x80830038u,Wr=0x90830038u,Site=H+36;
            need(v958::third_alarm_active()&&v958::ack.stage()==5u&&v958::next_device.held_now());
            c.gpr[3]=Base;
            if(mode=="error-abi-live-alarm-skip")visit(H+32,Wr);
            if(mode=="error-abi-live-alarm-frame")c.mmu.words[v958::context+124]^=1u;
            visit(H+28,Rd);
            if(mode!="error-abi-live-alarm-missing"){
                auto status_read=SiBinding::read32(Base+S);need(status_read.has_value());c.gpr[4]=*status_read;
            }
            if(mode=="error-abi-live-alarm-value")c.gpr[4]^=1u;
            visit(H+32,Wr);
            need(SiBinding::write32(Base+S,c.gpr[4]));
            c.gpr[3]=Node;visit(Site,bl(Site,A));
            c.pc=A;c.lr=Site+4;v958::observe(c.pc,c);
            visit(A,bl(A,D));c.pc=D;c.lr=A+4;v958::observe(c.pc,c);
            c.gpr[3]=c.msr;visit(D,Mtmsr);c.gpr[3]=0;visit(D+4,Blr);
            visit(A+4,Nop);visit(A+8,bl(A+8,Q));
            c.pc=Q;c.lr=A+12;v958::observe(c.pc,c);
            c.gpr[3]=c.msr;visit(Q,Mtmsr);c.gpr[3]=0;visit(Q+4,Blr);
            visit(A+12,Nop);c.lr=Site+4;visit(A+16,Blr);
            if(mode=="error-abi-live-alarm-queue")c.mmu.words[Head]=Node;
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
            const bool callback_mode=mode.starts_with("error-abi-live-alarm-callback");
            if(callback_mode){
                need(c.gpr[1]==0x8000b000u);c.gpr[3]=2u;c.ctr=v958::transfer_callback;
                if(mode=="error-abi-live-alarm-callback-word")c.mmu.words[Site+8]^=1u;
            }
#endif
            visit(Site+4,Nop); // production observer owns terminal result
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
            if(callback_mode){
                constexpr uint32_t Root=v958::transfer_callback,Leaf=v958::third_postalarm_save_root,Stack=0x8000b000u;
                if(mode=="error-abi-live-alarm-callback-frame")c.mmu.words[v958::context+124]^=1u;
                if(mode=="error-abi-live-alarm-callback-target")c.ctr=Leaf;
                visit(Site+8,0x4e800421u);c.pc=Root;c.lr=Site+12;
                if(mode!="error-abi-live-alarm-callback-poll")need(!v958::poll(c));
                scheduler.advance(++tick);v958::observe(Root,c);
                visit(Root,v958::third_postalarm_prefix[0]);c.gpr[1]=Stack-64;c.mmu.words[Stack-64]=Stack;
                if(mode=="error-abi-live-alarm-callback-stack")c.mmu.words[Stack-64]^=1u;
                visit(Root+4,v958::third_postalarm_prefix[1]);c.gpr[0]=c.lr;
                visit(Root+8,v958::third_postalarm_prefix[2]);c.mmu.words[Stack+4]=c.gpr[0];
                visit(Root+12,v958::third_postalarm_prefix[3]);c.gpr[11]=Stack;
                visit(Root+16,v958::third_postalarm_prefix[4]);c.pc=Leaf;c.lr=Root+20;
                v958::observe(Leaf,c);visit(Leaf,v958::third_postalarm_save[0]);c.mmu.words[Stack-8]=c.gpr[30];
                visit(Leaf+4,v958::third_postalarm_save[1]);c.mmu.words[Stack-4]=c.gpr[31];
                visit(Leaf+8,Blr);visit(Root+20,Nop);
            }
#endif
        }
#endif
        need(false);
    }
#endif
#ifdef UNDERCOVER_V1025_PRIVATE_TRANSFER
    if(mode.starts_with("error-third")){
        // Synthetic frontier: native call admission and the next device's
        // MMIO are tested independently of the not-yet-installed labels.
        scheduler.advance(++tick);c.pc=H+20;
        need(v958::ack.before(c,c.pc,v958::transfer_branch,true));
        if(mode=="error-third-mismatch")c.mmu.words[v958::transfer_slots+64+28]^=1;
        if(mode=="error-third-frame")c.mmu.words[v958::context+124]^=1;
        if(mode=="error-third-stale")++tick;
        if(mode=="error-third-word")c.mmu.words[c.pc]^=4u;
        std::atomic<uint32_t> wrong_mask{SI};
        const auto ctrl=ctl.read(C),status=ctl.read(S),buffer=ctl.read(B);
        const bool good=SiBinding::handoff_second_transfer(c,cause,mode=="error-third-mask"?wrong_mask:mask);
        const bool refused=mode=="error-third-mismatch"||mode=="error-third-frame"||mode=="error-third-stale"||mode=="error-third-word"||mode=="error-third-mask";
        need(good!=refused&&ctl.read(C)==ctrl&&ctl.read(S)==status&&ctl.read(B)==buffer&&ctl.issued_tokens()==2u&&cause==Other);
        if(refused){
            need(v958::ack.stage()==4u&&!v958::next_device.stage());
            std::cout<<"V1025_THIRD_HANDOFF refused=1 mutation=0 token=2 original_execution=0"<<std::endl;return 0;
        }
        auto& third=v958::next_device;
        need(v958::ack.stage()==5u&&third.stage()==1u&&!v958::ack.postack_held());
        need(!SiBinding::handoff_second_transfer(c,cause,mask)&&third.stage()==1u&&ctl.issued_tokens()==2u);
        if(mode.starts_with("error-third-native")){
            // Independently authored instruction fixture, not game code.
            constexpr uint32_t Root=H+0x700u,L1=H+0x800u,L2=H+0x900u,L3=H+0xa00u;
            constexpr std::array<AckCallSpan,5> spans{{{H,H+32},{Root,Root+80},{L1,L1+4},{L2,L2+4},{L3,L3+4}}};
            constexpr std::array<AckCallEdge,4> edges{{{H+20,Root},{Root,L1},{Root+4,L2},{Root+8,L3}}};
            c.mmu.words[H+24]=Nop;
            for(auto e:edges)c.mmu.words[e.site]=bl(e.site,e.target);
            for(auto leaf:{L1,L2,L3})c.mmu.words[leaf]=Blr;
            c.mmu.words[Root+12]=Load;
            c.mmu.words[Root+16]=0x90830000u|B;
            c.mmu.words[Root+20]=0x90830000u|S;
            c.mmu.words[Root+24]=Store;
            for(unsigned i=0;i<9;++i)c.mmu.words[Root+28+4*i]=Nop;
            c.mmu.words[Root+64]=Blr;
            ThirdSiTransferRoute route;
            const auto admitted=inspect_si_transfer_arguments(c,v958::transfer_data,v958::transfer_slots,v958::transfer_callback);
            need(route.start(c,H+20,c.mmu.words[H+20],admitted,spans,edges,{},v958::transfer_data));
            auto refusal=[&](bool rejected){
                need(rejected&&route.failure()!=0u);
                std::cout<<"V1030_NATIVE_ROUTE refused=1 original_execution=0"<<std::endl;
            };
            auto at=[&](uint32_t pc,uint32_t word){scheduler.advance(++tick);c.pc=pc;return route.before(c,pc,word,third);};
            c.pc=Root;c.lr=H+24;
            if(mode=="error-third-native-entry"){refusal(!route.entry(c,L1,third));return 0;}
            need(route.entry(c,Root,third));
            if(mode=="error-third-native-skip"){refusal(!at(Root+4,c.mmu.words[Root+4]));return 0;}
            if(mode=="error-third-native-word"){refusal(!at(Root,Nop));return 0;}
            if(mode=="error-third-native-srr"){c.srr0^=4u;refusal(!at(Root,c.mmu.words[Root]));return 0;}
            for(unsigned i=1;i<edges.size();++i){
                const auto e=edges[i];
                need(at(e.site,c.mmu.words[e.site]));
                c.pc=e.target;c.lr=e.site+4;need(route.entry(c,c.pc,third));
                need(at(e.target,Blr));
                if(i==1&&mode=="error-third-native-abi"){
                    c.gpr[31]^=1u;refusal(!at(e.site+4,c.mmu.words[e.site+4]));return 0;
                }
            }
            c.gpr[3]=Base;need(at(Root+12,Load));read=SiBinding::read32(Base+C);need(read&&*read==ctrl);
            c.gpr[4]=0;need(at(Root+16,c.mmu.words[Root+16])&&SiBinding::write32(Base+B,0));
            c.gpr[4]=0x00000800u;need(at(Root+20,c.mmu.words[Root+20])&&SiBinding::write32(Base+S,c.gpr[4]));
            c.gpr[4]=0xc0010305u;need(at(Root+24,Store)&&SiBinding::write32(Base+C,c.gpr[4]));
            for(unsigned i=0;i<9;++i){need(at(Root+28+4*i,Nop));need(route.poll(c,third));}
            c.gpr[3]=1;c.lr=H+24;
            c.mmu.words[v958::transfer_data]=2u;c.mmu.words[v958::transfer_data+8]=3u;
            c.mmu.words[v958::transfer_data+12]=Resp;c.mmu.words[v958::transfer_data+16]=v958::transfer_callback;
            need(at(Root+64,Blr));
            if(mode=="error-third-native-data"){
                c.mmu.words[v958::transfer_data+12]^=4u;refusal(!at(H+24,Nop));return 0;
            }
            need(at(H+24,Nop)&&route.stage()==2u&&route.entries()==4u&&route.returns()==4u&&
                 route.visits()==21u&&third.held_now()&&third.token()==3u&&third.follow_stage()==3u&&scheduler.completed()==3u);
            if(mode.starts_with("error-third-native-alarm")){
                constexpr uint32_t A=H+0xb00u,D=H+0xc00u,Q=H+0xd00u,Head=0x8000e000u,Tail=Head+4,Node=Head+0x100u;
                constexpr uint32_t Rd=0x80830038u,Wr=0x90830038u,Site=H+36;
                c.mmu.words[H+28]=Rd;c.mmu.words[H+32]=Wr;c.mmu.words[Site]=bl(Site,A);c.mmu.words[Site+4]=Nop;
                c.mmu.words[A]=bl(A,D);c.mmu.words[A+4]=Nop;c.mmu.words[A+8]=bl(A+8,Q);c.mmu.words[A+12]=Nop;c.mmu.words[A+16]=Blr;
                c.mmu.words[D]=Mtmsr;c.mmu.words[D+4]=Blr;c.mmu.words[Q]=Mtmsr;c.mmu.words[Q+4]=Blr;
                c.mmu.words[Head]=c.mmu.words[Tail]=0;for(unsigned i=0;i<10;++i)c.mmu.words[Node+4*i]=0;
                AlarmCancelExpectation expectation{};expectation.site=Site;expectation.branch=bl(Site,A);
                expectation.root=A;expectation.end=A+20;expectation.head=Head;expectation.tail=Tail;
                expectation.root_calls[0]={A,D,D+8,bl(A,D)};expectation.root_calls[1]={A+8,Q,Q+8,bl(A+8,Q)};
                const std::array<HandlerSuffixLabel,4> rows{{{H+24,Nop,0,0},{H+28,Rd,0,0},{H+32,Wr,0,0},{Site,bl(Site,A),5,1}}};
                ThirdAlarmSuffixRoute alarm(expectation);
                need(alarm.start(c,H+24,rows,third)&&alarm.before(c,H+24,Nop,third));
                auto alarm_at=[&](uint32_t pc,uint32_t w){scheduler.advance(++tick);c.pc=pc;return alarm.before(c,pc,w,third);};
                auto refused=[&](bool bad){
                    need(bad&&alarm.failure()&&ctl.issued_tokens()==3u);
                    std::cout<<"V1047_THIRD_ALARM refused=1 original_execution=0"<<std::endl;return 0;
                };
                c.gpr[3]=Base;
                if(mode=="error-third-native-alarm-srr"){c.srr0^=4u;return refused(!alarm_at(H+28,Rd));}
                if(mode=="error-third-native-alarm-skip")return refused(!alarm_at(H+32,Wr));
                need(alarm_at(H+28,Rd));
                if(mode=="error-third-native-alarm-missing")return refused(!alarm_at(H+32,Wr));
                auto status_read=SiBinding::read32(Base+S);need(status_read.has_value());c.gpr[4]=*status_read;
                if(mode=="error-third-native-alarm-value"){c.gpr[4]^=1u;return refused(!alarm_at(H+32,Wr));}
                need(alarm_at(H+32,Wr)&&SiBinding::write32(Base+S,c.gpr[4]));
                c.gpr[3]=Node;need(alarm_at(Site,bl(Site,A))&&alarm.stage()==2u);
                c.pc=A;c.lr=Site+4;need(alarm.entry(c,A,third));
                need(alarm_at(A,bl(A,D)));c.pc=D;c.lr=A+4;need(alarm.entry(c,D,third));
                c.gpr[3]=c.msr;need(alarm_at(D,Mtmsr));c.gpr[3]=0;need(alarm_at(D+4,Blr));
                need(alarm_at(A+4,Nop)&&alarm_at(A+8,bl(A+8,Q)));
                c.pc=Q;c.lr=A+12;need(alarm.entry(c,Q,third));
                c.gpr[3]=c.msr;need(alarm_at(Q,Mtmsr));c.gpr[3]=0;need(alarm_at(Q+4,Blr));
                need(alarm_at(A+12,Nop));c.lr=Site+4;need(alarm_at(A+16,Blr));
                if(mode=="error-third-native-alarm-queue"){c.mmu.words[Head]=Node;return refused(!alarm_at(Site+4,Nop));}
                need(alarm_at(Site+4,Nop)&&alarm.stage()==3u&&alarm.alarm().total()==9u&&
                     alarm.alarm().calls()==3u&&third.held_now()&&third.suffix_status_reads()==1u&&third.suffix_status_writes()==1u&&cause==(Other|SI));
                std::cout<<"V1047_THIRD_ALARM verified=1 token=3 status_reads=1 status_writes=1 alarm_return=1 original_execution=0"<<std::endl;return 0;
            }
            std::cout<<"V1030_NATIVE_ROUTE verified=1 entries=4 returns=4 visits=21 token=3 original_execution=0"<<std::endl;
            return 0;
        }
        const auto before=[&](Access access=Access::None,uint32_t a=0,std::optional<uint32_t> v=std::nullopt){
            scheduler.advance(++tick);need(third.before(tick,access,a,v));
        };
        if(mode=="error-third-unarmed"){SiBinding::read32(Base+C);need(false);}
        before(Access::Read,Base+C);read=SiBinding::read32(Base+C);need(read&&*read==ctrl);
        before(Access::Write,Base+B,0x00000000u);need(SiBinding::write32(Base+B,0u));
        before(Access::Write,Base+S,0x00000800u);need(SiBinding::write32(Base+S,0x00000800u));
        before(Access::Write,Base+C,0xc0010305u);need(SiBinding::write32(Base+C,0xc0010305u));
        for(unsigned i=0;i<9;++i)before();
        need(third.finish(tick,1u)&&third.held_now()&&third.token()==3u&&third.follow_stage()==3u&&
             ctl.issued_tokens()==3u&&scheduler.completed()==3u&&cause==(Other|SI)&&!ctl.pending()&&
             (ctl.read(C)&SiController::COM_ERR)&&v958::ack.stage()==5u);
        std::cout<<"V1025_THIRD_HANDOFF original_execution=0 token=3 completed=1 exclusive_device=1 duplicate_refused=1 reads="<<third.reads()<<" writes="<<third.writes()<<std::endl;
        return 0;
    }
#endif
    visit(H+20,v958::transfer_branch,true);need(false);
}
