#include "wii_sram_write_witness_v818.h"
#include "wii_exi_endpoint_scheduler_v495.h"
#include "wii_physical_ram.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
static void need(bool ok,const std::source_location l=std::source_location::current()){
    if(!ok){std::cerr<<"V818_ASSERT line="<<l.line()<<'\n';throw std::runtime_error("SRAM write witness");}
}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned t=0;t<80;++t){
        std::vector<uint8_t> m1(256,0x55),m2(256,0xaa);WiiPhysicalRam ram(m1,m2);
        std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController ctl(banks,&ram);
        ExiMxDevice::Sram seed{};for(unsigned i=0;i<64;++i)seed[i]=uint8_t(7u+13u*i);
        ExiMxDevice mx(seed,[]{return 0u;});ExiIdEndpoint id(0u);ExiEndpointScheduler scheduler(ctl,mx,id,8);
        SramWriteWitness w;
        const unsigned offset=t<64?t:20u;
        auto wanted=seed;for(unsigned i=offset;i<64;++i)wanted[i]^=0xffu;
        auto select=[&]{ctl.write(0,0,0x134u);};
        auto deselect=[&]{ctl.write(0,0,8u);};
        uint64_t tick=0;
        auto issue=[&](unsigned n,uint32_t data){
            ctl.write(0,16,data);ctl.write(0,12,((n-1u)<<4)|5u);
            auto q=ctl.pending(0);need(q.has_value());scheduler.advance(++tick);return *q;
        };
        auto complete=[&]{tick+=8;scheduler.advance(tick);need(!ctl.pending(0));};
        if(t==64)wanted[0]^=1u;
        if(t==65)select();
        bool ok=w.begin(ctl,mx,t==66?64u:offset,wanted);
        if(t>=64&&t<=66){need(!ok&&w.failure()==1);++refused;continue;}
        need(ok);select();
        auto q=issue(4,0xa0000100u+64u*(offset+(t==67?1u:0u)));
        if(t==68){need(!w.record(q,ctl,mx)&&w.failure()==2);++refused;continue;}
        complete();
        if(t==69)q.token=0;
        if(t==70)q.device=2;
        if(t==71)ctl.write(0,16,q.tx^1u);
        ok=w.record(q,ctl,mx);
        if(t>=67&&t<=71){need(!ok&&w.failure()==(t==67?3u:2u));++refused;continue;}
        need(ok&&w.stage()==2&&w.completed()==1&&w.bytes()==0);
        if(t==72){need(!w.record(q,ctl,mx)&&w.failure()==2);++refused;continue;}
        if(t==73){deselect();select();q=issue(4,0xa0000100u+64u*offset);complete();
            need(!w.record(q,ctl,mx)&&w.failure()==4);++refused;continue;}
        if(t==74){need(!w.finish(ctl,mx)&&w.failure()==6);++refused;continue;}
        unsigned sent=0;
        for(unsigned i=offset;i<64;){
            // Alternate chunk widths; real EXIImmEx typically emits full
            // words then a short tail, but the witness accepts any legal mix.
            const unsigned n=std::min(1u+(i+t)%4u,64u-i);
            uint32_t data=0;for(unsigned j=0;j<n;++j)data|=uint32_t(wanted[i+j])<<(24u-8u*j);
            if(t==75&&i==offset)data^=0x01000000u;
            q=issue(n,data);complete();
            if(t==76&&i==offset)mx.mark_saved();
            if(t==77&&i==offset){auto forged=q;forged.channel=1;q=forged;}
            ok=w.record(q,ctl,mx);
            if(t>=75&&t<=77){need(!ok&&w.failure()==(t==75?4u:t==76?5u:2u));break;}
            need(ok);i+=n;++sent;need(w.bytes()==i-offset&&w.completed()==sent+1);
        }
        if(t>=75&&t<=77){++refused;continue;}
        need(w.stage()==3&&w.bytes()==64u-offset&&mx.sram()==wanted);
        if(t==78){need(!w.finish(ctl,mx)&&w.failure()==6);++refused;continue;}
        deselect();
        if(t==79)mx.mark_saved();
        ok=w.finish(ctl,mx);
        if(t==79){need(!ok&&w.failure()==6);++refused;continue;}
        need(ok&&w.stage()==4&&scheduler.completed()==w.completed()&&mx.dirty());
        need(m1==std::vector<uint8_t>(256,0x55)&&m2==std::vector<uint8_t>(256,0xaa));
        ++valid;
    }
    need(valid==64&&refused==16);
    std::cout<<"V818_SRAM_WRITE_WITNESS valid=64 refused=16 real_device=1 real_scheduler=1 original_execution=0\n";
}
