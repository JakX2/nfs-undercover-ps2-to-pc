#include "wii_ios_bus.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string_view>
using namespace undercover::wii;
using M=IpcMailbox;using B=IosBus;using H=HollywoodIrq;using S=StmIos;

// Synthetic fixture only: this test verifies guest IPC semantics, not
// provenance or contents of a retail Wii NAND configuration file.
struct Ram final:IosMemory{
    std::array<uint8_t,4096> mem{};
    bool valid(uint32_t p,uint32_t n)const override{return uint64_t(p)+n<=mem.size();}
    uint8_t read8(uint32_t p)const override{return mem.at(p);}
    void write8(uint32_t p,uint8_t x)override{mem.at(p)=x;}
    void str(uint32_t p,std::string_view s){for(char x:s)write8(p++,uint8_t(x));write8(p,0);}
};
int main(){
    Ram ram;B bus(ram);
    constexpr uint32_t request=0x100,event=0x180,async=0x200,path=0x300;
    constexpr uint32_t fileout=0x500,stats=0x600,eventout=0x700;
    constexpr uint32_t enabled=M::IY1|M::IY2;
    auto wr=[&](uint32_t a,uint32_t v){assert(bus.write32(a,v));};
    auto submit=[&](uint32_t slot,uint32_t command,uint32_t fd,uint32_t a=0,uint32_t b=0,
                    uint32_t c=0,uint32_t d=0,uint32_t e=0){
        const std::array<uint32_t,8> words{command,0xabcdef01u,fd,a,b,c,d,e};
        for(unsigned i=0;i<words.size();++i)ram.write32(slot+4u*i,words[i]);
        wr(B::IPC+M::PPCMSG,slot);wr(B::IPC+M::PPCCTRL,enabled|M::X1);
    };
    auto clear=[&](uint32_t flag){
        assert(bus.external_irq_level());
        wr(B::IPC+M::PPCCTRL,enabled|flag);
        assert(bus.tick()==S::Pump::Busy);
        wr(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        assert(!bus.external_irq_level());
    };
    auto ack=[&](S::Pump p){
        assert(bus.tick()==p);
        clear(M::Y2);
    };
    auto reply=[&](uint32_t slot,uint32_t command,int32_t expected){
        assert(bus.tick()==S::Pump::Replied);
        assert(bus.read32(B::IPC+M::ARMMSG).value()==slot);
        assert(ram.read32(slot)==S::Reply&&ram.read32(slot+4u)==uint32_t(expected));
        assert(ram.read32(slot+8u)==command);
        clear(M::Y1);
        assert(bus.tick()==S::Pump::Idle);
    };
    auto call=[&](uint32_t slot,uint32_t cmd,uint32_t fd,int32_t result,uint32_t a=0,uint32_t b=0,
                  uint32_t c=0,uint32_t d=0,uint32_t e=0){
        submit(slot,cmd,fd,a,b,c,d,e);ack(S::Pump::Ack);reply(slot,cmd,result);
    };
    auto open=[&](uint32_t slot,std::string_view name,uint32_t mode,int32_t result){
        ram.str(path,name);call(slot,S::Open,0,result,path,mode);
    };
    wr(B::IPC+H::PPC_MASK,H::IPC_PPC);
    wr(B::PI_MASK,H::PI_HOLLYWOOD);
    open(request,"/dev/stm/immediate",0,0);
    open(request,"/dev/stm/eventhook",0,1);
    ram.write32(eventout,0xbadc0ffeu);
    submit(event,S::Ioctl,1,S::EventHook,0,0,eventout,4);
    ack(S::Pump::Deferred);
    assert(bus.services().event_pending()&&ram.read32(event)==S::Ioctl);

    constexpr std::string_view scpath="/shared2/sys/SYSCONF";
    open(async,scpath,1,S::NotFound);
    auto empty=std::make_shared<GuestFiles>();
    assert(bus.services().mount_filesystem(empty));
    open(async,scpath,1,S::FsMissing);
    auto fs=std::make_shared<GuestFiles>();
    const GuestFiles::Bytes fixture{0x53,0x43,0x01,0x00,0x40,0x7f,0x09};
    assert(fs->add(std::string(scpath),fixture));
    assert(bus.services().mount_filesystem(fs));
    open(request,"/dev/fs",0,2);
    assert(bus.services().is_open(2,S::Device::Fs));
    open(async,scpath,0,S::FsAccess);
    open(async,scpath,2,S::FsAccess);
    open(async,scpath,1,3);
    assert(bus.services().is_open(3,S::Device::File));
    assert(!bus.services().mount_filesystem(empty)); // active descriptor pins the backend

    ram.write32(eventout,0xbadc0ffeu);
    call(async,S::Read,3,S::FsInvalid,eventout,4);
    call(async,S::Read,3,S::FsInvalid,async+4,4);
    for(uint32_t n=0;n<fixture.size();++n)ram.write8(fileout+n,0xffu);
    call(async,S::Read,3,int32_t(fixture.size()),fileout,uint32_t(fixture.size()));
    for(uint32_t n=0;n<fixture.size();++n)assert(ram.read8(fileout+n)==fixture[n]);
    call(async,S::Read,3,0,fileout,1); // actual EOF
    call(async,S::Ioctl,3,0,S::FileStats,0,0,stats,8);
    assert(ram.read32(stats)==fixture.size()&&ram.read32(stats+4u)==fixture.size());
    call(async,S::Seek,3,0,0,0);
    call(async,S::Read,3,3,fileout,3);
    assert(ram.read8(fileout)==fixture[0]&&ram.read8(fileout+2u)==fixture[2]);
    call(async,S::Write,3,S::FsAccess,fileout,1);
    call(async,S::Close,3,0);
    assert(!bus.services().is_open(3,S::Device::File));
    assert(bus.services().event_pending()&&ram.read32(event)==S::Ioctl&&
           ram.read32(eventout)==0xbadc0ffeu&&bus.services().queued_replies()==0u);
    assert(fs->find(scpath)&&*fs->find(scpath)==fixture);
    call(request,S::Close,2,0);
    assert(bus.services().mount_filesystem(empty));
    open(async,scpath,1,S::FsMissing);
    assert(bus.services().signal_event(0x20000u));
    reply(event,S::Ioctl,0);
    assert(ram.read32(eventout)==0x20000u);
    std::cout<<"PASS: native read-only SC config async IPC, absent/explicit bytes, access control, and pending STM isolation\n";
}
