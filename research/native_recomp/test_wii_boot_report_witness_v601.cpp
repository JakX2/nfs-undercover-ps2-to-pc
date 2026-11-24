#include "wii_boot_report_witness_v600.h"
#include <iostream>
#include <map>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=BootReportWitness;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V601 line "+std::to_string(loc.line()));
}
struct Mmu{
    std::map<uint32_t,uint8_t> mem;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint8_t read8(uint32_t a){auto it=mem.find(a);return it==mem.end()?0:it->second;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)mem[a+i]=uint8_t(v>>(24-8*i));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    struct Cr{bool eq=false;};std::array<Cr,8> cr{};
    uint32_t pc=0,lr=0,ctr=0,msr=0x32;uint64_t inst_count=10;bool is_running=true;
};
constexpr uint32_t R13=0x8070e8e0u,Sp=0x80751c60u,Bctr=0x805204e8u;
constexpr std::array<uint32_t,4> Arenas{0x80754000,0x81700000,0x90000800,0x93e00000};
constexpr std::array<uint32_t,4> Off{16400,3472,16396,3468};
static uint32_t branch(uint32_t pc,uint32_t target){return 0x48000001u|((target-pc)&0x03fffffcu);}
static BootReportEdge edge(uint32_t pc,uint32_t lr){return {pc,lr,branch(lr-4,pc),0x60000000u};}
static BootReportExpectations expected(){
    BootReportExpectations e{};
    e.report=edge(0x805203c4,0x805208f8);e.console=edge(0x8051fd44,0x80520410);e.mem2=edge(0x8052701c,0x8051fec8);
    e.getters={edge(0x80527034,0x805205fc),edge(0x80527028,0x80520604),edge(0x80521d18,0x8052061c),edge(0x80521d30,0x80520624),edge(0x80521d20,0x8052063c),edge(0x80521d38,0x80520644)};
    e.helpers.push_back(edge(0x805450e8,0x805203d0));
    e.bctr=Bctr;e.bctr_word=0x4e800420;e.console_return=0x60000000;e.entry_word=e.report.branch;e.return_word=0x60000000;
    for(unsigned i=0;i<26;++i){e.table[i]=W::Case+16*(i%7);for(unsigned j=0;j<4;++j)e.data[496+4*i+j]=uint8_t(e.table[i]>>(24-8*j));}
    e.case_words.fill(0x60000000);e.small[0]=0x80;e.small[1]=0x60;e.small[2]=0xb7;e.small[3]=0xa8;
    auto add=[&](uint32_t lr){e.calls.push_back({lr,branch(lr-4,W::Print),0x60000000});};
    for(uint32_t lr:{0x805203ecu,0x80520400u,0x8052040cu,0x8052047cu,0x8052048cu,0x805204c0u,0x8052055cu,0x805205acu,0x805205f8u,0x80520618u,0x80520638u,0x80520658u,W::Return})add(lr);
    for(unsigned i=0;i<6;++i)add(W::Case+16*i+12);
    // In the original, several report resumes are themselves the next BL.
    for(auto& c:e.calls){
        if(c.lr==e.console.lr-4)c.resume=e.console.branch;
        for(auto g:e.getters)if(c.lr==g.lr-4)c.resume=g.branch;
        if(c.lr==W::Return)c.resume=e.return_word;
    }
    return e;
}
struct Rejected{};
static void trial(unsigned mode,unsigned fault){
    auto e=expected();if(mode&1u)e.size_sources={0x8000311cu,0x80003104u};W w(e);Cpu c;
    const bool table=mode>=2&&mode<9;const uint32_t value=mode==0?0x10000002u:mode==1?17u:mode<9?0x10000008u+mode-2:mode-9u;
    const uint32_t target=table?e.table[value-0x10000008u]:0;
    c.gpr[1]=Sp;c.gpr[2]=0x80715ee0;c.gpr[13]=R13;c.pc=c.lr=W::Begin;
    auto put=[&](uint32_t a,uint32_t v){c.mmu.write32(a,v);};
    put(W::Begin,e.entry_word);put(R13-3400,1);
    for(unsigned i=0;i<e.data.size();++i)c.mmu.mem[W::Data+i]=e.data[i];
    for(unsigned i=0;i<e.small.size();++i)c.mmu.mem[W::Small+i]=e.small[i];
    for(unsigned i=0;i<4;++i)put(R13-Off[i],Arenas[i]);
    put(0x80003100,0x01800000);put(0x80003104,0x01800000);put(0x8000311c,0x04000000);put(0x80003140,0x00040a21);put(0x80003144,0x00191226);
    auto load=[&](BootReportEdge a){put(a.pc,a.entry);put(a.lr-4,a.branch);};
    load(e.report);load(e.console);load(e.mem2);for(auto a:e.getters)load(a);for(auto a:e.helpers)load(a);
    for(auto a:e.calls){put(a.lr-4,a.branch);put(a.lr,a.resume);}
    // Restore adjacent callsites overwritten by synthetic resume setup.
    for(auto a:e.getters)load(a);
    load(e.console);load(e.report);
    put(e.bctr,e.bctr_word);put(e.console.lr,e.console_return);for(unsigned i=0;i<7;++i)put(W::Case+16*i,e.case_words[i]);
    if(fault==1)put(R13-3400,0);
    if(fault==2)put(R13-Off[0],Arenas[1]);
    need(w.begin(c)==(fault!=1&&fault!=2));if(fault==1||fault==2)return;
    auto event=[&](uint32_t pc,unsigned f=0){c.inst_count+=10;
        const bool ok=w.observe(pc,c);need(ok==(!f||fault!=f));if(!ok)throw Rejected{};};
    auto enter=[&](BootReportEdge x,unsigned f=0){c.pc=x.pc;c.lr=x.lr;event(c.pc,f);};
    auto report=[&](uint32_t lr,uint32_t fmt,std::array<uint32_t,3> a={},unsigned fault_arg=0){
        c.pc=W::Print;c.lr=lr;c.gpr[3]=fmt;for(unsigned i=0;i<3;++i)c.gpr[4+i]=a[i];
        if(fault_arg&&fault==fault_arg)c.gpr[4]^=1;
        if(lr==0x805203ec&&fault==3)c.gpr[3]+=4;
        if(lr==0x805203ec&&fault==4)c.cr[1].eq=true;
        if(lr==0x805203ec&&fault==5)c.gpr[1]-=4;
        const unsigned f=lr==0x805203ec&&fault>=3&&fault<=5?fault:fault_arg;
        event(c.pc,f);
        // One nested original-like helper entry before each explicit resume.
        const uint32_t saved=c.gpr[1];c.gpr[1]-=32;c.pc=0x80540000;c.lr=0x80522f40;event(c.pc);
        c.gpr[1]=saved;c.pc=c.lr=lr;
        if(lr==0x805203ec&&fault==6)c.pc+=4;
        if(lr==0x805203ec&&fault==7)put(lr,0);
        event(lr,lr==0x805203ec&&(fault==6||fault==7)?fault:0);
    };
    bool rejected=false;
    try{
        enter(e.report);c.gpr[1]=Sp-16;enter(e.helpers[0]);
        report(0x805203ec,W::Data+72);report(0x80520400,W::Data+88,{W::Data+112,W::Data+124,0},8);
        report(0x8052040c,W::Data+136);enter(e.console);
        if(mode)enter(e.mem2);
        c.pc=c.lr=e.console.lr;c.gpr[3]=value;
        if(fault==9)c.lr+=4;
        event(e.console.lr,9);
        if(table){
            c.ctr=target;if(fault==10)c.ctr+=16;event(e.bctr,10);
            c.pc=target;if(fault==11)c.pc+=4;event(target,11);
        }
        if(value==17)report(0x8052047c,W::Data+152);
        else if(value==18)report(0x8052048c,W::Data+176);
        else if(value<32u)report(0x805204c0,W::Data+232,{value,0,0},20);
        else if(table&&target!=W::Case+96)report(target+12,W::Data+244+12*((target-W::Case)/16));
        else report(0x8052055c,W::Data+328,{value,0,0});
        report(0x805205ac,W::Data+384,{4,10,33},12);report(0x805205f8,W::Data+412,{19,12,2026},13);
        enter(e.getters[fault==14?1:0],14);enter(e.getters[1]);report(0x80520618,W::Data+424,{88,0,0},15);
        enter(e.getters[2]);enter(e.getters[3]);report(0x80520638,W::Data+440,{Arenas[0],Arenas[1],0},16);
        enter(e.getters[4]);enter(e.getters[5]);report(0x80520658,W::Data+468,{Arenas[2],Arenas[3],0},17);
        c.gpr[1]=Sp;if(fault==18)put(R13-Off[3],0);
        c.pc=W::Print;c.lr=W::Return;c.gpr[3]=R13-16436;c.gpr[4]=W::Data;event(c.pc,18);
        c.pc=c.lr=W::Return;if(fault==19)c.mmu.mem[W::Data+72]^=1;
        event(c.pc,19);
    }catch(const Rejected&){rejected=true;}
    need(rejected==(fault!=0));
    if(!fault){need(w.stage()==3&&w.reports()==10&&w.getters()==6&&w.computed()==table);need(!w.observe(W::Return,c));}
    else need(w.failure()!=0);
}
int main(){
    for(unsigned mode=0;mode<41;++mode)trial(mode,0);
    trial(9,20);
    for(unsigned fault=1;fault<=19;++fault)trial(2,fault);
    std::cout<<"V601_BOOT_REPORT paths=41 reports=410 getters=246 refusal=20 table_cases=7 output_backend=0 boot_verified=0\n";
}
