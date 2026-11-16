#include "huff_decoder_v11.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
int main(int argc, char** argv) {
    if (argc<3 || argc>4) {
        std::cerr<<"Usage: huff_cli_v11 original.HUFF output.bin [expected.bin]\n";
        return 2;
    }
    std::ifstream in(argv[1],std::ios::binary);
    if (!in) {std::cerr<<"Missing compressed input\n"; return 2;}
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(in)),{});
    auto result=nwii::runtime::decode_huff_v11(data);
    if (!result) {std::cerr<<"HUFF error: "<<result.error<<'\n';return 1;}
    if (argc==4) {
        std::ifstream expected_file(argv[3],std::ios::binary);
        if (!expected_file) {std::cerr<<"Missing reference output\n";return 2;}
        std::vector<uint8_t> expected((std::istreambuf_iterator<char>(expected_file)),{});
        if (expected!=result.output) {std::cerr<<"HUFF result differs from reference!\n";return 1;}
        std::cout<<"BYTE-EXACT comparison passed ("<<result.output.size()<<" bytes)\n";
    }
    std::ofstream out(argv[2],std::ios::binary);
    if (!out) {std::cerr<<"Cannot create output\n";return 2;}
    out.write(reinterpret_cast<const char*>(result.output.data()),result.output.size());
    if (!out) {std::cerr<<"Output write error\n";return 1;}
    std::cout<<"Decoded "<<result.input_consumed<<" compressed bytes into "<<result.output.size()<<" bytes\n";
}
