#include "wii_external_return_v706.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t Resume=0x80004010u,Rfi=0x80005000u,Other=0x100u,Mask=8u,Word=0x60000000u;
struct Field{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t p){return p>=0x80004000u&&p<0x80006000u?&b:nullptr;}
    uint32_t read32(uint32_t p){return words.at(p);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Field,8> cr{};
    uint32_t pc=Resume,lr=0x80006000u,msr=0x8032u,ctr=17,xer=0x80000000u,
             srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("V706 return witness assertion");}
int main(){
    for(unsigned trial=0;trial<22;++trial){
        Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=0x1234567u*(i+1u);
        for(unsigned i=0;i<8;++i)c.cr[i]={bool(i&1),bool(i&2),bool(i&4),bool(i==7)};
        c.mmu.words={{Resume,Word},{Rfi,0x4c000064u}};
        ExternalReturnWitness w;
        if(trial==1)c.msr=0x32;
        auto ok=w.capture(c,trial==2?Other:Other|8u,Mask);
        if(trial==1||trial==2){need(!ok&&w.failure()==1);continue;}need(ok);
        // Synthetic context restoration boundary; no original execution.
        c.pc=Rfi;c.msr=0x0;c.srr0=Resume;c.srr1=0x8032u;c.inst_count=300;
        if(trial==3)c.gpr[0]^=1;
        if(trial==4)c.cr[4].so=!c.cr[4].so;
        if(trial==5)c.lr^=4;
        if(trial==6)c.ctr^=1;
        if(trial==7)c.xer^=1;
        if(trial==8)c.srr0^=4;
        if(trial==9)c.srr1^=1;
        if(trial==10)c.mmu.words[Rfi]^=1;
        ok=w.before_rfi(c,Rfi,0x4c000064u,trial==11?Other|8u:Other,trial==12?Mask|Other:Mask);
        if(trial>=3&&trial<=12){need(!ok&&w.failure()==2);continue;}need(ok);
        c.pc=Resume;c.msr=c.srr1;
        if(trial==13)c.pc+=4;
        if(trial==14)c.msr^=1;
        if(trial==15)++c.inst_count;
        ok=w.poll(c,Other,Mask);
        if(trial>=13&&trial<=15){need(!ok&&w.failure()==3);continue;}need(ok);
        if(trial!=16)need(w.poll(c,Other,Mask));
        if(trial==17){need(!w.poll(c,Other,Mask)&&w.failure()==3);continue;}
        c.inst_count+=trial==18?1u:2u;
        if(trial==19)c.gpr[31]^=1;
        if(trial==20)c.mmu.words[Resume]^=1;
        ok=w.resume(c,Resume,Word,trial==21?Other|8u:Other,Mask);
        if(trial>=16){need(!ok&&w.failure()==4);continue;}need(ok&&w.stage()==5);
    }
    std::cout<<"V706_EXTERNAL_RETURN synthetic=1 cases=22 valid=1 rejects=21 integer_context=1 original_execution=0\n";
}
