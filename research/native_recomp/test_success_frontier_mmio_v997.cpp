#include "wii_si_binding_v512.h"
#include "wii_si_type_scheduler_v514.h"
#include "wii_third_si_transfer_v1028.h"
#include "wii_third_alarm_suffix_v1047.h"
#include <iostream>
#include <map>
#include <memory>
#include <vector>
#include <source_location>
#include <string_view>
#ifdef UNDERCOVER_V1199_TEST_SRAM
#include "v1199_test_sram.h"
#endif
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
    // Dense backing is enabled only by the positive IPC fixture. All older
    // sparse-memory rejection lanes retain their exact previous semantics.
    std::vector<uint8_t> mem1,mem2;
    uint8_t* dense(uint32_t a){
        if(a>=0x80000000u&&uint64_t(a)-0x80000000u<mem1.size())return mem1.data()+a-0x80000000u;
        if(a>=0x90000000u&&uint64_t(a)-0x90000000u<mem2.size())return mem2.data()+a-0x90000000u;
        return nullptr;
    }
    uint8_t* get_ptr(uint32_t a){if(auto* p=dense(a))return p;return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){
        if(auto i=words.find(a);i!=words.end())return i->second;
        if(mem1.empty())return words.at(a);
        uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;
    }
    uint8_t read8(uint32_t a){
        if(auto i=words.find(a&~3u);i!=words.end())return uint8_t(i->second>>(24u-8u*(a&3u)));
        if(auto* p=dense(a))return *p;
        return uint8_t(words.at(a&~3u)>>(24u-8u*(a&3u)));
    }
    uint16_t read16(uint32_t a){return uint16_t((uint16_t(read8(a))<<8)|read8(a+1u));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};uint64_t inst_count=100;
    uint32_t pc=Resume,lr=H+0x2000u,ctr=17,xer=0x80000000u,msr=0x8032u,dispatch_saved_ctx=0,srr0=Resume,srr1=0x8032u;
    bool is_running=true,in_callback=false,dec_irq_pending=true;
    uint32_t dec_value=300;uint64_t dec_written_tb=50;
    uint64_t read_timebase()const{return 0x100000020ull;}
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
    uint32_t fixture_stack=0x8000b000u;
#ifdef UNDERCOVER_V1230_PRIVATE_ACK_IPC
    const bool ipc_fixture=mode.find("-ipc-valid")!=std::string_view::npos;
    std::unique_ptr<NativeIosTransport> ipc_transport;
    std::unique_ptr<NativeIosBinding> ipc_binding;
    if(ipc_fixture){
        using W=IpcClientWitness;
        c.mmu.mem1.resize(WiiPhysicalRam::MEM1_SIZE);
        c.mmu.mem2.resize(WiiPhysicalRam::MEM2_SIZE);
        ipc_transport=std::make_unique<NativeIosTransport>(c.mmu.mem1,c.mmu.mem2,cause,mask);
        ipc_binding=std::make_unique<NativeIosBinding>(*ipc_transport);
        fixture_stack=W::Stack;c.lr=W::Call;
    }
#endif
    c.gpr[1]=fixture_stack;c.gpr[3]=Base;
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
    const bool epilogue=v958::held_epilogue_enabled();
    if(epilogue){c.gpr[13]=0x80039000u;c.gpr[21]=v958::context;}
#ifdef UNDERCOVER_V1230_PRIVATE_ACK_IPC
    if(ipc_fixture)c.gpr[13]=IpcClientWitness::Sda;
#endif
    const auto interrupted_gp=c.gpr;const auto interrupted_lr=c.lr,interrupted_ctr=c.ctr,interrupted_xer=c.xer;
#endif
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
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    std::array<uint32_t,32> incoming_handler{};
    const bool handler_return=v958::third_postalarm_handler_return_enabled();
    if(handler_return){
        c.gpr[1]+=128u;c.lr=v1145::expected.caller;incoming_handler=c.gpr;
    }
#endif
    scheduler.advance(++tick);need(old.after_return_at(tick));
    need(v958::start(c,frame)&&SiBinding::handoff_second_ack(cause,mask,tick));
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    // Synthetic prologue effects only, not runtime patches.
    if(handler_return)c.gpr[1]-=128u;
#endif
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
            constexpr uint32_t Site=H+36;
            c.mmu.words[H+28]=v958::third_alarm_suffix[1].word;
            c.mmu.words[H+32]=v958::third_alarm_suffix[2].word;
            c.mmu.words[Site]=bl(Site,A);c.mmu.words[Site+4]=Nop;
            c.mmu.words[A]=bl(A,D);c.mmu.words[A+4]=Nop;c.mmu.words[A+8]=bl(A+8,Q);c.mmu.words[A+12]=Nop;c.mmu.words[A+16]=Blr;
            c.mmu.words[D]=Mtmsr;c.mmu.words[D+4]=Blr;c.mmu.words[Q]=Mtmsr;c.mmu.words[Q+4]=Blr;
            c.mmu.words[Head]=c.mmu.words[Tail]=0;for(unsigned i=0;i<10;++i)c.mmu.words[Node+4*i]=0;
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
            if(mode.starts_with("error-abi-live-alarm-callback")){
                c.mmu.words[Site+8]=0x4e800421u;
                for(unsigned i=0;i<v958::third_postalarm_prefix.size();++i)c.mmu.words[v958::transfer_callback+4u*i]=v958::third_postalarm_prefix[i];
                for(unsigned i=0;i<v958::third_postalarm_save.size();++i)c.mmu.words[v958::third_postalarm_save_root+4u*i]=v958::third_postalarm_save[i];
                const uint32_t Stack=fixture_stack;
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
            if(v958::third_alarm_suffix[1].word==Nop){
                visit(H+28,Nop);visit(H+32,Nop);
            }else{
                visit(H+28,Rd);
                if(mode!="error-abi-live-alarm-missing"){
                    auto status_read=SiBinding::read32(Base+S);need(status_read.has_value());c.gpr[4]=*status_read;
                }
                if(mode=="error-abi-live-alarm-value")c.gpr[4]^=1u;
                visit(H+32,Wr);
                need(SiBinding::write32(Base+S,c.gpr[4]));
            }
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
                need(c.gpr[1]==fixture_stack);c.gpr[3]=2u;c.ctr=v958::transfer_callback;
                if(mode=="error-abi-live-alarm-callback-word")c.mmu.words[Site+8]^=1u;
            }
#endif
            visit(Site+4,Nop); // production observer owns terminal result
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
            if(callback_mode){
                constexpr uint32_t Root=v958::transfer_callback,Leaf=v958::third_postalarm_save_root;
                const uint32_t Stack=fixture_stack;
                if(mode=="error-abi-live-alarm-callback-frame")c.mmu.words[v958::context+124]^=1u;
                if(mode=="error-abi-live-alarm-callback-target")c.ctr=Leaf;
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
                // Synthetic save slots for the four extra compiler loads;
                // the smaller existing prefix fixture saves only r30/r31.
                if(mode.find("-suffix-return")!=std::string_view::npos)
                    for(unsigned i=26;i<30;++i)c.mmu.words[Stack-4u*(32u-i)]=c.gpr[i];
#endif
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
                if(v958::third_postalarm_handler_enabled())c.gpr[20]=2u;
#endif
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
                visit(Leaf+8,Blr);
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
                if(mode.starts_with("error-abi-live-alarm-callback-time")){
                    const auto fault=mode.substr(std::string_view("error-abi-live-alarm-callback-time").size());
                    auto put=[&](uint32_t base,const auto& words){for(auto word:words){c.mmu.words[base]=word;base+=4;}};
                    put(Root+20,v813::continuation);put(v813::T,v813::system_words);
                    put(v813::D,v813::disable);put(v813::U,v813::timebase);put(v813::R,v813::restore);
                    if(fault!="-offset"){c.mmu.words[v813::Offset]=0;c.mmu.words[v813::Offset+4]=0x1234u;}
                    visit(Root+20,Nop);
                    need(v958::third_postalarm.stage()==4u&&v958::third_postalarm.time_witness()->visits()==1u&&v958::next_device.held_now());
                    if(fault=="-frame")c.mmu.words[v958::context+124]^=1u;
                    if(fault=="-tick")scheduler.advance(++tick);
                    if(fault=="-device")mask=0;
                    if(fault=="-word")c.mmu.words[Root+24]^=4u;
                    visit(Root+24,v813::continuation[1]);
                    c.pc=v813::T;c.lr=Root+28;v958::observe(fault=="-entry"?v813::D:c.pc,c);
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
                                    if(j==3&&fault!="-poll")v958::poll(c);
                                }else if(j==0){c.gpr[6]=c.msr;c.gpr[3]=0;}
                            }
                        }
                        if(i==5)c.gpr[3]=0;
                        if(i==23){c.gpr[3]=1;c.gpr[4]=fault=="-result"?0x1255u:0x1254u;c.lr=Root+28;}
                    }
                    if(fault=="-changed-offset")c.mmu.words[v813::Offset+4]^=1u;
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
                    if(fault.starts_with("-frontier")){
                        for(const auto& row:v831::words)c.mmu.words[row.pc]=row.word;
                        if(fault=="-frontier-identity")c.mmu.words[Root+36]^=1u;
                        visit(Root+28,v813::continuation.back());
                        need(v958::third_postalarm.stage()==6u&&v958::third_postalarm.frontier_witness()->visits()==1u);
                        if(fault=="-frontier-frame")c.mmu.words[v958::context+124]^=1u;
                        if(fault=="-frontier-tick")scheduler.advance(++tick);
                        if(fault=="-frontier-device")mask=0;
                        if(fault=="-frontier-entry")v958::observe(Root+32,c);
                        if(fault=="-frontier-poll")v958::poll(c);
                        visit(Root+32,v831::words[1].word);
                        c.gpr[3]=fault=="-frontier-channel"?1u:2u;c.gpr[4]=0u;
                        visit(Root+36,v831::words[2].word);
                        if(fault!="-frontier-store")c.mmu.words[c.gpr[1]+8u]=0;
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
                        if(fault.starts_with("-frontier-wireless")){
                            const auto wf=fault.substr(std::string_view("-frontier-wireless").size());
                            put(v847::A,v847::setter);put(v847::B,v847::getter);put(v847::U,v847::unlock);
                            put(v847::D,v847::disable);put(v847::R,v847::restore);
                            c.mmu.words[v847::L]=Nop;c.mmu.words[Root+44u]=Nop;c.mmu.words[Root+96u]=Nop;
                            for(unsigned i=0;i<20u;++i)c.mmu.words[v847::SRAM+4u*i]=0;
                            c.mmu.words[v847::SRAM+64u]=64u;c.mmu.words[v847::SRAM+76u]=1u;
#ifdef UNDERCOVER_V1199_TEST_SRAM
                            if(wf=="-pattern"||wf=="-zero-profile"){
                                const auto& data=wf=="-pattern"?v1199_test::pattern:v1199_test::zero;
                                for(unsigned i=0;i<64u;i+=4u){
                                    uint32_t word=0;for(unsigned j=0;j<4u;++j)word=(word<<8)|data[i+j];
                                    c.mmu.words[v847::SRAM+i]=word;
                                }
                            }
#endif
                            if(wf=="-changed")c.mmu.words[v847::SRAM+52u]=0x01000100u;
                            if(wf=="-identity")c.mmu.words[v847::A]^=1u;
                            visit(Root+40,v831::words[3].word);
                            need(v958::third_postalarm.stage()==8u&&v958::third_postalarm.wireless_witness()&&!v958::third_postalarm.wireless_witness()->changed());
                            c.pc=v847::A;c.lr=Root+44u;
                            v958::observe(wf=="-entry"?v847::B:c.pc,c);
                            if(wf=="-frame")c.mmu.words[v958::context+124]^=1u;
                            if(wf=="-tick")scheduler.advance(++tick);
                            if(wf=="-device")mask=0;
                            if(wf=="-poll")v958::poll(c);
                            visit(v847::A,v847::setter[0]);
                            c.gpr[3]=0;c.gpr[4]=20;c.gpr[5]=v847::SRAM;c.mmu.words[v847::SRAM+72u]=1u;
                            c.pc=v847::U;c.lr=v847::A+4u;v958::observe(c.pc,c);
                            visit(v847::U,v847::unlock[0]);c.pc=v847::D;c.lr=v847::U+4u;v958::observe(c.pc,c);
                            visit(v847::D,Blr);c.gpr[4]=0;visit(v847::U+4u,v847::unlock[1]);
                            c.mmu.words[v847::SRAM+72u]=wf=="-store"?1u:0u;
                            visit(v847::U+8u,v847::unlock[2]);c.pc=v847::R;c.lr=v847::U+12u;v958::observe(c.pc,c);
                            visit(v847::R,Blr);visit(v847::U+12u,Nop);c.lr=v847::A+4u;
                            visit(v847::U+16u,Blr);visit(v847::A+4u,Nop);c.lr=Root+44u;
                            if(wf=="-abi")c.gpr[31]^=1u;
                            visit(v847::A+8u,Blr);
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
                            if(wf.starts_with("-suffix")){
                                const auto sf=wf.substr(std::string_view("-suffix").size());
                                for(const auto& row:v1123::rows)c.mmu.words[row.pc]=row.word;
                                if(sf=="-identity")c.mmu.words[Root+52u]^=1u;
                                visit(Root+44u,Nop);
                                need(v958::third_postalarm.stage()==10u&&v958::third_postalarm.callback_suffix_witness()->visits()==1u);
                                if(sf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                if(sf=="-tick")scheduler.advance(++tick);
                                if(sf=="-device")mask=0;
                                if(sf=="-entry")v958::observe(Root+48u,c);
                                if(sf=="-early-poll")v958::poll(c);
                                c.gpr[4]=0x12345678u;
                                visit(Root+48u,v1123::rows[1].word);
                                if(sf!="-store")c.mmu.words[c.gpr[1]+8u]=c.gpr[4];
                                c.cr[0].eq=false;visit(Root+52u,v1123::rows[2].word);
                                if(sf!="-missing-poll")v958::poll(c);
                                if(sf=="-double-poll")v958::poll(c);
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
                                if(sf.starts_with("-return")){
                                    const auto rf=sf.substr(std::string_view("-return").size());
                                    const auto e=v1132::expected;
                                    put(e.root,e.restore);put(e.call+4u,e.tail);
                                    c.mmu.words[e.caller]=e.caller_word;
                                    if(rf=="-identity")c.mmu.words[e.root]^=1u;
                                    c.gpr[30]^=0x55u;c.gpr[31]^=0xaau;c.gpr[11]=Stack;
                                    visit(e.call,v1123::rows[3].word);
                                    need(v958::third_postalarm.stage()==12u);
                                    c.pc=e.root;c.lr=e.call+4u;
                                    v958::observe(rf=="-entry"?e.root+4u:e.root,c);
                                    if(rf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                    if(rf=="-tick")scheduler.advance(++tick);
                                    if(rf=="-device")mask=0;
                                    if(rf=="-slot")c.mmu.words[Stack-24u]^=1u;
                                    for(unsigned i=0;i<6;++i){
                                        visit(e.root+4u*i,e.restore[i]);
                                        c.gpr[26+i]=c.mmu.words[Stack-24u+4u*i];
                                    }
                                    visit(e.root+24u,Blr);
                                    visit(e.call+4u,e.tail[0]);c.gpr[0]=c.mmu.words[Stack+4u];
                                    visit(e.call+8u,e.tail[1]);c.lr=c.gpr[0];
                                    visit(e.call+12u,e.tail[2]);c.gpr[1]+=64u;
                                    visit(e.call+16u,Blr);c.pc=e.caller;
                                    if(rf!="-poll")v958::poll(c);
                                    if(rf=="-double-poll")v958::poll(c);
                                    if(rf!="-dispatch"){
                                        scheduler.advance(++tick);v958::postalarm_dispatch_resume(c,e.caller,e.caller_word);
                                    }
                                    if(rf=="-abi")c.gpr[31]^=1u;
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
                                    if(rf.starts_with("-handler")){
                                        const auto hf=rf.substr(std::string_view("-handler").size());
                                        for(auto row:v1139::rows)c.mmu.words[row.pc]=row.word;
                                        const uint32_t datum=hf=="-not-taken"?9u:7u;
                                        for(unsigned i=0;i<4;++i)c.mmu.words[v1139::Table+4u*i]=i==2u?datum:13u;
                                        if(hf=="-identity")c.mmu.words[v1139::A+44u]^=1u;
                                        visit(e.caller,e.caller_word);
                                        need(v958::third_postalarm.stage()==14u&&v958::third_postalarm.handler_witness()->visits()==1u);
                                        if(hf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                        if(hf=="-tick")scheduler.advance(++tick);
                                        if(hf=="-poll")v958::poll(c);
                                        if(hf=="-entry")v958::observe(v1139::rd,c);
                                        c.gpr[3]=Base;
                                        if(hf=="-address")c.gpr[3]+=4u;
                                        visit(v1139::rd,v1139::Rd);
                                        if(hf!="-missing-read"){
                                            const auto got=SiBinding::read32(Base+S);need(got.has_value());
                                            c.gpr[4]=*got^(hf=="-load-value"?1u:0u);
                                        }
                                        visit(v1139::wr,v1139::Wr);
                                        if(hf!="-missing-write")need(SiBinding::write32(Base+S,c.gpr[4]));
                                        visit(v1139::A+12u,Nop);
                                        for(unsigned i=4;i<11;++i)visit(v1139::A+4u*i,Nop);
                                        c.gpr[3]=v1139::Table;c.gpr[4]=8u;visit(v1139::A+44u,v1139::Indexed);
                                        c.gpr[5]=datum;visit(v1139::A+48u,v1139::Compare);
                                        c.cr[0]={false,datum>7u,datum==7u,false};
                                        if(hf=="-branch")c.cr[0].eq=!c.cr[0].eq;
                                        visit(v1139::A+52u,v1139::Branch);
                                        if(datum!=7u)visit(v1139::A+56u,v1139::rows[14].word);
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
                                        if(handler_return){
                                            need(hf.starts_with("-return"));
                                            const auto ff=hf.substr(std::string_view("-return").size());
                                            const auto& e2=v1145::expected;
                                            for(unsigned i=0;i<e2.restore.size();++i)c.mmu.words[e2.root+4u*i]=e2.restore[i];
                                            for(unsigned i=0;i<e2.tail.size();++i)c.mmu.words[e2.call+4u+4u*i]=e2.tail[i];
                                            c.mmu.words[e2.caller]=e2.caller_word;
                                            for(unsigned i=17;i<32;++i)c.mmu.words[incoming_handler[1]-4u*(32u-i)]=incoming_handler[i];
                                            c.mmu.words[incoming_handler[1]+4u]=e2.caller;
                                            c.gpr[11]=incoming_handler[1];
                                            if(ff=="-identity")c.mmu.words[e2.root]^=1u;
                                            visit(e2.call,v1139::rows[15].word);
                                            c.pc=e2.root;c.lr=e2.call+4u;
                                            v958::observe(ff=="-entry"?e2.root+4u:e2.root,c);
                                            if(ff=="-frame")c.mmu.words[v958::context+124]^=1u;
                                            if(ff=="-tick")scheduler.advance(++tick);
                                            if(ff=="-device")mask=0;
                                            if(ff=="-slot")c.mmu.words[incoming_handler[1]-60u]^=1u;
                                            for(unsigned i=0;i<15;++i){
                                                visit(e2.root+4u*i,e2.restore[i]);c.gpr[17u+i]=incoming_handler[17u+i];
                                            }
                                            visit(e2.root+60u,e2.restore.back());
                                            visit(e2.call+4u,e2.tail[0]);c.gpr[0]=e2.caller;
                                            visit(e2.call+8u,e2.tail[1]);c.lr=e2.caller;
                                            visit(e2.call+12u,e2.tail[2]);c.gpr[1]=incoming_handler[1];
                                            visit(e2.call+16u,e2.tail[3]);c.pc=e2.caller;
                                            if(ff!="-poll")v958::poll(c);
                                            if(ff=="-double-poll")v958::poll(c);
                                            if(ff!="-dispatch"){
                                                scheduler.advance(++tick);v958::postalarm_handler_dispatch_resume(c,e2.caller,e2.caller_word);
                                            }
                                            if(ff=="-abi")c.gpr[31]^=1u;
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
                                            if(epilogue){
                                                namespace q=v1151;
                                                c.mmu.words[c.gpr[13]+4]=2;c.mmu.words[c.gpr[13]+8]=0;
                                                for(unsigned i=0;i<8;++i)c.mmu.words[v958::context+0x1a4u+4*i]=0;
                                                c.mmu.words[v958::context+0x1a0u]=0;
                                                c.mmu.words[q::En]=q::branch(q::En,q::Di)|1u;
                                                c.mmu.words[q::En+4]=q::branch(q::En+4,q::Rs)|1u;c.mmu.words[q::En+8]=Blr;
                                                c.mmu.words[q::Di]=Blr;c.mmu.words[q::Rs]=Blr;c.mmu.words[q::Re]=Blr;
                                                c.mmu.words[q::Dest+4]=q::branch(q::Dest+4,q::Re)|1u;
                                                c.mmu.words[q::Dest+8]=Nop;c.mmu.words[q::Dest+12]=q::branch(q::Dest+12,q::Lo)|1u;
                                                c.mmu.words[q::Lo]=q::Rfi;c.mmu.words[ExternalVector]=Nop;c.mmu.words[ExternalVector+4]=q::Rfi;
                                                c.mmu.words[q::T]=Nop;c.mmu.words[q::T+4]=q::tramp[1];c.mmu.words[q::D]=Nop;
                                            }
#endif
                                            visit(e2.caller,e2.caller_word);
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
                                            if(epilogue){
                                                need(ff.starts_with("-epilogue"));
                                                const auto ef=ff.substr(std::string_view("-epilogue").size());
                                                namespace q=v1151;
                                                need(v958::held_epilogue.stage()==1u);
                                                auto ent=[&](uint32_t pc,uint32_t link){c.pc=pc;c.lr=link;v958::observe(pc,c);};
                                                ent(ef=="-entry"?q::Di:q::En,q::Dest+4);
                                                if(ef=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                if(ef=="-tick")scheduler.advance(++tick);
                                                visit(q::En,q::branch(q::En,q::Di)|1u);
                                                ent(q::Di,q::En+4);visit(q::Di,Blr);
                                                visit(q::En+4,q::branch(q::En+4,q::Rs)|1u);
                                                ent(q::Rs,q::En+8);visit(q::Rs,Blr);
                                                c.lr=q::Dest+4;c.gpr[3]=2;c.mmu.words[c.gpr[13]+4]=1;
                                                visit(q::En+8,Blr);visit(q::Dest+4,q::branch(q::Dest+4,q::Re)|1u);
                                                ent(q::Re,q::Dest+8);visit(q::Re,Blr);
                                                visit(q::Dest+8,Nop);c.gpr[3]=v958::context;
                                                visit(q::Dest+12,q::branch(q::Dest+12,q::Lo)|1u);ent(q::Lo,q::Dest+16);
                                                c.gpr=interrupted_gp;c.lr=interrupted_lr;c.ctr=interrupted_ctr;c.xer=interrupted_xer;
                                                c.cr.fill({});c.srr0=Resume;c.srr1=0x8032u;
                                                visit(q::Lo,q::Rfi);c.pc=Resume;c.msr=c.srr1;
                                                if(ef=="-gqr")c.gqr[0]^=1u;
                                                if(ef=="-image")c.mmu.words[ExternalVector]^=1u;
                                                need(v958::poll(c)&&c.pc==ExternalVector);
                                                if(ef!="-outer-poll")need(!v958::poll(c));
                                                scheduler.advance(++tick);v958::observe(ExternalVector,c);
                                                visit(ExternalVector,Nop);
                                                for(unsigned i=3;i<=5;++i)c.mmu.words[v958::context+4*i]=interrupted_gp[i];
                                                c.srr0=q::T;c.srr1=0x32u;visit(ExternalVector+4,q::Rfi);
                                                c.pc=q::T;c.msr=c.srr1;c.gpr[3]=4;c.gpr[4]=v958::context;
                                                need(!v958::poll(c));scheduler.advance(++tick);v958::observe(q::T,c);
                                                visit(q::T,Nop);visit(q::T+4,q::tramp[1]);
                                                for(unsigned i=0;i<32;++i)c.mmu.words[v958::context+4*i]=interrupted_gp[i];
                                                c.pc=q::D;need(!v958::poll(c));scheduler.advance(++tick);
                                                if(ef=="-saved")c.mmu.words[v958::context+124]^=1u;
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
                                                if(v958::held_dispatch_enabled()){
                                                    need(ef.starts_with("-dispatch"));
                                                    const auto df=ef.substr(std::string_view("-dispatch").size());
                                                    const auto& e3=v1158::expected;
                                                    constexpr uint32_t Handler=SiDispatchWitness::Handler;
                                                    for(auto edge:e3.edges){
                                                        c.mmu.words[edge.pc]=edge.entry_word;c.mmu.words[edge.lr-4u]=edge.branch_word;
                                                    }
                                                    c.mmu.words[e3.indirect_pc]=e3.indirect_word;c.mmu.words[Handler]=e3.handler_word;
                                                    c.mmu.words[0x80003090u]=Handler;c.mmu.words[0x800000d4u]=v958::context;c.mmu.words[0x800000e4u]=v958::context;
                                                    if(df=="-owner")c.mmu.words[0x80003090u]^=4u;
                                                    SecondSiDispatchWitness busy(e3);
                                                    if(df=="-busy")second_dispatch_mmio=&busy;
                                                    v958::observe(q::D,c);
                                                    need(v958::held_epilogue.stage()==6u&&second_dispatch_mmio==v958::held_epilogue.dispatch_witness());
                                                    if(df=="-tick")scheduler.advance(++tick);
                                                    if(df=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                    if(df=="-trace")second_dispatch_mmio=nullptr;
                                                    visit(q::D,Nop,df=="-guard");
                                                    record_second_dispatch_pi(false,0x0c003000u,32,cause.load()^(df=="-value"?SI:0),false);
                                                    if(df!="-missing")record_second_dispatch_pi(false,0x0c003004u,32,mask.load(),false);
                                                    if(df=="-duplicate")record_second_dispatch_pi(false,0x0c003000u,32,cause.load(),false);
                                                    for(unsigned i=0;i<4;++i){
                                                        const auto edge=e3.edges[i];
                                                        visit(edge.lr-4u,edge.branch_word);
                                                        c.pc=edge.pc;c.lr=edge.lr;v958::observe(df=="-entry"&&i==0?edge.pc+4u:edge.pc,c);
                                                        visit(edge.pc,edge.entry_word);need(!v958::poll(c));
                                                    }
                                                    visit(e3.indirect_pc,e3.indirect_word);
                                                    c.pc=Handler;c.ctr=Handler;c.lr=e3.indirect_pc+4u;c.gpr[3]=df=="-handler"?19u:20u;c.gpr[4]=v958::context;
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
                                                    if(v958::third_ack_enabled()){
                                                        need(df.starts_with("-ack"));
                                                        const auto af=df.substr(std::string_view("-ack").size());
                                                        namespace q3=v1167;
                                                        c.mmu.words[Handler+4]=q3::CallHelper;c.mmu.words[Handler+8]=Nop;c.mmu.words[Handler+12]=Blr;
                                                        c.mmu.words[q3::Save]=Blr;c.mmu.words[q3::Helper]=Nop;
                                                        c.mmu.words[q3::Helper+4]=Load;c.mmu.words[q3::Helper+8]=Nop;
                                                        c.mmu.words[q3::Helper+12]=Store;c.mmu.words[q3::Helper+16]=Nop;c.mmu.words[q3::Helper+20]=Blr;
#ifdef UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN
                                                        const auto held_handler_incoming=c.gpr;
#endif
                                                        v958::observe(Handler,c);
                                                        need(v958::third_ack_active()&&v958::next_device.stage()==3u&&v958::ack.stage()==5u);
                                                        if(af=="-unarmed")SiBinding::read32(Base+C);
                                                        if(af=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                        if(af=="-tick")scheduler.advance(++tick);
                                                        visit(Handler,q3::CallSave,af=="-guard");
                                                        c.pc=q3::Save;c.lr=Handler+4;v958::observe(af=="-entry"?q3::Save+4:q3::Save,c);
                                                        visit(q3::Save,Blr);visit(Handler+4,q3::CallHelper);
                                                        c.pc=q3::Helper;c.lr=Handler+8;v958::observe(q3::Helper,c);
                                                        visit(q3::Helper,Nop);c.gpr[3]=af=="-mirror"?Mirror:Base;
                                                        visit(q3::Helper+4,Load);
                                                        if(af=="-width")SiBinding::check(Base+C,2u,true);
                                                        auto val=SiBinding::read32(c.gpr[3]+(af=="-offset"?S:C));need(val.has_value());
                                                        c.gpr[4]=*val^(af=="-value"?1u:0u);
                                                        visit(q3::Helper+8,Nop);
                                                        if(af=="-w1c")c.gpr[4]&=~SiController::TC_INT;
                                                        visit(q3::Helper+12,Store);
                                                        need(SiBinding::write32(c.gpr[3]+C,c.gpr[4]^(af=="-write"?2u:0u)));
                                                        need(cause==Other&&ctl.issued_tokens()==3u&&scheduler.completed()==3u);
                                                        if(af=="-post-frame")c.mmu.words[v958::context+124]^=1u;
                                                        visit(q3::Helper+16,Nop);
#ifdef UNDERCOVER_V1175_PRIVATE_ACK_HELPER
                                                        if(v958::ack_helper_enabled()){
                                                            need(af.starts_with("-helper"));
                                                            const auto hf=af.substr(std::string_view("-helper").size());
                                                            namespace q4=v1175;
                                                            need(v958::held_epilogue.stage()==10u&&v958::held_epilogue.helper_visits()==0u);
                                                            for(const auto& row:q4::labels)c.mmu.words[row.pc]=row.word;
                                                            if(hf=="-tick")scheduler.advance(++tick);
                                                            if(hf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                            if(hf=="-bus")SiBinding::write32(Base+C,*val);
                                                            if(hf=="-word")c.mmu.words[q3::Helper+20]^=4u;
                                                            visit(q3::Helper+20,q4::link(q3::Helper+20,q4::Nested),hf=="-guard");
                                                            c.pc=q4::Nested;c.lr=q3::Helper+24;v958::observe(c.pc,c);
                                                            visit(q4::Nested,q4::link(q4::Nested,q4::Disable));
                                                            c.pc=q4::Disable;c.lr=q4::Nested+4;v958::observe(hf=="-entry"?q4::Time:c.pc,c);
                                                            c.gpr[3]=c.msr^(hf=="-msr"?0x8000u:0u);
                                                            visit(q4::Disable,Mtmsr);visit(q4::Disable+4,Blr);
                                                            visit(q4::Nested+4,q4::link(q4::Nested+4,q4::Time));
                                                            c.pc=q4::Time;c.lr=q4::Nested+8;v958::observe(c.pc,c);
                                                            visit(q4::Time,Nop);need(!v958::poll(c));visit(q4::Time+4,Blr);
                                                            visit(q4::Nested+8,q4::link(q4::Nested+8,q4::Restore));
                                                            c.pc=q4::Restore;c.lr=q4::Nested+12;v958::observe(c.pc,c);
                                                            c.gpr[3]=c.msr;visit(q4::Restore,Mtmsr);visit(q4::Restore+4,Blr);
                                                            // Verify the inner LR before modeling the native LR restore.
                                                            visit(q4::Nested+12,Nop);c.lr=q3::Helper+24;visit(q4::Nested+16,Blr);
                                                            visit(q3::Helper+24,Nop);c.lr=Handler+8;visit(q3::Helper+28,Blr);
                                                            if(hf=="-abi")c.gpr[31]^=1u;
                                                            visit(Handler+8,Nop);
                                                            if(v958::ack_callback_enabled()){
                                                                need(hf.starts_with("-callback"));
                                                                const auto cf=hf.substr(std::string_view("-callback").size());
                                                                need(v958::held_epilogue.stage()==12u);
                                                                for(unsigned i=0;i<q4::callback_words.size();++i)
                                                                    c.mmu.words[v958::transfer_callback+4u*i]=q4::callback_words[i];
                                                                c.ctr=v958::transfer_callback+(cf=="-target"?4u:cf=="-unaligned"?1u:0u);
                                                                c.gpr[3]=cf=="-channel"?4u:2u;
#ifdef UNDERCOVER_V1210_PRIVATE_ACK_HANDLER
                                                                // Model the handler's channel selection before the indirect
                                                                // callback captures its ABI. RFI restored the old r20.
                                                                if(v958::ack_handler_enabled())c.gpr[20]=2u;
#ifdef UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN
                                                                if(v958::ack_handler_return_enabled())c.gpr[1]=held_handler_incoming[1]-128u;
#endif
#endif
                                                                if(cf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                if(cf=="-word")c.mmu.words[v958::transfer_callback+4u]^=1u;
                                                                if(cf=="-siteword")c.mmu.words[q4::callback_sites[0]]^=1u;
                                                                if(cf=="-tick")scheduler.advance(++tick);
                                                                if(cf=="-bus")SiBinding::write32(Base+C,*val);
#ifdef UNDERCOVER_V1184_PRIVATE_ACK_PREFIX
                                                                const bool prefix_mode=v958::ack_prefix_enabled();
                                                                const auto pf=cf.starts_with("-prefix")?cf.substr(std::string_view("-prefix").size()):std::string_view{};
                                                                constexpr uint32_t Root2=v958::transfer_callback,Leaf2=v958::third_postalarm_save_root;
                                                                const uint32_t stack=c.gpr[1];
                                                                if(prefix_mode){
                                                                    need(cf.starts_with("-prefix"));
                                                                    for(uint32_t a=stack-0x400u;a<stack+0x100u;a+=4u)c.mmu.words[a]=a^0xbadc0deu;
                                                                    for(unsigned i=0;i<v958::third_postalarm_save.size();++i)c.mmu.words[Leaf2+4u*i]=v958::third_postalarm_save[i];
                                                                    if(pf=="-identity")c.mmu.words[Leaf2]^=1u;
                                                                }
#endif
                                                                visit(q4::callback_sites[0],0x4e800421u,cf!="-guard");
#ifdef UNDERCOVER_V1184_PRIVATE_ACK_PREFIX
                                                                if(prefix_mode){
                                                                    need(v958::held_epilogue.stage()==14u);
                                                                    c.pc=Root2;c.lr=q4::callback_sites[0]+4u;
                                                                    if(pf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                    if(pf=="-bus")SiBinding::write32(Base+C,*val);
                                                                    if(pf=="-tick")scheduler.advance(++tick);
                                                                    if(pf!="-poll")need(!v958::poll(c));
                                                                    if(pf=="-double-poll")v958::poll(c);
                                                                    scheduler.advance(++tick);v958::observe(Root2,c);
                                                                    visit(Root2,v958::third_postalarm_prefix[0],pf=="-guard");
                                                                    c.gpr[1]=stack-64u;c.mmu.words[stack-64u]=stack;
                                                                    if(pf=="-stack")c.mmu.words[stack-64u]^=1u;
                                                                    visit(Root2+4u,v958::third_postalarm_prefix[1]);c.gpr[0]=c.lr;
                                                                    visit(Root2+8u,v958::third_postalarm_prefix[2]);c.mmu.words[stack+4u]=c.gpr[0];
                                                                    visit(Root2+12u,v958::third_postalarm_prefix[3]);c.gpr[11]=stack;
                                                                    visit(Root2+16u,v958::third_postalarm_prefix[4]);c.pc=Leaf2;c.lr=Root2+20u;
                                                                    v958::observe(pf=="-entry"?Leaf2+4u:Leaf2,c);
                                                                    visit(Leaf2,v958::third_postalarm_save[0]);c.mmu.words[stack-8u]=c.gpr[30];
                                                                    visit(Leaf2+4u,v958::third_postalarm_save[1]);c.mmu.words[stack-4u]=c.gpr[31];
                                                                    visit(Leaf2+8u,Blr);
                                                                    if(pf=="-slot")c.mmu.words[stack-8u]^=1u;
#ifdef UNDERCOVER_V1189_PRIVATE_ACK_TIME
                                                                    const bool time_mode=v958::ack_time_enabled();
                                                                    const auto tf=pf.starts_with("-time")?pf.substr(std::string_view("-time").size()):std::string_view{};
                                                                    if(time_mode){
                                                                        need(pf.starts_with("-time"));
                                                                        auto put2=[&](uint32_t base,const auto& ws){for(auto word:ws){c.mmu.words[base]=word;base+=4;}};
                                                                        put2(Root2+20u,v813::continuation);put2(v813::T,v813::system_words);
                                                                        put2(v813::D,v813::disable);put2(v813::U,v813::timebase);put2(v813::R,v813::restore);
                                                                        c.mmu.words[v813::Offset]=0;c.mmu.words[v813::Offset+4u]=0x1234u;
                                                                        if(tf=="-identity")c.mmu.words[Root2+24u]^=4u;
                                                                    }
#endif
                                                                    visit(Root2+20u,v958::third_postalarm_prefix[5]);
#ifdef UNDERCOVER_V1189_PRIVATE_ACK_TIME
                                                                    if(time_mode){
                                                                        need(v958::held_epilogue.stage()==16u&&v958::ack_time.visits()==1u);
                                                                        if(tf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                        if(tf=="-tick")scheduler.advance(++tick);
                                                                        if(tf=="-device")mask=0;
                                                                        if(tf=="-bus")SiBinding::write32(Base+C,*val);
                                                                        visit(Root2+24u,v813::continuation[1],tf=="-guard");
                                                                        c.pc=v813::T;c.lr=Root2+28u;v958::observe(tf=="-entry"?v813::D:c.pc,c);
                                                                        for(unsigned i=0;i<25;++i){
                                                                            const uint32_t pc=v813::T+4u*i;visit(pc,v813::system_words[i]);
                                                                            if(i==1||i==4||i==7){
                                                                                const uint32_t leaf=i==1?v813::D:i==4?v813::U:v813::R;
                                                                                const auto& ws=i==1?v813::disable:i==4?v813::timebase:v813::restore;
                                                                                c.pc=leaf;c.lr=pc+4u;v958::observe(leaf,c);
                                                                                for(unsigned j=0;j<ws.size();++j){
                                                                                    visit(leaf+4u*j,ws[j]);
                                                                                    if(i==4){
                                                                                        if(j==0)c.gpr[3]=uint32_t(c.read_timebase()>>32);
                                                                                        if(j==1)c.gpr[4]=uint32_t(c.read_timebase());
                                                                                        if(j==2)c.gpr[5]=uint32_t(c.read_timebase()>>32);
                                                                                        if(j==3&&tf!="-poll")v958::poll(c);
                                                                                    }else if(j==0){c.gpr[6]=c.msr;c.gpr[3]=0;}
                                                                                }
                                                                            }
                                                                            if(i==5)c.gpr[3]=0;
                                                                            if(i==23){c.gpr[3]=1;c.gpr[4]=tf=="-result"?0x1255u:0x1254u;c.lr=Root2+28u;}
                                                                        }
                                                                        if(tf=="-offset")c.mmu.words[v813::Offset+4u]^=1u;
#ifdef UNDERCOVER_V1193_PRIVATE_ACK_FRONTIER
                                                                        const bool frontier_mode=v958::ack_frontier_enabled();
                                                                        const auto ff=tf.starts_with("-frontier")?tf.substr(std::string_view("-frontier").size()):std::string_view{};
                                                                        if(frontier_mode){
                                                                            need(tf.starts_with("-frontier"));
                                                                            for(auto row:v831::words)c.mmu.words[row.pc]=row.word;
                                                                            if(ff=="-identity")c.mmu.words[Root2+36u]^=1u;
                                                                        }
#endif
                                                                        visit(Root2+28u,v813::continuation.back());
#ifdef UNDERCOVER_V1193_PRIVATE_ACK_FRONTIER
                                                                        if(frontier_mode){
                                                                            need(v958::held_epilogue.stage()==18u&&v958::ack_frontier.visits()==1u);
                                                                            if(ff=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                            if(ff=="-tick")scheduler.advance(++tick);
                                                                            if(ff=="-device")mask=0;
                                                                            if(ff=="-bus")SiBinding::write32(Base+C,*val);
                                                                            if(ff=="-entry")v958::observe(Root2+32u,c);
                                                                            if(ff=="-poll")v958::poll(c);
                                                                            visit(Root2+32u,v831::words[1].word,ff=="-guard");
                                                                            c.gpr[3]=ff=="-channel"?1u:2u;c.gpr[4]=0u;
                                                                            visit(Root2+36u,v831::words[2].word);
                                                                            if(ff!="-store")c.mmu.words[c.gpr[1]+8u]=0;
#ifdef UNDERCOVER_V1197_PRIVATE_ACK_WIRELESS
                                                                            const bool wireless_mode=v958::ack_wireless_enabled();
                                                                            const auto wf2=ff.starts_with("-wireless")?ff.substr(std::string_view("-wireless").size()):std::string_view{};
                                                                            if(wireless_mode){
                                                                                need(ff.starts_with("-wireless"));
                                                                                auto put3=[&](uint32_t base,const auto& ws){for(auto word:ws){c.mmu.words[base]=word;base+=4;}};
                                                                                put3(v847::A,v847::setter);put3(v847::B,v847::getter);put3(v847::U,v847::unlock);
                                                                                put3(v847::D,v847::disable);put3(v847::R,v847::restore);
                                                                                c.mmu.words[v847::L]=Nop;c.mmu.words[Root2+44u]=Nop;c.mmu.words[Root2+96u]=Nop;
                                                                                for(unsigned i=0;i<20u;++i)c.mmu.words[v847::SRAM+4u*i]=0;
                                                                                c.mmu.words[v847::SRAM+64u]=64u;c.mmu.words[v847::SRAM+76u]=1u;
                                                                                if(wf2=="-changed")c.mmu.words[v847::SRAM+52u]=0x01000100u;
                                                                                if(wf2=="-identity")c.mmu.words[v847::A]^=1u;
                                                                            }
#endif
                                                                            visit(Root2+40u,v831::words[3].word);
#ifdef UNDERCOVER_V1197_PRIVATE_ACK_WIRELESS
                                                                            if(wireless_mode){
                                                                                need(v958::held_epilogue.stage()==20u&&!v958::ack_wireless.changed());
                                                                                c.pc=v847::A;c.lr=Root2+44u;v958::observe(wf2=="-entry"?v847::B:c.pc,c);
                                                                                if(wf2=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                                if(wf2=="-tick")scheduler.advance(++tick);
                                                                                if(wf2=="-device")mask=0;
                                                                                if(wf2=="-bus")SiBinding::write32(Base+C,*val);
                                                                                if(wf2=="-poll")v958::poll(c);
                                                                                visit(v847::A,v847::setter[0],wf2=="-guard");
                                                                                c.gpr[3]=0;c.gpr[4]=20;c.gpr[5]=v847::SRAM;c.mmu.words[v847::SRAM+72u]=1u;
                                                                                c.pc=v847::U;c.lr=v847::A+4u;v958::observe(c.pc,c);
                                                                                visit(v847::U,v847::unlock[0]);c.pc=v847::D;c.lr=v847::U+4u;v958::observe(c.pc,c);
                                                                                visit(v847::D,Blr);c.gpr[4]=0;visit(v847::U+4u,v847::unlock[1]);
                                                                                c.mmu.words[v847::SRAM+72u]=wf2=="-store"?1u:0u;
                                                                                visit(v847::U+8u,v847::unlock[2]);c.pc=v847::R;c.lr=v847::U+12u;v958::observe(c.pc,c);
                                                                                visit(v847::R,Blr);visit(v847::U+12u,Nop);c.lr=v847::A+4u;
                                                                                visit(v847::U+16u,Blr);visit(v847::A+4u,Nop);c.lr=Root2+44u;
                                                                                if(wf2=="-abi")c.gpr[31]^=1u;
                                                                                visit(v847::A+8u,Blr);
#ifdef UNDERCOVER_V1201_PRIVATE_ACK_SUFFIX
                                                                                const bool suffix_mode=v958::ack_suffix_enabled();
                                                                                const auto sf2=wf2.starts_with("-suffix")?wf2.substr(std::string_view("-suffix").size()):std::string_view{};
                                                                                if(suffix_mode){
                                                                                    need(wf2.starts_with("-suffix"));
                                                                                    for(const auto& row:v1123::rows)c.mmu.words[row.pc]=row.word;
                                                                                    if(sf2=="-identity")c.mmu.words[Root2+52u]^=1u;
                                                                                }
#endif
                                                                                visit(Root2+44u,Nop);
#ifdef UNDERCOVER_V1201_PRIVATE_ACK_SUFFIX
                                                                                if(suffix_mode){
                                                                                    need(v958::held_epilogue.stage()==22u&&v958::ack_suffix.visits()==1u);
                                                                                    if(sf2=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                                    if(sf2=="-tick")scheduler.advance(++tick);
                                                                                    if(sf2=="-device")mask=0;
                                                                                    if(sf2=="-bus")SiBinding::write32(Base+C,*val);
                                                                                    if(sf2=="-entry")v958::observe(Root2+48u,c);
                                                                                    if(sf2=="-early-poll")v958::poll(c);
                                                                                    c.gpr[4]=0x12345678u;
                                                                                    visit(Root2+48u,v1123::rows[1].word,sf2=="-guard");
                                                                                    if(sf2!="-store")c.mmu.words[c.gpr[1]+8u]=c.gpr[4];
                                                                                    c.cr[0].eq=false;visit(Root2+52u,v1123::rows[2].word);
                                                                                    if(sf2!="-missing-poll")v958::poll(c);
                                                                                    if(sf2=="-double-poll")v958::poll(c);
#ifdef UNDERCOVER_V1205_PRIVATE_ACK_RETURN
                                                                                    const bool return_mode=v958::ack_return_enabled();
                                                                                    const auto rf2=sf2.starts_with("-return")?sf2.substr(std::string_view("-return").size()):std::string_view{};
                                                                                    const auto e2=q4::return_expected;
                                                                                    if(return_mode){
                                                                                        need(sf2.starts_with("-return"));
                                                                                        for(unsigned i=0;i<e2.restore.size();++i)c.mmu.words[e2.root+4u*i]=e2.restore[i];
                                                                                        for(unsigned i=0;i<e2.tail.size();++i)c.mmu.words[e2.call+4u+4u*i]=e2.tail[i];
                                                                                        c.mmu.words[e2.caller]=e2.caller_word;
                                                                                        if(rf2=="-identity")c.mmu.words[e2.root]^=1u;
                                                                                        c.gpr[30]^=0x55u;c.gpr[31]^=0xaau;c.gpr[11]=stack;
                                                                                    }
#endif
                                                                                    visit(Root2+56u,v1123::rows[3].word);
#ifdef UNDERCOVER_V1205_PRIVATE_ACK_RETURN
                                                                                    if(return_mode){
                                                                                        need(v958::held_epilogue.stage()==24u);
                                                                                        c.pc=e2.root;c.lr=e2.call+4u;v958::observe(rf2=="-entry"?e2.root+4u:e2.root,c);
                                                                                        if(rf2=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                                        if(rf2=="-tick")scheduler.advance(++tick);
                                                                                        if(rf2=="-device")mask=0;
                                                                                        if(rf2=="-bus")SiBinding::write32(Base+C,*val);
                                                                                        if(rf2=="-slot")c.mmu.words[stack-8u]^=1u;
                                                                                        visit(e2.root,e2.restore[0],rf2=="-guard");c.gpr[30]=c.mmu.words[stack-8u];
                                                                                        visit(e2.root+4u,e2.restore[1]);c.gpr[31]=c.mmu.words[stack-4u];
                                                                                        visit(e2.root+8u,Blr);
                                                                                        visit(e2.call+4u,e2.tail[0]);c.gpr[0]=c.mmu.words[stack+4u];
                                                                                        visit(e2.call+8u,e2.tail[1]);c.lr=c.gpr[0];
                                                                                        visit(e2.call+12u,e2.tail[2]);c.gpr[1]+=64u;
                                                                                        visit(e2.call+16u,Blr);c.pc=e2.caller;
                                                                                        if(rf2!="-poll")v958::poll(c);
                                                                                        if(rf2=="-double-poll")v958::poll(c);
                                                                                        if(rf2!="-dispatch"){scheduler.advance(++tick);v958::postalarm_dispatch_resume(c,e2.caller,e2.caller_word);}
                                                                                        if(rf2=="-abi")c.gpr[31]^=1u;
#ifdef UNDERCOVER_V1210_PRIVATE_ACK_HANDLER
                                                                                        const bool handler_mode=v958::ack_handler_enabled();
                                                                                        const auto hf2=rf2.starts_with("-handler")?rf2.substr(std::string_view("-handler").size()):std::string_view{};
                                                                                        if(handler_mode){
                                                                                            need(rf2.starts_with("-handler"));
                                                                                            for(auto row:q4::handler_rows)c.mmu.words[row.pc]=row.word;
                                                                                            for(unsigned i=0;i<4;++i)c.mmu.words[q4::handler_index.table[i]]=i==2u?7u:9u;
                                                                                            if(hf2=="-identity")c.mmu.words[e2.caller+44u]^=1u;
                                                                                        }
#endif
                                                                                        visit(e2.caller,e2.caller_word);
#ifdef UNDERCOVER_V1210_PRIVATE_ACK_HANDLER
                                                                                        if(handler_mode){
                                                                                            need(v958::held_epilogue.stage()==26u&&v958::held_epilogue.prefix_handler_visits()==1u);
                                                                                            if(hf2=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                                            if(hf2=="-tick")scheduler.advance(++tick);
                                                                                            if(hf2=="-poll")v958::poll(c);
                                                                                            if(hf2=="-entry")v958::observe(q4::handler_rd,c);
                                                                                            if(hf2=="-bus")SiBinding::write32(Base+C,*val);
                                                                                            c.gpr[3]=Base+(hf2=="-address"?4u:0u);
                                                                                            visit(q4::handler_rd,v1139::Rd,hf2=="-guard");
                                                                                            if(hf2!="-missing-read"){
                                                                                                const auto got=SiBinding::read32(Base+S);need(got.has_value());
                                                                                                c.gpr[4]=*got^(hf2=="-load-value"?1u:0u);
                                                                                            }
                                                                                            visit(q4::handler_wr,v1139::Wr);
                                                                                            if(hf2!="-missing-write")need(SiBinding::write32(Base+S,c.gpr[4]^(hf2=="-write-value"?1u:0u)));
                                                                                            visit(e2.caller+12u,Nop);
                                                                                            for(unsigned i=4;i<11;++i)visit(e2.caller+4u*i,Nop);
                                                                                            c.gpr[3]=q4::handler_index.table[0];c.gpr[4]=8u;visit(e2.caller+44u,v1139::Indexed);
                                                                                            c.gpr[5]=7u;visit(e2.caller+48u,v1139::Compare);
                                                                                            c.cr[0]={false,false,hf2!="-branch",false};visit(e2.caller+52u,v1139::Branch);
#ifdef UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN
                                                                                            const bool hr_mode=v958::ack_handler_return_enabled();
                                                                                            const auto hrf=hf2.starts_with("-return")?hf2.substr(std::string_view("-return").size()):std::string_view{};
                                                                                            const auto hre=q4::handler_return_expected;
                                                                                            const uint32_t hsp=held_handler_incoming[1];
                                                                                            if(hr_mode){
                                                                                                need(hf2.starts_with("-return"));
                                                                                                for(unsigned i=0;i<hre.restore.size();++i)c.mmu.words[hre.root+4u*i]=hre.restore[i];
                                                                                                for(unsigned i=0;i<hre.tail.size();++i)c.mmu.words[hre.call+4u+4u*i]=hre.tail[i];
                                                                                                c.mmu.words[hre.caller]=hre.caller_word;
                                                                                                c.gpr[11]=hsp;
                                                                                                for(unsigned i=17;i<32;++i)c.mmu.words[hsp-4u*(32u-i)]=held_handler_incoming[i];
                                                                                                c.mmu.words[hsp+4u]=hre.caller;
                                                                                                if(hrf=="-identity")c.mmu.words[hre.root]^=1u;
                                                                                            }
#endif
                                                                                            visit(e2.caller+64u,q4::handler_rows.back().word);
#ifdef UNDERCOVER_V1214_PRIVATE_ACK_HANDLER_RETURN
                                                                                            if(hr_mode){
                                                                                                need(v958::held_epilogue.stage()==28u);
                                                                                                c.pc=hre.root;c.lr=hre.call+4u;
                                                                                                v958::observe(hrf=="-entry"?hre.root+4u:hre.root,c);
                                                                                                if(hrf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                                                if(hrf=="-tick")scheduler.advance(++tick);
                                                                                                if(hrf=="-device")mask=0;
                                                                                                if(hrf=="-bus")SiBinding::write32(Base+C,*val);
                                                                                                if(hrf=="-slot")c.mmu.words[hsp-60u]^=1u;
                                                                                                for(unsigned i=0;i<15;++i){
                                                                                                    visit(hre.root+4u*i,hre.restore[i],hrf=="-guard"&&i==0);
                                                                                                    c.gpr[17+i]=c.mmu.words[hsp-60u+4u*i];
                                                                                                }
                                                                                                visit(hre.root+60u,Blr);
                                                                                                visit(hre.call+4u,hre.tail[0]);c.gpr[0]=c.mmu.words[hsp+4u];
                                                                                                visit(hre.call+8u,hre.tail[1]);c.lr=c.gpr[0];
                                                                                                visit(hre.call+12u,hre.tail[2]);c.gpr[1]+=128u;
                                                                                                visit(hre.call+16u,Blr);c.pc=hre.caller;
                                                                                                if(hrf!="-poll")v958::poll(c);
                                                                                                if(hrf=="-double-poll")v958::poll(c);
                                                                                                if(hrf!="-dispatch"){scheduler.advance(++tick);v958::postalarm_handler_dispatch_resume(c,hre.caller,hre.caller_word);}
                                                                                                if(hrf=="-abi")c.gpr[31]^=1u;
#ifdef UNDERCOVER_V1217_PRIVATE_ACK_FINAL
                                                                                                const bool final_mode=v958::ack_final_enabled();
                                                                                                const auto zf=hrf.starts_with("-final")?hrf.substr(std::string_view("-final").size()):std::string_view{};
                                                                                                if(final_mode){
                                                                                                    need(hrf.starts_with("-final"));
                                                                                                    c.mmu.words[c.gpr[13]+4u]=2;c.mmu.words[c.gpr[13]+8u]=0;
                                                                                                    if(zf=="-counter")c.mmu.words[c.gpr[13]+4u]=0;

                                                                                                }
#endif
                                                                                                visit(hre.caller,hre.caller_word);
#ifdef UNDERCOVER_V1217_PRIVATE_ACK_FINAL
                                                                                                if(final_mode){
                                                                                                    need(v958::held_epilogue.stage()==30u);
                                                                                                    auto ent3=[&](uint32_t pc,uint32_t link){c.pc=pc;c.lr=link;v958::observe(pc,c);};
                                                                                                    ent3(zf=="-entry"?q::Di:q::En,q::Dest+4u);
                                                                                                    if(zf=="-frame")c.mmu.words[v958::context+124]^=1u;
                                                                                                    if(zf=="-tick")scheduler.advance(++tick);
                                                                                                    if(zf=="-bus")SiBinding::write32(Base+C,*val);
                                                                                                    if(zf=="-device")mask=0;
                                                                                                    if(zf=="-early-poll")v958::poll(c);
                                                                                                    visit(q::En,q::branch(q::En,q::Di)|1u,zf=="-guard");
                                                                                                    ent3(q::Di,q::En+4u);visit(q::Di,Blr);
                                                                                                    visit(q::En+4u,q::branch(q::En+4u,q::Rs)|1u);
                                                                                                    ent3(q::Rs,q::En+8u);visit(q::Rs,Blr);
                                                                                                    c.lr=q::Dest+4u;c.gpr[3]=2;c.mmu.words[c.gpr[13]+4u]=1;
                                                                                                    visit(q::En+8u,Blr);visit(q::Dest+4u,q::branch(q::Dest+4u,q::Re)|1u);
                                                                                                    ent3(q::Re,q::Dest+8u);visit(q::Re,Blr);
                                                                                                    visit(q::Dest+8u,Nop);c.gpr[3]=v958::context;
                                                                                                    visit(q::Dest+12u,q::branch(q::Dest+12u,q::Lo)|1u);ent3(q::Lo,q::Dest+16u);
                                                                                                    c.gpr=interrupted_gp;c.lr=interrupted_lr;c.ctr=interrupted_ctr;c.xer=interrupted_xer;
                                                                                                    c.cr.fill({});c.srr0=Resume;c.srr1=0x8032u;
                                                                                                    if(zf=="-restore")c.gpr[31]^=1u;
                                                                                                    visit(q::Lo,q::Rfi);c.pc=Resume;c.msr=c.srr1;
                                                                                                    if(zf=="-gqr")c.gqr[0]^=1u;
                                                                                                    if(zf=="-rfi-tick")scheduler.advance(++tick);
                                                                                                    need(!v958::poll(c));
                                                                                                    if(zf=="-second-gqr")c.gqr[7]^=1u;
                                                                                                    v958::poll(c);
#ifdef UNDERCOVER_V1220_PRIVATE_ACK_RESUME
                                                                                                    if(v958::ack_resume_enabled()){
                                                                                                        need(zf.starts_with("-resume"));
                                                                                                        const auto rf3=zf.substr(std::string_view("-resume").size());
                                                                                                        // This original-free fixture previously stopped before the resume label.
                                                                                                        // Supply an independently mapped synthetic instruction for this new lane.
                                                                                                        c.mmu.words[Resume]=Nop;
#ifdef UNDERCOVER_V1227_PRIVATE_ACK_LEAF
                                                                                                        const bool leaf_mode=v958::ack_leaf_enabled();
                                                                                                        const auto lf=rf3.starts_with("-leaf")?rf3.substr(std::string_view("-leaf").size()):std::string_view{};
                                                                                                        const auto le=v1227::expected;
                                                                                                        if(leaf_mode){
                                                                                                            need(rf3.starts_with("-leaf")&&le.resume==Resume&&le.caller==interrupted_lr);
                                                                                                            c.mmu.words[Resume]=le.extract;
                                                                                                            c.mmu.words[Resume+4u]=Blr;
                                                                                                            c.mmu.words[le.caller]=le.caller_word;
                                                                                                            if(lf=="-leaf-word")c.mmu.words[Resume+4u]^=1u;
                                                                                                            if(lf=="-caller-word")c.mmu.words[le.caller]^=1u;
                                                                                                        }
#endif
                                                                                                        const uint32_t rw=c.mmu.read32(Resume);
                                                                                                        if(rf3!="-missing-dispatch-tick")scheduler.advance(++tick);
                                                                                                        if(rf3=="-extra-dispatch-tick")scheduler.advance(++tick);
                                                                                                        if(rf3=="-pc")c.pc=Resume+4u;
                                                                                                        if(rf3=="-srr0")c.srr0=Resume+4u;
                                                                                                        if(rf3=="-mask")mask=0;
                                                                                                        if(rf3!="-missing-dispatch")v958::observe(Resume,c);
                                                                                                        if(rf3=="-double-dispatch")v958::observe(Resume,c);
                                                                                                        if(rf3=="-integer")c.gpr[31]^=1u;
                                                                                                        if(rf3=="-gqr")c.gqr[0]^=1u;
                                                                                                        if(rf3=="-word")c.mmu.words[Resume]^=1u;
                                                                                                        if(rf3=="-extra-label-tick")scheduler.advance(++tick);
                                                                                                        if(rf3=="-missing-label-tick")v958::before(c,Resume,rw,false);
                                                                                                        else visit(Resume,rw,rf3=="-guard");
#ifdef UNDERCOVER_V1227_PRIVATE_ACK_LEAF
                                                                                                        if(leaf_mode){
                                                                                                            need(v958::held_epilogue.stage()==34u);
                                                                                                            if(lf!="-extract")c.gpr[3]=0;
                                                                                                            if(lf=="-tick")scheduler.advance(++tick);
                                                                                                            if(lf=="-mask")mask=0;
                                                                                                            if(lf=="-bus")SiBinding::write32(Base+C,*val);
                                                                                                            visit(Resume+4u,Blr,lf=="-guard");
                                                                                                            c.pc=le.caller;
                                                                                                            if(lf=="-abi")c.gpr[31]^=1u;
                                                                                                            if(lf!="-poll")v958::poll(c);
                                                                                                            if(lf=="-double-poll")v958::poll(c);
                                                                                                            scheduler.advance(++tick);
#ifdef UNDERCOVER_V1230_PRIVATE_ACK_IPC
                                                                                                            if(ipc_fixture){
                                                                                                                using W=IpcClientWitness;
                                                                                                                constexpr uint32_t Heap=0x93380000u,Hi=0x93400000u;
                                                                                                                for(const auto e:v624::expected_client.edges){
                                                                                                                    c.mmu.words[e.pc]=e.entry_word;c.mmu.words[e.lr-4u]=e.branch_word;
                                                                                                                }
                                                                                                                c.mmu.words[W::Return]=v624::expected_client.return_word;
                                                                                                                c.mmu.words[W::Root]=Nop;
                                                                                                                c.mmu.words[v624::expected_client.handler]=v624::expected_client.handler_word;
                                                                                                                c.mmu.words[W::Lo]=Heap;c.mmu.words[W::Hi]=Hi;
                                                                                                                c.mmu.words[W::Sda-16336u]=Heap;c.mmu.words[W::Sda-3352u]=Hi;
                                                                                                                c.mmu.words[W::MaskA]=0xf7fff7f0u;c.mmu.words[W::MaskB]=0;
                                                                                                                c.mmu.words[W::IrqGlobal]=W::Table;
                                                                                                                need(ipc_transport&&ipc_transport->serviced_steps()==0);
                                                                                                            }
#endif
                                                                                                            if(lf!="-dispatch")v958::observe(lf=="-target"?le.caller+4u:le.caller,c);
                                                                                                            if(lf=="-gqr")c.gqr[0]^=1u;
                                                                                                            visit(le.caller,le.caller_word);
#ifdef UNDERCOVER_V1230_PRIVATE_ACK_IPC
                                                                                                            if(ipc_fixture){
                                                                                                                need(v958::ack_ipc.stage()==2u);
                                                                                                                c.pc=IpcClientWitness::Root;c.lr=IpcClientWitness::Return;
                                                                                                                v958::observe(c.pc,c);
#ifdef UNDERCOVER_V1235_PRIVATE_ACK_IPC_COMPLETE
                                                                                                                using W=IpcClientWitness;using I=NativeIosBinding;using Hq=HollywoodIrq;using M=IpcMailbox;
                                                                                                                constexpr uint32_t Heap=0x93380000u;
                                                                                                                need(v958::ack_ipc.stage()==3u);
                                                                                                                if(mode.ends_with("-ipc-pending"))cause.fetch_or(SI);
                                                                                                                if(mode.ends_with("-ipc-si"))ctl.write(SiController::Buffer,0xfeedu);
                                                                                                                need(!v958::poll(c));
                                                                                                                for(unsigned i=1;i<17;++i){
                                                                                                                    const auto e=v624::expected_client.edges[i];
                                                                                                                    scheduler.advance(++tick);c.pc=e.pc;c.lr=e.lr;
                                                                                                                    c.msr=(i==8||i==13||i==14)?0x32u:0x8032u;
                                                                                                                    if(i==5)c.gpr[3]=Heap;
                                                                                                                    if(i==6){c.gpr[3]=Heap;c.gpr[4]=64;}
                                                                                                                    if(i==8||i==14)c.gpr[3]=1;
                                                                                                                    if(i==9){c.gpr[3]=Heap+64;c.mmu.words[Heap]=0x12345678u;if(mode.ends_with("-ipc-heap"))c.mmu.words[Heap+64]=1;}
                                                                                                                    if(i==10){c.gpr[3]=27;c.gpr[4]=v624::expected_client.handler;}
                                                                                                                    if(i==11){c.gpr[3]=0x10;c.mmu.words[W::Table+108u]=v624::expected_client.handler;}
                                                                                                                    if(i==13)c.gpr[3]=0x10;
                                                                                                                    if(i==15){
                                                                                                                        mask.fetch_or(Hq::PI_HOLLYWOOD);
                                                                                                                        if(mode.ends_with("-ipc-mask"))mask.fetch_and(~SI);
                                                                                                                        c.mmu.words[W::MaskA]=0xf7fff7e0u;
                                                                                                                        need(I::write32(IosBus::IPC+Hq::PPC_MASK,Hq::IPC_PPC));
                                                                                                                        c.gpr[3]=1;c.gpr[4]=0x36;
                                                                                                                    }
                                                                                                                    if(i==16&&!mode.ends_with("-ipc-missing-control"))need(I::write32(IosBus::IPC+M::PPCCTRL,0x36));
                                                                                                                    v958::observe(c.pc,c);
                                                                                                                    visit(e.pc,e.entry_word);
                                                                                                                    need(!v958::poll(c));
                                                                                                                }
                                                                                                                scheduler.advance(++tick);c.pc=c.lr=W::Return;c.gpr[3]=0;c.msr=0x8032u;
                                                                                                                v958::observe(c.pc,c);
#endif
                                                                                                            }
#endif
                                                                                                        }
#endif
                                                                                                    }
#endif
                                                                                                }
#endif
                                                                                            }
#endif
                                                                                        }
#endif
                                                                                    }
#endif
                                                                                }
#endif
                                                                            }
#endif
                                                                        }
#endif
                                                                    }
#endif
                                                                }
#endif
                                                            }
                                                            need(false);
                                                        }
#endif
                                                        need(false);
                                                    }
#endif
                                                    v958::observe(Handler,c);need(false);
                                                }
#endif
                                                v958::observe(q::D,c);need(false);
                                            }
#endif
                                            need(false);
                                        }
#endif
                                        visit(v1139::A+64u,v1139::rows[15].word);need(false);
                                    }
#endif
                                    visit(e.caller,e.caller_word);need(false);
                                }
#endif
                                visit(Root+56u,v1123::rows[3].word);need(false);
                            }
#endif
                            visit(Root+44u,Nop);need(false);
                        }
#endif
                        visit(Root+40,v831::words[3].word);need(false);
                    }
#endif
                    visit(Root+28,v813::continuation.back());need(false);
                }
#endif
                visit(Root+20,Nop);
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
