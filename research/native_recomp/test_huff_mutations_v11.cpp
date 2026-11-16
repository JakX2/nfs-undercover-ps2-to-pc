// Deterministic synthetic mutation corpus; no original Undercover assets.
#include "huff_decoder_v11.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using nwii::runtime::decode_huff_v11;
int main(){
    std::vector<uint8_t> fixture={0x48,0x55,0x46,0x46,0x01,0x10,0,0,
                                  0x05,0,0,0,0x0b,0,0,0,0x30,0xfb,0,0,
                                  0x05,0,0xc1,0x14,0x18,0x4a,0x32};
    auto baseline=decode_huff_v11(fixture);
    if (!baseline || baseline.output!=std::vector<uint8_t>(5,'A'))
        throw std::runtime_error("synthetic fixture invalid");
    uint32_t x=0x715d2f3au;
    auto rand32=[&](){x^=x<<13;x^=x>>17;x^=x<<5;return x;};
    unsigned accepted=0;
    for(unsigned i=0;i<25000;++i) {
        auto b=fixture;
        if(i%3==0)b.resize(rand32()%75,0);
        for(unsigned j=0,N=rand32()%11;j<N;++j)
            if(!b.empty())b[rand32()%b.size()]=uint8_t(rand32());
        auto d=decode_huff_v11(b,4096);
        if(d){
            if(d.output.size()>4096||d.input_consumed>b.size())
                throw std::runtime_error("decoder exceeded resource bounds");
            ++accepted;
        }
    }
    std::cout<<"PASS: 25000 mutated HUFF payloads, accepted "<<accepted<<" (no memory violations)\n";
}
