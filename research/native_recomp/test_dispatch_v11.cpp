// Uses two small artificial compression samples only.
#include "ea_resource_decoder_v11.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace nwii::runtime;
int main() {
    std::vector<uint8_t> jdlz={'J','D','L','Z',2,16,0,0,3,0,0,0,21,0,0,0,0,0,'A','B','C'};
    auto j=decode_ea_resource_v11(jdlz);
    assert(j);
    assert(j.compression==EaCompressionV11::Jdlz);
    assert(j.output==std::vector<uint8_t>({'A','B','C'}));
    assert(j.input_consumed==jdlz.size());
    std::vector<uint8_t> huff={0x48,0x55,0x46,0x46,0x01,0x10,0,0,
                               0x05,0,0,0,0x0b,0,0,0,0x30,0xfb,0,0,
                               0x05,0,0xc1,0x14,0x18,0x4a,0x32};
    auto h=decode_ea_resource_v11(huff);
    assert(h);
    assert(h.compression==EaCompressionV11::Huff);
    assert(h.output==std::vector<uint8_t>(5,'A'));
    assert(h.input_consumed==huff.size());
    std::vector<uint8_t> other={'B','U','N',' '};
    auto n=decode_ea_resource_v11(other);
    assert(!n && n.compression==EaCompressionV11::Unknown);
    assert(!decode_ea_resource_v11(std::vector<uint8_t>{}));
    assert(!decode_ea_resource_v11(huff,3));
    std::cout<<"PASS: 11 synthetic mixed JDLZ/HUFF dispatch assertions\n";
}
