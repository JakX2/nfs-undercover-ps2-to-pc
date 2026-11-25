#include "wii_si_first_helper_v680.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,B=0x80005000u,Site=H+4,Call=0x48000ffdu,Other=0x100u;
constexpr uint32_t Store=0x90030000u,Nop=0x60000000u,Cond=0x4082fffcu,Jump=0x4bfffffcu,Blr=0x4e800020u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=B&&a<B+16?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint64_t inst_count=100;
    uint32_t pc=Site,lr=0x80006000u,msr=0x32u,dispatch_saved_ctx=0,ctr=4,srr0=0x80007000u,srr1=0x8032u,xer=0;
    bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("V719 poll assertion");}
int main(){
    for(unsigned trial=0;trial<18;++trial){
        std::atomic<uint32_t> cause{Other},mask{SiController::PI_SI};
        SiController ctl(cause);ctl.write(SiController::Control,0xc0010301u);
        ctl.complete(ctl.pending()->token,{},SiController::ERR_NOREP);
        Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*23+1;
        const auto branch=trial==2||trial==15?Jump:Cond;
        c.mmu.words={{B,Store},{B+4,Nop},{B+8,branch},{B+12,Blr}};
        SiCompletionAckTrace ack;SiFirstHelper helper({Site,B,B+16,Call});
        need(ack.arm(ctl,cause,mask,c.inst_count,H,H+32));++c.inst_count;
        need(ack.before(Site,Call)&&ack.allow_helper(B,B+16)&&helper.start(c,Site,Call));
        c.pc=B;c.lr=Site+4;need(helper.entry(B,c));++c.inst_count;
        need(helper.instruction(c,B,Store,ack,true));ack.write(ctl,SiController::Control,0xe0010300u);
        ++c.inst_count;need(helper.instruction(c,B+4,Nop,ack,true));need(ack.resume_after_ack(B+4,Nop));
        ++c.inst_count;need(helper.instruction(c,B+8,branch,ack,true));
        need(helper.arm_postack_poll(c,B+8,branch,ack)&&helper.poll_pending());
        if(trial==3){++c.inst_count;need(!helper.instruction(c,B+12,Blr,ack,true));continue;}
        c.pc=B+8;
        if(trial==4)c.pc=B;
        if(trial==5)++c.inst_count;
        if(trial==6)c.msr|=0x8000u;
        if(trial==7)c.lr^=4u;
        if(trial==8)c.ctr^=1u;
        if(trial==9)c.srr0^=4u;
        if(trial==10)c.cr[0].eq=true;
        if(trial==11)c.gpr[3]^=1u;
        if(trial==12)cause.fetch_or(0x200u);
        if(trial==17)c.xer^=1u;
        const auto ok=helper.postack_poll(c,ack);
        if((trial>=4&&trial<=12)||trial==17){need(!ok&&helper.failure()==6);continue;}
        need(ok&&helper.polls()==1&&!helper.poll_pending());
        if(trial==13){need(!helper.postack_poll(c,ack)&&helper.failure()==6);continue;}
        if(trial==14){need(!helper.arm_postack_poll(c,B+8,branch,ack));continue;}
        ++c.inst_count;
        if(trial==15){need(!helper.instruction(c,B+12,Blr,ack,true));continue;}
        if(trial==16){need(!helper.instruction(c,B,Store,ack,true));continue;}
        if(trial==1||trial==2){
            need(helper.instruction(c,B+4,Nop,ack,true));++c.inst_count;
            need(helper.instruction(c,B+8,branch,ack,true));
            need(helper.arm_postack_poll(c,B+8,branch,ack));c.pc=B+8;need(helper.postack_poll(c,ack));
            need(helper.polls()==2);
            if(trial==2)continue; // unconditional branch has no fallthrough
            ++c.inst_count;
        }
        need(helper.instruction(c,B+12,Blr,ack,true));
        c.pc=Site+4;need(helper.returned(c,c.pc));
    }
    std::cout<<"V719_POSTACK_POLL synthetic=1 cases=18 valid=3 rejects=15 original_execution=0\n";
}
