#include "wii_alarm_cancel_queue_v780.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80001000u,T=H+4u,A=0x80002000u,B=A+0x100u,N=B+0x100u,Callback=0x80006000u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t msr=0x32u,srr0=0x80009000u,srr1=0x8032u,dispatch_saved_ctx=0,dec_value=300;
    uint64_t inst_count=100,dec_written_tb=50;bool is_running=true,in_callback=false,dec_irq_pending=true;
};
static void need(bool ok,unsigned line){if(!ok){std::cerr<<"V780_ASSERT line="<<line<<'\n';throw std::runtime_error("queue");}}
#define CHECK(x) need((x),__LINE__)
int main(){
    unsigned valid=0,refused=0;
    for(unsigned trial=0;trial<30;++trial){
        Cpu c;auto& m=c.mmu.words;
        for(auto a:{A,B,N}){
            for(unsigned i=0;i<10;++i)m[a+4*i]=0x12340000u+i;
            m[a]=Callback;m[a+16]=m[a+20]=0;m[a+8]=0;m[a+12]=1000u;
        }
        const unsigned lane=trial<7?trial%5:trial==23?0u:4u;
        m[H]=A;m[T]=N;
        if(lane==0){m[B]=0;m[A+20]=N;m[N+16]=A;}
        if(lane==1){m[A+20]=B;m[B+16]=A;m[B+20]=N;m[N+16]=B;}
        if(lane==2){m[T]=B;m[A+20]=B;m[B+16]=A;}
        if(lane==3){m[H]=m[T]=B;}
        if(lane==4){m[H]=B;m[B+20]=N;m[N+16]=B;}
        if(trial==7)m[N+20]=B;
        if(trial==8)m[N+16]=A;
        if(trial==9)m[T]=A;
        if(trial==10)m[B]=0;
        if(trial==11)m.erase(N+32);
        if(trial==12)m[H]=B+4;
        if(trial==13)c.msr|=0x8000u;
        AlarmCancelQueueWitness w;bool ok=w.capture(c,H,T,B);
        if(trial>=7&&trial<=13){CHECK(!ok);++refused;continue;}
        CHECK(ok&&unsigned(w.lane())==lane);
        ++c.inst_count;
        if(trial<24)m[B]=0;
        if(lane==1){m[A+20]=N;m[N+16]=A;}
        if(lane==2){m[T]=A;m[A+20]=0;}
        if(lane==3)m[H]=m[T]=0;
        if(lane==4){m[H]=N;m[N+16]=0;}
        if(trial==14)m[N+4]^=1;
        if(trial==15)m[B+12]^=1;
        if(trial==16)m[N+16]=B;
        if(trial==17)c.dec_value^=1;
        if(lane==4){
            if(trial==25)m[B]^=1u;
            uint64_t time=trial==4?1100:trial==18?0x100000000ull:500;
            c.gpr[3]=uint32_t(time>>32);c.gpr[4]=uint32_t(time);
            ok=w.time_returned(c,time);
            if((trial>=14&&trial<=17)||trial==25){CHECK(!ok);++refused;continue;}CHECK(ok);
            if(trial>=24)CHECK(w.deferred_clear());
            CHECK(w.expected_dec()==(time>=1000?0:1000-time));
            ++c.inst_count;c.gpr[3]=w.expected_dec();
            if(trial==26)m[B]=0;
            if(trial==18)c.gpr[3]^=1;
            ok=w.timer_before(c,0x7c7603a6u);
            if(trial==18){CHECK(!ok);++refused;continue;}CHECK(ok);
            c.dec_value=w.expected_dec();c.dec_written_tb=c.inst_count;c.dec_irq_pending=true;++c.inst_count;
            if(trial==26)m[B]=Callback;
            if(trial==27)m[N+12]^=1;
            if(trial==19)c.dec_written_tb^=1;
            if(trial==20)c.dec_irq_pending=false;
            ok=w.timer_after(c);
            if(trial==19||trial==20||trial==26||trial==27){CHECK(!ok);++refused;continue;}CHECK(ok);
        }
        ++c.inst_count;
        if(trial==21)c.gpr[15]^=1;
        if(trial==22)c.srr0^=4;
        if(trial==23)m[A+20]=B;
        if(trial==24||trial==29)m[B]=0;
        if(trial==29)m[B+24]^=1;
        ok=w.finish(c);
        if((trial>=21&&trial<=23)||trial==28||trial==29){CHECK(!ok);++refused;continue;}
        CHECK(ok&&w.stage()==5);++valid;
    }
    CHECK(valid==8&&refused==22);
    std::cout<<"V785_ALARM_QUEUE synthetic=1 valid=8 refused=22 original_execution=0\n";
}
