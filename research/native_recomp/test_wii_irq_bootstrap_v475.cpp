#include "wii_irq_bootstrap_v475.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool ok){if(!ok)throw std::runtime_error("IRQ bootstrap");}
struct Mmu {
    std::map<uint32_t,uint32_t> words;
    std::atomic<uint32_t>& mask;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint32_t read32(uint32_t a){
        if(auto value=NativeIosBinding::read32(a))return *value;
        if(a==0xcc003004u)return mask.load();
        auto p=words.find(a);return p==words.end()?0:p->second;
    }
    void write(uint32_t a,uint32_t v){
        const bool native=NativeIosBinding::write32(a,v);
        if(!native&&a==0xcc003004u){mask.store(v);NativeIosBinding::refresh_pi(a);}
        irq_boot_trace.record(a,v,32,native);
    }
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x8052664cu,lr=pc,msr=0x2000u;
    bool is_running=true;uint64_t inst_count=1;
};
int main(){
    for(unsigned fault=0;fault<=12;++fault){
        irq_boot_trace={};
        std::array<uint8_t,8192> one{},two{};std::atomic<uint32_t> mask{0},cause{1u<<8};
        NativeIosTransport host(one,two,cause,mask);
        NativeIosBinding bound(host);
        Cpu c{{{},mask}};auto& m=c.mmu.words;
        VectorEdge e{0x805265acu,0x80526678u,123,456};
        m[c.pc]=789;m[e.pc]=e.entry_word;m[e.lr-4]=e.branch_word;
        m[0x800000c0u]=0x11;m[0x800000ccu]=0x22;
        m[0x800000c4u]=0x33;m[0x800000c8u]=0x44;
        c.gpr[1]=0x80751000;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        IrqMmioWitness w(789,e);
        // No writes before the exact observed IRQ-table return are counted.
        c.mmu.write(0xcd000034u,0);need(w.begin(c));
        if(fault==1)c.mmu.write(0xcd000034u,0x40000000u);
        c.mmu.write(0xcc003004u,fault==2?0xf1u:0xf0u);
        if(fault==3)irq_boot_trace.record(0xcd000034u,0x40000000u,16,true);
        if(fault!=4)c.mmu.write(0xcd000034u,fault==5?0:0x40000000u);
        if(fault==6)c.mmu.write(0xcd000034u,0x40000000u);
        if(fault==7)mask.store(0);
        c.pc=e.pc;c.lr=e.lr;c.inst_count+=12;
        c.gpr[3]=0xcd000000u;c.gpr[4]=0xcc000000u;c.gpr[5]=0xf0u;c.gpr[0]=0x40000000u;
        m[0x800000c4u]=m[0x800000c8u]=0;
        if(fault==8)m[0x800000c8u]=1;
        if(fault==9)m[0x800000ccu]++;
        if(fault==10)c.lr+=4;
        if(fault==11)c.gpr[5]++;
        if(fault==12)c.gpr[1]+=4;
        const auto before=m;bool ok=w.observe(c.pc,c);
        need(ok==(fault==0));need(before==m&&host.serviced_steps()==0&&cause.load()==(1u<<8));
        if(ok){need(w.stage()==2&&irq_boot_trace.count()==2);need(!w.observe(c.pc,c));}
        else need(w.failure()!=0);
    }
    IrqBootTrace unbound;need(!unbound.begin(false));need(!unbound.complete());
    std::cout<<"PASS: real native Hollywood transport, PI mask readback, ordered IRQ bootstrap and 13 negative controls\n";
}
