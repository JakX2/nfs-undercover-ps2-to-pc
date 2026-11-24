#pragma once
#include "wii_audio_reset_witness_v556.h"
namespace undercover::wii {
struct DspStageExpectations {
    std::array<VectorEdge,4> edges;
    std::array<uint8_t,128> image;
    uint32_t syscall_word;
};
// Read-only proof of original firmware staging, not DSP execution.
// Private expected bytes are generated from the authenticated owner DOL.
class DspStageWitness {
public:
    static constexpr uint32_t Source=0x8060bcc8u,Staging=0x81000000u,Syscall=0x805222e8u;
    explicit DspStageWitness(const DspStageExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.lr!=AudioResetWitness::Return||
           c.gpr[1]!=ThreadInitWitness::StackTop-104u||(c.msr&0x8000u)||
           !equal(c,AudioResetWitness::Return,e_.edges[0].branch_word)||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread)||
           !mapped(c,Source,128)||!mapped(c,Staging-1,130))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        const uint32_t hi=c.mmu.read32(r13_-3472u);
        if(hi!=0x81700000u)return fail(1); // explicit cold arena profile
        backup_=hi-128u;
        if(!mapped(c,backup_-1,130))return fail(1);
        for(unsigned i=0;i<128;++i){
            if(c.mmu.read8(Source+i)!=e_.image[i])return fail(1);
            original_[i]=c.mmu.read8(Staging+i);
        }
        guards_={c.mmu.read8(Staging-1),c.mmu.read8(Staging+128),
                 c.mmu.read8(backup_-1),c.mmu.read8(backup_+128)};
        flush_=c.guest_flush_count;
        if(uint64_t(flush_)+4>c.guest_flush_lines.size())return fail(1);
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>5||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>1000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread)||!equal(c,r13_-3472u,backup_+128)||
           !preserved(c))return fail(2);
        if(stage_==5){
            // The injected trace sits at the authenticated SC label before
            // the emitter updates PC. Do not manufacture that PC in the CPU.
            if(addr!=Syscall||c.lr!=e_.edges[3].lr||c.gpr[1]!=sp_||
               !equal(c,Syscall,e_.syscall_word)||!bytes(c,Staging,e_.image)||
               !bytes(c,backup_,original_)||uint64_t(c.guest_flush_count)!=uint64_t(flush_)+4)
                return fail(5);
            for(unsigned i=0;i<4;++i)if(c.guest_flush_lines[flush_+i]!=Staging+32*i)return fail(5);
            stage_=6;last_=c.inst_count;return true;
        }
        if(matches(c,e_.edges[stage_-1])){
            if(c.gpr[1]!=sp_||c.guest_flush_count!=flush_)return fail(3);
            switch(stage_){
            case 1:if(!bytes(c,Staging,original_))return fail(4);break;
            case 2:if(c.gpr[3]!=backup_||c.gpr[4]!=Staging||c.gpr[5]!=128||!bytes(c,Staging,original_))return fail(4);break;
            case 3:
                if(c.gpr[3]!=Staging||c.gpr[4]!=Source||c.gpr[5]!=128||
                   !bytes(c,backup_,original_)||!bytes(c,Staging,original_))return fail(4);
                break;
            case 4:if(c.gpr[3]!=Staging||c.gpr[4]!=128||!bytes(c,backup_,original_)||!bytes(c,Staging,e_.image))return fail(4);break;
            }
            ++stage_;last_=c.inst_count;return true;
        }
        // memcpy may use internal helper calls. Never accept a repeated or
        // out-of-order expected callsite as an unrelated helper.
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||++extra_>64)return fail(6);
        for(auto e:e_.edges)if(addr==e.pc&&c.lr==e.lr)return fail(6);
        if(stage_==1||stage_==4)return fail(6);
        return true;
    }
    // Optional continuation only after the independently authenticated
    // SC vector completed RFI and the original flush executed BLR.
    template<class Cpu>bool finish_sc(uint32_t addr,Cpu& c,uint32_t return_word){
        if(error_||stage_!=6||!c.is_running||addr!=e_.edges[3].lr||
           c.pc!=addr||c.lr!=addr||c.gpr[1]!=sp_||c.gpr[2]!=r2_||
           c.gpr[13]!=r13_||c.msr!=msr_||c.inst_count<last_||
           c.inst_count-last_!=9u||!equal(c,addr,return_word)||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread)||
           !equal(c,r13_-3472u,backup_+128)||!preserved(c)||
           !bytes(c,Staging,e_.image)||!bytes(c,backup_,original_)||
           uint64_t(c.guest_flush_count)!=uint64_t(flush_)+4)return fail(7);
        for(unsigned i=0;i<4;++i)if(c.guest_flush_lines[flush_+i]!=Staging+32*i)return fail(7);
        stage_=7;return true;
    }
    template<class Cpu>bool restore_ready(Cpu& c){
        if(error_||stage_!=7||!c.is_running||c.gpr[1]!=sp_||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread)||
           !equal(c,r13_-3472u,backup_+128)||!preserved(c)||
           !bytes(c,Staging,e_.image)||!bytes(c,backup_,original_)||
           uint64_t(c.guest_flush_count)!=uint64_t(flush_)+4)return fail(8);
        for(unsigned i=0;i<4;++i)if(c.guest_flush_lines[flush_+i]!=Staging+32*i)return fail(8);
        return true;
    }
    template<class Cpu>bool finish_restore(Cpu& c){
        if(error_||stage_!=7||!c.is_running||c.gpr[1]!=sp_+16u||
           c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_||
           !equal(c,0x800000e4u,ThreadInitWitness::Thread)||
           !equal(c,r13_-3472u,backup_+128)||!preserved(c)||
           !bytes(c,Staging,original_)||!bytes(c,backup_,original_)||
           uint64_t(c.guest_flush_count)!=uint64_t(flush_)+4)return fail(9);
        for(unsigned i=0;i<4;++i)if(c.guest_flush_lines[flush_+i]!=Staging+32*i)return fail(9);
        stage_=8;return true;
    }
private:
    DspStageExpectations e_;unsigned stage_=0,error_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,backup_=0,flush_=0;uint64_t last_=0;
    std::array<uint8_t,128> original_{};std::array<uint8_t,4> guards_{};
    bool fail(unsigned why){if(!error_)error_=why;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);
    }
    template<class Cpu>static bool bytes(Cpu& c,uint32_t addr,const std::array<uint8_t,128>& data){
        if(!mapped(c,addr,128))return false;
        for(unsigned i=0;i<data.size();++i)if(c.mmu.read8(addr+i)!=data[i])return false;
        return true;
    }
    template<class Cpu>bool preserved(Cpu& c){
        return bytes(c,Source,e_.image)&&c.mmu.read8(Staging-1)==guards_[0]&&
            c.mmu.read8(Staging+128)==guards_[1]&&c.mmu.read8(backup_-1)==guards_[2]&&c.mmu.read8(backup_+128)==guards_[3];
    }
};
}
