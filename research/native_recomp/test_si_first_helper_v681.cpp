#include "wii_si_first_helper_v680.h"
#include "wii_si_type_scheduler_v514.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,Root=0x80005000u,Site=H+4,Branch=0x48000ffdu,Other=0x100u;
constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,Store=0x90030000u;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=Root&&a<Root+16?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint64_t inst_count=100;
    uint32_t pc=Site,lr=0x80006000,msr=0x32,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;
};
static void need(bool ok){if(!ok)throw std::runtime_error("V681 helper assertion");}
int main(){
    using Port=SiTypeScheduler::Port;
    for(unsigned trial=0;trial<15;++trial){
        std::atomic<uint32_t> cause{Other},mask{SiController::PI_SI};
        SiController ctl(cause);SiTypeScheduler sched(ctl,{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
        ctl.write(SiController::Control,0xc0010301u);sched.advance(1);sched.advance(9);
        Cpu c;c.mmu.words={{Root,Nop},{Root+4,Blr}};
        for(unsigned i=0;i<32;++i)c.gpr[i]=i*0x1234567u+7u;
        SiCompletionAckTrace ack;SiFirstHelper helper({Site,Root,Root+16,Branch});
        need(ack.arm(ctl,cause,mask,c.inst_count,H,H+32));
        ++c.inst_count;need(ack.before(Site,Branch));
        bool ok=helper.start(c,Site,trial==1?Branch^4u:Branch);
        if(trial==1){need(!ok&&helper.failure()==1);continue;}need(ok);
        c.pc=trial==2?Root+4:Root;c.lr=trial==3?Site:Site+4;
        ok=helper.entry(c.pc,c);
        if(trial==2||trial==3){need(!ok&&helper.failure()==2);continue;}need(ok);
        if(trial==4)c.inst_count++;
        if(trial==5)c.msr|=0x8000;
        if(trial==6)c.mmu.words[Root]^=1u;
        uint32_t word=Nop;
        if(trial==7)word=0x48000009u;
        if(trial==8)word=0x48000100u;
        if(trial==9)word=0x4c000064u;
        if(trial>=7&&trial<=9)c.mmu.words[Root]=word;
        ++c.inst_count;ok=helper.instruction(c,Root,word,ack);
        if(trial>=4&&trial<=9){need(!ok&&helper.failure()==(trial<7?3u:4u));continue;}need(ok);
        if(trial==10){
            try{ack.write(ctl,SiController::Control,0xe0010300u);throw std::logic_error("write escaped");}
            catch(const std::runtime_error&){need(ack.failure()==5&&cause==(Other|SiController::PI_SI));}
            continue;
        }
        ++c.inst_count;
        if(trial==11)c.lr=Site;
        ok=helper.instruction(c,Root+4,Blr,ack);
        if(trial==11){need(!ok&&helper.failure()==5);continue;}need(ok);
        c.pc=trial==12?Site+8:Site+4;
        if(trial==13)c.gpr[14]^=1u;
        if(trial==14)c.gpr[1]^=8u;
        c.gpr[3]=42; // volatile result allowed
        ok=helper.returned(c,c.pc);
        if(trial>=12){need(!ok&&helper.failure()==5);continue;}need(ok&&helper.stage()==4);
        ++c.inst_count;need(ack.before(Site+4,Store));
        ack.write(ctl,SiController::Control,0xe0010300u);
        ++c.inst_count;need(ack.before(Site+8,Nop)&&ack.phase()==SiCompletionAckTrace::Phase::Complete);
        need(cause==Other&&mask==SiController::PI_SI);
    }
    std::cout<<"V681_SI_HELPER synthetic=1 cases=15 valid=1 rejects=14 real_device=1 original_execution=0\n";
}
