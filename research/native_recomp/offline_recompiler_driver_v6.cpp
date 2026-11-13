// Standalone, offline-only driver for the upstream NWiiRecomp analyzer/recompiler.
// Removes TOML/SDL GUI dependencies from the *build-time* translation step.
// It does not emulate Wii hardware or execute copyrighted game code.
#include <iostream>
#include <filesystem>
#include <string>
#include <vector>
#include <chrono>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <limits>
#include "loader/loader.h"
#include "analyzer/analyzer.h"
#include "recompiler/recompiler.h"

int main(int argc, char** argv) {
    if (argc < 4) {
        std::cerr << "Usage: offline_recompiler_driver DOL SYMBOL_CSV OUTPUT_DIR [--strict-symbol-spans] [--trusted-extra-spans FILE] [--generate UPSTREAM_RUNTIME_SRC]\n";
        return 2;
    }
    const auto start = std::chrono::steady_clock::now();
    const std::string dol = argv[1], csv = argv[2], out = argv[3];
    nwii::loader::Executable exec;
    if (!exec.load_dol(dol)) { std::cerr << "DOL load failed\n"; return 3; }
    std::cout << "DOL: " << std::hex << exec.entry_point << std::dec << " sections=" << exec.sections.size() << std::endl;
    nwii::recomp::SymbolTable symbols;
    if (!symbols.load_csv(csv)) { std::cerr << "Symbol import failed\n"; return 4; }
    std::vector<uint32_t> addrs;
    for (const auto& p : symbols.get_all_symbols()) addrs.push_back(p.first);
    std::cout << "Root symbols=" << addrs.size() << std::endl;
    nwii::analyzer::Analyzer analyzer(exec);
    bool strict = false, do_generate = false;
    std::string runtime_dir, extra_spans_csv;
    for (int i = 4; i < argc; ++i) {
        const std::string flag = argv[i];
        if (flag == "--strict-symbol-spans") strict = true;
        else if (flag == "--trusted-extra-spans" && ++i < argc) extra_spans_csv = argv[i];
        else if (flag == "--generate" && ++i < argc) {
            do_generate = true;
            runtime_dir = argv[i];
        } else { std::cerr << "Unknown or incomplete flag: " << flag << "\n"; return 2; }
    }
    if (!extra_spans_csv.empty() && !strict) {
        std::cerr << "Extra spans require --strict-symbol-spans\n"; return 2;
    }
    if (strict) {
        // Original-free parser; this CSV's Size column is decimal and its
        // Location column is hexadecimal (the NWii symbol map format).
        std::ifstream in(csv);
        if (!in) { std::cerr << "Cannot read sized symbol map\n"; return 4; }
        std::string line; std::getline(in, line);
        if (line != "Name,Location,Size") {
            std::cerr << "Expected 3-column Name,Location,Size header\n"; return 4;
        }
        std::vector<std::pair<uint32_t,uint32_t>> spans;
        while (std::getline(in, line)) {
            if (line.empty()) continue;
            std::stringstream ss(line);
            std::string name, address, size, extra;
            if (!std::getline(ss,name,',') || !std::getline(ss,address,',') ||
                !std::getline(ss,size,',') || std::getline(ss,extra,',')) {
                std::cerr << "Malformed sized symbol record\n"; return 4;
            }
            try {
                size_t consumed = 0;
                const auto start64 = std::stoull(address,&consumed,16);
                if (consumed != address.size()) throw std::invalid_argument("address");
                const auto length64 = std::stoull(size,&consumed,10);
                if (consumed != size.size() || length64 == 0) throw std::invalid_argument("size");
                if (start64 > UINT32_MAX || start64 + length64 > UINT32_MAX)
                    throw std::out_of_range("address overflow");
                spans.push_back({static_cast<uint32_t>(start64),static_cast<uint32_t>(start64+length64)});
            } catch(const std::exception& e) {
                std::cerr << "Invalid symbol address/size: " << e.what() << "\n"; return 4;
            }
        }
        if (!extra_spans_csv.empty()) {
            // Extra ranges must be independently verified against the owner's
            // ELF. Never blanket-trust unknown NOTYPE symbols, which can be data.
            std::ifstream extras(extra_spans_csv);
            std::string record;
            if (!extras || !std::getline(extras,record) || record != "Start,Size") {
                std::cerr << "Extra spans need Start,Size CSV header\n"; return 4;
            }
            size_t added = 0;
            while (std::getline(extras,record)) {
                if (record.empty()) continue;
                const auto comma = record.find(',');
                if (comma == std::string::npos || record.find(',',comma+1) != std::string::npos) {
                    std::cerr << "Invalid extra span record\n"; return 4;
                }
                try {
                    const std::string textStart=record.substr(0,comma);
                    const std::string textSize=record.substr(comma+1);
                    size_t n=0;
                    uint64_t a=std::stoull(textStart,&n,16);
                    if(n!=textStart.size()) throw std::invalid_argument("extra address");
                    uint64_t size=std::stoull(textSize,&n,10);
                    if(n!=textSize.size() || size==0 || a+size>UINT32_MAX)
                        throw std::invalid_argument("extra size");
                    spans.push_back({uint32_t(a),uint32_t(a+size)});
                    ++added;
                } catch(const std::exception& e) {
                    std::cerr << "Invalid extra span: " << e.what() << "\n"; return 4;
                }
            }
            std::cout << "Independent source-verified extra spans=" << added << "\n";
        }
        try { analyzer.set_trusted_code_spans(spans); }
        catch(const std::exception& e) {
            std::cerr << "Invalid trusted code spans: " << e.what() << "\n"; return 4;
        }
        std::cout << "ELF-sized trusted function spans=" << spans.size() << "\n";
    }
    analyzer.analyze(addrs);
    const auto& funcs = analyzer.get_functions();
    std::cout << "Discovered functions=" << funcs.size() << std::endl;
    uint64_t ninst = 0;
    for (const auto& [addr, fun] : funcs) ninst += fun.instructions.size();
    std::cout << "Analyzed instruction slots=" << ninst << std::endl;
    const auto dt = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();
    std::cout << "Analysis seconds=" << dt << std::endl;
    if (do_generate) {
        nwii::recomp::RecompilerConfig cfg;
        cfg.project_name = "UndercoverWiiLocal";
        cfg.output_dir = out;
        cfg.runtime_source_dir = runtime_dir;
        cfg.split_output = true;
        cfg.instructions_per_file = 16000;
        nwii::recomp::Recompiler recomp(analyzer, &symbols, cfg);
        const bool ok = recomp.generate_cmake_project(exec.entry_point);
        std::cout << "Generated_project=" << ok << std::endl;
        if (!ok) return 5;
    }
    return 0;
}
