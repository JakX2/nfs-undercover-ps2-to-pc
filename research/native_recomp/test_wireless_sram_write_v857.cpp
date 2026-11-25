#include "wii_wireless_sram_write_v857.h"
#include "wii_exi_endpoint_scheduler_v495.h"
#include <cstdlib>
#include <iostream>
#include <source_location>
using namespace undercover::wii;
static void need(bool ok,const std::source_location l=std::source_location::current()){
    if(!ok){std::cerr<<"V857_ASSERT line="<<l.line()<<'\n';std::exit(1);}
}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned trial=0;trial<28;++trial){
        std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController ctl(banks);
        ExiMxDevice::Sram seed{};for(unsigned i=0;i<64;++i)seed[i]=uint8_t(17u*i+7u);
        ExiMxDevice mx(seed,[]{return 0u;});ExiIdEndpoint id(0x12345678u);
        ExiEndpointScheduler scheduler(ctl,mx,id,1u+trial);
        WirelessSramWriteTrace trace;
        uint64_t tick=0;
        auto complete=[&](uint32_t tx,unsigned length=4u){
            ctl.write(0,16,tx);ctl.write(0,12,((length-1u)<<4)|5u);
            const auto q=ctl.pending(0);need(q.has_value());scheduler.advance(++tick);
            tick+=1u+trial;scheduler.advance(tick);need(!ctl.pending(0));return *q;
        };
        // Genuine earlier device traffic, not an artificial count reset.
        ctl.write(0,0,0x200u);complete(0,2);ctl.write(0,12,0x31u);
        scheduler.advance(++tick);tick+=1u+trial;scheduler.advance(tick);
        ctl.write(0,0,8u);scheduler.advance(++tick);need(scheduler.completed()==2);
        const unsigned ch=trial%4;
        auto desired=seed;desired[48+2*ch]=0;desired[49+2*ch]=0;
        auto guest=seed;
        if(trial==12)guest[0]^=1u;
        const auto new_id=trial==13?uint16_t((unsigned(seed[48+2*ch])<<8)|seed[49+2*ch]):0u;
        bool ok=trace.begin(ctl,mx,scheduler.completed(),guest,trial==14?4u:ch,new_id);
        if(trial>=12&&trial<=14){need(!ok&&trace.failure()==1u);++refused;continue;}
        need(ok);guest=desired;
        if(trial==15)guest[0]^=1u;
        if(trial==16){ctl.write(0,0,0x100u);ctl.write(0,0,0u);}
        ok=trace.preselect(ctl,mx,scheduler.completed()+(trial==17),guest);
        if(trial>=15&&trial<=17){need(!ok&&trace.failure()==2u);++refused;continue;}
        need(ok);ctl.write(0,0,0x130u);
        auto q=complete(trial==18?0xa0000640u:0xa0000600u);
        // Short command is rejected by the actual device before the trace;
        // use a forged length on the observed record instead.
        if(trial==19)q.length=3u;
        if(trial==20)q.device=2u;
        ok=trace.record(q,ctl,mx,scheduler.completed()+(trial==21));
        if(trial==18||trial==19||trial==20||trial==21){need(!ok&&trace.failure()==3u);++refused;continue;}
        need(ok);
        if(trial==22){need(!trace.record(q,ctl,mx,scheduler.completed()));++refused;continue;}
        for(unsigned i=20;i<64;i+=4){
            uint32_t word=0;for(unsigned j=0;j<4;++j)word=(word<<8)|desired[i+j];
            if(trial==23&&i==20)word^=1u;
            q=complete(word);
            ok=trace.record(q,ctl,mx,scheduler.completed());
            if(trial==23){need(!ok&&trace.failure()==3u);break;}
            need(ok);
        }
        if(trial==23){++refused;continue;}
        need(trace.stage()==3u&&trace.bytes()==44u&&trace.completed()==12u);
        if(trial==24){need(!trace.deselected(ctl,mx,scheduler.completed(),guest));++refused;continue;}
        ctl.write(0,0,8u);scheduler.advance(++tick);
        need(trace.deselected(ctl,mx,scheduler.completed(),guest));
        if(trial==25)guest[2]^=1u;
        if(trial==26)mx.mark_saved();
        if(trial==27){ctl.write(0,0,0x100u);ctl.write(0,0,0u);}
        ok=trace.returned(ctl,mx,scheduler.completed(),guest);
        if(trial>=25){need(!ok&&trace.failure()==5u);++refused;continue;}
        need(ok&&trace.held(ctl,mx,scheduler.completed())&&scheduler.completed()==14u&&mx.sram()==desired);
        ++valid;
    }
    need(valid==12&&refused==16);
    std::cout<<"V857_WIRELESS_SRAM_TRACE valid="<<valid<<" refused="<<refused<<" transfers=12 bytes=44 prior_tokens=2 real_device=1 original_execution=0\n";
}
