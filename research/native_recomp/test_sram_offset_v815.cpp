#include "wii_exi_endpoint_scheduler_v495.h"
#include "wii_physical_ram.h"
#include <iostream>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b){std::cerr<<"V815_ASSERT line="<<l.line()<<'\n';throw std::runtime_error("MX offset");}
}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}need(caught);}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned offset=0;offset<64;++offset){
        std::vector<uint8_t> m1(256,0xa5),m2(256,0x5a);WiiPhysicalRam ram(m1,m2);
        std::atomic<uint32_t> cause{0x100};WiiIrqBanks banks(cause);ExiController ctl(banks,&ram);
        ExiMxDevice::Sram before{};for(unsigned i=0;i<64;++i)before[i]=uint8_t(17u*i+7u);
        ExiMxDevice mx(before,[]{return 0x12345678u;});ExiIdEndpoint id(0xffffffffu);
        ExiEndpointScheduler sched(ctl,mx,id,8);uint64_t tick=0;
        auto send=[&](unsigned n,unsigned dir,uint32_t data){
            const auto done=sched.completed();const auto snapshot=mx.sram();const auto dirty=mx.dirty();
            ctl.write(0,16,data);ctl.write(0,12,((n-1u)<<4)|(dir<<2)|1u);
            sched.advance(++tick);
            for(unsigned i=0;i<8;++i){sched.advance(tick+i);need(ctl.pending(0)&&mx.sram()==snapshot&&mx.dirty()==dirty&&sched.completed()==done);}
            tick+=8;sched.advance(tick);
            need(!ctl.pending(0)&&sched.completed()==done+1&&!(ctl.read(0,12)&1u));
            sched.advance(tick);need(sched.completed()==done+1);
            return ctl.read(0,16);
        };
        auto select=[&]{ctl.write(0,0,0x134u);};
        auto deselect=[&]{ctl.write(0,0,8u);};
        select();send(4,1,0xa0000100u+64u*offset);
        need(!mx.dirty()&&mx.sram()==before);
        auto wanted=before;
        for(unsigned i=offset;i<64;){
            const unsigned n=std::min(4u,64u-i);
            uint32_t data=0;for(unsigned j=0;j<n;++j){wanted[i+j]=uint8_t(before[i+j]^0xffu);data|=uint32_t(wanted[i+j])<<(24u-8u*j);}
            send(n,1,data);i+=n;need(mx.sram()==wanted&&mx.dirty());
        }
        deselect();select(); // epoch must reset even without an intermediate tick
        send(4,1,0x20000100u+64u*offset);
        for(unsigned i=offset;i<64;){
            const unsigned n=std::min(4u,64u-i);const uint32_t data=send(n,0,0xdeadbeefu);
            for(unsigned j=0;j<n;++j)need(uint8_t(data>>(24u-8u*j))==wanted[i+j]);
            i+=n;
        }
        need(mx.sram()==wanted&&mx.dirty());
        mx.mark_saved();need(!mx.dirty());deselect();select();
        send(4,1,0x20000100u);
        ctl.write(0,4,0x80000040u);ctl.write(0,8,64);ctl.write(0,12,3);
        sched.advance(++tick);tick+=8;sched.advance(tick);
        need(!ctl.pending(0)&&std::equal(wanted.begin(),wanted.end(),m1.begin()+64)&&!mx.dirty());
        need(m1[63]==0xa5&&m1[128]==0xa5&&m2==std::vector<uint8_t>(256,0x5a));
        ++valid;
    }
    for(unsigned trial=0;trial<8;++trial){
        std::vector<uint8_t> m1(256,0xa5),m2(256,0x5a);WiiPhysicalRam ram(m1,m2);
        std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController ctl(banks,&ram);
        ExiMxDevice::Sram before{};before.fill(0x55);
        ExiMxDevice mx(before,[]{return 0u;});ExiIdEndpoint id(0u);ExiEndpointScheduler sched(ctl,mx,id,8);
        uint64_t tick=0;
        auto issue=[&](unsigned n,unsigned dir,uint32_t data){
            ctl.write(0,16,data);ctl.write(0,12,((n-1u)<<4)|(dir<<2)|1u);sched.advance(++tick);tick+=8;
        };
        ctl.write(0,0,0x134u);
        if(trial<4){
            constexpr std::array<uint32_t,4> bad{0xa00000c0u,0xa0001100u,0xa0000101u,0x20000120u};
            issue(4,1,bad[trial]);
        }else{
            issue(4,1,(trial==6||trial==7?0x20000100u:0xa0000100u)+63u*64u);sched.advance(tick);
            if(trial==4)issue(2,1,0xdead0000u);
            if(trial==5)issue(1,0,0);
            if(trial==6)issue(2,0,0);
            if(trial==7){ctl.write(0,4,0x80000040u);ctl.write(0,8,32u);ctl.write(0,12,3);sched.advance(++tick);tick+=8;}
        }
        const auto req=ctl.pending(0);need(req.has_value());const auto done=sched.completed();
        reject([&]{sched.advance(tick);});
        need(ctl.pending(0)&&ctl.pending(0)->token==req->token&&sched.completed()==done&&mx.sram()==before&&!mx.dirty());
        need(m1==std::vector<uint8_t>(256,0xa5)&&m2==std::vector<uint8_t>(256,0x5a));
        ++refused;
    }
    need(valid==64&&refused==8);
    std::cout<<"V815_SRAM_OFFSET valid=64 refused=8 scheduler=1 readback=1 original_execution=0\n";
}
