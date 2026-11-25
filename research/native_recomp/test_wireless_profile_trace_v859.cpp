#include "wii_wireless_profile_trace_v859.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b){std::cerr<<"V859_ASSERT line="<<l.line()<<'\n';std::exit(1);}
}
int main(){
    unsigned valid=0,refused=0;
    WirelessProfileTrace absent;need(!absent.begin({},0,0,1)&&absent.failure()==1);++refused;
    for(unsigned trial=0;trial<27;++trial){
        std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController ctl(banks);
        ExiHostProfile p{};p.latency=1+trial%4;p.di_config=1;
        for(unsigned i=0;i<64;++i)p.sram[i]=uint8_t(17*i+7);
        need(!ExiProfileSession::current());
        ExiProfileSession s(ctl,p);need(ExiProfileSession::current()==&s);
        uint64_t tick=0;
        ctl.write(0,0,0x234u);ctl.write(0,16,0);ctl.write(0,12,0x15u);
        for(unsigned i=0;i<=p.latency;++i)ExiTickBinding::advance(++tick);
        ctl.write(0,12,0x31u);
        for(unsigned i=0;i<=p.latency;++i)ExiTickBinding::advance(++tick);
        ctl.write(0,0,8u);ExiTickBinding::advance(++tick);
        need(s.completed()==2&&s.scheduler().last_completion()->device==2);
        const unsigned ch=trial%4;
        auto guest=s.sram(),wanted=guest;
        wanted[48u+2u*ch]=0;wanted[49u+2u*ch]=0;
        WirelessProfileTrace w;
        if(trial==12)guest[0]^=1u;
        bool ok=w.begin(guest,trial==13?4u:ch,0,tick);
        if(trial==12||trial==13){need(!ok&&w.failure()==1);++refused;continue;}
        need(ok);
        if(trial==24){need(!w.observe_dispatch(tick+1)&&w.failure()==2);++refused;continue;}
        auto visit=[&](){ExiTickBinding::advance(++tick);return w.observe(tick);};
        if(trial==14){need(!w.observe(tick)&&w.failure()==2);++refused;continue;}
        if(trial==15){ctl.write(1,16,1);need(!visit()&&w.failure()==2);++refused;continue;}
        if(trial==16){ctl.write(0,0,0x130u);need(!visit()&&w.failure()==3);++refused;continue;}
        need(visit());guest=wanted;
        if(trial==17){need(!w.preselect(guest,tick-1)&&w.failure()==5);++refused;continue;}
        need(w.preselect(guest,tick));
        ctl.write(0,0,0x130u);need(visit());
        if(trial==18){ctl.write(0,0,8u);need(!visit()&&w.failure()==3);++refused;continue;}
        auto issue=[&](uint32_t word,unsigned n=4u){
            ctl.write(0,16,word);ctl.write(0,12,((n-1u)<<4)|5u);
            for(unsigned i=0;i<=p.latency;++i)if(!visit())return false;
            return true;
        };
        if(trial==19){need(!issue(0xa0000600u,3u)&&w.failure()==3);++refused;continue;}
        if(trial==20){need(!issue(0xa0000640u)&&w.failure()==4);++refused;continue;}
        need(issue(0xa0000600u));
        for(unsigned i=20;i<64;i+=4){
            uint32_t v=0;for(unsigned j=0;j<4;++j)v=(v<<8)|guest[i+j];
            if(trial==21&&i==20){need(!issue(v^1u)&&w.failure()==4);break;}
            need(issue(v));
        }
        if(trial==21){++refused;continue;}
        need(w.bytes()==44&&w.completed()==12&&s.completed()==14);
        if(trial==22){need(!w.deselected(guest,tick)&&w.failure()==5);++refused;continue;}
        ctl.write(0,0,8u);need(visit());need(w.deselected(guest,tick));need(visit());
        need(w.returned(guest,tick)&&w.held()&&s.sram()==guest);
        if(trial==23){ctl.write(0,0,0x130u);need(!w.held());++refused;continue;}
        if(trial==25){need(!w.observe_dispatch(tick+2)&&w.failure()==2);++refused;continue;}
        need(w.observe_dispatch(++tick)&&w.held());
        if(trial==26){need(!w.observe_dispatch(tick)&&w.failure()==2);++refused;continue;}
        need(visit()&&w.held());++valid;
    }
    need(valid==12&&refused==16&&!ExiProfileSession::current());
    std::cout<<"V859_WIRELESS_PROFILE valid="<<valid<<" refused="<<refused<<" bytes=44 tokens=12 prior_tokens=2 scheduler=1 original_execution=0\n";
}
