#include "wii_callback_identity_v796.h"
#include "wii_si_handler_return_v725.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,C=0x80006000u,
    Nop=0x60000000u,Blr=0x4e800020u,Indirect=0x4e800421u;
constexpr uint32_t Call=0x48000ffdu;
constexpr std::array<uint32_t,3> code{Nop,0x38630001u,Blr};
constexpr std::array<uint32_t,2> sites{H+16u,H+24u};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;
    uint8_t byte=0;unsigned reads=0;
    uint32_t hole=0;
    uint8_t* get_ptr(uint32_t a){return a!=hole&&words.contains(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){++reads;return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=R,msr=0x32u,srr0=0x80007000u,srr1=0x8032u,
             ctr=C,xer=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
void need(bool ok){if(!ok)throw std::runtime_error("V796 synthetic invariant");}
int main(){
    unsigned classes=0,slots=0;
    for(unsigned t=0;t<14;++t){
        Cpu c;
        c.mmu.words={{C,code[0]},{C+4u,code[1]},{C+8u,code[2]},{R,Nop}};
        uint32_t pc=sites[0],w=Indirect,candidate=C;
        unsigned ordinal=6,kind=2,expected=2,reads=3;
        if(t==1){pc=sites[1];ordinal=11;}
        if(t==2)c.ctr|=3u;
        if(t==3){c.ctr=R;expected=1;reads=0;}
        if(t==4){c.ctr=0;expected=3;reads=0;}
        if(t==5){c.mmu.words[C+4u]^=1u;expected=4;reads=2;}
        if(t==6){c.mmu.words[C+8u]^=1u;expected=4;reads=3;}
        if(t==7){c.mmu.words.erase(C+4u);expected=3;reads=0;}
        if(t==8){c.mmu.hole=C+11u;expected=3;reads=0;}
        if(t==9){candidate=c.ctr=0x817ffffcu;c.mmu.words[candidate]=Nop;expected=3;reads=0;}
        if(t==10){kind=1;expected=0;reads=0;}
        if(t==11){w=Nop;expected=0;reads=0;}
        if(t==12){pc=sites[1];expected=0;reads=0;}
        if(t==13){ordinal=7;expected=0;reads=0;}
        const auto before=c.mmu.words;const auto ctr=c.ctr;
        need(classify_callback_identity(c,pc,w,ordinal,kind,candidate,code,sites)==expected);
        need(c.mmu.words==before&&c.ctr==ctr&&c.mmu.reads==reads);++classes;
    }
    for(unsigned t=0;t<12;++t){
        Cpu c;c.mmu.words={{H,Nop},{H+4,Call},{H+8,Call},{H+12,Nop},
            {H+16,Indirect},{H+20,Blr},{R,Nop}};
        SiHandlerReturnWitness s({H,H+24,H+4,R,Nop});
        need(s.capture(c));c.pc=c.lr=H+4;c.inst_count+=50;
        need(s.start(c,H+4,true)&&s.before_authenticated(c,H+4,Call,true,4));
        c.inst_count+=81;c.pc=c.lr=H+8;
        need(s.transfer_returned(c,H+8,80,true)&&s.completed_calls()==8);
        need(s.before_authenticated(c,H+8,Call,true,t==3?6u:5u));
        const unsigned n=t==1?2u:t==2?256u:t==4?1u:t==5?257u:90u;
        c.inst_count+=n+1u;c.pc=c.lr=H+12;
        if(t==6)++c.inst_count;
        if(t==7)c.lr=H+8;
        if(t==8)c.msr|=0x8000u;
        if(t==9)c.srr0^=4u;
        if(t==10)c.pc=H+16;
        bool ok=s.alarm_returned(c,H+12,n,t!=11);
        if(t<=2){
            need(ok&&s.completed_calls()==24u&&s.before(c,H+12,Nop,true));
            ++c.inst_count;c.pc=H+16;
            need(!s.before(c,H+16,Indirect,true)&&s.failure()==4&&s.stage()==2);
        }else need(!ok&&s.failure()==8&&s.completed_calls()==8u);
        ++slots;
    }
    std::cout<<"V796_CALLBACK_IDENTITY synthetic=1 classes="<<classes
             <<" slot_cases="<<slots<<" original_execution=0\n";
}
