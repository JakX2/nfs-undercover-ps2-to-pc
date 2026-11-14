#include "ea_resource_decoder_v11.h"
#include <fstream>
#include <iostream>
#include <iterator>
#include <vector>
int main(int argc,char** argv) {
    if(argc<3||argc>4) {
        std::cerr<<"Usage: ea_resource_cli_v11 original.LZC output.bin [expected.bin]\n";
        return 2;
    }
    std::ifstream input(argv[1],std::ios::binary);
    if(!input){std::cerr<<"Cannot open compressed input\n";return 2;}
    std::vector<uint8_t> raw((std::istreambuf_iterator<char>(input)),{});
    auto decoded=nwii::runtime::decode_ea_resource_v11(raw);
    if(!decoded){std::cerr<<"Decoder error: "<<decoded.error<<"\n";return 1;}
    if(argc==4){
        std::ifstream reference(argv[3],std::ios::binary);
        if(!reference){std::cerr<<"Cannot open original reference\n";return 2;}
        std::vector<uint8_t> expected((std::istreambuf_iterator<char>(reference)),{});
        if(expected!=decoded.output){std::cerr<<"Verification mismatch\n";return 1;}
        std::cout<<"BYTE-EXACT match for "<<decoded.output.size()<<" bytes\n";
    }
    std::ofstream output(argv[2],std::ios::binary);
    if(!output){std::cerr<<"Cannot open output\n";return 2;}
    output.write(reinterpret_cast<const char*>(decoded.output.data()), decoded.output.size());
    if(!output){std::cerr<<"Output write failed\n";return 1;}
    std::cout<<"Decoded "<<(decoded.compression==nwii::runtime::EaCompressionV11::Jdlz?"JDLZ":"HUFF")
             <<" input="<<decoded.input_consumed<<" output="<<decoded.output.size()<<"\n";
}
