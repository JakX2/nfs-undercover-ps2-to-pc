#include "wii_exception_pack_route_v466.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu{
    std::map<uint32_t,uint8_t> mem;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint8_t read8(uint32_t a)const{auto p=mem.find(a);return p==mem.end()?0:p->second;}
    uint32_t read32(uint32_t a)const{uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)mem[a+i]=uint8_t(v>>(24u-8u*i));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80520bf4u,lr=0x805208acu,msr=0x2000u;
    uint64_t inst_count=100;bool is_running=true;
    uint32_t guest_flush_count=0,guest_invalidate_count=0,guest_sync_count=0,guest_isync_count=0;
    std::array<uint32_t,256> guest_flush_lines{},guest_invalidate_lines{};
};
static void need(bool b){if(!b)throw std::runtime_error("exception pack");}
int main(){
    constexpr uint32_t table=0x8060bbe0u,source=0x80520ec0u,sys=0x805290a8u,
        sda=0x8070e8e0u,sp=0x80751c68u,sd=0x80000c00u;
    for(unsigned mode=0;mode<2;++mode)for(unsigned fault=0;fault<16;++fault){
        ExceptionPackRouteExpectations e{};auto& im=e.image;
        Cpu c;c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        for(unsigned i=0;i<12;++i)c.gpr[20+i]=0x12340000u+i;
        for(unsigned i=0;i<15;++i){
            unsigned index=i;if(mode&&i==3)index=11;else if(mode&&i==11)index=3;
            im.offsets[i]=0x100u*(index+1);c.mmu.write32(table+4u*i,im.offsets[i]);
            const uint32_t dest=0x80000000u+im.offsets[i];
            c.mmu.mem[dest-1]=0xa5;c.mmu.mem[dest+152]=0x5a;
            for(unsigned n=0;n<152;++n)c.mmu.mem[dest+n]=0xcc;
        }
        c.mmu.write32(table+60,0xdeadbeefu);c.mmu.write32(0x8000303c,0x76543210u);
        for(unsigned i=0;i<152;++i){im.handler[i]=uint8_t(i*3u+17u);c.mmu.mem[source+i]=im.handler[i];}
        for(unsigned i=0;i<28;++i){im.syscall[i]=uint8_t(0xc7u^i);c.mmu.mem[sys+i]=im.syscall[i];}
        auto make_edge=[&](uint32_t pc,uint32_t lr,uint32_t id){
            c.mmu.write32(pc,0x11110000u+(pc&0xffffu));c.mmu.write32(lr-4,0x22220000u+id);
            return VectorEdge{pc,lr,0x22220000u+id,0x11110000u+(pc&0xffffu)};
        };
        e.exception_edges[0]=make_edge(0x80004338u,0x80520d9cu,0);
        e.exception_edges[1]=make_edge(0x80522320u,0x80520da8u,1);
        e.exception_edges[2]=make_edge(0x80522378u,0x80520db8u,2);
        e.exception_edges[3]=make_edge(0x804e50a0u,0x80520cc8u,3);
        e.exception_edges[4]=make_edge(0x80545134u,0x80520e64u,4);
        e.exception_count=5;
        e.syscall_edges[0]=make_edge(0x80004338u,0x805290f8u,5);
        e.syscall_edges[1]=make_edge(0x80522320u,0x80529104u,6);
        e.syscall_edges[2]=make_edge(0x80522378u,0x80529114u,7);
        e.syscall_count=3;e.syscall_entry=make_edge(0x805290c8u,0x805208b0u,8);
        e.alarm_entry=make_edge(0x805210ccu,0x805208b4u,9);
        e.vector_return_word=0x99999999u;c.mmu.write32(0x80520db8u,e.vector_return_word);
        if(fault==1)e.exception_count=33;
        ExceptionPackRoute route(e);
        bool ok=route.begin(c);need(ok==(fault!=1));if(!ok)continue;
        auto set=[&](VectorEdge edge){c.pc=edge.pc;c.lr=edge.lr;c.inst_count+=10;};
        auto observe=[&](VectorEdge edge){set(edge);const auto prior=c.mmu.mem;bool pass=route.observe(c.pc,c);need(prior==c.mmu.mem);return pass;};
        c.gpr[1]=sp-64u;c.mmu.write32(source+0x58,0x60000000u);c.mmu.write32(sda-3552u,0x80003000u);
        for(unsigned i=0;i<15;++i){
            const uint32_t dest=0x80000000u+im.offsets[i];
            c.gpr[29]=i;c.gpr[3]=dest;c.gpr[4]=source;c.gpr[5]=152u;
            if(i){
                need(observe(e.exception_edges[3]));
                if(fault==2&&i==2)c.gpr[29]++;
                if(fault==3&&i==2)c.gpr[3]+=32;
                if(fault==4&&i==2)c.mmu.write32(e.exception_edges[0].lr-4,0);
                ok=observe(e.exception_edges[0]);
                if(fault>=2&&fault<=4&&i==2){need(!ok);break;}
                need(ok);
            }else{set(e.exception_edges[0]);need(route.first_copy(c));}
            for(unsigned n=0;n<152;++n)c.mmu.mem[dest+n]=c.mmu.read8(source+n);
            c.mmu.mem[dest+0x6b]=uint8_t(im.handler[0x6b]|i);
            c.mmu.write32(0x80003000u+4u*i,0x80520f5cu);
            c.gpr[4]=152u;
            if(fault==5&&i==2)c.gpr[4]--;
            auto cache_event=[&](unsigned n){
                if(i==0){set(e.exception_edges[n]);return route.first_vector_event(c.pc,c,n+1);}
                return observe(e.exception_edges[n]);
            };
            ok=cache_event(1);if(fault==5&&i==2){need(!ok);break;}need(ok);
            for(unsigned n=0;n<5;++n)c.guest_flush_lines[c.guest_flush_count++]=dest+32u*n;
            ++c.guest_sync_count;
            if(fault==6&&i==2)c.mmu.write32(e.exception_edges[2].pc,0);
            ok=cache_event(2);if(fault==6&&i==2){need(!ok);break;}need(ok);
            for(unsigned n=0;n<5;++n)c.guest_invalidate_lines[c.guest_invalidate_count++]=dest+32u*n;
            ++c.guest_sync_count;++c.guest_isync_count;
            c.pc=c.lr=0x80520db8u;c.inst_count+=10;
            if(fault==7&&i==2)c.lr+=4;
            if(fault==8&&i==2)c.inst_count-=10;
            ok=i==0?route.first_vector_event(c.pc,c,4):route.observe(c.pc,c);
            if((fault==7||fault==8)&&i==2){need(!ok);break;}need(ok&&route.vectors()==i+1);
            if(fault==9&&i==2){
                c.inst_count+=10;need(!route.observe(c.pc,c));ok=false;break;
            }
            if(fault==10&&i==2){ok=observe(e.syscall_entry);need(!ok);break;}
        }
        if(fault>=2&&fault<=10){need(!ok&&route.failure()!=0);continue;}
        need(observe(e.exception_edges[4]));
        c.gpr[1]=sp;c.gpr[29]=0x12340009u;
        if(fault==11)c.mmu.mem[0x80000000u+im.offsets[5]]++;
        ok=observe(e.syscall_entry);if(fault==11){need(!ok);continue;}need(ok&&route.phase()==3);
        c.gpr[3]=sd;c.gpr[4]=sys;c.gpr[5]=28;
        if(fault==12)c.gpr[5]=24;
        ok=observe(e.syscall_edges[0]);if(fault==12){need(!ok);continue;}need(ok);
        for(unsigned n=0;n<28;++n)c.mmu.mem[sd+n]=im.syscall[n];
        c.gpr[4]=256;
        if(fault==13){need(!observe(e.syscall_edges[2]));continue;}
        need(observe(e.syscall_edges[1]));
        for(unsigned n=0;n<8;++n)c.guest_flush_lines[c.guest_flush_count++]=sd+32u*n;
        ++c.guest_sync_count;
        need(observe(e.syscall_edges[2]));
        for(unsigned n=0;n<8;++n)c.guest_invalidate_lines[c.guest_invalidate_count++]=sd+32u*n;
        ++c.guest_sync_count;++c.guest_isync_count;
        if(fault==14)c.mmu.mem[sd+28]++;
        if(fault==15)c.mmu.write32(e.alarm_entry.lr-4,0);
        ok=observe(e.alarm_entry);need(ok==(fault==0));
        if(ok){need(route.phase()==4&&route.vectors()==15);need(!observe(e.alarm_entry));}
    }
    std::cout<<"PASS: two full exception routes, 30 negative controls, original edge and loop-order checks\n";
}
