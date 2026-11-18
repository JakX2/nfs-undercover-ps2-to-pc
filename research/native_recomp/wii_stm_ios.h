#pragma once
#include "wii_ipc_mailbox.h"
#include "wii_guest_filesystem.h"
#include <algorithm>
#include <limits>
#include <memory>
#include <string>
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
    enum : uint32_t { Open=1, Close=2, Read=3, Write=4, Seek=5, Ioctl=6, Ioctlv=7, Reply=8,
                     EventHook=0x1000, GetState=0x3001, Release=0x3002, FileStats=0x0b };
    enum : int32_t { Invalid=-4, NotFound=-6, QueueFull=-8,
                     FsInvalid=-101, FsAccess=-102, FsMissing=-106, FsFull=-109, EsInvalid=-1017 };
    enum class Device : uint8_t { None, Immediate, Event, Fs, File, Es };
    enum : uint32_t { EsGetDataDir=0x1d, EsGetTitleId=0x20 };
    enum class Pump { Idle, Ack, Replied, Deferred, InvalidAddress, Busy };
    static constexpr unsigned DescriptorCount=24;
    explicit StmIos(IpcMailbox& mailbox,IosMemory& memory):mail_(mailbox),mem_(memory){}
    // An explicit reset of the host device broker, not a system reboot.
    void reset() noexcept {
        fds_.fill(Device::None);files_.fill({});pending_.reset();front_=count_=0;idle_=false;
    }
    void set_idle(bool idle) noexcept {idle_=idle;}
    // Explicitly mounted native guest resources only. No host pathname is
    // ever opened here; existing handles cannot be silently remounted.
    bool mount_filesystem(std::shared_ptr<const GuestFiles> fs) noexcept {
        for(auto dev:fds_)if(dev==Device::Fs||dev==Device::File)return false;
        filesystem_=std::move(fs);return true;
    }
    // Only read-only metadata for the explicitly selected guest title.
    // This does not establish permissions, validate tickets, launch
    // titles, or change the identity of a running guest.
    bool mount_title_metadata(std::optional<uint64_t> id) noexcept {
        if(id&&!*id)return false;
        for(auto dev:fds_)if(dev==Device::Es)return false;
        title_metadata_=id;return true;
    }
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
            if(!request_span(address)||!disjoint_outstanding(address,64u))
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
    struct FileHandle {GuestFiles::Blob data;uint32_t offset=0;};
    std::array<FileHandle,DescriptorCount> files_{};
    std::shared_ptr<const GuestFiles> filesystem_;
    std::optional<uint64_t> title_metadata_;
    std::optional<Pending> pending_;
    std::array<Completion,8> replies_{};
    unsigned front_=0,count_=0;
    bool idle_=false;

    bool request_span(uint32_t a) const {
        return a!=0u&&(a&31u)==0u&&a<=0xffffffffu-63u&&mem_.valid(a,64);
    }
    static bool disjoint(uint32_t a,uint32_t n,uint32_t b,uint32_t m) {
        return uint64_t(a)+n<=b||uint64_t(b)+m<=a;
    }
    bool disjoint_outstanding(uint32_t a,uint32_t n) const {
        if(pending_&&(!disjoint(a,n,pending_->request,64u)||
                      !disjoint(a,n,pending_->output,4u)))return false;
        for(unsigned i=0;i<count_;++i)
            if(!disjoint(a,n,replies_[(front_+i)%replies_.size()].address,64u))return false;
        return true;
    }
    void enqueue(uint32_t a,uint32_t cmd,int32_t result){
        replies_[(front_+count_)%replies_.size()]={a,cmd,result};++count_;
    }
    std::optional<std::string> path(uint32_t a) const {
        std::array<char,64> s{};
        for(unsigned i=0;i<s.size();++i){
            if(a>0xffffffffu-i||!mem_.valid(a+i,1))return std::nullopt;
            s[i]=char(mem_.read8(a+i));
            if(!s[i])return std::string(s.data(),i);
        }
        return std::nullopt;
    }
    bool output_range(uint32_t request,uint32_t a,uint32_t n) const {
        return n==0u||(a!=0u&&uint64_t(a)+n<=0x100000000ull&&mem_.valid(a,n)&&
            disjoint(a,n,request,64u)&&disjoint_outstanding(a,n));
    }
    unsigned fs_handles() const {
        return unsigned(std::count(fds_.begin(),fds_.end(),Device::Fs)+
                        std::count(fds_.begin(),fds_.end(),Device::File));
    }
    int32_t file_request(const Request&r){
        auto& h=files_[r.fd];
        if(!h.data)return FsInvalid;
        const uint32_t size=uint32_t(h.data->size());
        if(r.command==Read){
            if(r.b>uint32_t(std::numeric_limits<int32_t>::max())||!output_range(r.address,r.a,r.b))
                return FsInvalid;
            const uint32_t count=std::min(r.b,size-h.offset);
            for(uint32_t i=0;i<count;++i)mem_.write8(r.a+i,h.data->at(h.offset+i));
            h.offset+=count;return int32_t(count);
        }
        if(r.command==Seek){
            if(r.b>2u)return FsInvalid;
            const int64_t base=r.b==0u?0:r.b==1u?h.offset:size;
            const int64_t next=base+int64_t(int32_t(r.a));
            if(next<0||next>size)return FsInvalid;
            h.offset=uint32_t(next);return int32_t(h.offset);
        }
        if(r.command==Write)return FsAccess;
        if(r.command==Ioctl&&r.a==FileStats){
            if(r.c!=0u||r.e<8u||!output_range(r.address,r.d,8u))return FsInvalid;
            mem_.write32(r.d,size);mem_.write32(r.d+4u,h.offset);return 0;
        }
        return FsInvalid;
    }
    // Public ES query ABI: https://wiibrew.org/wiki//dev/es
    // Implement only GetTitleId and GetTitleDir. No other ES commands.
    bool es_range(const Request&r,uint32_t a,uint32_t n) const {
        return n&&output_range(r.address,a,n);
    }
    int32_t title_request(const Request&r){
        if(!title_metadata_||r.command!=Ioctlv)return EsInvalid;
        const bool id=r.a==EsGetTitleId&&r.b==0u&&r.c==1u;
        const bool dir=r.a==EsGetDataDir&&r.b==1u&&r.c==1u;
        if(!id&&!dir)return EsInvalid;
        const uint32_t table_size=id?8u:16u;
        if((r.d&3u)||!es_range(r,r.d,table_size))return EsInvalid;
        const uint32_t input=dir?mem_.read32(r.d):0u;
        const uint32_t input_size=dir?mem_.read32(r.d+4u):0u;
        const uint32_t output=mem_.read32(r.d+(dir?8u:0u));
        const uint32_t output_size=mem_.read32(r.d+(dir?12u:4u));
        constexpr std::string_view path_template="/title/00000000/00000000/data";
        constexpr uint32_t path_size=uint32_t(path_template.size()+1u);
        if(output_size<(id?8u:path_size)||!es_range(r,output,output_size)||
           !disjoint(output,output_size,r.d,table_size))return EsInvalid;
        if(dir){
            if(input_size!=8u||!es_range(r,input,input_size)||
               !disjoint(input,input_size,r.d,table_size)||
               !disjoint(input,input_size,output,output_size))return EsInvalid;
            const uint64_t requested=uint64_t(mem_.read32(input))<<32|mem_.read32(input+4u);
            if(requested!=*title_metadata_)return EsInvalid;
            std::array<char,path_size> path{};
            std::copy(path_template.begin(),path_template.end(),path.begin());
            constexpr std::string_view digits="0123456789abcdef";
            for(unsigned i=0;i<16u;++i){
                const unsigned index=i<8u?7u+i:8u+i;
                path[index]=digits[(*title_metadata_>>(60u-4u*i))&15u];
            }
            for(unsigned i=0;i<path.size();++i)mem_.write8(output+i,uint8_t(path[i]));
        }else{
            mem_.write32(output,uint32_t(*title_metadata_>>32));
            mem_.write32(output+4u,uint32_t(*title_metadata_));
        }
        return 0;
    }
    bool output_ok(const Request&r) const {
        return r.e>=4u&&output_range(r.address,r.d,4u);
    }
    std::optional<int32_t> dispatch(const Request&r){
        if(r.command==Open){
            if(r.b>3u||r.a==0u)return Invalid;
            const auto p=path(r.a);
            if(!p)return NotFound;
            Device dev=Device::None;GuestFiles::Blob data;
            if(*p=="/dev/stm/immediate")dev=Device::Immediate;
            else if(*p=="/dev/stm/eventhook")dev=Device::Event;
            else if(filesystem_&&*p=="/dev/fs")dev=Device::Fs;
            else if(title_metadata_&&*p=="/dev/es"&&r.b==0u)dev=Device::Es;
            else if(filesystem_&&!p->starts_with("/dev/")){
                if(!GuestFiles::valid_path(*p))return FsInvalid;
                if(r.b!=1u)return FsAccess;
                data=filesystem_->find(*p);
                if(!data)return FsMissing;
                dev=Device::File;
            }
            if(dev==Device::None)return NotFound;
            const bool fs=dev==Device::Fs||dev==Device::File;
            if(fs&&fs_handles()>=16u)return FsFull;
            for(unsigned i=0;i<fds_.size();++i)if(fds_[i]==Device::None){
                fds_[i]=dev;files_[i]={std::move(data),0u};return int32_t(i);
            }
            return QueueFull;
        }
        if(r.fd>=fds_.size()||fds_[r.fd]==Device::None)return Invalid;
        const Device dev=fds_[r.fd];
        if(r.command==Close){
            if(pending_&&pending_->fd==r.fd)return Invalid;
            fds_[r.fd]=Device::None;files_[r.fd]={};return 0;
        }
        if(dev==Device::File)return file_request(r);
        if(dev==Device::Es)return title_request(r);
        // Control device is real but unsupported operations remain errors.
        // Never report successful writes, format, mutation, or directory I/O.
        if(dev==Device::Fs)return r.command==Write?FsAccess:FsInvalid;
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
