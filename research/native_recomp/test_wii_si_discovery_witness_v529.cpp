#include "wii_si_discovery_witness_v529.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI discovery witness");}
struct Mmu{
    std::map<uint32_t,uint32_t> mem;uint8_t byte=0;SiController* si=nullptr;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){
        if(si&&a>=0xcd006430u&&a<0xcd006500u)return si->read(a-0xcd006400u);
        auto i=mem.find(a);return i==mem.end()?0:i->second;
    }
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=10000;};
int main(){
    constexpr uint32_t sp=0x80751000,r13=0x8070e8e0,id=0xbeef0010,Data=0x80619a60u,
        TypeData=Data+24,Slot=0x806fe340u,TypeTime=Slot+160,Callback=0x805327f8u,Delay=3948;
    constexpr SiDiscoveryExpectations e{{VectorEdge{0x80532aa8,0x80532110,1,2},VectorEdge{0x80532aa8,0x80532118,3,2},
        VectorEdge{0x80532aa8,0x80532120,4,2},VectorEdge{0x80532aa8,0x80532128,5,2}},
        {0x8053268c,0x80532c38,6,7},{0x80532140,0x8053279c,8,9},{0x80528754,0x805208d0,10,11}};
    for(unsigned fault=0;fault<=17;++fault){
        exi_id_completion={};si_sampling_trace={};si_discovery_trace={};
        need(exi_id_completion.begin(true));
        exi_id_completion.record({1,0,2,2,1,0},0);exi_id_completion.record({2,0,2,4,0,0},id);
        need(exi_id_completion.finish());
        need(si_sampling_trace.begin(0x000f0200,0));
        si_sampling_trace.vi(false,0);si_sampling_trace.si(true,SiController::Poll,0x000f0200);
        si_sampling_trace.si(false,SiController::Control,0);si_sampling_trace.si(true,SiController::Control,SiController::TC_INT);
        need(si_sampling_trace.finish());
        std::atomic<uint32_t> pi{0};SiController si(pi);Cpu c;c.mmu.si=&si;auto& m=c.mmu.mem;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;c.gpr[3]=0;
        m[r13-3824]=id;m[r13-3148]=1;m[0x800000f8]=243000000;m[Data]=0xffffffffu;
        m[Data+4]=si_sampling_trace.poll();m[0x80003090]=0x80531b34;
        for(unsigned i=0;i<4;++i){m[TypeData+4*i]=8;m[Slot+32*i]=0xffffffffu;}
        for(auto x:{e.type[0],e.type[1],e.type[2],e.type[3],e.transfer,e.start,e.sram}){
            m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;
        }
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;c.inst_count+=100;};
        enter(e.type[0]);SiDiscoveryWitness w(e);
        if(fault==1)c.msr|=0x8000u;
        need(w.begin(c,fault!=2)==(fault!=1&&fault!=2));
        if(fault==1||fault==2)continue;
        bool rejected=false;
        for(unsigned ch=0;ch<4;++ch){
            if(ch){
                enter(e.type[ch]);c.gpr[1]=sp;c.gpr[3]=ch;
                if(fault==3&&ch==1)c.gpr[3]=0;
                if(fault==4&&ch==1)c.lr^=4;
                const bool bad=ch==1&&(fault==3||fault==4||fault==5||fault==6);
                need(w.observe(c.pc,c)==!bad);
                if(bad){rejected=true;break;}
            }
            enter(e.transfer);c.gpr[1]=sp-32;c.gpr[3]=ch;c.gpr[4]=r13-3144;
            c.gpr[5]=1;c.gpr[6]=TypeData+4*ch;c.gpr[7]=3;c.gpr[8]=Callback;c.gpr[9]=0;c.gpr[10]=Delay;
            m[TypeData+4*ch]=128;m[TypeTime+8*ch+4]=5000+1000*ch;
            if(fault==7&&ch==0)c.gpr[7]=4;
            if(fault==8&&ch==1)m[TypeTime+8*ch+4]=5000;
            if(fault==9&&ch==0)c.gpr[10]=0;
            if(fault==10&&ch==0)m[Slot+128]=1;
            const bool bad=(ch==0&&(fault==7||fault==9||fault==10))||(ch==1&&fault==8);
            need(w.observe(c.pc,c)==!bad);
            if(bad){rejected=true;break;}
            enter(e.start);c.gpr[1]=sp-96;
            if(fault==11&&ch==0)c.gpr[1]+=4;
            need(w.observe(c.pc,c)==!(fault==11&&ch==0));
            if(fault==11&&ch==0){rejected=true;break;}
            if(!ch){
                auto read=[&](unsigned off){si_discovery_trace.mmio(false,off,si.read(off));};
                auto write=[&](unsigned off,uint32_t v){si.write(off,v);si_discovery_trace.mmio(true,off,v);};
                read(SiController::Status);write(SiController::Status,0);
                write(SiController::Buffer,fault==5?1u:0u);read(SiController::Control);
                write(SiController::Control,0xc0010301);
                const auto q=*si.pending();m[Data]=0;m[Data+8]=3;m[Data+12]=TypeData;m[Data+16]=Callback;
                if(fault!=12){
                    if(fault==6)si.complete(q.token,std::array<uint8_t,3>{1,2,3});
                    else si.complete(q.token,{},SiController::ERR_NOREP);
                    si_discovery_trace.completion(q,si,c.inst_count+8);
                }
            }else{
                const std::array<uint32_t,8> packet{ch,r13-3144,1,TypeData+4*ch,3,Callback,0,Delay};
                for(unsigned i=0;i<8;++i)m[Slot+32*ch+4*i]=packet[i];
            }
        }
        if(rejected)continue;
        enter(e.sram);c.gpr[1]=sp+16;m[0xcc003000]=pi.load();m[0xcc003004]=0xf8;
        if(fault==13)m[Slot+32*2+4]^=4;
        if(fault==14)m[Data+16]=0;
        if(fault==15)m[0xcc003000]=0;
        if(fault==16)c.gpr[1]-=4;
        if(fault==17)m[TypeTime+4]^=1;
        need(w.observe(c.pc,c)==(fault==0));if(!fault)need(w.stage()==13);
    }
    std::cout<<"PASS: SI type transfer, native NOREP, four original query ABIs, three guest queue packets and 17 negative controls\n";
}
