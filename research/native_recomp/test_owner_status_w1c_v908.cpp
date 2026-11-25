#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_restore_input.h"
#include "wii_postack_transfer_device_v771.h"
#include "wii_si_type_scheduler_v514.h"
#include "wii_handler_suffix_guard_v868.h"
#include <array>
#include <algorithm>
#include <bit>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t Bus=0xcd006400u,Other=0x100u,SI=SiController::PI_SI,MSR=0x32u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer;
static std::atomic<uint32_t> cause{Other},mask{SI};
static SiController ctl(cause);
static std::unique_ptr<SiTypeScheduler> scheduler;
static PostAckTransferDevice device;
static SiCompletionAckTrace ack;
static HandlerSuffixGuard guard;
static std::array<uint32_t,32> gp{};
static CPUContext* cpu=nullptr;
static uint64_t last=0;
static unsigned entries=0,outer=0,visits=0,reads=0,writes=0,negative=0;
static uint32_t expected_status=0,expected_control=0,expected_buffer=0,expected_store=0;
static uint64_t tokens=0;
static unsigned channel=0;static bool present=false;
static std::array<uint32_t,4> table{};static bool index_read=false;
static bool taken=false;static uint32_t next_pc=0;
static constexpr uint32_t BranchTarget=BranchDestination;
static bool arm_pending=false;static unsigned arm_reads=0,arm_words=0,arm_reg=0;static uint32_t arm_value=0;
static constexpr auto labels=[]{
    std::array<HandlerSuffixLabel,ArmLabels.size()> r{};
    for(unsigned i=0;i<r.size();++i)r[i]={ArmLabels[i],loader_words[(ArmLabels[i]-L)/4u],0,0};
    return r;
}();
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<"V908_STATUS_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits
        <<" reads="<<reads<<" writes="<<writes<<" guard="<<guard.failure()<<" device="<<device.failure()<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)fail(1,l.line());}
static void advance(CPUContext& c){
    need(&c==cpu&&c.inst_count==last+1u);
    last=c.inst_count;scheduler->advance(last);
    need(device.after_return_at(c.inst_count)&&device.held_now()&&cause==(Other|SI)&&ctl.issued_tokens()==tokens);
}
static void reference(uint32_t w){
    const unsigned op=w>>26,xo=(w>>1)&1023u,rd=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
    if(op==15u)gp[rd]=(ra?gp[ra]:0u)+(uint32_t(w&0xffffu)<<16);
    else if(op==21u){
        const unsigned mb=(w>>6)&31u,me=(w>>1)&31u;uint32_t m=0;
        for(unsigned i=0;i<32;++i)if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))m|=1u<<(31u-i);
        gp[ra]=std::rotl(gp[rd],int(rb))&m;
    }else if(op==31u&&xo==792u){
        const unsigned sh=gp[rb]&63u;
        gp[ra]=uint32_t(std::bit_cast<int32_t>(gp[rd])>>std::min(sh,31u));
    }else if(op==14u)gp[rd]=(ra?gp[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
    else if(op==31u&&xo==28u)gp[ra]=gp[rd]&gp[rb];
    else if(op==31u&&xo==60u)gp[ra]=gp[rd]&~gp[rb];
    else if(op==31u&&xo==444u)gp[ra]=gp[rd]|gp[rb];
    else if(op==31u&&xo==316u)gp[ra]=gp[rd]^gp[rb];
    else if(op==31u&&xo==24u)gp[ra]=(gp[rb]&32u)?0u:gp[rd]<<(gp[rb]&31u);
    else if(op==31u&&xo==536u)gp[ra]=(gp[rb]&32u)?0u:gp[rd]>>(gp[rb]&31u);
    else if(op==31u&&xo==824u)gp[ra]=uint32_t(std::bit_cast<int32_t>(gp[rd])>>rb);
    else if(op==31u&&xo==266u)gp[rd]=gp[ra]+gp[rb];
    else if(op==31u&&xo==40u)gp[rd]=gp[rb]-gp[ra];
    else if(op==31u&&xo==23u){
        const uint32_t a=(ra?gp[ra]:0u)+gp[rb];
        need(!index_read&&a==ChannelTable[channel]&&cpu->mmu.read32(a)==table[channel]);
        gp[rd]=table[channel];index_read=true;
    }else if(op==32u){
        const uint32_t a=(ra?gp[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
        need(PostAckTransferDevice::offset(a)==S);
        gp[rd]=expected_status;
    }else if(op==36u){
        const uint32_t a=(ra?gp[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
        need(PostAckTransferDevice::offset(a)==S);
        expected_store=gp[rd];need(expected_store==(expected_status&(0x0fu<<((3u-channel)*8u)))&&bool(expected_status&expected_store)==!present);
    }else fail(2);
}
static void observe_arm(CPUContext& c,uint32_t w){
    const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u;
    unsigned width=0;bool sign=false,reverse=false;
    if(op==32u||op==33u)width=4;
    else if(op==34u||op==35u)width=1;
    else if(op>=40u&&op<=43u){width=2;sign=op>=42u;}
    else if(op==31u){
        if(xo==23u||xo==55u||xo==534u){width=4;reverse=xo==534u;}
        else if(xo==87u||xo==119u)width=1;
        else if(xo==279u||xo==311u||xo==343u||xo==375u||xo==790u){width=2;sign=xo==343u||xo==375u;reverse=xo==790u;}
    }
    if(width){
        const uint32_t base=ra?c.gpr[ra]:0u;
        const uint32_t a=op==31u?base+c.gpr[rb]:base+((w&0xffffu)^0x8000u)-0x8000u;
        need(a>=0x80000000u&&uint64_t(a)+width<=0x81800000u);
        uint32_t v=0;
        for(unsigned i=0;i<width;++i){const uint32_t p=a+(reverse?width-1u-i:i);need(c.mmu.get_ptr(p));v=(v<<8)|c.mmu.read8(p);}
        if(sign&&(v&0x8000u))v|=0xffff0000u;
        arm_pending=true;arm_reg=(w>>21)&31u;arm_value=v;
    }else need(op!=46u);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    advance(c);need(c.mmu.read32(pc)==w&&c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    if(pc==H){need(entries==1&&outer==1&&visits==0&&c.gpr==gp);return;}
    need(entries==2&&visits<24u&&pc==(visits>=14u?next_pc:L+4*visits));
    if(visits==0)need(guard.start(c,labels,pc));
    if(visits==6u&&negative==2u){
        c.gpr[(loader_words[5]>>21)&31u]^=1u;
        need(c.gpr!=gp);
        std::cout<<"V908_STATUS_REFUSAL kind=2"<<std::endl;std::_Exit(126);
    }
    if(visits==12u&&negative==5u){
        c.gpr[(loader_words[11]>>21)&31u]^=1u;
        need(c.gpr!=gp&&index_read);
        std::cout<<"V908_STATUS_REFUSAL kind=5"<<std::endl;std::_Exit(126);
    }
    if(visits<=14u)need(c.gpr==gp);
    need(guard.before(c,pc,w,0,0,visits==5u,visits==9u));
    if(visits>=14u){
        if(arm_pending){
            if(negative==7u){c.gpr[arm_reg]^=1u;need(c.gpr[arm_reg]!=arm_value);std::cout<<"V908_STATUS_REFUSAL kind=7"<<std::endl;std::_Exit(126);}
            need(c.gpr[arm_reg]==arm_value);arm_pending=false;++arm_reads;
        }
        if(arm_words!=(taken?3u:5u)){
            need(w!=0x4e800020u);observe_arm(c,w);++arm_words;++visits;next_pc=pc+4u;return;
        }
        need(w==0x4e800020u&&reads==1u&&writes==1u&&guard.visits()==15u+arm_words&&arm_reads==unsigned(!taken)&&index_read&&guard.writes()==0u&&
             device.suffix_status_reads()==1u&&device.suffix_status_writes()==1u&&device.suffix_status_value()==expected_status&&
             ctl.read(S)==(expected_status&~expected_store)&&ctl.read(C)==expected_control&&ctl.read(B)==expected_buffer&&scheduler->completed()==2u&&device.held_now());
        std::cout<<"V908_OWNER_STATUS_W1C prefix_words=14 native_gpr=1 indexed_ram=1 reads=1 writes=1 w1c=1 changed="<<unsigned((expected_status&expected_store)!=0u)
                 <<" follow_held=1 branch_taken="<<unsigned(taken)<<" arm_words="<<arm_words<<" arm_reads="<<arm_reads<<" fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
    if(visits==5u){
        const auto a=PostAckTransferDevice::word_access(c,w);
        need(a.kind==Access::Read&&PostAckTransferDevice::offset(a.address)==S);
        if(negative!=1u)need(device.arm_suffix_status_read(c.inst_count,a.address));
    }
    if(visits==12u){
        need(w>>26==10u&&index_read&&gp[(w>>16)&31u]==table[channel]);
    }else if(visits==13u){
        const uint32_t cmp=loader_words[12],v=table[channel],imm=cmp&0xffffu;
        const unsigned field=(cmp>>23)&7u,bo=(w>>21)&31u,bi=(w>>16)&31u;
        auto& f=c.cr[field];
        if(negative==6u){
            f.eq=!f.eq;
            need(f.eq!=(v==imm));
            std::cout<<"V908_STATUS_REFUSAL kind=6"<<std::endl;std::_Exit(126);
        }
        need(f.lt==(v<imm)&&f.gt==(v>imm)&&f.eq==(v==imm)&&bi/4u==field);
        const std::array<bool,3> flags{v<imm,v>imm,v==imm};
        taken=flags[bi%4u]==bool(bo&8u);
        next_pc=taken?BranchTarget:pc+4u;
    }else reference(w);
    if(visits==9u){
        const auto a=PostAckTransferDevice::word_access(c,w);
        need(a.kind==Access::Write&&PostAckTransferDevice::offset(a.address)==S&&a.store&&*a.store==expected_store);
        if(negative!=3u)need(device.arm_suffix_status_write(c.inst_count,a.address,expected_store));
    }
    ++visits;
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc&&((entries==0&&pc==H)||(entries==1&&pc==L)));
    if(!entries)advance(c);else need(c.inst_count==last);
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){need(!outer&&!entries&&c.inst_count==last&&device.held_now());++outer;return false;}
bool handle_syscall(CPUContext&){fail(3);}
void interpret_step(CPUContext&){fail(4);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}
void note_null_call(uint32_t,uint32_t){fail(5);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}
uint32_t HW_Reg_Read32(uint32_t a){
    need(cpu&&cpu->inst_count==last&&visits==6u&&!reads&&PostAckTransferDevice::offset(a)==S);
    uint32_t result=0;
    if(negative==1u){need(!device.read(ctl,S,result)&&device.failure()==8u);std::cout<<"V908_STATUS_REFUSAL kind=1"<<std::endl;std::_Exit(126);}
    need(device.read(ctl,S,result)&&result==expected_status&&device.held_now());++reads;return result;
}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}
void HW_Reg_Write32(uint32_t a,uint32_t value){
    need(cpu&&cpu->inst_count==last&&visits==10u&&reads==1u&&!writes&&PostAckTransferDevice::offset(a)==S&&value==expected_store);
    if(negative==3u||negative==4u){
        const auto bad=negative==4u?value^1u:value;
        need(!device.write(ctl,S,bad)&&device.failure()==9u&&ctl.read(S)==expected_status);
        std::cout<<"V908_STATUS_REFUSAL kind="<<negative<<std::endl;std::_Exit(126);
    }
    need(device.write(ctl,S,value)&&device.held_now());++writes;
}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==3);const unsigned trial=unsigned(std::stoul(argv[1]));negative=unsigned(std::stoul(argv[2]));need(trial<8u&&negative<8u);
    auto c=std::make_unique<CPUContext>();cpu=c.get();
    const auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c->mmu.write32(a,w);a+=4u;}};
    put(H,resume_words);put(L,loader_words);
    for(unsigned i=0;i<4;++i){table[i]=0x12340000u^(trial*0x9e3779b9u)^(i*0x01010101u);c->mmu.write32(ChannelTable[i],table[i]);}
    using Port=SiTypeScheduler::Port;
    const auto port=(trial&4u)?Port::present({1,2,3}):Port::absent();
    // The inherited first ACK witness authenticates a channel-0 NOREP.
    // Keep that first endpoint absent even in present follow-on trials.
    const SiTypeScheduler::Profile ports{Port::absent(),port,port,port};
    scheduler=std::make_unique<SiTypeScheduler>(ctl,ports,8);
    ctl.write(C,0xc0010301u);scheduler->advance(1);scheduler->advance(9);
    auto& tick=c->inst_count;tick=100;
    need(ack.arm(ctl,cause,mask,tick,H,H+16));++tick;need(ack.before(H,0x90030000u));
    ack.write(ctl,C,0xe0010300u);++tick;need(ack.before(H+4,0x60000000u)&&ack.resume_after_ack(H+4,0x60000000u));
    const unsigned ch=trial<4u?trial:1u+(trial-4u)%3u;
    channel=ch;present=bool(ports[ch].type);
    table[ch]=BranchSeeds[trial&1u];c->mmu.write32(ChannelTable[ch],table[ch]);
    need(device.begin(ctl,cause,mask,ack,tick,ch,true,ports[ch].type,8));
    auto step=[&](Access a=Access::None,uint32_t address=0){scheduler->advance(++tick);return device.before(tick,a,address);};
    uint32_t result=0;
    need(step(Access::Read,Bus+C)&&device.read(ctl,C,result));
    need(step(Access::Write,Bus+B)&&device.write(ctl,B,0x00abcdefu));
    need(step(Access::Write,Bus+S)&&device.write(ctl,S,0x08000000u));
    need(step(Access::Write,Bus+C)&&device.write(ctl,C,0xc0010301u|(ch<<1)));
    for(unsigned i=0;i<9;++i)need(step());
    need(device.finish(tick,1)&&device.follow_stage()==3u&&device.held_now());
    need(bool(ports[ch].type)==bool(trial&4u));
    need(bool(ctl.read(C)&SiController::COM_ERR)==!ports[ch].type);
    last=tick;tokens=ctl.issued_tokens();expected_status=ctl.read(S);expected_control=ctl.read(C);expected_buffer=ctl.read(B);
    for(unsigned i=0;i<32;++i)c->gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    c->gpr[1]=0x80022000u;c->gpr[2]=0x80025000u;c->gpr[13]=0x8070e8e0u;
    need(StatusChannelRegister>=14u&&StatusChannelRegister<32u);c->gpr[StatusChannelRegister]=ch;gp=c->gpr;
    c->pc=H;c->lr=0x80007000u;c->msr=MSR;c->srr0=0x80030000u;c->srr1=0x8032u;
    c->is_running=true;c->in_callback=false;c->dispatch_saved_ctx=0;
    run_game(*c);fail(8);
}catch(...){fail(8);}
