#include "wii_callback_return_v846.h"
#include "wii_si_handler_return_v725.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
using undercover::wii::HandlerNativeReturnWitness;
using undercover::wii::HandlerReturnExpectation;
namespace {
constexpr uint32_t Call=0x80001000,Restore=0x80002000,Caller=0x80003000,Stack=0x80010000;
constexpr uint32_t Branch=0x48000001u|(Restore-Call),Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t Lwz(unsigned r,unsigned b,int d){return (32u<<26)|(r<<21)|(b<<16)|(uint32_t(d)&0xffffu);}
constexpr uint32_t Addi(unsigned r,unsigned b,int d){return (14u<<26)|(r<<21)|(b<<16)|(uint32_t(d)&0xffffu);}
constexpr auto restore_words=[] {
    std::array<uint32_t,16> a{};
    for(unsigned i=0;i<15;++i)a[i]=Lwz(17u+i,11u,-60+int(i)*4);
    a[15]=Blr;return a;
}();
constexpr std::array<uint32_t,4> tail_words{Lwz(0,1,68),0x7c0803a6u,Addi(1,1,64),Blr};
struct MMU {
    std::map<uint32_t,uint8_t> bytes;
    const uint8_t* get_ptr(uint32_t a)const{auto i=bytes.find(a);return i==bytes.end()?nullptr:&i->second;}
    uint32_t read32(uint32_t a)const{uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|bytes.at(a+i);return v;}
    void put(uint32_t a,uint32_t w){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(w>>(24u-8u*i));}
};
struct CPU {
    struct Cr{bool lt=false,gt=false,eq=false,so=false;};
    std::array<uint32_t,32> gpr{};
    std::array<Cr,8> cr{};
    MMU mmu;
    uint32_t pc=Call,lr=0,msr=0x32,srr0=0x80004000,srr1=0x8032,ctr=0,xer=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false,dispatch_saved_ctx=false;
};
void need(bool value){if(!value){std::cerr<<"V879_TEST_FAILURE\n";std::exit(1);}}
struct Fixture {
    CPU c;
    std::array<uint32_t,32> original{};
    HandlerNativeReturnWitness w{HandlerReturnExpectation{Call,Restore,Caller,restore_words,tail_words,Nop}};
    Fixture(){
        for(unsigned i=0;i<32;++i)original[i]=0xabc00000u+i;
        original[1]=Stack;c.gpr=original;c.gpr[1]=Stack-64;c.gpr[11]=Stack;
        for(unsigned i=0;i<15;++i){c.gpr[17+i]^=0xffffu;c.mmu.put(Stack-60+4*i,original[17+i]);}
        c.mmu.put(Stack+4,Caller);
        c.mmu.put(Call,Branch);c.mmu.put(Caller,Nop);
        for(unsigned i=0;i<restore_words.size();++i)c.mmu.put(Restore+4*i,restore_words[i]);
        for(unsigned i=0;i<tail_words.size();++i)c.mmu.put(Call+4+4*i,tail_words[i]);
    }
    void run_to_blr(bool dispatch){
        need(dispatch?w.start_dispatch(c,Call,Branch,original,0,true):w.start(c,Call,Branch,original,0,true));
        c.pc=Restore;c.lr=Call+4;
        need(w.entry(c,Restore,true));
        for(unsigned i=0;i<16;++i){
            ++c.inst_count;need(w.before(c,Restore+4*i,restore_words[i],true));
            if(i<15)c.gpr[17+i]=c.mmu.read32(Stack-60+4*i);
            else c.pc=c.lr;
        }
        for(unsigned i=0;i<4;++i){
            ++c.inst_count;need(w.before(c,Call+4+4*i,tail_words[i],true));
            if(i==0)c.gpr[0]=c.mmu.read32(c.gpr[1]+68);
            else if(i==1)c.lr=c.gpr[0];
            else if(i==2)c.gpr[1]+=64;
            else c.pc=c.lr;
        }
        need(w.stage()==4&&w.visits()==20&&c.pc==Caller&&c.lr==Caller);
    }
};
}
int main(){
    unsigned valid=0,refused=0;
    for(bool dispatch:{false,true}){
        Fixture f;f.run_to_blr(dispatch);
        if(dispatch){need(f.w.dispatch_poll(f.c,true));++f.c.inst_count;need(f.w.dispatch_resume(f.c,Caller,Nop,true));}
        ++f.c.inst_count;need(f.w.before(f.c,Caller,Nop,true)&&f.w.stage()==5&&f.w.visits()==21);
        ++valid;
    }
    for(unsigned kind=0;kind<11;++kind){
        Fixture f;f.run_to_blr(true);auto& c=f.c;auto& w=f.w;
        bool ok=false;
        switch(kind){
        case 0: ++c.inst_count;ok=w.before(c,Caller,Nop,true);break;
        case 1: ++c.inst_count;ok=w.dispatch_resume(c,Caller,Nop,true);break;
        case 2: ++c.inst_count;ok=w.dispatch_poll(c,true);break;
        case 3: need(w.dispatch_poll(c,true));ok=w.dispatch_poll(c,true);break;
        case 4: need(w.dispatch_poll(c,true));c.inst_count+=2;ok=w.dispatch_resume(c,Caller,Nop,true);break;
        case 5: need(w.dispatch_poll(c,true));++c.inst_count;ok=w.dispatch_resume(c,Caller+4,Nop,true);break;
        case 6: need(w.dispatch_poll(c,true));++c.inst_count;ok=w.dispatch_resume(c,Caller,Nop,false);break;
        case 7: need(w.dispatch_poll(c,true));++c.inst_count;c.gpr[26]^=1;ok=w.dispatch_resume(c,Caller,Nop,true);break;
        case 8: need(w.dispatch_poll(c,true));++c.inst_count;need(w.dispatch_resume(c,Caller,Nop,true));ok=w.dispatch_resume(c,Caller,Nop,true);break;
        case 9: need(w.dispatch_poll(c,true));++c.inst_count;need(w.dispatch_resume(c,Caller,Nop,true));++c.inst_count;c.gpr[31]^=1;ok=w.before(c,Caller,Nop,true);break;
        case 10: c.mmu.put(Caller,Nop^1u);ok=w.dispatch_poll(c,true);break;
        }
        need(!ok&&w.failure()!=0&&w.stage()!=5);++refused;
    }
    unsigned joined=0,join_refused=0;
    for(unsigned t=0;t<12;++t){
        Fixture f;auto& c=f.c;auto& w=f.w;
        constexpr uint32_t H=Call-12u,A=H+4u,B=H+8u,Alarm=0x48000101u,Indirect=0x4e800421u;
        c.mmu.put(H,Nop);c.mmu.put(A,Alarm);c.mmu.put(B,Indirect);
        undercover::wii::SiHandlerReturnWitness h({H,Call+20u,A,Caller,Nop});
        const auto framed=c.gpr;c.gpr=f.original;c.pc=H;c.lr=Caller;
        need(h.capture(c));c.gpr=framed;c.pc=c.lr=A;c.inst_count+=50;
        need(h.start(c,A,true)&&h.before_authenticated(c,A,Alarm,true,5u));
        c.pc=c.lr=B;c.inst_count+=11;need(h.alarm_returned(c,B,10u,true)&&h.before_authenticated_indirect(c,B,Indirect,true,6u));
        const uint64_t at=c.inst_count;c.pc=c.lr=Call;c.inst_count+=200;
        need(h.callback_returned(c,Call,at,true,true,6u));
        if(t==1){need(!h.before_authenticated(c,Call,Branch,false,12u));++join_refused;continue;}
        need(h.before_authenticated(c,Call,Branch,true,12u));
        need(w.start_dispatch(c,Call,Branch,h.entry_gprs(),h.entry_cr(),true));
        c.pc=Restore;c.lr=Call+4u;need(w.entry(c,Restore,true));
        for(unsigned i=0;i<16;++i){
            ++c.inst_count;need(w.before(c,Restore+4u*i,restore_words[i],true));
            if(i<15)c.gpr[17u+i]=c.mmu.read32(Stack-60u+4u*i);
            else c.pc=c.lr;
        }
        ++c.inst_count;
        if(t==2){need(!h.restore_returned(c,Call+4u,15u,true,12u));++join_refused;continue;}
        if(t==3){++c.inst_count;need(!h.restore_returned(c,Call+4u,16u,true,12u));++join_refused;continue;}
        if(t==4){need(!h.restore_returned(c,Call+4u,16u,false,12u));++join_refused;continue;}
        need(h.restore_returned(c,Call+4u,16u,true,12u));
        if(t==5){need(!h.restore_returned(c,Call+4u,16u,true,12u));++join_refused;continue;}
        if(t==6){++c.inst_count;need(!h.before(c,Call+4u,tail_words[0],true));++join_refused;continue;}
        for(unsigned i=0;i<4;++i){
            if(i)++c.inst_count;
            need(w.before(c,Call+4u+4u*i,tail_words[i],true)&&h.before(c,Call+4u+4u*i,tail_words[i],true));
            if(i==0)c.gpr[0]=c.mmu.read32(c.gpr[1]+68u);
            else if(i==1)c.lr=c.gpr[0];
            else if(i==2)c.gpr[1]+=64u;
            else c.pc=c.lr;
        }
        need(h.stage()==3u&&w.stage()==4u&&h.completed_calls()==(16u|32u|2048u));
        if(t==7){need(!h.poll(c,false));++join_refused;continue;}
        need(h.poll(c,true)&&w.dispatch_poll(c,true));
        if(t==8){need(!w.dispatch_resume(c,Caller,Nop,true));++join_refused;continue;}
        ++c.inst_count;need(w.dispatch_resume(c,Caller,Nop,true));
        if(t==9){need(!h.resumed(c,Caller,Nop,true));++join_refused;continue;}
        ++c.inst_count;
        if(t==10){c.gpr[31]^=1;need(!w.before(c,Caller,Nop,true));++join_refused;continue;}
        if(t==11){need(!h.resumed(c,Caller,Nop,false));++join_refused;continue;}
        need(w.before(c,Caller,Nop,true)&&h.resumed(c,Caller,Nop,true)&&h.stage()==5u&&w.stage()==5u);++joined;
    }
    need(joined==1u&&join_refused==11u);
    std::cout<<"V886_HANDLER_TAIL_JOIN valid="<<joined<<" refused="<<join_refused<<" same_tick=1 original_execution=0\n";
    std::cout<<"V879_RETURN_DISPATCH valid="<<valid<<" refused="<<refused<<" original=0 execution=0\n";
}
