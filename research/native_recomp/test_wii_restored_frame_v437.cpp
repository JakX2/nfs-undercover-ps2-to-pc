#include "wii_restored_frame_v437.h"
#include <iostream>
#include <stdexcept>
using undercover::wii::RestoredFrameWitness;
static void need(bool ok){if(!ok)throw std::runtime_error("frame witness");}
int main(){
    constexpr uint32_t lr=0x80501004u,sp=0x80700000u;
    for(unsigned fault=0;fault<12;++fault){
        RestoredFrameWitness w;
        need(!w.active());
        if(fault==1){need(!w.begin(lr+1,sp,10));continue;}
        if(fault==2){need(!w.begin(lr,sp+4,10));continue;}
        if(fault==3){need(!w.begin(lr,0x81800000u,10));continue;}
        need(w.begin(lr,sp,10)&&w.active());
        if(fault==4){need(!w.begin(lr,sp,11));continue;}
        if(fault==5){need(!w.after_return(lr,sp,20));continue;}
        if(fault==6){need(!w.before_return(lr+4,sp,20));continue;}
        if(fault==7){need(!w.before_return(lr,sp-8,20));continue;}
        if(fault==8){need(!w.before_return(lr,sp,10));continue;}
        need(w.before_return(lr,sp,20)&&w.active());
        if(fault==9){need(!w.after_return(lr+4,sp,20));continue;}
        if(fault==10){need(!w.after_return(lr,sp-8,20));continue;}
        if(fault==11){need(!w.after_return(lr,sp,19));continue;}
        need(w.after_return(lr,sp,20)&&!w.active()&&w.stage()==3);
        need(!w.after_return(lr,sp,21)&&!w.before_return(lr,sp,21));
    }
    std::cout<<"PASS: restored frame return pair, eleven negative controls and duplicate stops\n";
}
