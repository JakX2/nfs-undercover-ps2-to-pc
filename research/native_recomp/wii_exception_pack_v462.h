#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
// Source bytes come from an authenticated original image at preparation
// time. No observer writes guest memory or substitutes an exception body.
struct ExceptionPackExpectations {
    std::array<uint32_t,15> offsets{};
    std::array<uint8_t,152> handler{};
    std::array<uint8_t,28> syscall{};
};
class ExceptionPackWitness {
public:
    explicit ExceptionPackWitness(const ExceptionPackExpectations& e):e_(e){}
    unsigned failure() const{return failure_;}
    unsigned phase() const{return phase_;}
    template<class Cpu> bool begin(Cpu& c){
        if(phase_||failure_||!c.is_running||c.pc!=0x80520bf4u||c.lr!=0x805208acu||
           c.gpr[13]!=Sda||(c.msr&0x8000u)||!mapped(c,Table,64)||!mapped(c,Source,152)||
           !mapped(c,SysSource,28)||!mapped(c,Dispatch,64))return fail(1);
        unsigned syscall_slots=0;
        for(unsigned i=0;i<15;++i){
            const uint32_t a=e_.offsets[i];
            if(a<0x100u||a>0x3000u-256u||(a&31u)||c.mmu.read32(Table+4u*i)!=a)return fail(2);
            for(unsigned j=0;j<i;++j)
                if(a<e_.offsets[j]+152u&&e_.offsets[j]<a+152u)return fail(2);
            if(a==0xc00u){++syscall_slots;sys_index_=i;}
            const uint32_t dest=0x80000000u+a;
            if(!mapped(c,dest-1u,154))return fail(2);
            guards_[i]={c.mmu.read8(dest-1u),c.mmu.read8(dest+152u)};
        }
        if(syscall_slots!=1||!mapped(c,SysDest,256))return fail(2);
        for(unsigned i=0;i<e_.handler.size();++i)if(c.mmu.read8(Source+i)!=e_.handler[i])return fail(3);
        for(unsigned i=0;i<e_.syscall.size();++i)if(c.mmu.read8(SysSource+i)!=e_.syscall[i])return fail(3);
        for(unsigned i=152;i<256;++i)sys_tail_[i-152]=c.mmu.read8(SysDest+i);
        table_guard_=c.mmu.read32(Dispatch+60u);table_source_guard_=c.mmu.read32(Table+60u);
        sp_=c.gpr[1];r2_=c.gpr[2];msr_=c.msr;last_=c.inst_count;
        for(unsigned i=0;i<12;++i)nv_[i]=c.gpr[20u+i];
        // Baseline for the install loop is recorded separately at first
        // original memcpy; debug initialization may perform other cache ops.
        phase_=1;return true;
    }
    template<class Cpu> bool first_copy(Cpu& c){
        if(phase_!=1||failure_||!c.is_running||c.pc!=Copy||c.lr!=0x80520d9cu||
           c.gpr[3]!=0x80000000u+e_.offsets[0]||c.gpr[4]!=Source||c.gpr[5]!=152u||
           c.gpr[29]!=0||c.gpr[1]!=sp_-64u||c.inst_count<=last_)return fail(4);
        f_=c.guest_flush_count;i_=c.guest_invalidate_count;s_=c.guest_sync_count;is_=c.guest_isync_count;
        if(uint64_t(f_)+83u>c.guest_flush_lines.size()||uint64_t(i_)+83u>c.guest_invalidate_lines.size())return fail(5);
        phase_=2;last_=c.inst_count;return true;
    }
    template<class Cpu> bool syscall_entry(Cpu& c){
        if(phase_!=2||failure_||!common(c)||c.pc!=SysInit||c.lr!=0x805208b0u)return fail(6);
        if(!image(c,false)||!events(c,false))return false;
        phase_=3;last_=c.inst_count;return true;
    }
    template<class Cpu> bool alarm_entry(Cpu& c){
        if(phase_!=3||failure_||!common(c)||c.pc!=Alarm||c.lr!=0x805208b4u)return fail(6);
        if(!image(c,true)||!events(c,true))return false;
        phase_=4;last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Table=0x8060bbe0u,Dispatch=0x80003000u,Source=0x80520ec0u;
    static constexpr uint32_t SysSource=0x805290a8u,SysDest=0x80000c00u;
    static constexpr uint32_t Copy=0x80004338u,SysInit=0x805290c8u,Alarm=0x805210ccu,Sda=0x8070e8e0u;
    ExceptionPackExpectations e_;unsigned failure_=0,phase_=0,sys_index_=0;
    uint32_t sp_=0,r2_=0,msr_=0,f_=0,i_=0,s_=0,is_=0,table_guard_=0,table_source_guard_=0;
    uint64_t last_=0;
    std::array<uint32_t,12> nv_{};
    std::array<std::array<uint8_t,2>,15> guards_{};
    std::array<uint8_t,104> sys_tail_{};
    bool fail(unsigned n){if(!failure_)failure_=n;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> bool common(Cpu& c) const{
        if(!c.is_running||c.inst_count<=last_||c.gpr[1]!=sp_||c.gpr[2]!=r2_||c.gpr[13]!=Sda||c.msr!=msr_)return false;
        for(unsigned i=0;i<12;++i)if(c.gpr[20u+i]!=nv_[i])return false;
        return true;
    }
    uint8_t expected(unsigned vector,unsigned byte,bool overlay) const{
        if(overlay&&vector==sys_index_&&byte<28u)return e_.syscall[byte];
        if(byte>=0x58u&&byte<0x5cu)return byte==0x58u?0x60u:0u;
        if(byte==0x6bu)return uint8_t(e_.handler[byte]|vector);
        return e_.handler[byte];
    }
    template<class Cpu> bool image(Cpu& c,bool overlay){
        if(!mapped(c,Table,64)||!mapped(c,Dispatch,64)||!mapped(c,Sda-3552u,4)||
           c.mmu.read32(Sda-3552u)!=Dispatch||c.mmu.read32(Dispatch+60u)!=table_guard_||
           c.mmu.read32(Table+60u)!=table_source_guard_)return fail(7);
        for(unsigned i=0;i<15;++i){
            const uint32_t dest=0x80000000u+e_.offsets[i];
            if(c.mmu.read32(Table+4u*i)!=e_.offsets[i]||c.mmu.read32(Dispatch+4u*i)!=0x80520f5cu||
               !mapped(c,dest-1u,154)||c.mmu.read8(dest-1u)!=guards_[i][0]||
               c.mmu.read8(dest+152u)!=guards_[i][1])return fail(7);
            for(unsigned n=0;n<152;++n)if(c.mmu.read8(dest+n)!=expected(i,n,overlay))return fail(8);
        }
        if(!mapped(c,Source,152)||!mapped(c,SysSource,28)||!mapped(c,SysDest,256))return fail(9);
        for(unsigned n=0;n<152;++n)if(c.mmu.read8(Source+n)!=expected(0,n,false))return fail(9);
        for(unsigned n=0;n<28;++n)if(c.mmu.read8(SysSource+n)!=e_.syscall[n])return fail(9);
        for(unsigned n=152;n<256;++n)if(c.mmu.read8(SysDest+n)!=sys_tail_[n-152])return fail(9);
        return true;
    }
    template<class Cpu> bool events(Cpu& c,bool overlay){
        const unsigned total=overlay?83u:75u;
        if(uint64_t(c.guest_flush_count)!=uint64_t(f_)+total||uint64_t(c.guest_invalidate_count)!=uint64_t(i_)+total||
           uint64_t(c.guest_sync_count)!=uint64_t(s_)+(overlay?32u:30u)||
           uint64_t(c.guest_isync_count)!=uint64_t(is_)+(overlay?16u:15u))return fail(10);
        for(unsigned n=0;n<total;++n){
            const uint32_t addr=n<75u?0x80000000u+e_.offsets[n/5u]+32u*(n%5u):SysDest+32u*(n-75u);
            if(c.guest_flush_lines[f_+n]!=addr||c.guest_invalidate_lines[i_+n]!=addr)return fail(10);
        }
        return true;
    }
};
}
