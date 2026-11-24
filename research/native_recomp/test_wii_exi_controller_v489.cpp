#include "wii_exi_controller_v489.h"
#include <iostream>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI controller");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    std::atomic<uint32_t> cause{0x4100};WiiIrqBanks banks(cause);ExiController exi(banks);
    for(unsigned ch=0;ch<3;++ch){
        for(unsigned r=0;r<20;r+=4)need(exi.read(ch,r)==0);
        exi.write(ch,4,0x81234567);exi.write(ch,8,0x123f);
        need(exi.read(ch,4)==0x81234560&&exi.read(ch,8)==0x1220);
        exi.write(ch,16,0x12345678+ch);need(exi.read(ch,16)==0x12345678+ch);
        exi.write(ch,12,0x34);need(exi.read(ch,12)==0x34);
        reject([&]{exi.write(ch,12,0x35);});
        need(exi.read(ch,12)==0x34&&!exi.pending(ch));
        exi.write(ch,0,0x84); // select device 0, enable completion interrupt
        exi.attach(ch,0,true);
        for(unsigned len=1;len<=4;++len)for(unsigned dir=0;dir<=2;++dir){
            exi.write(ch,0,0x8c); // acknowledge previous completion
            exi.write(ch,16,0xaabbccdd);
            const uint32_t control=((len-1)<<4)|(dir<<2)|1;
            exi.write(ch,12,control);
            auto p=exi.pending(ch);need(p&&p->channel==ch&&p->device==0&&p->length==len&&p->direction==dir&&p->tx==0xaabbccdd);
            for(unsigned i=0;i<100;++i)need(exi.read(ch,12)==control);
            need(cause==0x4100);
            reject([&]{exi.complete_immediate(ch,p->token+1,0);});
            reject([&]{exi.write(ch,16,0);});reject([&]{exi.attach(ch,0,false);});
            exi.complete_immediate(ch,p->token,0x12345678);
            const uint32_t mask=0xffffffffu<<((4-len)*8);
            need(exi.read(ch,16)==(dir==1?0xaabbccddu:((0xaabbccdd&~mask)|(0x12345678&mask))));
            need(!exi.pending(ch)&&exi.read(ch,12)==(control&~1u));
            need((cause&WiiIrqBanks::PI_EXI)!=0&&exi.read(ch,0)==0x8c);
            reject([&]{exi.complete_immediate(ch,p->token,0);});
        }
        exi.write(ch,0,0x8c);need(cause==0x4100);
        reject([&]{exi.write(ch,12,3);});
        reject([&]{exi.write(ch,12,0x0d);});
        reject([&]{exi.write(ch,12,0x40);});
        exi.write(ch,0,0x180);reject([&]{exi.write(ch,12,1);});
        exi.write(ch,0,0x100);reject([&]{exi.write(ch,12,1);});
        need(!exi.pending(ch)&&cause==0x4100);
    }
    exi.write(0,0,0x2000);need(exi.read(0,0)==0x2000);
    exi.write(0,0,0);need(exi.read(0,0)==0);
    reject([&]{exi.write(1,0,0x2000);});
    reject([&]{exi.read(3,0);});reject([&]{exi.write(0,2,0);});
    need(cause==0x4100);
    std::cout<<"PASS: EXI cold register state, 36 explicit immediate transfers, no auto-completion or fabricated device reply\n";
}
