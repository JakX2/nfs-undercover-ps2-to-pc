// Synthetic CPUContext SPR shadow/strict-mode tests, not Wii MMU emulation.
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <array>
#include "runtime/cpu_context.h"
static void require(bool ok, const char* desc) { if (!ok) throw std::runtime_error(desc); }
int main() {
    nwii::runtime::CPUContext ctx;
    int assertions=0;
    require(ctx.read_unmodeled_spr(528)==0,"initial shadow 0"); ++assertions;
    require(ctx.unmodeled_spr_write_count==0,"initial count"); ++assertions;
    for (const auto word: ctx.sprg) { require(word==0,"SPRG startup initialization"); ++assertions; }
    require(ctx.needs_hardware_spr_effect(528),"BAT critical"); ++assertions;
    require(ctx.needs_hardware_spr_effect(560),"extended BAT critical"); ++assertions;
    require(ctx.needs_hardware_spr_effect(25),"SDR1 critical"); ++assertions;
    require(ctx.needs_hardware_spr_effect(1008),"HID critical"); ++assertions;
    require(ctx.needs_hardware_spr_effect(284),"timebase critical"); ++assertions;
    require(!ctx.needs_hardware_spr_effect(952),"monitor counter tracked but not marked MMU critical"); ++assertions;
    constexpr std::array<uint32_t,14> ids={528,529,543,560,568,575,25,18,284,920,1008,1017,952,958};
    for (auto spr : ids) {
        ctx.write_unmodeled_spr(spr, 0xA5A50000u | spr);
        require(ctx.read_unmodeled_spr(spr)==(0xA5A50000u | spr),"read-back"); ++assertions;
        require(ctx.unmodeled_spr_written[spr]==1,"written marker"); ++assertions;
    }
    require(ctx.unmodeled_spr_write_count==ids.size(),"write count"); ++assertions;
    ctx.write_unmodeled_spr(528,0x12345678);
    require(ctx.read_unmodeled_spr(528)==0x12345678,"rewrite"); ++assertions;
    require(ctx.unmodeled_spr_write_count==ids.size()+1,"rewrite count"); ++assertions;
    ctx.strict_unmodeled_sprs=true;
    for(auto critical: {528u,560u,25u,18u,284u,1008u,1017u,920u}) {
        bool threw=false;
        auto old=ctx.read_unmodeled_spr(critical);
        try {ctx.write_unmodeled_spr(critical,123);} catch(const std::runtime_error&) {threw=true;}
        require(threw,"strict mode should trap critical write"); ++assertions;
        require(ctx.read_unmodeled_spr(critical)==old,"strict mode must leave shadow untouched"); ++assertions;
    }
    ctx.write_unmodeled_spr(952,123);
    require(ctx.read_unmodeled_spr(952)==123,"monitor shadow is diagnostic"); ++assertions;
    for(auto bad : {1024u, 0xffffffffu}) {
        bool threw=false;
        try {ctx.write_unmodeled_spr(bad,1);} catch(const std::out_of_range&) {threw=true;}
        require(threw,"out-of-range write"); ++assertions;
        threw=false;
        try {(void)ctx.read_unmodeled_spr(bad);} catch(const std::out_of_range&) {threw=true;}
        require(threw,"out-of-range read"); ++assertions;
    }
    std::cout << "PASS: " << assertions << " V7 synthetic SPR shadow assertions\n";
}
