#include "wii_callback_return_v846.h"
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <map>
using undercover::wii::CallbackReturnWitness;
using undercover::wii::CallbackReturnExpectation;
namespace {
constexpr uint32_t Call=0x80001000,Restore=0x80002000,Caller=0x80003000,Stack=0x80010000;
constexpr uint32_t Branch=0x48000001u|(Restore-Call),Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t Lwz(unsigned r,unsigned b,int d){return (32u<<26)|(r<<21)|(b<<16)|(uint32_t(d)&0xffffu);}
constexpr uint32_t Addi(unsigned r,unsigned b,int d){return (14u<<26)|(r<<21)|(b<<16)|(uint32_t(d)&0xffffu);}
constexpr auto restore_words=[] {
    std::array<uint32_t,7> a{};
    for(unsigned i=0;i<6;++i)a[i]=Lwz(26u+i,11u,-24+int(i)*4);
    a[6]=Blr;return a;
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
    uint32_t pc=Call,lr=0,msr=0x32,srr0=0x80004000,srr1=0x8032;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false,dispatch_saved_ctx=false;
};
void need(bool value){if(!value){std::cerr<<"V849_TEST_FAILURE\n";std::exit(1);}}
struct Fixture {
    CPU c;
    std::array<uint32_t,32> original{};
    CallbackReturnWitness w{CallbackReturnExpectation{Call,Restore,Caller,restore_words,tail_words,Nop}};
    Fixture(){
        for(unsigned i=0;i<32;++i)original[i]=0xabc00000u+i;
        original[1]=Stack;c.gpr=original;c.gpr[1]=Stack-64;c.gpr[11]=Stack;
        for(unsigned i=0;i<6;++i){c.gpr[26+i]^=0xffffu;c.mmu.put(Stack-24+4*i,original[26+i]);}
        c.mmu.put(Stack+4,Caller);
        c.mmu.put(Call,Branch);c.mmu.put(Caller,Nop);
        for(unsigned i=0;i<restore_words.size();++i)c.mmu.put(Restore+4*i,restore_words[i]);
        for(unsigned i=0;i<tail_words.size();++i)c.mmu.put(Call+4+4*i,tail_words[i]);
    }
    void run_to_blr(bool dispatch){
        need(dispatch?w.start_dispatch(c,Call,Branch,original,0,true):w.start(c,Call,Branch,original,0,true));
        c.pc=Restore;c.lr=Call+4;
        need(w.entry(c,Restore,true));
        for(unsigned i=0;i<7;++i){
            ++c.inst_count;need(w.before(c,Restore+4*i,restore_words[i],true));
            if(i<6)c.gpr[26+i]=c.mmu.read32(Stack-24+4*i);
            else c.pc=c.lr;
        }
        for(unsigned i=0;i<4;++i){
            ++c.inst_count;need(w.before(c,Call+4+4*i,tail_words[i],true));
            if(i==0)c.gpr[0]=c.mmu.read32(c.gpr[1]+68);
            else if(i==1)c.lr=c.gpr[0];
            else if(i==2)c.gpr[1]+=64;
            else c.pc=c.lr;
        }
        need(w.stage()==4&&w.visits()==11&&c.pc==Caller&&c.lr==Caller);
    }
};
}
int main(){
    unsigned valid=0,refused=0;
    for(bool dispatch:{false,true}){
        Fixture f;f.run_to_blr(dispatch);
        if(dispatch){need(f.w.dispatch_poll(f.c,true));++f.c.inst_count;need(f.w.dispatch_resume(f.c,Caller,Nop,true));}
        ++f.c.inst_count;need(f.w.before(f.c,Caller,Nop,true)&&f.w.stage()==5&&f.w.visits()==12);
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
    std::cout<<"V849_RETURN_DISPATCH valid="<<valid<<" refused="<<refused<<" original=0 execution=0\n";
}
