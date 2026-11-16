// Entirely synthetic Huffman fixtures; no game-derived compressed bytes.
#include "huff_decoder_v11.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using nwii::runtime::decode_huff_v11;
static unsigned assertions=0;
static void check(bool truth,const char* msg) {
    if(!truth) throw std::runtime_error(msg);
    ++assertions;
}
struct Bits {
    std::vector<uint8_t> data;
    size_t at=0;
    void put(uint32_t value,unsigned width) {
        for(unsigned n=0;n<width;++n) {
            if(at%8==0)data.push_back(0);
            const unsigned bit=(value>>(width-1-n))&1u;
            data.back()|=static_cast<uint8_t>(bit<<(7-(at%8)));
            ++at;
        }
    }
    void var(uint32_t value) {
        unsigned width=2;
        while(value>=((1u<<(width+1))-4u))++width;
        for(unsigned i=2;i<width;++i)put(0,1);
        put(1,1);
        put(value-((1u<<width)-4u),width);
    }
};
static void le32(std::vector<uint8_t>& b,uint32_t x) {
    for(unsigned n=0;n<4;++n)b.push_back(static_cast<uint8_t>(x>>(n*8)));
}
static std::vector<uint8_t> make_fixture(unsigned method,bool raw=false,bool eos=true) {
    Bits b;
    b.put(method,16);if(method&0x100u)b.put(0x123456u,24);
    b.put(raw?2u:5u,24);b.put(0,8); // escape is 0
    b.var(2); // two width-1 symbols, canonical codes 0 and 1
    b.var(65); // assign ASCII 'A' to code 0
    b.var(190); // circularly assign byte 0 to code 1
    b.put(0,1); // A
    if(raw) {
        b.put(1,1);b.var(0);b.put(0,1);b.put('Z',8);
    } else {
        b.put(1,1);b.var(4); // repeat previous byte four more times
    }
    if(eos) {b.put(1,1);b.var(0);b.put(1,1);}
    std::vector<uint8_t> result={'H','U','F','F',1,16,0,0};
    le32(result,raw?2u:5u);le32(result,static_cast<uint32_t>(b.data.size()));
    result.insert(result.end(),b.data.begin(),b.data.end());
    return result;
}
int main() {
    auto a=make_fixture(0x30fb);
    auto out=decode_huff_v11(a);
    check(bool(out),"synthetic 30FB decode");
    check(out.output==std::vector<uint8_t>(5,'A'),"30FB repeat payload");
    check(out.input_consumed==a.size(),"input size counted");
    auto r=decode_huff_v11(make_fixture(0x30fb,true));
    check(bool(r),"literal escape fixture");
    check(r.output==std::vector<uint8_t>({'A','Z'}),"explicit raw byte");
    auto extended=decode_huff_v11(make_fixture(0x31fb));
    check(bool(extended) && extended.output==std::vector<uint8_t>(5,'A'),"31FB extended header");
    auto once=decode_huff_v11(make_fixture(0x32fb));
    check(bool(once),"32FB decode");
    check(once.output==std::vector<uint8_t>({65,130,195,4,69}),"single prefix-sum unfilter");
    auto twice=decode_huff_v11(make_fixture(0x34fb));
    check(bool(twice),"34FB decode");
    check(twice.output==std::vector<uint8_t>({65,195,134,138,207}),"double prefix-sum unfilter");
    auto trailing=a;trailing.insert(trailing.end(),{'T','A','I','L'});
    out=decode_huff_v11(trailing);
    check(bool(out)&&out.input_consumed==a.size(),"embedded compressed stream length");
    auto err=[&](std::vector<uint8_t> b,const char* why) {
        check(!decode_huff_v11(b),why);
    };
    {auto b=a;b[0]='X';err(b,"invalid wrapper magic");}
    {auto b=a;b[4]=2;err(b,"invalid wrapper version");}
    {auto b=a;b[12]=255;err(b,"compressed size out of range");}
    {auto b=a;b[8]=33;err(b,"mismatched uncompressed wrapper size");}
    {auto b=a;b[8]=55;err(b,"size limit error");}
    check(!decode_huff_v11(a,3),"user-defined output size limit");
    {auto b=a;b[16]=0x10;err(b,"unsupported EAC codec method");}
    {auto b=a;b[18]=0xff;err(b,"mismatched EAC output length");}
    {auto b=make_fixture(0x30fb,false,false);err(b,"missing mandatory EOS");}
    for(size_t n=0;n<a.size();++n) {
        check(!decode_huff_v11(std::span<const uint8_t>(a.data(),n)),"truncated prefix accepted");
    }
    std::cout<<"PASS: "<<assertions<<" synthetic HUFF wrapper/EAC decoder assertions\n";
}
