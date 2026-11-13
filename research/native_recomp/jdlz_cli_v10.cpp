// Original-free test/diagnostic command-line tool; never commit game assets.
#include "jdlz_decoder_v10.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <string>
#include <vector>
namespace fs = std::filesystem;
int main(int argc, char** argv) {
    if (argc < 3 || argc > 4) {
        std::cerr << "Usage: jdlz_cli_v10 input.LZC output.bin [expected-original-file]\n";
        return 2;
    }
    std::ifstream in(argv[1], std::ios::binary);
    if (!in) { std::cerr << "Cannot open input\n"; return 2; }
    std::vector<uint8_t> bytes((std::istreambuf_iterator<char>(in)), {});
    auto decoded = nwii::runtime::decode_jdlz_v10(bytes);
    if (!decoded) { std::cerr << "Decode failed: " << decoded.error << '\n'; return 1; }
    if (argc == 4) {
        std::ifstream check(argv[3], std::ios::binary);
        if (!check) { std::cerr << "Cannot open expected file\n"; return 2; }
        std::vector<uint8_t> expected((std::istreambuf_iterator<char>(check)), {});
        if (expected != decoded.output) {
            std::cerr << "Decoded output does not match expected original\n";
            return 1;
        }
        std::cout << "BYTE-EXACT match against original (" << expected.size() << " bytes)\n";
    }
    // Emit only after all checks succeeded. A private owner-provided output
    // destination is required; no files are bundled with this project.
    std::ofstream out(argv[2], std::ios::binary);
    if (!out) { std::cerr << "Cannot write output\n"; return 2; }
    out.write(reinterpret_cast<const char*>(decoded.output.data()), decoded.output.size());
    if (!out) { std::cerr << "Writing output failed\n"; return 1; }
    std::cout << "JDLZ decoded " << bytes.size() << " -> " << decoded.output.size() << " bytes\n";
}
