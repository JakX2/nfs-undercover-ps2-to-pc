#pragma once
#include <cstdint>

namespace undercover::wii {
struct IosMemory {
    virtual ~IosMemory()=default;
    // Physical guest RAM only. Implementors must reject MMIO, wraparound,
    // unmapped ranges and aliases. A successful range remains valid until
    // the synchronous host operation completes.
    virtual bool valid(uint32_t address,uint32_t size) const=0;
    virtual uint8_t read8(uint32_t address) const=0;
    virtual void write8(uint32_t address,uint8_t value)=0;
    uint32_t read32(uint32_t a) const {
        return uint32_t(read8(a))<<24|uint32_t(read8(a+1))<<16|
               uint32_t(read8(a+2))<<8|uint32_t(read8(a+3));
    }
    void write32(uint32_t a,uint32_t v) {
        for(unsigned i=0;i<4;++i)write8(a+i,uint8_t(v>>(24-8*i)));
    }
};
}
