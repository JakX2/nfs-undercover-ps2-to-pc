#pragma once
#include "wii_ipc_mailbox.h"
#include <array>
#include <cstdint>
#include <optional>
#include <string_view>

// Original-free native IOS service dispatcher for the documented Wii STM
// devices. No game-specific address, code, or fabricated general IOS success.
// Protocol references:
// https://wiibrew.org/wiki/IOS/resource_request
// https://wiibrew.org/wiki/Hardware/IPC
// https://wiibrew.org/wiki//dev/stm/immediate
// https://wiibrew.org/wiki//dev/stm/eventhook
// https://wiibrew.org/wiki/IOS/Syscalls
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

class StmIos {
public:
    enum : uint32_t { Open=1, Close=2, Ioctl=6, Reply=8,
                     EventHook=0x1000, GetState=0x3001, Release=0x3002 };
    enum : int32_t { Invalid=-4, NotFound=-6, QueueFull=-8 };
    enum class Device : uint8_t { None, Immediate, Event };
    enum class Pump { Idle, Ack, Replied, Deferred, InvalidAddress, Busy };
    static constexpr unsigned DescriptorCount=24;
    explicit StmIos(IpcMailbox& mailbox,IosMemory& memory):mail_(mailbox),mem_(memory){}
    // An explicit reset of the host device broker, not a system reboot.
    void reset() noexcept {
        fds_.fill(Device::None);pending_.reset();front_=count_=0;idle_=false;
    }
    void set_idle(bool idle) noexcept {idle_=idle;}
    bool event_pending() const noexcept {return pending_.has_value();}
    unsigned queued_replies() const noexcept {return count_;}
    bool is_open(unsigned fd,Device kind) const noexcept {
        return fd<fds_.size()&&kind!=Device::None&&fds_[fd]==kind;
    }

    // Called by the host scheduler. First acknowledge X1; only publish a
    // reply once Broadway has cleared both prior Y flags. No automatic IRQ
    // delivery, guest scheduler, or invented hardware timing is provided.
    Pump pump() {
        using M=IpcMailbox;
        constexpr auto A=M::Side::Starlet;
        const uint32_t ctrl=mail_.read(A,M::ARMCTRL);
        if(ctrl&(M::ARM_Y1|M::ARM_Y2))return Pump::Busy;
        if(mail_.request_pending()){
            if(count_>=replies_.size()-1u)return Pump::Busy;
            const uint32_t address=mail_.read(A,M::PPCMSG);
            if(!request_span(address)|| (pending_&&pending_->request==address)||in_queue(address))
                return Pump::InvalidAddress;
            const Request r{address,mem_.read32(address),mem_.read32(address+8),
                mem_.read32(address+12),mem_.read32(address+16),
                mem_.read32(address+20),mem_.read32(address+24),mem_.read32(address+28)};
            mail_.write(A,M::ARMCTRL,(ctrl&48u)|M::ARM_X1|M::ARM_Y2);
            const auto result=dispatch(r);
            if(result){enqueue(r.address,r.command,*result);return Pump::Ack;}
            return Pump::Deferred;
        }
        if(count_){
            const Completion r=replies_[front_];
            if(!request_span(r.address))return Pump::InvalidAddress;
            mem_.write32(r.address+4,uint32_t(r.result));
            mem_.write32(r.address+8,r.command);
            mem_.write32(r.address,Reply);
            front_=(front_+1u)%replies_.size();--count_;
            mail_.write(A,M::ARMMSG,r.address);
            mail_.write(A,M::ARMCTRL,(ctrl&48u)|M::ARM_Y1);
            return Pump::Replied;
        }
        return Pump::Idle;
    }
    // Explicit host event, e.g. reset-button notification. No host shutdown
    // or real filesystem access occurs. EventHook stays pending until this
    // or a valid RELEASE request completes it.
    bool signal_event(uint32_t code) {
        if(!pending_||!mem_.valid(pending_->output,4)||!request_span(pending_->request)||
           count_>=replies_.size())return false;
        mem_.write32(pending_->output,code);
        enqueue(pending_->request,Ioctl,0);
        pending_.reset();
        return true;
    }
private:
    struct Request {uint32_t address,command,fd,a,b,c,d,e;};
    struct Pending {uint32_t request,output,fd;};
    struct Completion {uint32_t address,command;int32_t result;};
    IpcMailbox& mail_;IosMemory& mem_;
    std::array<Device,DescriptorCount> fds_{};
    std::optional<Pending> pending_;
    std::array<Completion,8> replies_{};
    unsigned front_=0,count_=0;
    bool idle_=false;

    bool request_span(uint32_t a) const {
        return a!=0u&&(a&31u)==0u&&a<=0xffffffffu-31u&&mem_.valid(a,32);
    }
    bool in_queue(uint32_t a) const {
        for(unsigned i=0;i<count_;++i)
            if(replies_[(front_+i)%replies_.size()].address==a)return true;
        return false;
    }
    void enqueue(uint32_t a,uint32_t cmd,int32_t result){
        replies_[(front_+count_)%replies_.size()]={a,cmd,result};++count_;
    }
    Device path(uint32_t a) const {
        std::array<char,64> s{};
        for(unsigned i=0;i<s.size();++i){
            if(a>0xffffffffu-i||!mem_.valid(a+i,1))return Device::None;
            s[i]=char(mem_.read8(a+i));
            if(!s[i]){
                const std::string_view p(s.data(),i);
                if(p=="/dev/stm/immediate")return Device::Immediate;
                if(p=="/dev/stm/eventhook")return Device::Event;
                return Device::None;
            }
        }
        return Device::None;
    }
    bool output_ok(const Request&r) const {
        // An output word may not overlap the IPC request header.
        return r.e>=4u&&r.d!=0u&&r.d<=0xffffffffu-3u&&mem_.valid(r.d,4)&&
            (uint64_t(r.d)+4u<=r.address||uint64_t(r.address)+32u<=r.d);
    }
    std::optional<int32_t> dispatch(const Request&r){
        if(r.command==Open){
            if(r.b>3u||r.a==0u)return Invalid;
            const Device dev=path(r.a);
            if(dev==Device::None)return NotFound;
            for(unsigned i=0;i<fds_.size();++i)if(fds_[i]==Device::None){
                fds_[i]=dev;return int32_t(i);
            }
            return QueueFull;
        }
        if(r.fd>=fds_.size()||fds_[r.fd]==Device::None)return Invalid;
        const Device dev=fds_[r.fd];
        if(r.command==Close){
            if(pending_&&pending_->fd==r.fd)return Invalid;
            fds_[r.fd]=Device::None;return 0;
        }
        if(r.command!=Ioctl)return Invalid;
        if(dev==Device::Event&&r.a==EventHook){
            if(pending_||!output_ok(r))return Invalid;
            pending_=Pending{r.address,r.d,r.fd};return std::nullopt;
        }
        if(dev==Device::Immediate&&r.a==GetState){
            if(!output_ok(r))return Invalid;
            mem_.write32(r.d,idle_?1u:0u);return 0;
        }
        if(dev==Device::Immediate&&r.a==Release){
            if(pending_&&!signal_event(0))return Invalid;
            return 0;
        }
        return Invalid;
    }
};
}
