#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_transfer_input.h"
#include "wii_si_controller_v511.h"
#include "wii_si_type_scheduler_v514.h"
#include "wii_transfer_return_v774.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
constexpr uint32_t Sda=0x8070e8e0u,Data=0x80619a60u,TypeData=Data+24u,Command=Sda-3144u,Callback=0x805327f8u;
constexpr uint32_t MSR=0x32u,Mask=8u,Other=0x100u,Call=H+8u,Return=Call+4u;
static std::atomic<uint32_t> cause{Other},mask{Mask};
static std::unique_ptr<SiController> si;
static std::unique_ptr<SiTypeScheduler> scheduler;
static PostAckTransferDevice device;
static SiCompletionAckTrace ack;
static TransferReturnExpectation expectation(){
    return {Call,C,C+4u*uint32_t(transfer_words.size()),caller[2],transfer_words[0],
        {transfer_sites[0],S,S+4u*uint32_t(save_words.size()),transfer_branches[0],26u,transfer_save_base,transfer_disp},
        {transfer_sites[1],D,D+4u*uint32_t(disable_words.size()),transfer_branches[1],1u},Data,
        {{{transfer_sites[2],Q,Q+4u*uint32_t(irq_restore_words.size()),transfer_branches[2],3u},
          {transfer_sites[3],Q,Q+4u*uint32_t(irq_restore_words.size()),transfer_branches[3],3u}}},
        {transfer_sites[4],R,transfer_branches[4],26u,transfer_restore_base,transfer_disp}};
}
static TransferReturnWitness route(expectation());
using Access=PostAckTransferDevice::Access;
static CPUContext* cpu=nullptr;
static std::array<uint32_t,32> gp{};
static unsigned entries=0,visits=0,outer=0,stops=0,trial=0,reads=0,writes=0,loops=0;
static uint64_t last=0;
static uint32_t last_pc=0,last_word=0,channel=0;
static bool busy=false,corrupt=false,pending_poll=false,mmio_accessed=false,returned=false;
static unsigned resume_visits=0;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V775_TRANSFER_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits<<" busy="<<busy<<" reads="<<reads<<" writes="<<writes<<" follow="<<device.follow_stage()<<" reason="<<device.failure()<<" route="<<route.failure()<<" stage="<<route.stage()<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static bool abi(CPUContext& c){
    if(c.gpr[1]!=gp[1]||c.gpr[2]!=gp[2]||c.gpr[13]!=gp[13]||c.msr!=MSR)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp[i])return false;
    return true;
}
static bool span(uint32_t pc,uint32_t base,size_t n){return pc>=base&&pc<base+4*n;}
static unsigned offset(uint32_t a){
    need(a>=0x0d006400u&&a<0x0d006500u&&!(a&3u));return a-0x0d006400u;
}
static void mmio(bool write){
    need(cpu&&cpu->inst_count==last&&!mmio_accessed&&span(last_pc,C,transfer_words.size()));
    const auto op=last_word>>26,xo=(last_word>>1)&1023u;
    need(write?(op==36u||op==37u||(op==31u&&(xo==151u||xo==183u||xo==662u))):
               (op==32u||op==33u||(op==31u&&(xo==23u||xo==55u||xo==534u))));
    mmio_accessed=true;
}
static void advance(CPUContext& c,uint32_t pc,uint32_t w){
    scheduler->advance(c.inst_count);
    if(pc==H){need(ack.before(pc,w));return;}
    if(pc==H+4u){need(ack.before(pc,w)&&ack.resume_after_ack(pc,w)&&cause==Other);return;}
    if(pc==Call){
        need(ack.before(pc,w)&&route.start(c,pc,w,ack));return;
    }
    if(device.stage()==2){need(device.after_return(c.inst_count));return;}
    if(pc==Return){need(route.returned(c,pc,w,ack,device));return;}
    if(corrupt&&device.follow_stage()==2){
        mask=0;need(!device.before(c.inst_count));std::cout<<"V775_TRANSFER_REFUSAL mask_corruption=1"<<std::endl;std::_Exit(126);
    }
    if(span(pc,C,transfer_words.size()))need(route.before(c,pc,w,ack,device));
    else if(span(pc,S,save_words.size()))need(route.save_before(c,pc,w,ack,device));
    else if(span(pc,D,disable_words.size())){
        need(route.disable_before(c,pc,w,ack,device));
        if(route.handoff_due()){
            const auto cfg=scheduler->configuration(*si,route.channel(),c.inst_count);
            need(cfg&&device.begin(*si,cause,mask,ack,c.inst_count,route.channel(),route.idle(),cfg->response,cfg->latency));
        }
    }else if(span(pc,Q,irq_restore_words.size()))need(route.irq_before(c,pc,w,ack,device));
    else if(span(pc,R,restore_words.size()))need(route.restore_before(c,pc,w,ack,device));
    else need(false);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    if(!c.is_running){need(pc==Return+4u*16u);return;}
    need(c.msr==MSR&&!c.in_callback&&!c.dispatch_saved_ctx&&c.mmu.read32(pc)==w&&!pending_poll);
    if(visits)need(c.inst_count-last==1);
    last=c.inst_count;last_pc=pc;last_word=w;mmio_accessed=false;need(++visits<=256);
    advance(c,pc,w);
    if(pc==H||pc==H+4u||pc==Call){need(entries==1&&abi(c));return;}
    if(pc==Return){
        need(entries==6&&c.lr==pc&&abi(c)&&c.gpr[3]==(busy?0u:1u));
        if(busy){need(!reads&&!writes&&device.follow_stage()==0&&si->issued_tokens()==1&&c.mmu.read32(Data)==0);}
        else{
            need(device.follow_stage()>=2&&si->issued_tokens()==2&&reads>=2&&writes>=3);
            need(c.mmu.read32(Data)==channel&&c.mmu.read32(Data+8)==3&&c.mmu.read32(Data+12)==TypeData+4*channel&&c.mmu.read32(Data+16)==Callback);
        }
        need(route.stage()==4&&route.save_done()&&route.disable_done()&&route.irq_done()&&route.restore_done()&&route.total()==visits-4&&device.reads()==reads&&device.writes()==writes);
        returned=true;
    }
    if(pc>=Return&&pc<Return+4u*16u){
        need(returned&&pc==Return+4u*((++resume_visits)-1u)&&w==0x60000000u&&abi(c)&&c.gpr[3]==(busy?0u:1u));
        if(resume_visits==16){
            if(busy)need(device.follow_stage()==0&&scheduler->completed()==1&&cause==Other&&!si->pending());
            else need(device.follow_stage()==3&&scheduler->completed()==2&&cause==(Other|Mask)&&!si->pending()&&(si->read(SiController::Status)&(8u<<((3u-channel)*8u))));
            ++stops;c.is_running=false;
        }
        return;
    }
    need(span(pc,C,transfer_words.size())||span(pc,D,disable_words.size())||span(pc,Q,irq_restore_words.size())||span(pc,S,save_words.size())||span(pc,R,restore_words.size()));
    const auto op=w>>26;
    if((op==16u||op==18u)&&!(w&3u)){
        const auto bits=op==16u?0xfffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
        if(pc+(((w&bits)^sign)-sign)<=pc)pending_poll=true;
    }
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,6> order{H,C,S,D,Q,R};
    need(entries<order.size()&&pc==order[entries]&&c.pc==pc);
    if(entries)need(route.entry(c,pc,ack,device));
    else need(ack.arm(*si,cause,mask,c.inst_count,H,Return+4u*16u));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(!visits){need(!outer&&c.pc==H);++outer;return false;}
    need(pending_poll&&c.pc==last_pc&&c.inst_count==last&&c.msr==MSR);
    need(route.poll(c,ack,device));pending_poll=false;++loops;return false;
}
bool handle_syscall(CPUContext&){fail(2);}
void interpret_step(CPUContext&){fail(3);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}
void note_null_call(uint32_t,uint32_t){fail(5);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}
uint32_t HW_Reg_Read32(uint32_t a){mmio(false);uint32_t result=0;need(device.read(*si,offset(a),result));++reads;return result;}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    if(last_pc==H){need(!device.stage()&&cpu&&cpu->inst_count==last&&offset(a)==SiController::Control&&v==0xe0010300u);ack.write(*si,SiController::Control,v);return;}
    mmio(true);need(device.write(*si,offset(a),v));++writes;
}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    auto context=std::make_unique<CPUContext>();cpu=context.get();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller);put(C,transfer_words);put(D,disable_words);put(Q,irq_restore_words);put(S,save_words);put(R,restore_words);
    using Port=SiTypeScheduler::Port;
    for(trial=0;trial<(corrupt?1u:8u);++trial){
        entries=visits=outer=reads=writes=loops=resume_visits=0;returned=pending_poll=false;busy=trial>=4;channel=trial%4;
        scheduler.reset();si.reset();cause=Other;mask=Mask;device=PostAckTransferDevice{};ack=SiCompletionAckTrace{};route=TransferReturnWitness(expectation());
        si=std::make_unique<SiController>(cause);
        scheduler=std::make_unique<SiTypeScheduler>(*si,SiTypeScheduler::Profile{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
        si->write(SiController::Control,0xc0010301u);scheduler->advance(1);scheduler->advance(9);
        need(cause==(Other|Mask));
        for(unsigned i=0;i<8;++i)c.mmu.write32(Data+4*i,0);
        c.mmu.write32(Data,busy?0u:0xffffffffu);c.mmu.write32(Command,0);
        c.mmu.write32(TypeData+4*channel,128);
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80040000u+trial*0x100u;c.gpr[2]=0x80025000u;c.gpr[13]=Sda;
        c.gpr[3]=channel;c.gpr[4]=Command;c.gpr[5]=1;c.gpr[6]=TypeData+4*channel;c.gpr[7]=3;c.gpr[8]=Callback;c.gpr[9]=0xcd006434u;c.gpr[10]=0xe0010300u;gp=c.gpr;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80009000u;c.srr1=0x8032u;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;c.inst_count=100;
        run_game(c);need(!corrupt&&!c.is_running&&entries==6&&outer==1&&stops==trial+1&&abi(c)&&resume_visits==16);
    }
    std::cout<<"V775_OWNER_TRANSFER_RETURN valid=8 idle=4 busy=4 native_requests=4 original_return=8 exact_mmio=4 fallback=0 continuous_boot=0\n";
}catch(...){fail(8);}
