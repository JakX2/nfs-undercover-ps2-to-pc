// All test vectors below are synthetic; no copyrighted content is embedded.
#include "jdlz_decoder_v10.h"
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace nwii::runtime;
static unsigned checks = 0;
static void ck(bool b, const char* msg) {
    if (!b) throw std::runtime_error(msg);
    ++checks;
}
static std::vector<uint8_t> block(uint32_t output_size, std::vector<uint8_t> payload) {
    std::vector<uint8_t> b = {'J','D','L','Z',0x02,0x10,0,0};
    auto push = [&](uint32_t x) {for (unsigned n=0;n<4;++n)b.push_back(uint8_t(x >> (8*n)));};
    push(output_size);push(uint32_t(payload.size()+16));
    b.insert(b.end(),payload.begin(),payload.end());
    return b;
}
int main() {
    auto literal = block(3,{0,0,'A','B','C'});
    auto r=decode_jdlz_v10(literal);
    ck(bool(r),"literal decode");
    ck(std::string(r.output.begin(),r.output.end())=="ABC","literal data");
    ck(r.input_consumed==literal.size(),"compressed size readback");
    auto repeat=block(5,{2,1,'A',0,1});
    auto rep=decode_jdlz_v10(repeat);
    ck(bool(rep),"short back-reference decode");
    ck(rep.output==std::vector<uint8_t>(5,'A'),"overlapping back-reference output");
    // First 17 literals then a long-distance back-reference length 3.
    std::vector<uint8_t> far = {0,0};
    for (char c='a';c<='h';++c)far.push_back(uint8_t(c));
    far.push_back(0);
    for (char c='i';c<='p';++c)far.push_back(uint8_t(c));
    far.push_back(2);far.push_back('q');far.push_back(0);far.push_back(0);
    auto l=decode_jdlz_v10(block(20,far));
    ck(bool(l),"long-distance back-reference decode");
    ck(std::string(l.output.begin(),l.output.end())=="abcdefghijklmnopqabc","long-distance payload");
    auto wrapped=repeat;
    wrapped.push_back('X');wrapped.push_back('Y');
    auto w=decode_jdlz_v10(wrapped);
    ck(bool(w),"embedded decode with subsequent stream");
    ck(w.input_consumed==repeat.size(),"embedded input length");
    auto zero=decode_jdlz_v10(block(0,{}));
    ck(bool(zero) && zero.output.empty(),"zero-length data");
    auto bad=repeat;
    bad[0]='X';ck(!decode_jdlz_v10(bad),"bad magic");
    bad=repeat;bad[4]=1;ck(!decode_jdlz_v10(bad),"bad version");
    bad=repeat;bad[5]=1;ck(!decode_jdlz_v10(bad),"bad flags");
    bad=repeat;bad.resize(15);ck(!decode_jdlz_v10(bad),"short header");
    bad=repeat;bad[12]=255;ck(!decode_jdlz_v10(bad),"declared packed size unavailable");
    bad=repeat;bad[12]=15;ck(!decode_jdlz_v10(bad),"declared packed size shorter than header");
    bad=repeat;bad[8]=100;ck(!decode_jdlz_v10(bad,32),"output allocation cap");
    bad=repeat;bad[8]=7;ck(!decode_jdlz_v10(bad),"overshoot output");
    bad=block(5,{2,1,'A',0});ck(!decode_jdlz_v10(bad),"truncated two-byte reference");
    bad=block(1,{});ck(!decode_jdlz_v10(bad),"missing flag1");
    bad=block(1,{0});ck(!decode_jdlz_v10(bad),"missing flag2");
    bad=block(1,{0,0});ck(!decode_jdlz_v10(bad),"missing literal");
    bad=block(3,{1,1,0,0});ck(!decode_jdlz_v10(bad),"distance before start");
    bad=block(1,{1,1,0,0});ck(!decode_jdlz_v10(bad),"backref would exceed output");
    bad=block(2,{0,0,'A'});ck(!decode_jdlz_v10(bad),"partial literal output");
    // Unused padding/flag byte at the tail is permitted in shipping NFS files.
    auto padded=block(3,{0,0,'A','B','C',0,0});
    auto pad=decode_jdlz_v10(padded);
    ck(bool(pad) && pad.input_consumed==padded.size(),"shipping trailing padding accepted");
    // Truncated or random inputs must never crash or escape bounds.
    for (auto b : {literal,repeat,padded}) {
        for (size_t n=0;n<b.size();++n) {
            auto attempt=decode_jdlz_v10(std::span<const uint8_t>(b.data(),n));
            ck(!attempt,"truncated block erroneously accepted");
        }
    }
    std::cout << "PASS: " << checks << " synthetic JDLZ decoder assertions\n";
}
