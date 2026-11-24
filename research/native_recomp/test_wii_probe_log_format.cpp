#include "wii_probe_log_format.h"
#include <sstream>
#include <iostream>
#include <stdexcept>
using undercover::wii::ScopedProbeDecimal;
static void need(bool b){if(!b)throw std::runtime_error("probe format");}
int main(){
    for(unsigned mode=0;mode<8;++mode){
        std::ostringstream out;
        out.setf(mode&1?std::ios::hex:std::ios::oct,std::ios::basefield);
        if(mode&2)out.setf(std::ios::showbase|std::ios::uppercase);
        if(mode&4)out.setf(std::ios::showpos);
        out.width(30);auto flags=out.flags();
        {
            ScopedProbeDecimal scoped(out);
            for(unsigned n=1;n<=13;++n)out<<"V439_HW_STAGE n="<<n<<" valid=1\n";
        }
        need(out.flags()==flags&&out.width()==30);
        std::string expected;
        for(unsigned n=1;n<=13;++n)expected+="V439_HW_STAGE n="+std::to_string(n)+" valid=1\n";
        need(out.str()==expected);
    }
    std::ostringstream legacy;
    legacy<<std::hex;
    for(unsigned n=9;n<=13;++n)legacy<<"V439_HW_STAGE n="<<n<<" valid=1\n";
    need(legacy.str()=="V439_HW_STAGE n=9 valid=1\nV439_HW_STAGE n=a valid=1\nV439_HW_STAGE n=b valid=1\nV439_HW_STAGE n=c valid=1\nV439_HW_STAGE n=d valid=1\n");
    std::cout<<"PASS: eight inherited stream formats normalized; legacy nine-stage cutoff reproduced\n";
}
