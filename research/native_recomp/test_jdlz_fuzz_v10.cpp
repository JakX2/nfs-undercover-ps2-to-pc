// Deterministic original-free robustness test (not a substitute for fuzzing).
#include "jdlz_decoder_v10.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <vector>
using nwii::runtime::decode_jdlz_v10;
int main() {
    std::vector<uint8_t> seed={'J','D','L','Z',2,16,0,0,5,0,0,0,21,0,0,0,2,1,'A',0,1};
    uint32_t x=0xc001d00du;
    auto rnd=[&] { x ^= x << 13; x ^= x >> 17; x ^= x << 5; return x; };
    unsigned accepted=0;
    for (int n=0; n<20000; ++n) {
        auto b=seed;
        if (n%3==0) b.resize(rnd()%48,0);
        for (unsigned j=0;j<(rnd()%9);++j) {
            if (!b.empty()) b[rnd()%b.size()]=uint8_t(rnd());
        }
        auto out=decode_jdlz_v10(b,4096);
        if (out) {
            if (out.output.size()>4096 || out.input_consumed>b.size())
                throw std::runtime_error("decoder allocation or span escaped limits");
            ++accepted;
        }
    }
    std::cout<<"PASS: 20000 deterministic mutated JDLZ cases, "<<accepted
             <<" successfully decoded; no bounds escapes\n";
}
