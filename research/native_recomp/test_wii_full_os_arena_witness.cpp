#include "wii_full_os_arena_witness.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu {
    std::map<uint32_t,uint8_t> bytes;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint8_t read8(uint32_t a){auto i=bytes.find(a);return i==bytes.end()?0:i->second;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(24-8*i));}
};
struct Cpu {Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80520700u,lr=pc,msr=0x2000u;uint64_t inst_count=100;bool is_running=true;};
static void need(bool b){if(!b)throw std::runtime_error("arena witness");}
int main(){
    const OsArenaExpectations e{{ArenaEdge{0x80521d60u,0x805207ecu,1,2},ArenaEdge{0x80521d48u,0x80520818u,3,4}},5};
    constexpr uint32_t sda=0x8070e8e0u,base=sda-3512,record=sda-3516,fallback=sda-3520,field=sda-3216,mode=sda-16864,lo=sda-16400,hi=sda-3472;
    for(unsigned path=0;path<6;++path)for(unsigned fault=0;fault<12;++fault){
        Cpu c;c.gpr[1]=0x80751c68u;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        const uint32_t boot=path>=3?0x80038000u:0u,legacy=(path==1||path==4)?0x81700000u:0u;
        const uint32_t hint=(path==0||path==3)?0x80800000u:0u,high=(path==2||path==5)?0x81780000u:0u,over=path==5?0x80802000u:0u;
        const uint32_t selected=hint?hint:over?over:0x80753cc0u,upper=high?high:legacy?legacy:0x81700000u;
        auto put=[&](uint32_t a,uint32_t v){c.mmu.write32(a,v);};
        put(0x800000f4,boot);put(0x80000034,legacy);put(0x80000030,over);put(0x8000310c,hint);put(0x80003110,high);
        c.mmu.bytes[0x800030e8]=0x12;c.mmu.bytes[0x800030e9]=0x34;
        if(boot){put(boot+12,0xabcdef56);put(boot+36,0x12345678);}
        put(fallback,6);put(field,7);put(lo-4,8);put(hi+4,9);put(hi,10);
        for(auto edge:e.edges){put(edge.pc,edge.entry_word);put(edge.lr-4,edge.branch_word);}put(0x80520818,e.stop_word);
        FullOsArenaWitness w(e);auto before=c.mmu.bytes;need(w.begin(c)&&before==c.mmu.bytes);
        put(base,0x80000000);put(mode,1);put(record,boot?boot+12:legacy?fallback:0);
        if(boot){put(field,0x12345678);c.mmu.bytes[0x800030e8]=0x56;c.mmu.bytes[0x800030e9]=0x78;}
        else if(legacy){put(field,0x34);put(fallback,0x12);}
        if(fault==1)put(record,1);
        if(fault==2)put(mode,0);
        if(fault==3)put(0x80000030,1);
        if(fault==4)put(lo-4,0);
        c.pc=e.edges[0].pc;c.lr=e.edges[0].lr;c.inst_count+=30;c.gpr[3]=fault==5?0x80000004:selected;
        if(fault==6)c.lr+=4;
        before=c.mmu.bytes;bool ok=w.observe(c.pc,c);need(before==c.mmu.bytes);
        if(fault>=1&&fault<=6){need(!ok);continue;}need(ok);
        put(lo,fault==7?0:selected);c.pc=e.edges[1].pc;c.lr=e.edges[1].lr;c.inst_count+=10;c.gpr[3]=fault==8?upper-4:upper;
        if(fault==9)put(hi,0);
        before=c.mmu.bytes;ok=w.observe(c.pc,c);need(before==c.mmu.bytes);
        if(fault>=7&&fault<=9){need(!ok);continue;}need(ok);
        put(hi,fault==10?upper-4:upper);c.pc=0x80520818;c.lr=c.pc;c.inst_count+=2;if(fault==11)c.msr^=0x8000;
        before=c.mmu.bytes;ok=w.observe(c.pc,c);need(before==c.mmu.bytes);
        need(ok==(fault==0));if(ok){need(w.stage()==4&&!w.active());need(!w.observe(c.pc,c));}
    }
    std::cout<<"PASS: six boot/arena paths, 66 negative controls and duplicate stops\n";
}
