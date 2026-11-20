// Original-free Wii SYSCONF format + actual native IOS transport regression.
// No proprietary console NAND or game bytes are present in this test.
#include "wii_sysconf_image.h"
#include "wii_ios_bus.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>

using namespace undercover::wii;
using S = SysconfImage;
using IOS = StmIos;
using B = IosBus;
using M = IpcMailbox;
using H = HollywoodIrq;

static void expect(bool cond, const char* why) {
    if (!cond) throw std::runtime_error(why);
}
static uint16_t be16(const GuestFiles::Bytes& b, unsigned p) {
    return uint16_t(uint16_t(b.at(p)) << 8u | b.at(p+1u));
}

struct Ram final : IosMemory {
    std::array<uint8_t, 0x10000u> data{};
    bool valid(uint32_t a, uint32_t n) const override {
        return uint64_t(a) + n <= data.size();
    }
    uint8_t read8(uint32_t a) const override { return data.at(a); }
    void write8(uint32_t a, uint8_t val) override { data.at(a) = val; }
    void cstring(uint32_t addr, std::string_view path) {
        expect(valid(addr,uint32_t(path.size()+1u)), "path buffer invalid");
        for (char ch : path) write8(addr++, uint8_t(ch));
        write8(addr, 0);
    }
};

static void test_format() {
    const auto image = S::build();
    expect(image.has_value(), "default image construction failed");
    const auto& b = *image;
    expect(b.size() == S::Size, "SYSCONF size");
    expect(std::string_view(reinterpret_cast<const char*>(b.data()),4) == "SCv0", "header");
    expect(std::string_view(reinterpret_cast<const char*>(&b[S::Size-4]),4) == "SCed", "footer");
    expect(be16(b,4) == 9, "nine known display/control fields");
    struct Expected {
        std::string_view name;
        uint8_t value;
        uint16_t lut;
    };
    const std::array<Expected,9> known{{
        {"BT.BAR",1,0x3fb8},
        {"BT.MOT",1,0x3fba},
        {"BT.SPKV",0x58,0x3fbc},
        {"IPL.AR",1,0x3ff8},
        {"IPL.E60",1,0x3fee},
        {"IPL.LNG",1,0x3fe4},
        {"IPL.PGS",0,0x3fde},
        {"IPL.SND",1,0x3fd8},
        {"IPL.SSV",1,0x3fdc}
    }};
    uint16_t previous = 0;
    for (unsigned i=0; i<known.size(); ++i) {
        const auto& e = known[i];
        const uint16_t item_offset = be16(b, 6u+2u*i);
        const uint16_t next = be16(b, 8u+2u*i);
        expect(item_offset >= 6u+2u*(known.size()+1u) &&
               item_offset > previous && next > item_offset &&
               next < S::LookupBegin, "item index order/bounds");
        previous=item_offset;
        expect(be16(b,e.lut) == 6u + 2u*i, "lookup index points at wrong item");
        expect(b[item_offset] == ((3u << 5u) | (e.name.size() - 1u)),
               "byte item type or name length");
        expect(next == item_offset + e.name.size() + 2u, "item extent");
        const auto name = std::string_view(
            reinterpret_cast<const char*>(&b[item_offset + 1u]), e.name.size());
        expect(name == e.name, "item name");
        expect(b[next-1u] == e.value, "item value");
    }
    const auto bad_default = S::build(SysconfImageOptions{.language=10});
    expect(!bad_default.has_value(), "invalid language accepted");
    const auto bad_ratio = S::build(SysconfImageOptions{.widescreen=2});
    expect(!bad_ratio.has_value(), "invalid aspect accepted");
    const auto bad_sound = S::build(SysconfImageOptions{.sound=3});
    expect(!bad_sound.has_value(), "invalid sound accepted");
    SysconfImageOptions options{};
    options.language=4;options.widescreen=0;options.sound=2;options.progressive=1;
    const auto altered=S::build(options);
    expect(altered.has_value() && altered->size()==b.size(), "valid options rejected");
    expect(*altered != b, "options did not change generated file");
    expect(be16(*altered, 0x3fe4)==be16(b,0x3fe4), "options changed index");
    auto files=std::make_shared<GuestFiles>();
    expect(S::add_to(*files), "failed to register synthetic SYSCONF");
    expect(!S::add_to(*files), "allowed silently replacing mounted config");
    auto saved=files->find(S::Path);
    expect(saved && *saved==b, "mounted synthetic bytes differ");
}

static void test_ios_read_only() {
    Ram ram;
    B bus(ram);
    auto fs=std::make_shared<GuestFiles>();
    expect(S::add_to(*fs), "failed to create initial synthetic configuration");
    expect(bus.services().mount_filesystem(fs), "filesystem mount failed");
    constexpr uint32_t request=0x100u, path=0x400u, destination=0x1000u;
    constexpr uint32_t enable=M::IY1|M::IY2;
    auto write=[&](uint32_t addr,uint32_t value){
        expect(bus.write32(addr,value),"IOS register write rejected");
    };
    auto call=[&](uint32_t cmd,uint32_t fd,uint32_t a=0u,uint32_t b=0u,
                  uint32_t c=0u,uint32_t d=0u,uint32_t e=0u)->int32_t {
        const std::array<uint32_t,8> words{cmd, 0u, fd, a,b,c,d,e};
        for(unsigned i=0;i<words.size();++i)ram.write32(request+4u*i,words[i]);
        write(B::IPC+M::PPCMSG,request);
        write(B::IPC+M::PPCCTRL,enable|M::X1);
        expect(bus.tick()==IOS::Pump::Ack, "IOS did not ACK request");
        write(B::IPC+M::PPCCTRL,enable|M::Y2);
        write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        expect(bus.tick()==IOS::Pump::Replied, "IOS did not complete request");
        expect(ram.read32(request)==IOS::Reply,"IOS reply command missing");
        expect(ram.read32(request+8u)==cmd,"IOS original command not restored");
        const int32_t result=int32_t(ram.read32(request+4u));
        write(B::IPC+M::PPCCTRL,enable|M::Y1);
        write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        expect(bus.tick()==IOS::Pump::Idle, "IOS did not return to idle");
        return result;
    };
    ram.cstring(path,S::Path);
    expect(call(IOS::Open,0,path,0)==IOS::NotFound,
           "opened config without explicit filesystem root");
    expect(call(IOS::Open,0,path,1)==0,"read-only guest SYSCONF open failed");
    expect(bus.services().is_open(0,IOS::Device::File), "SYSCONF file descriptor type");
    expect(!bus.services().mount_filesystem(std::make_shared<GuestFiles>()),
           "permitted filesystem remount with live descriptor");
    expect(call(IOS::Read,0,destination,S::Size)==int32_t(S::Size),
           "IOS failed full SYSCONF transfer");
    const auto expected=S::build();
    for(unsigned i=0;i<S::Size;++i)
        expect(ram.read8(destination+i)==expected->at(i),"guest SYSCONF bytes differ");
    expect(call(IOS::Read,0,destination,16)==0,"EOF must return zero");
    expect(call(IOS::Seek,0,0,0)==0,"failed to rewind SYSCONF");
    expect(call(IOS::Read,0,destination,4)==4,"failed to read SC header");
    expect(ram.read8(destination)=='S'&&ram.read8(destination+1)=='C',
           "rewound header differs");
    expect(call(IOS::Write,0,destination,4)==IOS::FsAccess,
           "read-only SYSCONF accepted guest write");
    expect(call(IOS::Close,0)==0,"SYSCONF close failed");
    expect(bus.services().mount_filesystem(std::make_shared<GuestFiles>()),
           "filesystem could not be remounted after closing all files");
}

int main() {
    test_format();
    test_ios_read_only();
    std::cout<<"PASS: synthetic Wii SYSCONF file layout, lookups, options, original-free IOS full read/EOF/seek/read-only lifecycle\n";
}
