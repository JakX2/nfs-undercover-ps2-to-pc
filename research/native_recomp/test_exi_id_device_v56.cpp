// Host-only unit check for the bounded synthetic EXI transaction model.
#include "exi_id_test_device_v56.h"
#include <cassert>
#include <cstdint>
#include <iostream>

template<class F> void rejects(F f){
    bool threw=false;
    try{f();}catch(const std::runtime_error&){threw=true;}
    assert(threw);
}
int main(){
    using D=ExiIdTestDevice;
    for(unsigned w=0;w<4;++w)for(unsigned r=0;r<4;++r){
        D d;d.reset(0xabcdef00u+w*4u+r,w,r);
        rejects([&]{d.begin(0);});
        d.begin(0x2000);
        rejects([&]{d.read(D::DATA);});
        assert(d.read(D::CSR)==0x2000);
        rejects([&]{d.write(D::CSR,0x80);});
        d.write(D::CSR,0x200);
        rejects([&]{d.write(D::CR,0x31);});
        rejects([&]{d.write(D::DATA,0x10000);});
        d.write(D::DATA,0);
        d.write(D::CR,0x15);
        for(unsigned i=0;i<w;++i)assert(d.read(D::CR)==0x15);
        assert(d.read(D::CR)==0x14);
        assert(d.read(D::HWREV)==1);
        d.write(D::CR,0x31);
        for(unsigned i=0;i<r;++i)assert(d.read(D::CR)==0x31);
        assert(d.read(D::CR)==0x30);
        assert(d.read(D::DATA)==d.response);
        assert(d.read(D::HWREV)==1);
        assert(d.read(D::CSR)==0x200);
        d.write(D::CSR,0);
        assert(d.complete());
        rejects([&]{d.read(D::DATA);});
    }
    std::cout<<"PASS: EXI ID device host-only protocol, busy timing, and invalid-operation guards (16 schedules)\n";
}
