#include "open_cache_range_trace_v649.h"
#include <array>
#include <iostream>
#include <stdexcept>
using namespace undercover::wii;
static void need(bool v){if(!v)throw std::runtime_error("V649 test assertion");}
struct Mmu{
    std::array<uint8_t,0x2000> bytes{};
    uint8_t* get_ptr(uint32_t a){return a>=0x81000000u&&a<0x81002000u?bytes.data()+(a-0x81000000u):nullptr;}
};
struct Cpu{
    Mmu mmu;bool is_running=true;uint32_t guest_flush_count=20000,guest_last_flush=0;
};
int main(){
    unsigned passed=0,refused=0;
    for(unsigned offset=0;offset<32;++offset){
        Cpu c;OpenCacheRangeTrace w;const unsigned n=19,lines=(offset+n+31u)/32u;
        need(w.begin(c,0x81000000u+offset,n));
        for(unsigned i=0;i<lines;++i){const auto a=0x81000000u+32*i;w.on_flush(a);++c.guest_flush_count;c.guest_last_flush=a;}
        need(w.ready_sc(c)&&w.lines()==lines&&w.finish(c));++passed;
    }
    for(unsigned fault=0;fault<14;++fault){
        Cpu c;OpenCacheRangeTrace w;
        if(fault==0){need(!w.begin(c,0x41000000,64));}
        else if(fault==1){need(!w.begin(c,0x81001ff0,64));}
        else if(fault==2){c.guest_flush_count=0xffffffffu;need(!w.begin(c,0x81000000,64));}
        else if(fault==3){need(!w.begin(c,0x81000000,0));}
        else{
            need(w.begin(c,0x8100000c,64));
            const unsigned n=fault==4?2u:fault==5?4u:3u;
            for(unsigned i=0;i<n;++i){
                const uint32_t a=0x81000000u+32*(fault==6&&i==1?0u:i);
                w.on_flush(a);++c.guest_flush_count;c.guest_last_flush=a;
            }
            if(fault==7)w.on_zero(0x81000000u);
            if(fault==8)++c.guest_flush_count;
            if(fault==9)c.guest_last_flush+=32;
            if(fault==10)c.is_running=false;
            if(fault==11){Cpu other=c;need(!w.ready_sc(other));}
            else if(fault>=12){
                need(w.ready_sc(c));
                if(fault==12)w.on_flush(0x81000060u);
                else w.on_zero(0x81000000u);
                need(!w.finish(c));
            }else need(!w.ready_sc(c));
        }
        need(w.phase()==OpenCacheRangeTrace::Phase::Failed);++refused;
    }
    for(unsigned f=0;f<5;++f){
        Cpu c;OpenCacheRangeTrace w;
        need(w.begin(c,0x81000000u,16));
        w.on_flush(0x81000000u);++c.guest_flush_count;c.guest_last_flush=0x81000000u;
        need(w.ready_sc(c));
        if(f==1){need(!w.rearm(c));continue;}
        need(w.finish(c));
        if(f==2){Cpu other=c;need(!w.rearm(other));continue;}
        if(f==3){--c.guest_flush_count;need(!w.rearm(c));continue;}
        if(f==4){c.is_running=false;need(!w.rearm(c));continue;}
        c.guest_flush_count+=12;
        need(w.rearm(c)&&w.begin(c,0x81000020u,19));
        w.on_flush(0x81000020u);++c.guest_flush_count;c.guest_last_flush=0x81000020u;
        need(w.ready_sc(c)&&w.finish(c)&&w.lines()==1&&c.guest_flush_count==20014u);
    }
    std::cout<<"V1361_CACHE_REARM valid=1 refused=4\n";
    std::cout<<"V649_OPEN_CACHE positive="<<passed<<" refusal="<<refused<<" saturated_history=1 ordered=1\n";
}
